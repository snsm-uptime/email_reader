import logging
from pathlib import Path
from typing import Literal

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
    PAGE_SIZE: int = 15
    CACHE_CAPACITY_EMAIL_ID_LIST: int = 5
    CACHE_CAPACITY_EMAIL_MODEL_LIST: int = 5
    ENVIRONMENT: Literal['local', 'development', 'production'] = 'local'


config = Settings()
