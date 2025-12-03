"""
Model Management API Routes

Handles LLM and embedding model selection and monitoring.
"""

import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from finagent.config_manager import get_config_manager

router = APIRouter(prefix="/api/v1/models", tags=["models"])

# Cost info from model_config.yml (hardcoded for now, could be loaded from config)
COST_INFO = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}

EMBEDDING_COST_INFO = {
    "text-embedding-3-small": {"per_1k": 0.00002},
    "text-embedding-3-large": {"per_1k": 0.00013},
    "text-embedding-ada-002": {"per_1k": 0.0001},
}

MAX_TOKENS_INFO = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
}


class LLMModel(BaseModel):
    """Available LLM model."""

    id: str
    name: str
    description: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    recommended: bool = False
    is_active: bool = False


class EmbeddingModel(BaseModel):
    """Available embedding model."""

    id: str
    name: str
    description: str
    dimensions: int
    cost_per_1k_tokens: float
    recommended: bool = False
    is_active: bool = False


class ModelSelection(BaseModel):
    """Request to select a model."""

    model_id: str


class ConnectionTestResult(BaseModel):
    """Result of connection test."""

    success: bool
    message: str
    latency_ms: float | None = None
    model: str | None = None


class UsageStats(BaseModel):
    """Model usage statistics."""

    total_tokens: int
    total_cost: float
    queries_count: int
    session_start: str
    current_llm_model: str
    current_embedding_model: str


class CostEstimate(BaseModel):
    """Cost estimate for a query."""

    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    model: str


@router.get("/llm/available")
async def get_available_llm_models() -> list[LLMModel]:
    """Get list of available LLM models from model_config.yml."""
    config_manager = get_config_manager()
    model_choices = config_manager.get_model_choices()

    # Get current active model
    current_model = config_manager.get_setting("llm_model")

    llm_models = []
    for model_info in model_choices.get("openai_chat_models", []):
        model_id = model_info.id
        cost_info = COST_INFO.get(model_id, {"input": 0.0, "output": 0.0})

        llm_models.append(
            LLMModel(
                id=model_id,
                name=model_info.name,
                description=model_info.description,
                cost_per_1k_input=cost_info["input"],
                cost_per_1k_output=cost_info["output"],
                max_tokens=MAX_TOKENS_INFO.get(model_id, 128000),
                recommended=model_info.recommended,
                is_active=(model_id == current_model),
            )
        )

    return llm_models


@router.get("/llm/active")
async def get_active_llm() -> dict[str, Any]:
    """Get currently active LLM model."""
    config_manager = get_config_manager()

    model = config_manager.get_setting("llm_model")
    api_key = config_manager.get_setting("llm_api_key")
    base_url = config_manager.get_setting("llm_base_url")
    temperature = config_manager.get_setting("llm_temperature")

    # Mask API key
    masked_key = ""
    if api_key and len(api_key) >= 20:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}"
    elif api_key:
        masked_key = api_key

    return {
        "model": model or "gpt-4o-mini",
        "api_key": masked_key,
        "base_url": base_url or "",
        "temperature": float(temperature) if temperature else 0.0,
    }


@router.put("/llm/active")
async def set_active_llm(selection: ModelSelection) -> dict[str, str]:
    """Set the active LLM model."""
    config_manager = get_config_manager()

    # Update the model setting
    config_manager.set_setting("llm_model", selection.model_id, "llm", "LLM 模型名稱")

    return {
        "status": "success",
        "message": f"已切換到 {selection.model_id}",
        "model": selection.model_id,
    }


