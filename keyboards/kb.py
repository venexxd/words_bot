"""Все InlineKeyboard-меню бота."""
from aiogram.types import InlineKeyboardButton as Btn
from aiogram.types import InlineKeyboardMarkup as Kb

# Категории по популярности слов (частотный ранг)
LEVELS = ["P1", "P2", "P3", "P4", "P5"]

LEVEL_LABELS = {
    "P1": "🔥 Топ-1000",
    "P2": "⭐ Популярные (1000–2500)",
    "P3": "📗 Средние (2500–5000)",
    "P4": "📘 Редкие (5000–7500)",
    "P5": "💎 Очень редкие (7500+)",
    "all": "🌐 Все слова",
}


def levels_kb() -> Kb:
    rows = [[Btn(text=LEVEL_LABELS[lvl], callback_data=f"lvl:{lvl}")] for lvl in LEVELS]
    rows.append([Btn(text=LEVEL_LABELS["all"], callback_data="lvl:all")])
    return Kb(inline_keyboard=rows)


def main_menu() -> Kb:
    return Kb(
        inline_keyboard=[
            [Btn(text="📚 Новые слова", callback_data="mode:new"), Btn(text="🔁 Повторение", callback_data="mode:review")],
            [Btn(text="▶️ Обычный", callback_data="mode:normal"), Btn(text="🎲 Случайные", callback_data="mode:random")],
            [Btn(text="⭐ Избранное", callback_data="mode:fav"), Btn(text="⚡ Быстрое ×20", callback_data="mode:quick")],
            [Btn(text="🎮 Игры", callback_data="games"), Btn(text="🗂 Темы", callback_data="topics")],
            [Btn(text="📈 Статистика", callback_data="show:stats"), Btn(text="👤 Профиль", callback_data="show:profile")],
            [Btn(text="⚙️ Настройки", callback_data="settings")],
        ]
    )


def question_kb(word_id: int) -> Kb:
    return Kb(
        inline_keyboard=[
            [
                Btn(text="⭐", callback_data=f"act:fav:{word_id}"),
                Btn(text="⏭ Пропустить", callback_data="act:skip"),
            ],
            [Btn(text="🏠 Меню", callback_data="menu")],
        ]
    )


def games_menu() -> Kb:
    return Kb(
        inline_keyboard=[
            [Btn(text="🏼 Выбери перевод", callback_data="game:mc")],
            [Btn(text="🧩 Собери слово", callback_data="game:scr")],
            [Btn(text="✅ Правда/ложь", callback_data="game:tf")],
            [Btn(text="🏠 Меню", callback_data="menu")],
        ]
    )


def settings_menu(user) -> Kb:
    d = "🇬🇧→🇷🇺" if user.direction == "en_ru" else "🇷🇺→🇬🇧"
    rem = user.reminder_time or "выкл"
    return Kb(
        inline_keyboard=[
            [Btn(text=f"Направление: {d}", callback_data="set:direction")],
            [Btn(text=f"Категория: {LEVEL_LABELS.get(user.level, LEVEL_LABELS['all'])}", callback_data="set:level")],
            [Btn(text=f"🎯 Цель: {user.daily_goal} слов/день", callback_data="set:goal")],
            [Btn(text=f"⏰ Напоминание: {rem}", callback_data="set:reminder")],
            [Btn(text="🏠 Меню", callback_data="menu")],
        ]
    )


def goal_kb() -> Kb:
    return Kb(
        inline_keyboard=[
            [Btn(text=str(n), callback_data=f"goal:{n}") for n in (10, 20, 30)],
            [Btn(text=str(n), callback_data=f"goal:{n}") for n in (50, 100)],
        ]
    )


def topics_kb(topics: list[str]) -> Kb:
    rows = [[Btn(text=t, callback_data=f"topic:{t}") for t in topics[i : i + 2]] for i in range(0, len(topics), 2)]
    rows.append([Btn(text="❌ Без темы", callback_data="topic:-")])
    rows.append([Btn(text="🏠 Меню", callback_data="menu")])
    return Kb(inline_keyboard=rows)


def menu_btn() -> Kb:
    return Kb(inline_keyboard=[[Btn(text="🏠 Меню", callback_data="menu")]])
