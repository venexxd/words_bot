"""Настройки: направление, уровень, цель, напоминания."""
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.kb import goal_kb, levels_kb, settings_menu
from states import SettingsForm

router = Router()

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


@router.callback_query(F.data == "settings")
async def cb_settings(cq: CallbackQuery, state: FSMContext, session, user):
    await state.clear()
    await cq.message.edit_text("⚙️ Настройки:", reply_markup=settings_menu(user))
    await cq.answer()


@router.callback_query(F.data == "set:direction")
async def set_direction(cq: CallbackQuery, session, user):
    user.direction = "ru_en" if user.direction == "en_ru" else "en_ru"
    await session.commit()
    await cq.message.edit_reply_markup(reply_markup=settings_menu(user))
    await cq.answer("Направление изменено")


@router.callback_query(F.data == "set:level")
async def set_level_menu(cq: CallbackQuery):
    await cq.message.edit_text("🎓 Выбери уровень:", reply_markup=levels_kb())
    await cq.answer()


@router.callback_query(F.data == "set:goal")
async def set_goal_menu(cq: CallbackQuery):
    await cq.message.edit_text("🎯 Сколько слов в день?", reply_markup=goal_kb())
    await cq.answer()


@router.callback_query(F.data.startswith("goal:"))
async def set_goal(cq: CallbackQuery, session, user):
    user.daily_goal = int(cq.data.split(":")[1])
    await session.commit()
    await cq.message.edit_text(f"🎯 Цель: <b>{user.daily_goal}</b> слов в день ✅", reply_markup=settings_menu(user))
    await cq.answer()


@router.callback_query(F.data == "set:reminder")
async def set_reminder(cq: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsForm.reminder_time)
    await cq.message.answer("⏰ Напиши время в формате <b>ЧЧ:ММ</b> (например 19:00)\nили <b>выкл</b>, чтобы отключить.")
    await cq.answer()


@router.message(SettingsForm.reminder_time, F.text)
async def save_reminder(message: Message, state: FSMContext, session, user):
    text = message.text.strip().lower()
    if text in ("выкл", "off", "нет"):
        user.reminder_time = None
        await session.commit()
        await state.clear()
        await message.answer("🔕 Напоминания отключены.", reply_markup=settings_menu(user))
        return
    m = TIME_RE.match(text)
    if not m:
        await message.answer("⚠️ Неверный формат. Пример: <b>19:00</b>")
        return
    user.reminder_time = f"{int(m.group(1)):02d}:{m.group(2)}"
    await session.commit()
    await state.clear()
    await message.answer(f"⏰ Буду напоминать каждый день в <b>{user.reminder_time}</b> ✅", reply_markup=settings_menu(user))
