from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic import SecretStr

from app.utils.find_directory import find_directory_root


__all__ = ["Settings", "config"]


class Settings(BaseSettings):
    token_bot: SecretStr
    api_key_open_weather: SecretStr
    api_key_nutrition_training: SecretStr

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )


config = Settings()