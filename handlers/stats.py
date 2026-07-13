"""/stats, /profile, /top."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from database.models import Progress, User, UserAchievement, Word
from keyboards.kb import LEVEL_LABELS, LEVELS, menu_btn
from services.achievements import ACHIEVEMENTS
from services.srs import LEARNED_STAGE

router = Router()

MODE_LABELS = {
    "normal": "▶️ Обычный",
    "new": "📚 Новые слова",
    "review": "🔁 Повторение",
    "random": "🎲 Случайные",
    "fav": "⭐ Избранное",
    "quick": "⚡ Быстрое",
}


def _bar(done: int, total: int, width: int = 10) -> str:
    if total <= 0:
        return "▁" * width
    filled = round(width * min(done, total) / total)
    return "▰" * filled + "▱" * (width - filled)


async def _learned(session, user_id: int, level: str | None = None) -> int:
    q = (
        select(func.count())
        .select_from(Progress)
        .join(Word, Word.id == Progress.word_id)
        .where(Progress.user_id == user_id, Progress.stage >= LEARNED_STAGE)
    )
    if level:
        q = q.where(Word.level == level)
    return (await session.execute(q)).scalar() or 0


async def stats_text(session, user) -> str:
    total_words = (await session.execute(select(func.count()).select_from(Word))).scalar() or 0
    learned = await _learned(session, user.id)
    answers = user.correct_total + user.wrong_total
    accuracy = round(100 * user.correct_total / answers) if answers else 0

    lines = [
        "📈 <b>Статистика</b>",
        "",
        f"📚 Изучено слов: <b>{learned}</b> из {total_words}",
        f"✅ Правильных: <b>{user.correct_total}</b>",
        f"❌ Ошибок: <b>{user.wrong_total}</b>",
        f"🎯 Точность: <b>{accuracy}%</b>",
        f"🔥 Серия сейчас: <b>{user.combo}</b> (рекорд: {user.best_combo})",
        f"🗓 Сегодня: <b>{user.words_today}</b> / {user.daily_goal} {_bar(user.words_today, user.daily_goal)}",
        f"⏳ Осталось выучить: <b>{max(0, total_words - learned)}</b>",
        "",
        "<b>Прогресс по категориям:</b>",
    ]
    for lvl in LEVELS:
        total_l = (await session.execute(select(func.count()).select_from(Word).where(Word.level == lvl))).scalar() or 0
        if not total_l:
            continue
        learned_l = await _learned(session, user.id, lvl)
        lines.append(f"{LEVEL_LABELS.get(lvl, lvl)}: {_bar(learned_l, total_l)} {learned_l}/{total_l}")
    return "\n".join(lines)


async def profile_text(session, user) -> str:
    learned = await _learned(session, user.id)
    ach_codes = (await session.execute(select(UserAchievement.code).where(UserAchievement.user_id == user.id))).scalars().all()
    ach = " ".join(ACHIEVEMENTS[c][0] for c in ach_codes if c in ACHIEVEMENTS) or "пока нет"
    lvl = LEVEL_LABELS.get(user.level, LEVEL_LABELS["all"])
    reg = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    return "\n".join(
        [
            f"👤 <b>{user.first_name or 'Профиль'}</b>",
            "",
            f"🎯 Категория: <b>{lvl}</b>",
            f"❤️ Любимый режим: <b>{MODE_LABELS.get(user.mode, user.mode)}</b>",
            f"📚 Изучено слов: <b>{learned}</b>",
            f"⭐ XP: <b>{user.xp}</b>",
            f"🔥 Дней подряд: <b>{user.streak}</b> (рекорд: {user.best_streak})",
            f"🏅 Достижения: {ach}",
            f"📅 Регистрация: {reg}",
        ]
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, session, user):
    await message.answer(await stats_text(session, user), reply_markup=menu_btn())


@router.callback_query(F.data == "show:stats")
async def cb_stats(cq: CallbackQuery, session, user):
    await cq.message.answer(await stats_text(session, user), reply_markup=menu_btn())
    await cq.answer()


@router.message(Command("profile"))
async def cmd_profile(message: Message, session, user):
    await message.answer(await profile_text(session, user), reply_markup=menu_btn())


@router.callback_query(F.data == "show:profile")
async def cb_profile(cq: CallbackQuery, session, user):
    await cq.message.answer(await profile_text(session, user), reply_markup=menu_btn())
    await cq.answer()


@router.message(Command("top"))
async def cmd_top(message: Message, session, user):
    rows = (await session.execute(select(User).order_by(User.xp.desc()).limit(10))).scalars().all()
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ игроков</b>", ""]
    for i, u in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i + 1}."
        name = u.first_name or u.username or f"id{u.id}"
        marker = " ⬅️" if u.id == user.id else ""
        lines.append(f"{medal} {name} — {u.xp} XP 🔥{u.streak}{marker}")
    await message.answer("\n".join(lines), reply_markup=menu_btn())
