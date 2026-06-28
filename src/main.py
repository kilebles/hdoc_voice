import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger

from src.handlers import get_routers
from src.middlewares.services import ServicesMiddleware
from src.services.queue import UserQueue
from src.services.tts import TTSService
from src.settings import settings


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _setup_logging() -> None:
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    logger.add(
        "/app/logs/bot.log",
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        level="DEBUG",
    )


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start",      description="Начать / выбрать голос"),
            BotCommand(command="clearqueue", description="Очистить очередь"),
        ],
        scope=BotCommandScopeDefault(),
    )


async def on_startup(bot: Bot) -> None:
    await _set_commands(bot)
    logger.info("Bot started.")


async def on_shutdown(tts_service: TTSService) -> None:
    await tts_service.close()
    logger.info("Bot stopped.")


async def main() -> None:
    _setup_logging()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    tts_service = TTSService(api_key=settings.fish_audio_api_key.get_secret_value())
    user_queue = UserQueue(bot=bot, tts_service=tts_service)

    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    middleware = ServicesMiddleware(tts_service=tts_service, user_queue=user_queue)
    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)

    dp.include_routers(*get_routers())

    await dp.start_polling(
        bot,
        tts_service=tts_service,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
