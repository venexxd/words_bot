"""Начальное наполнение базы слов при первом запуске."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data.seed_words import SEED
from database.models import Word


async def seed_if_empty(session: AsyncSession) -> int:
    count = (await session.execute(select(func.count()).select_from(Word))).scalar()
    if count:
        return 0
    for i, item in enumerate(SEED, 1):
        session.add(
            Word(
                en=item["en"],
                ru=item["ru"],
                pos=item.get("pos"),
                level=item.get("level", "A1"),
                ipa=item.get("ipa"),
                example=item.get("example"),
                example_ru=item.get("example_ru"),
                synonyms=item.get("syn", []),
                forms=item.get("forms", []),
                topic=item.get("topic"),
                freq=item.get("freq", i),
            )
        )
    await session.commit()
    return len(SEED)
