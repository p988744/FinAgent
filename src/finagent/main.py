"""
FinAgent FastAPI Application

Main entry point for the Taiwan Legal Research Agent System API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from finagent.api.routes import config, documents, health, models, research, websocket, wiki
from finagent.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="backend.log",
    filemode="a",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")

    # TODO: Initialize resources
    # - Connect to vector database
    # - Initialize LLM clients
    # - Load models/embeddings

    yield

    # Shutdown
    logger.info("Shutting down application")
    # TODO: Cleanup resources


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered legal research system for Taiwan regulatory enforcement actions",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
# In development, allow all origins for WebSocket support
logger.info(f"DEBUG: is_development={settings.is_development}, cors_origins={settings.cors_origins}")
cors_origins = settings.cors_origins if not settings.is_development else ["*"]
logger.info(f"DEBUG: effective cors_origins={cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not (cors_origins == ["*"]),  # credentials not allowed with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health.router)
app.include_router(research.router)
app.include_router(config.router)
app.include_router(models.router)
app.include_router(documents.router)
app.include_router(websocket.router)
app.include_router(wiki.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "finagent.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
