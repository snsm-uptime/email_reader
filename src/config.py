from typing import Literal
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding='utf-8',
        extra="ignore"
    )
    EMAIL_PASSWORD: str
    EMAIL_USER: str
    ENVIRONMENT: Literal['local', 'dev', 'prod'] = 'local'


config = Settings()
