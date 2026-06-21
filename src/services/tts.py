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
        on_fragment: Callable[[int, int, bytes], None] | None = None,
    ) -> None:
        """
        Synthesize each paragraph and call on_fragment(idx, total, audio_bytes)
        immediately after each one is ready.
        """
        total = len(paragraphs)
        for idx, text in enumerate(paragraphs, start=1):
            logger.info("Synthesizing {}/{}: {:.60s}...", idx, total, text)
            audio = self._client.synthesize(text, template_uuid=template_uuid)
            logger.debug("Fragment {}/{} done ({} bytes)", idx, total, len(audio))
            if on_fragment:
                on_fragment(idx, total, audio)
