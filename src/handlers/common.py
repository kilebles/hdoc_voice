from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from services.tts import TTSService
from states.tts import TTSForm

common_router = Router(name="common")


def _start_keyboard(templates: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=t.name, callback_data=f"tpl:{t.uuid}")]
        for t in templates
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, tts: TTSService) -> None:
    # Only reset the template-selection state, never touch an active generation
    current = await state.get_state()
    if current != TTSForm.waiting_for_file.state:
        await state.clear()

    templates = tts.get_templates()
    balance = tts.get_balance_text()

    if not templates:
        await message.answer("Нет доступных голосов.")
        return

    await state.set_state(TTSForm.choosing_template)
    await state.update_data(templates={str(t.uuid): t.name for t in templates})

    await message.answer(
        f"Баланс: {balance}\n\nВыберите голос:",
        reply_markup=_start_keyboard(templates),
    )
