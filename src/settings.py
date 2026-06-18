from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    bot_token: SecretStr = Field(default="", description="Telegram bot token")
    voice_secret_key: SecretStr = Field(..., description="Voicer API key")
    voice_model_id: str = Field(default="", description="Default Voicer voice/model ID")
    voicer_base_url: AnyHttpUrl = Field(
        default="https://voiceapiru.csv666.ru",
        description="Voicer API base URL",
    )
    voicer_timeout: float = Field(default=30.0, gt=0, description="HTTP timeout in seconds")
    voicer_poll_interval: float = Field(default=3.0, gt=0, description="Polling interval in seconds")
    voicer_task_timeout: float = Field(default=300.0, gt=0, description="Max wait for TTS task")
    voicer_image_timeout: float = Field(default=120.0, gt=0, description="Max wait for image generation")


settings = Settings()
