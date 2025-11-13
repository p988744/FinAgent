"""Configuration manager with database persistence."""

from typing import Optional, Dict, Any
from pathlib import Path
import os

from .config import Settings, settings as env_settings
from .database import get_db, Setting, ModelConfig
from .model_config_loader import get_model_config


class ConfigManager:
    """Manager for application configuration with database persistence."""

    def __init__(self):
        """Initialize configuration manager."""
        self.db = get_db()
        self.model_config_loader = get_model_config()
        self._initialize_from_env()

    def _initialize_from_env(self):
        """Initialize database settings from environment variables on first run."""
        # Check if settings exist in database
        existing_settings = self.db.get_all_settings()

        if not existing_settings:
            # First run - populate database from .env
            self._sync_env_to_db()

    def _sync_env_to_db(self):
        """Sync environment variables to database."""
        # LLM settings
        self.db.set_setting(
            "llm_api_key",
            env_settings.llm_api_key,
            category="llm",
            description="LLM API key",
        )
        self.db.set_setting(
            "llm_base_url",
            env_settings.llm_base_url,
            category="llm",
            description="LLM base URL (empty for OpenAI)",
        )
        self.db.set_setting(
            "llm_model",
            env_settings.llm_model,
            category="llm",
            description="LLM model name",
        )
        self.db.set_setting(
            "llm_temperature",
            str(env_settings.llm_temperature),
            category="llm",
            description="LLM temperature",
        )

        # Embedding settings
        self.db.set_setting(
            "embedding_api_key",
            env_settings.embedding_api_key,
            category="embedding",
            description="Embedding API key (fallback to llm_api_key)",
        )
        self.db.set_setting(
            "embedding_base_url",
            env_settings.embedding_base_url,
            category="embedding",
            description="Embedding base URL (fallback to llm_base_url)",
        )
        self.db.set_setting(
            "embedding_model",
            env_settings.embedding_model,
            category="embedding",
            description="Embedding model name",
        )

        # Vector DB settings
        self.db.set_setting(
            "chroma_persist_directory",
            env_settings.chroma_persist_directory,
            category="vector_db",
            description="Chroma persistence directory",
        )
        self.db.set_setting(
            "chroma_collection_name",
            env_settings.chroma_collection_name,
            category="vector_db",
            description="Chroma collection name",
        )

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value from database.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        setting = self.db.get_setting(key)
        if setting:
            return setting.value
        return default

    def set_setting(self, key: str, value: str, category: str = "general", description: Optional[str] = None):
        """Set a setting value in database.

        Args:
            key: Setting key
            value: Setting value
            category: Setting category
            description: Optional description
        """
        self.db.set_setting(key, value, category, description)

    def get_all_settings(self, category: Optional[str] = None) -> Dict[str, str]:
        """Get all settings as dictionary.

        Args:
            category: Optional category filter

        Returns:
            Dictionary mapping keys to values
        """
        return self.db.get_settings_as_dict(category)

    def get_active_llm_config(self) -> Dict[str, Any]:
        """Get active LLM configuration.

        Returns:
            Dictionary with LLM configuration
        """
        # Check if there's an active model config in database
        active_config = self.db.get_active_model_config("llm")

        if active_config:
            return {
                "api_key": active_config.api_key,
                "base_url": active_config.base_url,
                "model": active_config.model,
                "temperature": active_config.temperature,
                "source": "database",
                "config_name": active_config.name,
            }

        # Fall back to database settings
        return {
            "api_key": self.get_setting("llm_api_key", env_settings.llm_api_key),
            "base_url": self.get_setting("llm_base_url", env_settings.llm_base_url),
            "model": self.get_setting("llm_model", env_settings.llm_model),
            "temperature": float(
                self.get_setting("llm_temperature", str(env_settings.llm_temperature))
            ),
            "source": "settings",
        }

    def get_active_embedding_config(self) -> Dict[str, Any]:
        """Get active embedding configuration.

        Returns:
            Dictionary with embedding configuration
        """
        # Check if there's an active model config in database
        active_config = self.db.get_active_model_config("embedding")

        if active_config:
            return {
                "api_key": active_config.api_key,
                "base_url": active_config.base_url,
                "model": active_config.model,
                "source": "database",
                "config_name": active_config.name,
            }

        # Fall back to database settings (with fallback logic)
        llm_api_key = self.get_setting("llm_api_key", env_settings.llm_api_key)
        llm_base_url = self.get_setting("llm_base_url", env_settings.llm_base_url)

        embedding_api_key = self.get_setting(
            "embedding_api_key", env_settings.embedding_api_key
        )
        embedding_base_url = self.get_setting(
            "embedding_base_url", env_settings.embedding_base_url
        )

        return {
            "api_key": embedding_api_key or llm_api_key,
            "base_url": embedding_base_url or llm_base_url,
            "model": self.get_setting("embedding_model", env_settings.embedding_model),
            "source": "settings",
        }

    def save_model_config(
        self,
        name: str,
        config_type: str,
        api_key: str,
        base_url: str,
        model: str,
        temperature: Optional[float] = 0.0,
        set_active: bool = False,
    ) -> ModelConfig:
        """Save a model configuration.

        Args:
            name: Configuration name
            config_type: 'llm' or 'embedding'
            api_key: API key
            base_url: Base URL
            model: Model name
            temperature: Temperature (LLM only)
            set_active: Whether to set as active

        Returns:
            Created ModelConfig object
        """
        return self.db.save_model_config(
            name=name,
            config_type=config_type,
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            is_active=set_active,
        )

    def get_all_model_configs(self, config_type: Optional[str] = None) -> list[ModelConfig]:
        """Get all saved model configurations.

        Args:
            config_type: Optional type filter ('llm' or 'embedding')

        Returns:
            List of ModelConfig objects
        """
        return self.db.get_all_model_configs(config_type)

    def set_active_model_config(self, config_id: int) -> Optional[ModelConfig]:
        """Set a model config as active.

        Args:
            config_id: Configuration ID

        Returns:
            Updated ModelConfig or None
        """
        return self.db.set_active_model_config(config_id)

    def delete_model_config(self, config_id: int) -> bool:
        """Delete a model configuration.

        Args:
            config_id: Configuration ID

        Returns:
            True if deleted
        """
        return self.db.delete_model_config(config_id)

    def get_model_choices(self):
        """Get model choices from model_config.yml.

        Returns:
            Dictionary with model choices
        """
        return {
            "openai_chat_models": self.model_config_loader.get_openai_chat_models(),
            "openai_embedding_models": self.model_config_loader.get_openai_embedding_models(),
            "local_llm_presets": self.model_config_loader.get_local_llm_presets(),
            "temperature_presets": self.model_config_loader.get_temperature_presets(),
        }

    def reload_model_choices(self):
        """Reload model choices from model_config.yml."""
        self.model_config_loader.reload()

    def sync_to_env_file(self, env_path: str = ".env"):
        """Sync current settings to .env file.

        Args:
            env_path: Path to .env file
        """
        settings_dict = self.get_all_settings()

        # Read existing .env
        env_file = Path(env_path)
        if env_file.exists():
            with open(env_file, "r") as f:
                lines = f.readlines()
        else:
            lines = []

        # Update or add settings
        updated_keys = set()
        new_lines = []

        for line in lines:
            line = line.rstrip()
            if "=" in line and not line.strip().startswith("#"):
                key = line.split("=")[0].strip()
                key_lower = key.lower()

                if key_lower in settings_dict:
                    # Update existing setting
                    new_lines.append(f"{key}={settings_dict[key_lower]}\n")
                    updated_keys.add(key_lower)
                else:
                    new_lines.append(line + "\n")
            else:
                new_lines.append(line + "\n")

        # Add new settings that weren't in .env
        for key, value in settings_dict.items():
            if key not in updated_keys:
                new_lines.append(f"{key.upper()}={value}\n")

        # Write back to .env
        with open(env_file, "w") as f:
            f.writelines(new_lines)


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
