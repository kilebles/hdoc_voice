from aiogram import Router

from .common import router as common_router
from .tts import router as tts_router


def get_routers() -> list[Router]:
    return [common_router, tts_router]
