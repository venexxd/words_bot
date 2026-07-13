"""Точка входа: инициализация БД, сид, роутеры, напоминания, polling."""
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

import config
from data.seed import seed_if_empty
from database.engine import Session, init_db
from database.models import User
from handlers import admin, games, settings, start, stats, training
from middlewares.db import DbMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bot")


async def reminders_job(bot: Bot):
    """Раз в минуту: шлём напоминание тем, у кого настало выбранное время."""
    now = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%H:%M")
    async with Session() as session:
        users = (await session.execute(select(User).where(User.reminder_time == now))).scalars().all()
    for u in users:
        try:
            await bot.send_message(u.id, "⏰ Пора повторить английские слова 🇬🇧\n\nЖми /menu и вперёд! 🚀")
        except Exception as e:
            logger.warning("Reminder failed for %s: %s", u.id, e)


async def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set")

    await init_db()
    async with Session() as session:
        added = await seed_if_empty(session)
        if added:
            logger.info("Seeded %s words", added)

    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.message.middleware(DbMiddleware())
    dp.callback_query.middleware(DbMiddleware())

    # Порядок важен: admin первым (перехват документов), затем остальные.
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(settings.router)
    dp.include_router(stats.router)
    dp.include_router(games.router)
    dp.include_router(training.router)

    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    scheduler.add_job(reminders_job, "cron", minute="*", args=[bot])
    scheduler.start()

    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
