"""
Configuration for MCP FatSecret service.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """MCP FatSecret service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # FatSecret API
    FATSECRET_CLIENT_ID: str
    FATSECRET_CLIENT_SECRET: str
    FATSECRET_API_URL: str = "https://platform.fatsecret.com/rest/server.api"
    FATSECRET_TOKEN_URL: str = "https://oauth.fatsecret.com/connect/token"

    # Logging
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Cache settings
    TOKEN_CACHE_TTL: int = 3600  # 1 hour


settings = Settings()
