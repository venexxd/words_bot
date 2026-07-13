"""Конфигурация через переменные окружения."""
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Локально — SQLite, на сервере — PostgreSQL (Railway выдаёт DATABASE_URL автоматически)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///bot.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Telegram ID админов через запятую: ADMIN_IDS="123,456"
ADMIN_IDS = {int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x}

TIMEZONE = os.environ.get("BOT_TZ", "Europe/Moscow")
QUICK_SESSION_SIZE = 20
XP_CORRECT = 10
XP_GAME = 5
