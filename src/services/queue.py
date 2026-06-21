"""
Per-user job queue. Each user gets one asyncio.Queue.
Jobs run sequentially per user, but different users run in parallel.
"""

import asyncio
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from loguru import logger


@dataclass
class Job:
    user_id: int
    file_name: str
    paragraphs: list[str]
    template_uuid: str


class UserQueue:
    """Manages one asyncio.Queue + worker task per user."""

    def __init__(self) -> None:
        self._queues: dict[int, asyncio.Queue[Job]] = {}
        self._workers: dict[int, asyncio.Task] = {}
        self._executor = ThreadPoolExecutor()

    def enqueue(self, job: Job, tts_service, on_fragment, on_done, on_error) -> int:
        uid = job.user_id
        if uid not in self._queues:
            self._queues[uid] = asyncio.Queue()
            self._workers[uid] = asyncio.create_task(
                self._worker(uid, tts_service), name=f"worker-{uid}"
            )
        self._queues[uid].put_nowait((job, on_fragment, on_done, on_error))
        return self._queues[uid].qsize()

    async def _worker(self, uid: int, tts_service) -> None:
        q = self._queues[uid]
        while True:
            job, on_fragment, on_done, on_error = await q.get()
            logger.info("User {} — starting job '{}' ({} paragraphs)", uid, job.file_name, len(job.paragraphs))
            try:
                # audio_queue bridges the thread and async world
                audio_queue: asyncio.Queue = asyncio.Queue()
                loop = asyncio.get_running_loop()

                def produce():
                    total = len(job.paragraphs)
                    for idx, text in enumerate(job.paragraphs, start=1):
                        logger.info("Synthesizing {}/{}: {:.60s}...", idx, total, text)
                        audio = tts_service._client.synthesize(text, template_uuid=job.template_uuid)
                        logger.debug("Fragment {}/{} done ({} bytes)", idx, total, len(audio))
                        loop.call_soon_threadsafe(audio_queue.put_nowait, (idx, total, audio))
                    loop.call_soon_threadsafe(audio_queue.put_nowait, None)  # sentinel

                fut = loop.run_in_executor(self._executor, produce)

                while True:
                    item = await audio_queue.get()
                    if item is None:
                        break
                    idx, total, audio = item
                    await on_fragment(idx, total, audio)

                await fut  # re-raise any exception from thread
                await on_done()
                logger.info("User {} — job '{}' done", uid, job.file_name)
            except Exception as e:
                logger.exception("User {} — job '{}' failed", uid, job.file_name)
                await on_error(e)
            finally:
                q.task_done()
