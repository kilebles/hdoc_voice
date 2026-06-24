import io

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.keyboards.voices import voices_keyboard
from src.services.queue import TTSJob, UserQueue
from src.states.tts import TTSForm
from src.voices import VOICES

router = Router(name="tts")


def _voice_name(voice_id: str) -> str:
    for v in VOICES:
        if v.id == voice_id:
            return v.name
    return voice_id


def _parse_txt(data: bytes) -> list[str]:
    text = data.decode("utf-8")
    return [c.strip() for c in text.split("\n\n") if c.strip()]


def _parse_docx(data: bytes) -> list[str]:
    import re
    from docx import Document  # type: ignore

    HEADING = re.compile(r'^(introduction|chapter\s+\d+)', re.IGNORECASE)
    doc = Document(io.BytesIO(data))
    return [p.text.strip() for p in doc.paragraphs if p.text.strip() and not HEADING.match(p.text.strip())]


@router.callback_query(TTSForm.choosing_voice, F.data.startswith("voice:"))
async def on_voice_selected(callback: CallbackQuery, state: FSMContext) -> None:
    voice_id = callback.data.removeprefix("voice:")
    await state.update_data(voice_id=voice_id)
    await state.set_state(TTSForm.waiting_for_file)
    await callback.message.edit_text(
        f"Голос: <b>{_voice_name(voice_id)}</b>\n\n"
        "Отправьте файл в .txt или .docx формате"
    )
    await callback.answer()


@router.message(TTSForm.waiting_for_file, F.document)
async def on_file_received(
    message: Message, state: FSMContext, user_queue: UserQueue
) -> None:
    doc = message.document
    name = doc.file_name or ""

    if not (name.endswith(".txt") or name.endswith(".docx")):
        await message.answer("Поддерживаются только .txt и .docx файлы.")
        return

    data = await state.get_data()
    voice_id = data.get("voice_id")
    if not voice_id:
        await state.set_state(TTSForm.choosing_voice)
        await message.answer("Выберите голос:", reply_markup=voices_keyboard())
        return

    # Download
    file = await message.bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await message.bot.download_file(file.file_path, destination=buf)
    raw = buf.getvalue()

    # Parse
    chunks = _parse_txt(raw) if name.endswith(".txt") else _parse_docx(raw)
    if not chunks:
        await message.answer("Файл пустой.")
        return

    job = TTSJob(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        voice_id=voice_id,
        filename=name,
        chunks=chunks,
    )
    queue_size = await user_queue.enqueue(job)

    if queue_size == 1:
        await message.answer(f"Обрабатываю <b>{name}</b> ({len(chunks)} фрагментов)...")
    else:
        await message.answer(f"<b>{name}</b> добавлен в очередь (позиция {queue_size}).")
