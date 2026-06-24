from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    bot_token: SecretStr = Field(..., description="Telegram bot token")
    fish_audio_api_key: SecretStr = Field(..., description="Fish Audio API key")


settings = Settings()
