"""
Configuration Management API Routes

Handles settings and preset management for FinAgent Web UI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class Setting(BaseModel):
    """Single configuration setting."""
    key: str
    value: str | int | float | bool
    category: str
    description: str


class SettingUpdate(BaseModel):
    """Request to update a setting."""
    value: str | int | float | bool


class Preset(BaseModel):
    """Configuration preset."""
    id: int
    name: str
    settings: dict[str, str | int | float | bool]
    is_active: bool
    created_at: str


class PresetCreate(BaseModel):
    """Request to create a preset."""
    name: str


@router.get("/settings")
async def get_all_settings() -> dict[str, list[Setting]]:
    """Get all settings grouped by category."""
    # TODO: Implement in alpha.3
    return {
        "llm": [
            Setting(
                key="llm_model",
                value="gpt-4o-mini",
                category="llm",
                description="LLM model name"
            ),
            Setting(
                key="llm_temperature",
                value=0.3,
                category="llm",
                description="LLM temperature"
            ),
        ],
        "embedding": [
            Setting(
                key="embedding_model",
                value="text-embedding-3-small",
                category="embedding",
                description="Embedding model name"
            ),
        ],
    }


@router.put("/settings/{key}")
async def update_setting(key: str, update: SettingUpdate) -> Setting:
    """Update a single setting."""
    # TODO: Implement in alpha.3
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/presets")
async def list_presets() -> list[Preset]:
    """List all saved presets."""
    # TODO: Implement in alpha.3
    return []


@router.post("/presets")
async def create_preset(preset: PresetCreate) -> Preset:
    """Save current settings as a named preset."""
    # TODO: Implement in alpha.3
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: int) -> dict[str, str]:
    """Delete a preset."""
    # TODO: Implement in alpha.3
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/presets/{preset_id}/activate")
async def activate_preset(preset_id: int) -> dict[str, str]:
    """Activate a preset (load its settings)."""
    # TODO: Implement in alpha.3
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/reload")
async def reload_from_env() -> dict[str, str]:
    """Reload configuration from .env file."""
    # TODO: Implement in alpha.3
    raise HTTPException(status_code=501, detail="Not implemented")
