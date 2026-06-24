from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.services.queue import UserQueue
from src.services.tts import TTSService


class ServicesMiddleware(BaseMiddleware):
    def __init__(self, tts_service: TTSService, user_queue: UserQueue) -> None:
        self.tts_service = tts_service
        self.user_queue = user_queue

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["tts_service"] = self.tts_service
        data["user_queue"] = self.user_queue
        return await handler(event, data)
