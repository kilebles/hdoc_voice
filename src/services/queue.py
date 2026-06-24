import asyncio
from dataclasses import dataclass

from aiogram import Bot


@dataclass
class TTSJob:
    user_id: int
    chat_id: int
    voice_id: str
    filename: str
    chunks: list[str]


class UserQueue:
    """Per-user job queue with a background worker per user."""

    def __init__(self, bot: Bot, tts_service) -> None:
        self._bot = bot
        self._tts = tts_service
        self._queues: dict[int, asyncio.Queue[TTSJob | None]] = {}
        self._workers: dict[int, asyncio.Task] = {}

    def _ensure_worker(self, user_id: int) -> None:
        if user_id not in self._queues:
            self._queues[user_id] = asyncio.Queue()
        task = self._workers.get(user_id)
        if task is None or task.done():
            self._workers[user_id] = asyncio.create_task(self._worker(user_id))

    async def enqueue(self, job: TTSJob) -> int:
        """Add job to queue. Returns queue size after adding."""
        self._ensure_worker(job.user_id)
        await self._queues[job.user_id].put(job)
        return self._queues[job.user_id].qsize()

    def clear(self, user_id: int) -> int:
        """Drain the queue (current job keeps running). Returns number of removed jobs."""
        q = self._queues.get(user_id)
        if q is None:
            return 0
        count = 0
        while not q.empty():
            try:
                q.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        return count

    def pending(self, user_id: int) -> int:
        q = self._queues.get(user_id)
        return q.qsize() if q else 0

    async def _worker(self, user_id: int) -> None:
        import io
        import zipfile

        q = self._queues[user_id]
        while True:
            job = await q.get()
            if job is None:
                break
            try:
                total = len(job.chunks)
                status = await self._bot.send_message(job.chat_id, f"0/{total}")

                sem = asyncio.Semaphore(5)
                done = 0
                audio_files: list[tuple[str, bytes]] = [("", b"")] * total

                async def synthesize_chunk(idx: int, text: str) -> None:
                    nonlocal done
                    async with sem:
                        audio_bytes = await self._tts.synthesize(text, job.voice_id)
                    audio_files[idx] = (f"{idx + 1}.mp3", audio_bytes)
                    done += 1
                    await status.edit_text(f"{done}/{total}")

                await asyncio.gather(
                    *[synthesize_chunk(i, chunk) for i, chunk in enumerate(job.chunks)]
                )

                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for fname, data in audio_files:
                        zf.writestr(fname, data)
                zip_buf.seek(0)

                from aiogram.types import BufferedInputFile
                stem = job.filename.rsplit(".", 1)[0]
                await self._bot.send_document(
                    job.chat_id,
                    BufferedInputFile(zip_buf.read(), filename=f"{stem}.zip"),
                )
                await status.delete()

                if q.empty():
                    await self._bot.send_message(job.chat_id, "Очередь пуста.")

            except Exception as e:
                await self._bot.send_message(job.chat_id, f"Ошибка: {e}")
            finally:
                q.task_done()
