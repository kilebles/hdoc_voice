"""
Per-user job queue. Each user gets one asyncio.Queue.
Jobs run sequentially per user, but different users run in parallel.
"""

import asyncio
from dataclasses import dataclass
from typing import Callable

from loguru import logger


@dataclass
class Job:
    user_id: int
    file_name: str
    paragraphs: list[str]
    template_uuid: str
    on_fragment: Callable[[int, int, bytes], None]   # idx, total, audio_bytes
    on_done: Callable[[], None]
    on_error: Callable[[Exception], None]


class UserQueue:
    """Manages one asyncio.Queue + worker task per user."""

    def __init__(self) -> None:
        self._queues: dict[int, asyncio.Queue[Job]] = {}
        self._workers: dict[int, asyncio.Task] = {}

    def enqueue(self, job: Job, tts_service) -> int:
        """Add job to user's queue. Returns queue size after enqueue."""
        uid = job.user_id
        if uid not in self._queues:
            self._queues[uid] = asyncio.Queue()
            self._workers[uid] = asyncio.create_task(
                self._worker(uid, tts_service), name=f"worker-{uid}"
            )
        self._queues[uid].put_nowait(job)
        return self._queues[uid].qsize()

    async def _worker(self, uid: int, tts_service) -> None:
        q = self._queues[uid]
        while True:
            job: Job = await q.get()
            logger.info("User {} — starting job '{}' ({} paragraphs)", uid, job.file_name, len(job.paragraphs))
            try:
                from concurrent.futures import ThreadPoolExecutor
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as ex:
                    await loop.run_in_executor(
                        ex,
                        lambda j=job: tts_service.synthesize_batch(
                            j.paragraphs, j.template_uuid, j.on_fragment
                        ),
                    )
                await job.on_done()
                logger.info("User {} — job '{}' done", uid, job.file_name)
            except Exception as e:
                logger.exception("User {} — job '{}' failed", uid, job.file_name)
                await job.on_error(e)
            finally:
                q.task_done()
