from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_FERNET_KEY = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    django_secret_key: str = Field(default="django-insecure-dev-only", validation_alias="DJANGO_SECRET_KEY")
    debug: bool = Field(default=True, validation_alias="DEBUG")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", validation_alias="ALLOWED_HOSTS")
    csrf_trusted_origins: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000",
        validation_alias="CSRF_TRUSTED_ORIGINS",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    token_encryption_key: str = Field(default=DEV_FERNET_KEY, validation_alias="TOKEN_ENCRYPTION_KEY")

    provider_mode: Literal["fake", "live"] = Field(default="fake", validation_alias="SYNC_PROVIDER_MODE")
    max_playlist_size: int = Field(default=200, validation_alias="SYNC_MAX_PLAYLIST_SIZE")
    job_timeout_seconds: int = Field(default=600, validation_alias="SYNC_JOB_TIMEOUT_SECONDS")
    youtube_request_budget: int = Field(default=80, validation_alias="SYNC_YOUTUBE_REQUEST_BUDGET")
    spotify_request_budget: int = Field(default=120, validation_alias="SYNC_SPOTIFY_REQUEST_BUDGET")
    ai_cost_budget_usd: float = Field(default=0.50, validation_alias="SYNC_AI_COST_BUDGET_USD")
    youtube_timeout_seconds: int = Field(default=10, validation_alias="SYNC_YOUTUBE_TIMEOUT_SECONDS")
    spotify_timeout_seconds: int = Field(default=10, validation_alias="SYNC_SPOTIFY_TIMEOUT_SECONDS")
    ai_timeout_seconds: int = Field(default=20, validation_alias="SYNC_AI_TIMEOUT_SECONDS")
    ai_model: str = Field(default="gpt-4o-mini", validation_alias="SYNC_AI_MODEL")
    confidence_threshold: float = Field(default=0.70, validation_alias="SYNC_CONFIDENCE_THRESHOLD")
    classification_cache_days: int = Field(default=30, validation_alias="SYNC_CLASSIFICATION_CACHE_DAYS")

    postgres_db: str = Field(default="sync", validation_alias=AliasChoices("POSTGRES_DB", "SQL_DATABASE"))
    postgres_user: str = Field(default="sync", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="sync", validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", validation_alias=AliasChoices("POSTGRES_HOST", "DB_HOST"))
    postgres_port: str = Field(default="5432", validation_alias=AliasChoices("POSTGRES_PORT", "DB_PORT"))
    sql_engine: str = Field(default="django.db.backends.postgresql", validation_alias="SQL_ENGINE")
    database_url: str = Field(default="", validation_alias="DATABASE_URL")

    redis_host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    redis_port: str = Field(default="6379", validation_alias="REDIS_PORT")
    rabbitmq_host: str = Field(default="localhost", validation_alias="RABBITMQ_HOST")

    youtube_api_key: str = Field(default="", validation_alias="YOUTUBE_API_KEY")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    spotify_client_id: str = Field(default="", validation_alias="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(default="", validation_alias="SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri: str = Field(
        default="http://localhost:8000/social-auth/complete/spotify/",
        validation_alias="SPOTIFY_REDIRECT_URI",
    )

    testing: bool = Field(default=False, validation_alias="SYNC_TESTING")

    @field_validator("debug", "testing", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).lower() in {"1", "true", "yes", "on"}

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_hosts.split(",") if item.strip()]

    @property
    def csrf_trusted_origins_list(self) -> list[str]:
        return [item.strip() for item in self.csrf_trusted_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
