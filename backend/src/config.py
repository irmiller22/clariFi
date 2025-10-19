"""Application configuration using pydantic-settings."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """
    Application settings.

    Configuration Philosophy:
    - Use environment variables as the single source of truth
    - POSTGRESQL_URL is the canonical database connection string
    - Leverage direnv + .env files for local development
    - No separate configs for test/dev/prod - one URL to rule them all
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "production", "test"] = "development"
    debug: bool = True

    # Database - Read from POSTGRESQL_URL environment variable
    # Format: postgresql://user:password@host:port/database
    # Default for local development
    @property
    def database_url(self) -> str:
        """
        Async database URL from POSTGRESQL_URL environment variable.
        Converts postgresql:// to postgresql+asyncpg:// for async support.
        """
        postgresql_url = os.getenv(
            "POSTGRESQL_URL",
            "postgresql://range:range@localhost:5432/range"
        )
        return postgresql_url.replace("postgresql://", "postgresql+asyncpg://")

    @property
    def database_url_sync(self) -> str:
        """
        Sync database URL from POSTGRESQL_URL environment variable.
        Used for Alembic migrations.
        """
        return os.getenv(
            "POSTGRESQL_URL",
            "postgresql://range:range@localhost:5432/range"
        )

    # API
    api_title: str = "Range Finance API"
    api_version: str = "0.1.0"
    api_description: str = "Personal finance application for analyzing credit card spending patterns"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # File Upload
    max_upload_size: int = 10 * 1024 * 1024  # 10MB in bytes


settings = Settings()
