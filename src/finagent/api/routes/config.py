"""
Configuration Management API Routes

Handles settings and preset management for FinAgent Web UI.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from finagent.config_manager import get_config_manager

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class SettingResponse(BaseModel):
    """Single configuration setting."""
    key: str
    value: str
    category: str
    description: str | None


class SettingUpdate(BaseModel):
    """Request to update a setting."""
    value: str
    description: str | None = None


class PresetResponse(BaseModel):
    """Configuration preset."""
    id: int
    name: str
    config_type: str
    model: str
    api_key: str  # Masked for security
    base_url: str
    temperature: float | None
    is_active: bool
    created_at: str


class PresetCreate(BaseModel):
    """Request to create a preset."""
    name: str
    config_type: str  # 'llm' or 'embedding'
    api_key: str = ""
    base_url: str = ""
    model: str
    temperature: float | None = 0.0
    set_active: bool = False


class BulkSettingUpdate(BaseModel):
    """Request to update multiple settings."""
    settings: dict[str, str]


def mask_api_key(api_key: str) -> str:
    """Mask API key for security (show first 8 and last 4 chars)."""
    if not api_key or len(api_key) < 20:
        return api_key
    return f"{api_key[:8]}...{api_key[-4:]}"


@router.get("/settings")
async def get_all_settings() -> dict[str, list[SettingResponse]]:
    """Get all settings grouped by category."""
    config_manager = get_config_manager()

    # Get all settings from database
    all_settings = config_manager.db.get_all_settings()

    # Group by category
    grouped: dict[str, list[SettingResponse]] = {}

    for setting in all_settings:
        category = setting.category
        if category not in grouped:
            grouped[category] = []

        # Mask API keys for security
        value = setting.value
        if "api_key" in setting.key:
            value = mask_api_key(value)

        grouped[category].append(SettingResponse(
            key=setting.key,
            value=value,
            category=category,
            description=setting.description,
        ))

    return grouped


@router.get("/settings/{category}")
async def get_settings_by_category(category: str) -> list[SettingResponse]:
    """Get settings for a specific category."""
    config_manager = get_config_manager()

    settings_dict = config_manager.get_all_settings(category)

    result = []
    for key, value in settings_dict.items():
        # Mask API keys
        display_value = mask_api_key(value) if "api_key" in key else value

        # Get description from database
        setting = config_manager.db.get_setting(key)
        description = setting.description if setting else None

        result.append(SettingResponse(
            key=key,
            value=display_value,
            category=category,
            description=description,
        ))

    return result


class SettingCreate(BaseModel):
    """Request to create or update a setting."""
    value: str
    category: str = "custom"
    description: str | None = None


@router.put("/settings/{key}")
async def update_setting(key: str, update: SettingUpdate) -> SettingResponse:
    """Update a single setting."""
    config_manager = get_config_manager()

    # Check if setting exists
    existing = config_manager.db.get_setting(key)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    # Update setting
    config_manager.set_setting(
        key=key,
        value=update.value,
        category=existing.category,
        description=update.description or existing.description,
    )

    # Return updated setting (with masked API key if applicable)
    display_value = mask_api_key(update.value) if "api_key" in key else update.value

    return SettingResponse(
        key=key,
        value=display_value,
        category=existing.category,
        description=update.description or existing.description,
    )


@router.post("/settings/{key}")
async def create_or_update_setting(key: str, setting: SettingCreate) -> SettingResponse:
    """Create a new setting or update if exists (upsert)."""
    config_manager = get_config_manager()

    # Check if setting exists
    existing = config_manager.db.get_setting(key)

    if existing:
        # Update existing
        category = existing.category
        description = setting.description or existing.description
    else:
        # Create new
        category = setting.category
        description = setting.description or f"Custom setting: {key}"

    # Save setting
    config_manager.set_setting(
        key=key,
        value=setting.value,
        category=category,
        description=description,
    )

    # Return setting (with masked API key if applicable)
    display_value = mask_api_key(setting.value) if "api_key" in key else setting.value

    return SettingResponse(
        key=key,
        value=display_value,
        category=category,
        description=description,
    )


@router.post("/settings/bulk")
async def bulk_update_settings(update: BulkSettingUpdate) -> dict[str, str]:
    """Update multiple settings at once."""
    config_manager = get_config_manager()

    updated_count = 0
    for key, value in update.settings.items():
        existing = config_manager.db.get_setting(key)
        if existing:
            config_manager.set_setting(key, value, existing.category, existing.description)
            updated_count += 1

    return {
        "status": "success",
        "message": f"Updated {updated_count} settings",
    }


@router.get("/presets")
async def list_presets(config_type: str | None = None) -> list[PresetResponse]:
    """List all saved presets."""
    config_manager = get_config_manager()

    presets = config_manager.get_all_model_configs(config_type)

    return [
        PresetResponse(
            id=preset.id or 0,
            name=preset.name,
            config_type=preset.config_type,
            model=preset.model,
            api_key=mask_api_key(preset.api_key),
            base_url=preset.base_url,
            temperature=preset.temperature,
            is_active=preset.is_active,
            created_at=preset.created_at.isoformat() if preset.created_at else "",
        )
        for preset in presets
    ]


@router.get("/presets/active")
async def get_active_presets() -> dict[str, PresetResponse | None]:
    """Get currently active presets for each type."""
    config_manager = get_config_manager()

    result: dict[str, PresetResponse | None] = {}

    for config_type in ["llm", "embedding"]:
        active = config_manager.db.get_active_model_config(config_type)
        if active:
            result[config_type] = PresetResponse(
                id=active.id or 0,
                name=active.name,
                config_type=active.config_type,
                model=active.model,
                api_key=mask_api_key(active.api_key),
                base_url=active.base_url,
                temperature=active.temperature,
                is_active=active.is_active,
                created_at=active.created_at.isoformat() if active.created_at else "",
            )
        else:
            result[config_type] = None

    return result


@router.post("/presets")
async def create_preset(preset: PresetCreate) -> PresetResponse:
    """Save current settings as a named preset."""
    config_manager = get_config_manager()

    # Validate config_type
    if preset.config_type not in ["llm", "embedding"]:
        raise HTTPException(
            status_code=400,
            detail="config_type must be 'llm' or 'embedding'"
        )

    # Create preset
    created = config_manager.save_model_config(
        name=preset.name,
        config_type=preset.config_type,
        api_key=preset.api_key,
        base_url=preset.base_url,
        model=preset.model,
        temperature=preset.temperature,
        set_active=preset.set_active,
    )

    return PresetResponse(
        id=created.id or 0,
        name=created.name,
        config_type=created.config_type,
        model=created.model,
        api_key=mask_api_key(created.api_key),
        base_url=created.base_url,
        temperature=created.temperature,
        is_active=created.is_active,
        created_at=created.created_at.isoformat() if created.created_at else "",
    )


@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: int) -> dict[str, str]:
    """Delete a preset."""
    config_manager = get_config_manager()

    success = config_manager.delete_model_config(preset_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    return {
        "status": "success",
        "message": f"Deleted preset {preset_id}",
    }


@router.post("/presets/{preset_id}/activate")
async def activate_preset(preset_id: int) -> dict[str, Any]:
    """Activate a preset (load its settings)."""
    config_manager = get_config_manager()

    activated = config_manager.set_active_model_config(preset_id)

    if not activated:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    return {
        "status": "success",
        "message": f"Activated preset '{activated.name}'",
        "preset": PresetResponse(
            id=activated.id or 0,
            name=activated.name,
            config_type=activated.config_type,
            model=activated.model,
            api_key=mask_api_key(activated.api_key),
            base_url=activated.base_url,
            temperature=activated.temperature,
            is_active=activated.is_active,
            created_at=activated.created_at.isoformat() if activated.created_at else "",
        ),
    }


@router.post("/reload")
async def reload_from_env() -> dict[str, str]:
    """Reload configuration from .env file."""
    config_manager = get_config_manager()

    # Re-sync environment variables to database
    config_manager._sync_env_to_db()

    # Reload model choices from model_config.yml
    config_manager.reload_model_choices()

    return {
        "status": "success",
        "message": "Configuration reloaded from .env and model_config.yml",
    }


@router.get("/model-choices")
async def get_model_choices() -> dict[str, Any]:
    """Get available model choices from model_config.yml."""
    config_manager = get_config_manager()

    return config_manager.get_model_choices()
