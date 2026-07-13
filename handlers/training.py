"""Тренировка: режимы, вопрос-ответ, избранное, темы."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

import config
from database.models import History, Word
from keyboards.kb import main_menu, question_kb, topics_kb
from services import training as ts
from services.achievements import check_achievements, format_achievement
from services.answer_checker import check_answer
from services.srs import apply_answer
from states import Training

router = Router()

EMPTY_TEXT = {
    "new": "🎉 Ты прошёл все слова этого уровня! Смени уровень в настройках.",
    "review": "🎉 Нечего повторять — ошибок нет!",
    "fav": "⭐ Избранное пусто. Добавляй слова кнопкой ⭐ во время тренировки.",
}


async def ask_question(target: Message, state: FSMContext, session, user, mode: str):
    word = await ts.pick_word(session, user, mode)
    if word is None:
        await state.clear()
        await target.answer(EMPTY_TEXT.get(mode, "🤔 Слов не нашлось."), reply_markup=main_menu())
        return
    await state.set_state(Training.answering)
    await state.update_data(word_id=word.id, mode=mode)
    await target.answer(ts.question_text(word, user.direction), reply_markup=question_kb(word.id))


@router.callback_query(F.data.startswith("mode:"))
async def cb_mode(cq: CallbackQuery, state: FSMContext, session, user):
    mode = cq.data.split(":")[1]
    user.mode = mode
    await session.commit()
    await state.clear()
    if mode == "quick":
        await state.update_data(quick_left=config.QUICK_SESSION_SIZE, quick_correct=0)
    await ask_question(cq.message, state, session, user, mode)
    await cq.answer()


@router.callback_query(F.data == "topics")
async def cb_topics(cq: CallbackQuery, session, user):
    rows = (await session.execute(select(Word.topic).where(Word.topic.is_not(None)).distinct().order_by(Word.topic))).all()
    await cq.message.edit_text("🗂 Выбери тему:", reply_markup=topics_kb([r[0] for r in rows]))
    await cq.answer()


@router.callback_query(F.data.startswith("topic:"))
async def cb_topic(cq: CallbackQuery, state: FSMContext, session, user):
    t = cq.data.split(":", 1)[1]
    user.topic = None if t == "-" else t
    user.mode = "normal"
    await session.commit()
    name = user.topic or "без темы"
    await cq.message.answer(f"🗂 Тема: <b>{name}</b>. Поехали! 🚀")
    await state.clear()
    await ask_question(cq.message, state, session, user, "normal")
    await cq.answer()


@router.message(Training.answering, F.text)
async def on_answer(message: Message, state: FSMContext, session, user):
    data = await state.get_data()
    word = await session.get(Word, data.get("word_id"))
    mode = data.get("mode", "normal")
    if word is None:
        await state.clear()
        await message.answer("🏠 Главное меню:", reply_markup=main_menu())
        return

    ok, typo = check_answer(message.text, ts.expected_variants(word, user.direction))

    progress = await ts.get_progress(session, user.id, word.id)
    apply_answer(progress, ok)
    session.add(History(user_id=user.id, word_id=word.id, correct=ok))
    user.words_today += 1
    if ok:
        user.correct_total += 1
        user.combo += 1
        user.best_combo = max(user.best_combo, user.combo)
        user.xp += config.XP_CORRECT
    else:
        user.wrong_total += 1
        user.combo = 0

    quick = mode == "quick"
    if ok:
        head = "✅ <b>Верно!</b>" + (" (почти — проверь написание 😉)" if typo else "") + f"  +{config.XP_CORRECT} XP"
        text = head + "\n\n" + ts.answer_card(word)
        if user.combo >= 5 and user.combo % 5 == 0:
            text += f"\n\n🔥 Серия: {user.combo} подряд!"
    else:
        text = "❌ <b>Неверно.</b>\n\n" + ts.answer_card(word) + "\n\n🔁 Покажу это слово ещё раз позже."
    await message.answer(text)

    if user.words_today == user.daily_goal:
        await message.answer(f"🎯 Цель дня выполнена: {user.daily_goal} слов! Так держать! 💪")

    for code in await check_achievements(session, user):
        await message.answer(format_achievement(code))

    await session.commit()

    if quick:
        left = data.get("quick_left", 1) - 1
        qc = data.get("quick_correct", 0) + (1 if ok else 0)
        if left <= 0:
            await state.clear()
            await message.answer(
                f"⚡ Готово! Результат: <b>{qc}/{config.QUICK_SESSION_SIZE}</b>",
                reply_markup=main_menu(),
            )
            return
        await state.update_data(quick_left=left, quick_correct=qc)

    await ask_question(message, state, session, user, mode)


@router.callback_query(F.data == "act:skip")
async def cb_skip(cq: CallbackQuery, state: FSMContext, session, user):
    data = await state.get_data()
    word_id = data.get("word_id")
    if word_id:
        word = await session.get(Word, word_id)
        if word:
            await cq.message.answer("⏭ " + ts.answer_card(word))
        await ask_question(cq.message, state, session, user, data.get("mode", "normal"))
    await cq.answer()


@router.callback_query(F.data.startswith("act:fav:"))
async def cb_fav(cq: CallbackQuery, session, user):
    word_id = int(cq.data.split(":")[2])
    progress = await ts.get_progress(session, user.id, word_id)
    progress.favorite = not progress.favorite
    await session.commit()
    await cq.answer("⭐ Добавлено в избранное!" if progress.favorite else "Убрано из избранного")
