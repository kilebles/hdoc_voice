import asyncio

from loguru import logger

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    BufferedInputFile,
)

from services.tts import TTSService
from services.queue import UserQueue, Job
from states.tts import TTSForm

tts_router = Router(name="tts")

PROGRESS_INTERVAL = 20  # seconds


def _parse_paragraphs(text: str) -> list[str]:
    """Split text by blank lines (handles \\r\\n and \\n), drop empty chunks."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [p.strip() for p in normalized.split("\n\n") if p.strip()]


@tts_router.callback_query(TTSForm.choosing_template, F.data.startswith("tpl:"))
async def on_template_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    template_uuid = callback.data.removeprefix("tpl:")  # type: ignore[union-attr]
    data = await state.get_data()
    template_name = data.get("templates", {}).get(template_uuid, template_uuid)

    await state.update_data(template_uuid=template_uuid)
    await state.set_state(TTSForm.waiting_for_file)

    logger.info("User {} chose template: {} ({})", callback.from_user.id, template_name, template_uuid)  # type: ignore[union-attr]

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Голос: <b>{template_name}</b>\n\nПришлите .txt файл для обработки."
    )
    await callback.answer()


@tts_router.message(TTSForm.waiting_for_file, F.document)
async def on_file_received(
    message: Message, state: FSMContext, tts: TTSService, user_queue: UserQueue
) -> None:
    doc = message.document

    if not doc.file_name.endswith(".txt"):  # type: ignore[union-attr]
        await message.answer("Поддерживается только формат .txt.")
        return

    data = await state.get_data()
    template_uuid: str = data["template_uuid"]

    file = await message.bot.get_file(doc.file_id)  # type: ignore[union-attr]
    downloaded = await message.bot.download_file(file.file_path)  # type: ignore[union-attr]
    text = downloaded.read().decode("utf-8")  # type: ignore[union-attr]

    paragraphs = _parse_paragraphs(text)
    if not paragraphs:
        await message.answer("Файл пустой или не содержит текста.")
        return

    total = len(paragraphs)
    user_id = message.from_user.id  # type: ignore[union-attr]
    file_name = doc.file_name  # type: ignore[union-attr]
    base_name = file_name.removesuffix(".txt")

    logger.info("User {} queued '{}' — {} paragraphs, template {}", user_id, file_name, total, template_uuid)

    status = await message.answer(f"0 / {total}")

    # progress counter written from worker thread, read from async timer
    progress: dict[str, int] = {"done": 0}

    async def _update_status() -> None:
        last = ""
        while True:
            await asyncio.sleep(PROGRESS_INTERVAL)
            new = f"{progress['done']} / {total}"
            if new != last:
                try:
                    await status.edit_text(new)
                    last = new
                except Exception:
                    pass

    updater = asyncio.create_task(_update_status())

    # capture the running loop in the async context before entering the thread
    loop = asyncio.get_running_loop()

    # called from worker thread — schedules coroutine on the captured event loop
    def on_fragment(idx: int, _total: int, audio: bytes) -> None:
        progress["done"] = idx
        name = f"{base_name} — {idx:02d}.mp3"
        audio_file = BufferedInputFile(audio, filename=name)
        asyncio.run_coroutine_threadsafe(
            message.answer_audio(audio_file, title=f"{base_name} — {idx:02d}", performer=""),
            loop,
        )

    async def on_done() -> None:
        updater.cancel()
        await status.delete()
        logger.info("All {} fragments sent to user {}", total, user_id)

    async def on_error(e: Exception) -> None:
        updater.cancel()
        await status.edit_text(f"Ошибка: {e}")

    queue_size = user_queue.enqueue(
        Job(
            user_id=user_id,
            file_name=file_name,
            paragraphs=paragraphs,
            template_uuid=template_uuid,
            on_fragment=on_fragment,
            on_done=on_done,
            on_error=on_error,
        ),
        tts,
    )

    if queue_size > 1:
        await message.answer(f"Файл добавлен в очередь (позиция {queue_size}).")
