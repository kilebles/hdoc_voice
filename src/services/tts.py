import io
import zipfile
from typing import Callable

from loguru import logger

from voicer_client import VoicerClient, TemplateResponse


class TTSService:
    def __init__(self, client: VoicerClient) -> None:
        self._client = client

    def get_templates(self) -> list[TemplateResponse]:
        return self._client.get_templates()

    def get_balance_text(self) -> str:
        balance = self._client.get_balance()
        return balance.balance_description.ru

    def synthesize_batch(
        self,
        paragraphs: list[str],
        template_uuid: str,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> bytes:
        """
        Synthesize each paragraph into a separate MP3,
        pack into a ZIP. Files named 01.mp3, 02.mp3, ...
        on_progress(done, total) called after each fragment.
        """
        total = len(paragraphs)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, text in enumerate(paragraphs, start=1):
                logger.info("Synthesizing {}/{}: {:.60s}...", idx, total, text)
                audio = self._client.synthesize(text, template_uuid=template_uuid)
                zf.writestr(f"{idx:02d}.mp3", audio)
                logger.debug("Fragment {}/{} done ({} bytes)", idx, total, len(audio))
                if on_progress:
                    on_progress(idx, total)
        return buf.getvalue()
