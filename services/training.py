"""Выбор слов для тренировки в зависимости от режима."""
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Progress, User, Word


def _level_filter(user: User):
    # "all" или старое значение (A1..C2) — без фильтра
    if user.level == "all" or user.level not in ("P1", "P2", "P3", "P4", "P5"):
        return []
    return [Word.level == user.level]


async def pick_word(session: AsyncSession, user: User, mode: str) -> Word | None:
    now = datetime.utcnow()

    if mode == "new":
        seen = select(Progress.word_id).where(Progress.user_id == user.id)
        q = select(Word).where(Word.id.not_in(seen), *_level_filter(user))
    elif mode == "review":
        q = (
            select(Word)
            .join(Progress, Progress.word_id == Word.id)
            .where(
                Progress.user_id == user.id,
                or_(Progress.wrong > Progress.correct, Progress.next_review <= now),
            )
        )
    elif mode == "fav":
        q = (
            select(Word)
            .join(Progress, Progress.word_id == Word.id)
            .where(Progress.user_id == user.id, Progress.favorite.is_(True))
        )
    elif mode in ("random", "quick"):
        q = select(Word)
    else:  # normal / topic
        q = select(Word).where(*_level_filter(user))
        if user.topic:
            q = q.where(Word.topic == user.topic)
        # Адаптивность: сначала слова, готовые к повторению по SRS
        due = (
            q.join(Progress, Progress.word_id == Word.id)
            .where(Progress.user_id == user.id, Progress.next_review <= now)
            .order_by(func.random())
            .limit(1)
        )
        word = (await session.execute(due)).scalars().first()
        if word:
            return word

    q = q.order_by(func.random()).limit(1)
    return (await session.execute(q)).scalars().first()


async def pick_words(session: AsyncSession, user: User, count: int, exclude_id: int | None = None) -> list[Word]:
    """Несколько случайных слов (для вариантов в мини-играх)."""
    q = select(Word)
    if exclude_id:
        q = q.where(Word.id != exclude_id)
    q = q.order_by(func.random()).limit(count)
    return list((await session.execute(q)).scalars().all())


async def get_progress(session: AsyncSession, user_id: int, word_id: int) -> Progress:
    q = select(Progress).where(Progress.user_id == user_id, Progress.word_id == word_id)
    p = (await session.execute(q)).scalars().first()
    if not p:
        p = Progress(user_id=user_id, word_id=word_id, correct=0, wrong=0, stage=0, favorite=False)
        session.add(p)
    return p


def expected_variants(word: Word, direction: str) -> list[str]:
    if direction == "en_ru":
        return list(word.ru or [])
    return [word.en] + list(word.synonyms or []) + list(word.forms or [])


def question_text(word: Word, direction: str) -> str:
    if direction == "en_ru":
        ipa = f"  <i>[{word.ipa}]</i>" if word.ipa else ""
        return f"🇬🇧 <b>{word.en}</b>{ipa}\n\n✏️ Напишите перевод на русском:"
    return f"🇷🇺 <b>{(word.ru or ['?'])[0]}</b>\n\n✏️ Напишите перевод на английском:"


def answer_card(word: Word) -> str:
    """Карточка слова после ответа."""
    parts = [f"<b>{word.en}</b>" + (f" <i>[{word.ipa}]</i>" if word.ipa else "") + f" — {', '.join(word.ru or [])}"]
    if word.pos:
        parts[0] += f"  <i>({word.pos})</i>"
    if word.example:
        ex = f"💬 <i>{word.example}</i>"
        if word.example_ru:
            ex += f"\n  <i>{word.example_ru}</i>"
        parts.append(ex)
    if word.synonyms:
        parts.append(f"🔗 Синонимы: {', '.join(word.synonyms)}")
    return "\n".join(parts)
