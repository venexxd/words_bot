"""Автосид отключён: словарь загружается через админ-импорт (пришли боту .json/.csv файл)."""
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_if_empty(session: AsyncSession) -> int:
    return 0
