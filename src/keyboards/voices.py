from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.voices import VOICES


def voices_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=v.name, callback_data=f"voice:{v.id}")]
        for v in VOICES
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
