from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from services.tts import TTSService
from services.queue import UserQueue


class ServicesMiddleware(BaseMiddleware):
    def __init__(self, tts: TTSService, user_queue: UserQueue) -> None:
        self.tts = tts
        self.user_queue = user_queue

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["tts"] = self.tts
        data["user_queue"] = self.user_queue
        return await handler(event, data)
