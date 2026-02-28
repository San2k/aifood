"""
API v1 router.
"""

from fastapi import APIRouter
from .endpoints import ingest, reports, users, oauth, food_log

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(ingest.router, tags=["ingest"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(oauth.router, tags=["oauth"])
api_router.include_router(food_log.router, tags=["food_log"])

@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "agent-api"}
