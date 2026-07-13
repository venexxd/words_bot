"""/start, выбор уровня, главное меню."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from database.models import Word
from keyboards.kb import levels_kb, main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session, user):
    await state.clear()
    total = (await session.execute(select(func.count()).select_from(Word))).scalar()
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Я помогу тебе выучить английские слова — в базе <b>{total}</b> слов.\n\n"
        "🎓 Выбери свой уровень:",
        reply_markup=levels_kb(),
    )


@router.callback_query(F.data.startswith("lvl:"))
async def set_level(cq: CallbackQuery, state: FSMContext, session, user):
    user.level = cq.data.split(":")[1]
    await session.commit()
    lvl = "Все уровни" if user.level == "all" else user.level
    await cq.message.edit_text(f"Уровень: <b>{lvl}</b> ✅\n\nВыбери режим:", reply_markup=main_menu())
    await cq.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, session, user):
    await state.clear()
    await message.answer("🏠 Главное меню:", reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def cb_menu(cq: CallbackQuery, state: FSMContext, session, user):
    await state.clear()
    await cq.message.answer("🏠 Главное меню:", reply_markup=main_menu())
    await cq.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, session, user):
    await message.answer(
        "🤖 <b>Команды:</b>\n"
        "/menu — главное меню\n"
        "/stats — статистика\n"
        "/profile — профиль\n"
        "/top — лидерборд\n"
        "/start — сменить уровень"
    )
