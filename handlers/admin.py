"""Админ-панель: добавление/удаление слов, импорт CSV/JSON.

Доступ только для ID из переменной окружения ADMIN_IDS.

CSV-колонки: en,ru,pos,level,topic,example,example_ru,ipa,synonyms,forms,freq
(ru, synonyms, forms — варианты через |)
JSON — список объектов с теми же полями (ru/synonyms/forms — массивы).
"""
import csv
import io
import json

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

import config
from database.models import Word

router = Router()


def _is_admin(message: Message) -> bool:
    return message.from_user.id in config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, session, user):
    if not _is_admin(message):
        return
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "➕ <code>/addword en | перевод1, перевод2 | pos | level | тема | пример</code>\n"
        "🗑 <code>/delword слово</code>\n"
        "📥 Пришли файл <b>.csv</b> или <b>.json</b> — импортирую слова (существующие обновлю).\n"
        "Формат — в README."
    )


@router.message(Command("addword"))
async def cmd_addword(message: Message, session, user):
    if not _is_admin(message):
        return
    payload = (message.text or "").removeprefix("/addword").strip()
    parts = [p.strip() for p in payload.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        await message.answer("Формат: <code>/addword en | перевод1, перевод2 | pos | level | тема | пример</code>")
        return
    en = parts[0].lower()
    word = (await session.execute(select(Word).where(Word.en == en))).scalars().first()
    if word is None:
        word = Word(en=en, ru=[])
        session.add(word)
    word.ru = [x.strip() for x in parts[1].split(",") if x.strip()]
    if len(parts) > 2 and parts[2]:
        word.pos = parts[2]
    if len(parts) > 3 and parts[3]:
        word.level = parts[3].upper()
    if len(parts) > 4 and parts[4]:
        word.topic = parts[4]
    if len(parts) > 5 and parts[5]:
        word.example = parts[5]
    await session.commit()
    await message.answer(f"✅ Слово <b>{en}</b> сохранено.")


@router.message(Command("delword"))
async def cmd_delword(message: Message, session, user):
    if not _is_admin(message):
        return
    en = (message.text or "").removeprefix("/delword").strip().lower()
    word = (await session.execute(select(Word).where(Word.en == en))).scalars().first()
    if word is None:
        await message.answer("Слово не найдено.")
        return
    await session.delete(word)
    await session.commit()
    await message.answer(f"🗑 Слово <b>{en}</b> удалено.")


def _split(value: str | None) -> list[str]:
    return [x.strip() for x in (value or "").split("|") if x.strip()]


async def _upsert(session, item: dict) -> bool:
    en = str(item.get("en", "")).strip().lower()
    ru = item.get("ru") or []
    if isinstance(ru, str):
        ru = _split(ru)
    if not en or not ru:
        return False
    word = (await session.execute(select(Word).where(Word.en == en))).scalars().first()
    if word is None:
        word = Word(en=en, ru=[])
        session.add(word)
    word.ru = ru
    for field in ("pos", "level", "topic", "example", "example_ru", "ipa"):
        if item.get(field):
            setattr(word, field, str(item[field]).strip())
    for field, attr in (("synonyms", "synonyms"), ("forms", "forms")):
        v = item.get(field)
        if isinstance(v, str):
            v = _split(v)
        if v:
            setattr(word, attr, v)
    if item.get("freq"):
        try:
            word.freq = int(item["freq"])
        except (TypeError, ValueError):
            pass
    return True


@router.message(F.document)
async def import_file(message: Message, session, user):
    if not _is_admin(message):
        return
    name = (message.document.file_name or "").lower()
    if not (name.endswith(".csv") or name.endswith(".json")):
        return
    file = await message.bot.get_file(message.document.file_id)
    buf: io.BytesIO = await message.bot.download_file(file.file_path)
    raw = buf.read().decode("utf-8-sig")

    count = 0
    try:
        if name.endswith(".json"):
            items = json.loads(raw)
        else:
            items = list(csv.DictReader(io.StringIO(raw)))
        for item in items:
            if await _upsert(session, item):
                count += 1
        await session.commit()
    except Exception as e:
        await message.answer(f"⚠️ Ошибка импорта: {e}")
        return
    await message.answer(f"📥 Импортировано/обновлено слов: <b>{count}</b>")
