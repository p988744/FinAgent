"""
Model Management API Routes

Handles LLM and embedding model selection and monitoring.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class LLMModel(BaseModel):
    """Available LLM model."""
    id: str
    name: str
    description: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int


class EmbeddingModel(BaseModel):
    """Available embedding model."""
    id: str
    name: str
    dimensions: int
    cost_per_1k_tokens: float


class ModelSelection(BaseModel):
    """Request to select a model."""
    model_id: str


class ConnectionTestResult(BaseModel):
    """Result of connection test."""
    success: bool
    message: str
    latency_ms: float | None = None


class UsageStats(BaseModel):
    """Model usage statistics."""
    total_tokens: int
    total_cost: float
    queries_count: int
    session_start: str


@router.get("/llm/available")
async def get_available_llm_models() -> list[LLMModel]:
    """Get list of available LLM models."""
    # TODO: Implement in alpha.4 - read from model_config.yml
    return [
        LLMModel(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            description="Fast and cost-effective model",
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.0006,
            max_tokens=128000
        ),
        LLMModel(
            id="gpt-4o",
            name="GPT-4o",
            description="Most capable model",
            cost_per_1k_input=0.0025,
            cost_per_1k_output=0.01,
            max_tokens=128000
        ),
    ]


@router.post("/llm/test")
async def test_llm_connection() -> ConnectionTestResult:
    """Test connection to current LLM."""
    # TODO: Implement in alpha.4
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/llm/active")
async def set_active_llm(selection: ModelSelection) -> dict[str, str]:
    """Set the active LLM model."""
    # TODO: Implement in alpha.4
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/embedding/available")
async def get_available_embedding_models() -> list[EmbeddingModel]:
    """Get list of available embedding models."""
    # TODO: Implement in alpha.4 - read from model_config.yml
    return [
        EmbeddingModel(
            id="text-embedding-3-small",
            name="Text Embedding 3 Small",
            dimensions=1536,
            cost_per_1k_tokens=0.00002
        ),
        EmbeddingModel(
            id="text-embedding-3-large",
            name="Text Embedding 3 Large",
            dimensions=3072,
            cost_per_1k_tokens=0.00013
        ),
    ]


@router.get("/stats")
async def get_usage_stats() -> UsageStats:
    """Get current session usage statistics."""
    # TODO: Implement in alpha.4 - query from history table
    return UsageStats(
        total_tokens=0,
        total_cost=0.0,
        queries_count=0,
        session_start="2025-01-01T00:00:00Z"
    )
