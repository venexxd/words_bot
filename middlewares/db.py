"""Middleware: открывает сессию БД, создаёт/обновляет пользователя, считает streak."""
from datetime import date, timedelta
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.engine import Session
from database.models import User


class DbMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        async with Session() as session:
            user = None
            if tg_user:
                user = await session.get(User, tg_user.id)
                if user is None:
                    user = User(id=tg_user.id, username=tg_user.username, first_name=tg_user.first_name)
                    session.add(user)
                today = date.today()
                if user.last_active != today:
                    if user.last_active == today - timedelta(days=1):
                        user.streak = (user.streak or 0) + 1
                    else:
                        user.streak = 1
                    user.best_streak = max(user.best_streak or 0, user.streak)
                    user.last_active = today
                    user.words_today = 0
                await session.commit()
            data["session"] = session
            data["user"] = user
            return await handler(event, data)
