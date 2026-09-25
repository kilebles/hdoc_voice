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
    return [c.strip() for c in text.splitlines() if c.strip()]


def _parse_docx(data: bytes) -> list[str]:
    import re
    import zipfile
    from docx import Document  # type: ignore

    HEADING = re.compile(
        r'^(?:'
        r'(?:introduction|introdu[cç][aã]o|introducci[oó]n|introduzione|einleitung|wst[eę]p|'
        r'conclusion|conclus[aã]o|conclusi[oó]n|conclusione|fazit|zako[nń]czenie|podsumowanie|'
        r'epilogue|ep[ií]logo|[eé]pilogue|epilogo|epilog|'
        r'prologue|pr[oó]logo|prologo|prolog)\b'
        r'|(?:chapter|cap[ií]tulo|chapitre|capitolo|kapitel|rozdzia[lł]|part|parte|partie|teil|cz[eę][sś][cć])\s+\d+'
        r')',
        re.IGNORECASE,
    )
    AD = re.compile(r'subscribe to deepl|visit www\.deepl\.com', re.IGNORECASE)
    SENTENCE_END = '.!?…»"”“)'

    def skip(text: str, style: str = "") -> bool:
        if not text or AD.search(text) or HEADING.match(text):
            return True
        if style.lower().startswith(("heading", "title", "заголов", "название")):
            return True
        return len(text) <= 120 and text[-1] not in SENTENCE_END

    # Some docx files have broken image references — patch the zip before opening
    buf = io.BytesIO(data)
    try:
        with zipfile.ZipFile(buf) as zf:
            names = set(zf.namelist())
        # Rewrite file stripping missing media references is complex;
        # instead just open with error handling below
    except Exception:
        pass

    buf.seek(0)
    try:
        doc = Document(buf)
    except KeyError:
        # Fallback: extract XML directly without loading media
        buf.seek(0)
        with zipfile.ZipFile(buf) as zf:
            xml = zf.read("word/document.xml")
        import re as _re
        from lxml import etree  # type: ignore
        root = etree.fromstring(xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        texts = []
        for p in root.iter(f"{{{ns['w'].split('}')[0][1:]}}}p" if False else "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            text = "".join(t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")).strip()
            if not skip(text):
                texts.append(text)
        return texts

    return [p.text.strip() for p in doc.paragraphs if not skip(p.text.strip(), p.style.name)]


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

    if queue_size > 1:
        await message.answer(f"<b>{name}</b> добавлен в очередь (позиция {queue_size}).")
