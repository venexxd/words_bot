"""Мини-игры: выбери перевод, собери слово, правда/ложь."""
import random

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Kb, Message

import config
from database.models import History, Word
from keyboards.kb import games_menu
from services import training as ts
from states import Games

router = Router()


def _again_kb(game: str) -> Kb:
    return Kb(inline_keyboard=[[Btn(text="▶️ Ещё", callback_data=f"game:{game}"), Btn(text="🏠 Меню", callback_data="menu")]])


async def _reward(session, user, word_id: int, ok: bool):
    progress = await ts.get_progress(session, user.id, word_id)
    if ok:
        progress.correct += 1
        user.correct_total += 1
        user.combo += 1
        user.best_combo = max(user.best_combo, user.combo)
        user.xp += config.XP_GAME
    else:
        progress.wrong += 1
        user.wrong_total += 1
        user.combo = 0
    session.add(History(user_id=user.id, word_id=word_id, correct=ok))
    await session.commit()


@router.callback_query(F.data == "games")
async def cb_games(cq: CallbackQuery, state: FSMContext, session, user):
    await state.clear()
    await cq.message.edit_text("🎮 Мини-игры:", reply_markup=games_menu())
    await cq.answer()


# ---------- Выбери перевод ----------
@router.callback_query(F.data == "game:mc")
async def game_mc(cq: CallbackQuery, session, user):
    word = await ts.pick_word(session, user, "random")
    if word is None:
        await cq.answer("Слов нет", show_alert=True)
        return
    others = await ts.pick_words(session, user, 3, exclude_id=word.id)
    options = [((w.ru or ["?"])[0], False) for w in others]
    options.append(((word.ru or ["?"])[0], True))
    random.shuffle(options)
    kb = Kb(
        inline_keyboard=[[Btn(text=text, callback_data=f"mc:{word.id}:{1 if right else 0}")] for text, right in options]
        + [[Btn(text="🏠 Меню", callback_data="menu")]]
    )
    await cq.message.answer(f"🏼 Как переводится <b>{word.en}</b>?", reply_markup=kb)
    await cq.answer()


@router.callback_query(F.data.startswith("mc:"))
async def mc_answer(cq: CallbackQuery, session, user):
    _, word_id, right = cq.data.split(":")
    word = await session.get(Word, int(word_id))
    ok = right == "1"
    await _reward(session, user, int(word_id), ok)
    head = f"✅ Верно! +{config.XP_GAME} XP" if ok else "❌ Неверно."
    await cq.message.edit_text(head + "\n\n" + ts.answer_card(word), reply_markup=_again_kb("mc"))
    await cq.answer()


# ---------- Собери слово ----------
@router.callback_query(F.data == "game:scr")
async def game_scr(cq: CallbackQuery, state: FSMContext, session, user):
    word = await ts.pick_word(session, user, "random")
    if word is None:
        await cq.answer("Слов нет", show_alert=True)
        return
    letters = list(word.en.replace(" ", "").upper())
    random.shuffle(letters)
    await state.set_state(Games.scramble)
    await state.update_data(scr_word_id=word.id)
    await cq.message.answer(
        f"🧩 Собери слово: <b>{' '.join(letters)}</b>\n"
        f"💡 Подсказка: {(word.ru or ['?'])[0]}\n\n"
        "✏️ Напиши слово:"
    )
    await cq.answer()


@router.message(Games.scramble, F.text)
async def scr_answer(message: Message, state: FSMContext, session, user):
    data = await state.get_data()
    word = await session.get(Word, data.get("scr_word_id"))
    await state.clear()
    if word is None:
        return
    ok = message.text.strip().lower().replace(" ", "") == word.en.lower().replace(" ", "")
    await _reward(session, user, word.id, ok)
    head = f"✅ Верно! +{config.XP_GAME} XP" if ok else "❌ Не совсем."
    await message.answer(head + "\n\n" + ts.answer_card(word), reply_markup=_again_kb("scr"))


# ---------- Правда/ложь ----------
@router.callback_query(F.data == "game:tf")
async def game_tf(cq: CallbackQuery, session, user):
    word = await ts.pick_word(session, user, "random")
    if word is None:
        await cq.answer("Слов нет", show_alert=True)
        return
    truth = random.random() < 0.5
    if truth:
        shown = (word.ru or ["?"])[0]
    else:
        other = await ts.pick_words(session, user, 1, exclude_id=word.id)
        shown = (other[0].ru or ["?"])[0] if other else (word.ru or ["?"])[0]
        truth = shown in (word.ru or [])
    kb = Kb(
        inline_keyboard=[
            [
                Btn(text="✅ Верно", callback_data=f"tf:1:{1 if truth else 0}:{word.id}"),
                Btn(text="❌ Неверно", callback_data=f"tf:0:{1 if truth else 0}:{word.id}"),
            ],
            [Btn(text="🏠 Меню", callback_data="menu")],
        ]
    )
    await cq.message.answer(f"🤔 <b>{word.en}</b> = <b>{shown}</b>?", reply_markup=kb)
    await cq.answer()


@router.callback_query(F.data.startswith("tf:"))
async def tf_answer(cq: CallbackQuery, session, user):
    _, claim, truth, word_id = cq.data.split(":")
    word = await session.get(Word, int(word_id))
    ok = claim == truth
    await _reward(session, user, int(word_id), ok)
    head = f"✅ Верно! +{config.XP_GAME} XP" if ok else "❌ Неверно."
    await cq.message.edit_text(head + "\n\n" + ts.answer_card(word), reply_markup=_again_kb("tf"))
    await cq.answer()
