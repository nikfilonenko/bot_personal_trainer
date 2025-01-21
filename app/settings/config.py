from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic import SecretStr

from app.utils.find_directory import find_directory_root


__all__ = ["Settings", "config"]


class Settings(BaseSettings):
    token: SecretStr
    model_config = SettingsConfigDict(env_file=find_directory_root(file_name='.env'), env_file_encoding='utf-8')


config = Settings()