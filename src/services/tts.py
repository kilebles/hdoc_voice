from fishaudio import AsyncFishAudio
from fishaudio.types import TTSConfig


class TTSService:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncFishAudio(api_key=api_key)
        self._config = TTSConfig(
            temperature=0.9,
            top_p=0.9,
            repetition_penalty=1.3,
            mp3_bitrate=192,
            latency="normal",
        )

    async def synthesize(self, text: str, voice_id: str) -> bytes:
        return await self._client.tts.convert(
            text=text,
            reference_id=voice_id,
            model="s2.1-pro",  # type: ignore[arg-type]
            speed=1.0,
            config=self._config,
        )

    async def close(self) -> None:
        await self._client.close()
