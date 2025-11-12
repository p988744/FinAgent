"""Configuration management for FinAgent."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", description="Environment: development, production")
    app_name: str = Field(default="Legal Research Agent", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    log_level: str = Field(default="INFO", description="Logging level")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="Auto-reload on code changes")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # OpenAI / LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )
    openai_temperature: float = Field(default=0.0, description="LLM temperature")

    # Local LLM (OpenAI-compatible API)
    use_local_llm: bool = Field(default=False, description="Use local LLM instead of OpenAI for chat/completion")
    use_local_embedding: bool = Field(default=False, description="Use local embedding model instead of OpenAI")
    local_llm_base_url: str = Field(default="http://localhost:11434/v1", description="Local LLM base URL (OpenAI-compatible)")
    local_llm_api_key: str = Field(default="ollama", description="Local LLM API key (can be any string for local models)")
    local_llm_model: str = Field(default="qwen2.5:7b", description="Local LLM model name")
    local_embedding_model: str = Field(default="", description="Local embedding model name (if using local embeddings)")
    local_embedding_base_url: str = Field(default="", description="Local embedding base URL (if different from LLM base URL)")
    local_embedding_api_key: str = Field(default="", description="Local embedding API key (if different from LLM API key)")

    # Vector Database (Chroma)
    chroma_persist_directory: str = Field(
        default="./data/vector_db", description="Chroma persistence directory"
    )
    chroma_collection_name: str = Field(
        default="legal_documents", description="Chroma collection name"
    )

    # FSC Scraping (金管會)
    fsc_base_url: str = Field(default="https://www.fsc.gov.tw", description="FSC base URL")
    scraping_delay_seconds: int = Field(default=1, description="Delay between scraping requests")
    scraping_max_retries: int = Field(default=3, description="Max retry attempts for scraping")
    scraping_timeout_seconds: int = Field(default=30, description="Scraping request timeout")

    # Feature Flags
    enable_caching: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    max_document_size_mb: int = Field(default=50, description="Maximum document size in MB")

    # Rate Limiting
    max_concurrent_requests: int = Field(default=5, description="Max concurrent requests")
    request_timeout_seconds: int = Field(default=60, description="Request timeout in seconds")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


# Global settings instance
settings = Settings()


def reload_settings():
    """Reload settings from .env file."""
    global settings
    settings = Settings()
    return settings
