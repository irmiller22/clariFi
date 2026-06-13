"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """
    Application settings.

    Configuration Philosophy:
    - Use environment variables as the single source of truth
    - Leverage direnv + .env files for local development
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

    # API
    api_title: str = "clariFi API"
    api_version: str = "0.1.0"
    api_description: str = "Personal finance application for analyzing credit card spending patterns"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # File Upload
    max_upload_size: int = 10 * 1024 * 1024  # 10MB in bytes


settings = Settings()
