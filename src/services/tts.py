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
