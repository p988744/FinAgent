"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from finagent.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns basic application status and metadata.
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(),
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Returns whether the application is ready to serve requests.
    """
    # TODO: Add checks for:
    # - Database connectivity
    # - Vector DB availability
    # - LLM API connectivity
    return {"status": "ready", "checks": {"api": "ok"}}
