from aiogram.fsm.state import State, StatesGroup


class TTSForm(StatesGroup):
    choosing_voice = State()
    waiting_for_file = State()
