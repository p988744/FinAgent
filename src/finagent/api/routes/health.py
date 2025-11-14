"""Health check endpoints."""

import time
from datetime import datetime

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from finagent.config import settings
from finagent.config_manager import get_config_manager
from finagent.database.db import Database
from finagent.document_processing.vector_store import get_vector_store

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
    Checks database, vector DB, and LLM API connectivity.
    """
    checks = {
        "api": "ok",
        "database": await check_database(),
        "vector_db": await check_vector_db(),
        "llm_api": await check_llm_api(),
    }

    # Determine overall status
    all_ok = all(
        check.get("status") == "ok" if isinstance(check, dict) else check == "ok"
        for check in checks.values()
    )

    return {"status": "ready" if all_ok else "not_ready", "checks": checks}


async def check_database() -> dict:
    """
    Check database connectivity and health.

    Returns:
        Dictionary with status and metadata
    """
    try:
        start_time = time.time()
        db = Database()

        # Try a simple query
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM history")
            result = cursor.fetchone()
            count = result["count"] if result else 0

        response_time_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "ok",
            "response_time_ms": response_time_ms,
            "history_count": count,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


async def check_vector_db() -> dict:
    """
    Check Chroma vector database connectivity and health.

    Returns:
        Dictionary with status and metadata
    """
    try:
        start_time = time.time()
        vector_store = get_vector_store()

        # Get collection info from Chroma vector store
        collection_name = vector_store._collection.name
        document_count = vector_store._collection.count()

        response_time_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "ok",
            "response_time_ms": response_time_ms,
            "collection": collection_name,
            "document_count": document_count,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


async def check_llm_api() -> dict:
    """
    Check LLM API connectivity and health.

    Returns:
        Dictionary with status and metadata
    """
    try:
        # Get active LLM configuration
        config_manager = get_config_manager()
        llm_config = config_manager.get_active_llm_config()

        if not llm_config:
            return {"status": "error", "error": "No active LLM configuration"}

        endpoint = llm_config.get("endpoint")
        model = llm_config.get("model")
        api_key = llm_config.get("api_key")

        # Test connectivity with a simple models list request
        start_time = time.time()

        # Try to list models endpoint
        models_url = f"{endpoint.rstrip('/')}/models"

        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = await client.get(models_url, headers=headers)
            response.raise_for_status()

        response_time_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "ok",
            "response_time_ms": response_time_ms,
            "endpoint": endpoint,
            "model": model,
        }

    except httpx.HTTPError as e:
        return {"status": "error", "error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
