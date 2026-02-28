"""
Configuration module for Agent API service.
Loads environment variables and provides application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    # API
    AGENT_API_HOST: str = "0.0.0.0"
    AGENT_API_PORT: int = 8000
    API_V1_PREFIX: str = "/v1"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_DECODE_RESPONSES: bool = True

    # LLM Provider Configuration
    LLM_PROVIDER: str = "ollama"  # "ollama" or "openai"

    # OpenAI
    OPENAI_API_KEY: str = ""  # Optional if using Ollama
    OPENAI_MODEL_TEXT: str = "gpt-4-turbo-preview"
    OPENAI_MODEL_VISION: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TIMEOUT: int = 60

    # Ollama
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"  # Mac host
    OLLAMA_MODEL_TEXT: str = "mistral"
    OLLAMA_MODEL_VISION: str = "llava:7b"
    OLLAMA_TIMEOUT: int = 120

    # FatSecret API
    FATSECRET_CLIENT_ID: str
    FATSECRET_CLIENT_SECRET: str
    FATSECRET_API_URL: str = "https://platform.fatsecret.com/rest/server.api"
    FATSECRET_TOKEN_URL: str = "https://oauth.fatsecret.com/connect/token"
    FATSECRET_REDIRECT_URI: str = "http://localhost:8000/v1/oauth/fatsecret/callback"

    # Session Configuration
    SESSION_EXPIRE_SECONDS: int = 3600  # 1 hour
    CONVERSATION_EXPIRE_SECONDS: int = 7200  # 2 hours

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Logging
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