@router.post("/llm/test")
async def test_llm_connection() -> ConnectionTestResult:
    """Test connection to current LLM with a simple API call."""
    config_manager = get_config_manager()

    model = config_manager.get_setting("llm_model") or "gpt-4o-mini"
    api_key = config_manager.get_setting("llm_api_key")
    base_url = config_manager.get_setting("llm_base_url")

    if not api_key:
        return ConnectionTestResult(
            success=False,
            message="未設定 API 金鑰",
            model=model,
        )

    # Test connection with OpenAI API
    try:
        import httpx

        # Build the API URL
        if base_url:
            url = f"{base_url.rstrip('/')}/chat/completions"
        else:
            url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Simple test request
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        }

        start_time = time.time()
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
        latency_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            return ConnectionTestResult(
                success=True,
                message=f"連線成功！回應時間: {latency_ms:.0f}ms",
                latency_ms=latency_ms,
                model=model,
            )
        elif response.status_code == 401:
            return ConnectionTestResult(
                success=False,
                message="API 金鑰無效",
                model=model,
            )
        elif response.status_code == 404:
            return ConnectionTestResult(
                success=False,
                message=f"模型 {model} 不存在或無權限存取",
                model=model,
            )
        else:
            error_detail = response.json().get("error", {}).get("message", "未知錯誤")
            return ConnectionTestResult(
                success=False,
                message=f"API 錯誤 ({response.status_code}): {error_detail}",
                model=model,
            )

    except httpx.ConnectError:
        return ConnectionTestResult(
            success=False,
            message=f"無法連線到 {base_url or 'OpenAI API'}",
            model=model,
        )
    except httpx.TimeoutException:
        return ConnectionTestResult(
            success=False,
            message="連線逾時",
            model=model,
        )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message=f"連線錯誤: {str(e)}",
            model=model,
        )


@router.get("/embedding/available")
async def get_available_embedding_models() -> list[EmbeddingModel]:
    """Get list of available embedding models from model_config.yml."""
    config_manager = get_config_manager()
    model_choices = config_manager.get_model_choices()

    # Get current active model
    current_model = config_manager.get_setting("embedding_model")

    embedding_models = []
    for model_info in model_choices.get("openai_embedding_models", []):
        model_id = model_info.id
        cost_info = EMBEDDING_COST_INFO.get(model_id, {"per_1k": 0.0})

        embedding_models.append(
            EmbeddingModel(
                id=model_id,
                name=model_info.name,
                description=model_info.description,
                dimensions=model_info.dimensions or 1536,
                cost_per_1k_tokens=cost_info["per_1k"],
                recommended=model_info.recommended,
                is_active=(model_id == current_model),
            )
        )

    return embedding_models


@router.get("/embedding/active")
async def get_active_embedding() -> dict[str, Any]:
    """Get currently active embedding model."""
    config_manager = get_config_manager()

    model = config_manager.get_setting("embedding_model")

    return {
        "model": model or "text-embedding-3-small",
    }


@router.put("/embedding/active")
async def set_active_embedding(selection: ModelSelection) -> dict[str, str]:
    """Set the active embedding model."""
    config_manager = get_config_manager()

    # Update the embedding model setting
    config_manager.set_setting(
        "embedding_model", selection.model_id, "embedding", "嵌入模型名稱"
    )

    return {
        "status": "success",
        "message": f"已切換到 {selection.model_id}",
        "model": selection.model_id,
    }


@router.get("/stats")
async def get_usage_stats() -> UsageStats:
    """Get current session usage statistics."""
    config_manager = get_config_manager()

    # Get current models
    current_llm = config_manager.get_setting("llm_model") or "gpt-4o-mini"
    current_embedding = (
        config_manager.get_setting("embedding_model") or "text-embedding-3-small"
    )

    # TODO: Query actual usage from history table when implemented
    # For now, return placeholder stats
    return UsageStats(
        total_tokens=0,
        total_cost=0.0,
        queries_count=0,
        session_start=datetime.now(UTC).isoformat(),
        current_llm_model=current_llm,
        current_embedding_model=current_embedding,
    )


@router.post("/cost/estimate")
async def estimate_cost(
    input_tokens: int = 1000, output_tokens: int = 500, model: str | None = None
) -> CostEstimate:
    """Estimate cost for given token counts."""
    config_manager = get_config_manager()

    if not model:
        model = config_manager.get_setting("llm_model") or "gpt-4o-mini"

    cost_info = COST_INFO.get(model, {"input": 0.0, "output": 0.0})

    input_cost = (input_tokens / 1000) * cost_info["input"]
    output_cost = (output_tokens / 1000) * cost_info["output"]
    total_cost = input_cost + output_cost

    return CostEstimate(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
        model=model,
    )


@router.get("/local-presets")
async def get_local_llm_presets() -> list[dict[str, Any]]:
    """Get local LLM presets for quick setup."""
    config_manager = get_config_manager()
    model_choices = config_manager.get_model_choices()

    presets = []
    for preset in model_choices.get("local_llm_presets", []):
        presets.append(
            {
                "name": preset.name,
                "base_url": preset.base_url,
                "model": preset.model,
                "api_key": preset.api_key,
                "description": preset.description,
                "recommended": preset.recommended,
            }
        )

    return presets
