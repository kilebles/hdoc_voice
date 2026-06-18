import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from settings import settings
from voicer_client import VoicerClient
from services.tts import TTSService
from services.queue import UserQueue
from middlewares.tts_service import ServicesMiddleware
from handlers.common import common_router
from handlers.tts import tts_router


def _setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - {message}",
        level="INFO",
        colorize=True,
    )

    class _InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno  # type: ignore[assignment]
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back  # type: ignore[assignment]
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[_InterceptHandler()], level=logging.INFO, force=True)


async def main() -> None:
    _setup_logging()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(common_router, tts_router)

    voicer = VoicerClient(settings)
    tts = TTSService(voicer)
    user_queue = UserQueue()

    dp.update.middleware(ServicesMiddleware(tts, user_queue))

    @dp.startup()
    async def on_startup() -> None:
        balance = tts.get_balance_text()
        logger.info("Bot started. Balance: {}", balance)

    @dp.shutdown()
    async def on_shutdown() -> None:
        voicer.close()
        logger.info("Bot stopped.")

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
