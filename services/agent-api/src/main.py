"""
Agent API - FastAPI application for nutrition label processing.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from .config import settings
from .services.redis_service import redis_service
from .api.v1.endpoints import label

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    """
    # Startup
    logger.info("Agent API starting up...")

    # Create temp upload directory
    os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
    logger.info(f"Temp upload directory: {settings.TEMP_UPLOAD_DIR}")

    # Connect to Redis
    await redis_service.connect()

    yield

    # Shutdown
    logger.info("Agent API shutting down...")
    await redis_service.disconnect()


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(label.router)


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
        Service status
    """
    return {
        "status": "ok",
        "service": "agent-api",
        "version": settings.API_VERSION
    }


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        API information
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
