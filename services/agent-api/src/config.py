"""
Configuration settings for agent-api service.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aifood:aifood_secure_password_2024@localhost:5433/aifood"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SCAN_TTL: int = 1800  # 30 minutes

    # OCR Service
    OCR_SERVICE_URL: str = "http://localhost:8001"
    OCR_TIMEOUT: int = 30

    # Vision Fallback (Gemini)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Latest flash model available

    # Image Processing
    IMAGE_DOWNLOAD_TIMEOUT: int = 10
    IMAGE_MAX_SIZE_MB: int = 10
    IMAGE_TARGET_SIZE: int = 1400  # Target width for upscaling (1200-1600px range)
    TEMP_UPLOAD_DIR: str = "/tmp/aifood/uploads"

    # OCR Quality Thresholds
    OCR_CONFIDENCE_THRESHOLD: float = 0.75
    MIN_NUTRITION_MARKERS: int = 2

    # API
    API_TITLE: str = "AiFood Agent API"
    API_VERSION: str = "2.0.0"
    API_DESCRIPTION: str = "Label processing API with PaddleOCR and Gemini Vision"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
