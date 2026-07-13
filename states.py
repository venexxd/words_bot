from aiogram.fsm.state import State, StatesGroup


class Training(StatesGroup):
    answering = State()


class Games(StatesGroup):
    scramble = State()


class SettingsForm(StatesGroup):
    reminder_time = State()
