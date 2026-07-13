"""Достижения. Проверяются после каждого ответа."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Progress, User, UserAchievement, Word
from services.srs import LEARNED_STAGE

ACHIEVEMENTS: dict[str, tuple[str, str]] = {
    "first": ("🌟", "Первый правильный ответ"),
    "correct_100": ("💯", "100 правильных ответов"),
    "correct_1000": ("🏆", "1000 правильных ответов"),
    "learned_100": ("📚", "Выучено 100 слов"),
    "learned_1000": ("🎓", "Выучено 1000 слов"),
    "streak_7": ("🔥", "7 дней подряд"),
    "streak_30": ("⚡", "30 дней подряд"),
    "combo_25": ("🎯", "25 правильных подряд"),
    "combo_100": ("🚀", "100 правильных подряд"),
    "level_a1": ("🥇", "Весь Топ-1000"),
    "level_a2": ("🥈", "Все популярные слова"),
}


async def _learned_count(session: AsyncSession, user_id: int, level: str | None = None) -> int:
    q = (
        select(func.count())
        .select_from(Progress)
        .join(Word, Word.id == Progress.word_id)
        .where(Progress.user_id == user_id, Progress.stage >= LEARNED_STAGE)
    )
    if level:
        q = q.where(Word.level == level)
    return (await session.execute(q)).scalar() or 0


async def _total_words(session: AsyncSession, level: str) -> int:
    q = select(func.count()).select_from(Word).where(Word.level == level)
    return (await session.execute(q)).scalar() or 0


async def check_achievements(session: AsyncSession, user: User) -> list[str]:
    """Возвращает список новых кодов достижений."""
    have = set(
        (await session.execute(select(UserAchievement.code).where(UserAchievement.user_id == user.id)))
        .scalars()
        .all()
    )
    new: list[str] = []

    def want(code: str, condition: bool):
        if condition and code not in have:
            new.append(code)

    want("first", user.correct_total >= 1)
    want("correct_100", user.correct_total >= 100)
    want("correct_1000", user.correct_total >= 1000)
    want("streak_7", user.streak >= 7)
    want("streak_30", user.streak >= 30)
    want("combo_25", user.best_combo >= 25)
    want("combo_100", user.best_combo >= 100)

    learned = await _learned_count(session, user.id)
    want("learned_100", learned >= 100)
    want("learned_1000", learned >= 1000)

    for code, level in (("level_a1", "P1"), ("level_a2", "P2")):
        if code in have:
            continue
        total = await _total_words(session, level)
        if total and await _learned_count(session, user.id, level) >= total:
            new.append(code)

    for code in new:
        session.add(UserAchievement(user_id=user.id, code=code))
    return new


def format_achievement(code: str) -> str:
    emoji, title = ACHIEVEMENTS.get(code, ("🏅", code))
    return f"{emoji} <b>Достижение:</b> {title}"
