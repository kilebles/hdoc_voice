from fishaudio import AsyncFishAudio


class TTSService:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncFishAudio(api_key=api_key)

    async def synthesize(self, text: str, voice_id: str) -> bytes:
        return await self._client.tts.convert(
            text=text,
            reference_id=voice_id,
            model="s2.1-pro",
            latency="normal",
        )

    async def close(self) -> None:
        await self._client.close()
