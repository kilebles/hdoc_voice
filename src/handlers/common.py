from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.keyboards.voices import voices_keyboard
from src.services.queue import UserQueue
from src.states.tts import TTSForm

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TTSForm.choosing_voice)
    await message.answer("Выберите голос:", reply_markup=voices_keyboard())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    await state.set_state(TTSForm.choosing_voice)
    if current is None:
        await message.answer("Нечего отменять.")
    else:
        await message.answer("Отменено.")
    await message.answer("Выберите голос:", reply_markup=voices_keyboard())


@router.message(Command("clearqueue"))
async def cmd_clearqueue(message: Message, user_queue: UserQueue) -> None:
    removed = user_queue.clear(message.from_user.id)
    if removed == 0:
        await message.answer("Очередь пуста.")
    else:
        await message.answer(f"Удалено из очереди: {removed}.")
