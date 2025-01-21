from pydantic.v1 import BaseSettings
from pydantic_settings import SettingsConfigDict
from pydantic import SecretStr


__all__ = ["Settings"]


class Settings(BaseSettings):
    def __init__(self):
        token: SecretStr
        model_config = SettingsConfigDict(env_file='')
        super().__init__()


config = Settings()