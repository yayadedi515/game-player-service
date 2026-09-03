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
    redis_host: str = Field(
        default="localhost",
        min_length=1
    )
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535
    )
    ranking_cache_ttl_seconds: int = Field(
        default=60,
        ge=1,
        le=3600
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()