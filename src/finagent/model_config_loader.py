"""Model configuration loader for managing LLM model choices."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ModelInfo:
    """Information about an LLM model."""

    id: str
    name: str
    description: str
    recommended: bool = False
    default: bool = False
    dimensions: int | None = None  # For embedding models


@dataclass
class LocalLLMPreset:
    """Preset configuration for local LLM."""

    name: str
    base_url: str
    model: str
    api_key: str
    description: str
    recommended: bool = False


class ModelConfigLoader:
    """Loads and manages model configuration from YAML file."""

    def __init__(self, config_path: str | None = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to model_config.yml (default: backend/model_config.yml)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Try to find config file
            possible_paths = [
                Path.cwd() / "model_config.yml",
                Path.cwd() / "backend" / "model_config.yml",
                Path(__file__).parent.parent.parent / "model_config.yml",
            ]

            self.config_path = None
            for path in possible_paths:
                if path.exists():
                    self.config_path = path
                    break

            if not self.config_path:
                raise FileNotFoundError(
                    f"model_config.yml not found. Searched: {[str(p) for p in possible_paths]}"
                )

        self.config: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load model_config.yml: {e}")

    def reload(self) -> None:
        """Reload configuration from file."""
        self.load()

    def get_openai_chat_models(self, recommended_only: bool = False) -> list[ModelInfo]:
        """
        Get list of OpenAI chat models.

        Args:
            recommended_only: If True, return only recommended models

        Returns:
            List of ModelInfo objects
        """
        models_data = self.config.get("openai_chat_models", [])
        models = [
            ModelInfo(
                id=m["id"],
                name=m.get("name", m["id"]),
                description=m.get("description", ""),
                recommended=m.get("recommended", False),
                default=m.get("default", False),
            )
            for m in models_data
        ]

        if recommended_only:
            models = [m for m in models if m.recommended]

        return models

    def get_openai_embedding_models(self, recommended_only: bool = False) -> list[ModelInfo]:
        """
        Get list of OpenAI embedding models.

        Args:
            recommended_only: If True, return only recommended models

        Returns:
            List of ModelInfo objects
        """
        models_data = self.config.get("openai_embedding_models", [])
        models = [
            ModelInfo(
                id=m["id"],
                name=m.get("name", m["id"]),
                description=m.get("description", ""),
                recommended=m.get("recommended", False),
                default=m.get("default", False),
                dimensions=m.get("dimensions"),
            )
            for m in models_data
        ]

        if recommended_only:
            models = [m for m in models if m.recommended]

        return models

    def get_local_llm_presets(self, recommended_only: bool = False) -> list[LocalLLMPreset]:
        """
        Get list of local LLM presets.

        Args:
            recommended_only: If True, return only recommended presets

        Returns:
            List of LocalLLMPreset objects
        """
        presets_data = self.config.get("local_llm_presets", [])
        presets = [
            LocalLLMPreset(
                name=p["name"],
                base_url=p["base_url"],
                model=p["model"],
                api_key=p["api_key"],
                description=p.get("description", ""),
                recommended=p.get("recommended", False),
            )
            for p in presets_data
        ]

        if recommended_only:
            presets = [p for p in presets if p.recommended]

        return presets

    def get_default_chat_model(self) -> str | None:
        """Get default chat model ID."""
        models = self.get_openai_chat_models()
        for model in models:
            if model.default:
                return model.id
        # Fallback to first model
        return models[0].id if models else None

    def get_default_embedding_model(self) -> str | None:
        """Get default embedding model ID."""
        models = self.get_openai_embedding_models()
        for model in models:
            if model.default:
                return model.id
        # Fallback to first model
        return models[0].id if models else None

    def should_fetch_openai_models_dynamically(self) -> bool:
        """Check if should fetch models from OpenAI API."""
        settings = self.config.get("settings", {})
        return settings.get("fetch_openai_models_dynamically", True)

    def use_static_model_list(self) -> bool:
        """Check if should use only static model list from config."""
        settings = self.config.get("settings", {})
        return settings.get("use_static_model_list", False)

    def get_max_models_to_display(self) -> int:
        """Get maximum number of models to display."""
        settings = self.config.get("settings", {})
        return settings.get("max_models_to_display", 10)

    def show_only_recommended(self) -> bool:
        """Check if should show only recommended models by default."""
        settings = self.config.get("settings", {})
        return settings.get("show_only_recommended", False)

    def get_temperature_presets(self) -> dict[str, float]:
        """Get temperature presets."""
        settings = self.config.get("settings", {})
        return settings.get(
            "temperature_presets",
            {"deterministic": 0.0, "balanced": 0.3, "creative": 0.7, "very_creative": 1.0},
        )

    def get_cost_info(self, model_id: str) -> dict[str, float] | None:
        """
        Get cost information for a model.

        Args:
            model_id: Model ID

        Returns:
            Dict with cost info or None if not available
        """
        cost_info = self.config.get("cost_info", {})
        return cost_info.get(model_id)


# Global instance
_model_config: ModelConfigLoader | None = None


def get_model_config() -> ModelConfigLoader:
    """Get global model config instance."""
    global _model_config
    if _model_config is None:
        _model_config = ModelConfigLoader()
    return _model_config


def reload_model_config() -> ModelConfigLoader:
    """Reload model configuration from file."""
    global _model_config
    _model_config = ModelConfigLoader()
    return _model_config
