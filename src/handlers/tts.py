import asyncio
import io
import re
import zipfile

from docx import Document
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

_DOCX_SKIP_RE = re.compile(r'^\s*(introduction|chapter\s+\d+[\.\:])', re.IGNORECASE)


def _parse_txt(raw: bytes) -> list[str]:
    text = raw.decode("utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [p.strip() for p in normalized.split("\n\n") if p.strip()]


def _parse_docx(raw: bytes) -> list[str]:
    doc = Document(io.BytesIO(raw))
    result = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        if _DOCX_SKIP_RE.match(text):
            continue
        result.append(text)
    return result


@tts_router.callback_query(TTSForm.choosing_template, F.data.startswith("tpl:"))
async def on_template_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    template_uuid = callback.data.removeprefix("tpl:")  # type: ignore[union-attr]
    data = await state.get_data()
    template_name = data.get("templates", {}).get(template_uuid, template_uuid)

    await state.update_data(template_uuid=template_uuid)
    await state.set_state(TTSForm.waiting_for_file)

    logger.info("User {} chose template: {} ({})", callback.from_user.id, template_name, template_uuid)  # type: ignore[union-attr]

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Голос: <b>{template_name}</b>\n\nПришлите .txt или .docx файл для обработки."
    )
    await callback.answer()


@tts_router.message(TTSForm.waiting_for_file, F.document)
async def on_file_received(
    message: Message, state: FSMContext, tts: TTSService, user_queue: UserQueue
) -> None:
    doc = message.document
    file_name = doc.file_name  # type: ignore[union-attr]

    if not (file_name.endswith(".txt") or file_name.endswith(".docx")):
        await message.answer("Поддерживается только формат .txt или .docx.")
        return

    data = await state.get_data()
    template_uuid: str = data["template_uuid"]

    file = await message.bot.get_file(doc.file_id)  # type: ignore[union-attr]
    downloaded = await message.bot.download_file(file.file_path)  # type: ignore[union-attr]
    raw = downloaded.read()  # type: ignore[union-attr]

    if file_name.endswith(".docx"):
        paragraphs = _parse_docx(raw)
        base_name = file_name.removesuffix(".docx")
    else:
        paragraphs = _parse_txt(raw)
        base_name = file_name.removesuffix(".txt")

    if not paragraphs:
        await message.answer("Файл пустой или не содержит текста.")
        return

    total = len(paragraphs)
    user_id = message.from_user.id  # type: ignore[union-attr]

    logger.info("User {} queued '{}' — {} paragraphs, template {}", user_id, file_name, total, template_uuid)

    status = await message.answer(f"0 / {total}")
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

    collected: list[tuple[int, bytes]] = []

    async def on_fragment(idx: int, _total: int, audio: bytes) -> None:
        progress["done"] = idx
        collected.append((idx, audio))

    async def on_done() -> None:
        updater.cancel()
        await status.delete()

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, audio in sorted(collected):
                zf.writestr(f"{idx:03d}.mp3", audio)
        zip_file = BufferedInputFile(buf.getvalue(), filename=f"{base_name}.zip")
        await message.answer_document(zip_file)

        logger.info("Sent archive ({} fragments) to user {}", total, user_id)

    async def on_error(e: Exception) -> None:
        updater.cancel()
        await status.edit_text(f"Ошибка: {e}")

    queue_size = user_queue.enqueue(
        Job(user_id=user_id, file_name=file_name, paragraphs=paragraphs, template_uuid=template_uuid),
        tts,
        on_fragment,
        on_done,
        on_error,
    )

    if queue_size > 1:
        await message.answer(f"Файл добавлен в очередь (позиция {queue_size}).")
