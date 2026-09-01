from pathlib import Path
from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from pydantic import Field, SecretStr


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    db_host: str
    db_port: int = Field(
        ge=1,
        le=65535
    )
    db_name: str
    db_user: str
    db_password: SecretStr

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()