"""Configuration management for FinAgent."""

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
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # LLM Configuration (OpenAI-compatible API)
    # Works with OpenAI, Ollama, or any OpenAI-compatible endpoint
    llm_api_key: str = Field(default="", description="LLM API key")
    llm_base_url: str = Field(
        default="", description="LLM base URL (leave empty for OpenAI, or provide custom endpoint)"
    )
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_temperature: float = Field(default=0.0, description="LLM temperature")

    # Embedding Configuration (OpenAI-compatible API)
    # Works with OpenAI, local embedding servers, or any OpenAI-compatible endpoint
    embedding_api_key: str = Field(
        default="", description="Embedding API key (leave empty to use llm_api_key)"
    )
    embedding_base_url: str = Field(
        default="", description="Embedding base URL (leave empty to use llm_base_url)"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Embedding model name"
    )

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

    @property
    def effective_llm_api_key(self) -> str:
        """Get effective LLM API key."""
        return self.llm_api_key

    @property
    def effective_llm_base_url(self) -> str:
        """Get effective LLM base URL (empty string means use OpenAI default)."""
        return self.llm_base_url

    @property
    def effective_embedding_api_key(self) -> str:
        """Get effective embedding API key (falls back to LLM API key)."""
        return self.embedding_api_key or self.llm_api_key

    @property
    def effective_embedding_base_url(self) -> str:
        """Get effective embedding base URL (falls back to LLM base URL)."""
        return self.embedding_base_url or self.llm_base_url

    @property
    def use_local_llm(self) -> bool:
        """Check if using custom endpoint (not OpenAI)."""
        return bool(self.llm_base_url)

    @property
    def use_local_embedding(self) -> bool:
        """Check if using custom endpoint for embeddings (not OpenAI)."""
        return bool(self.embedding_base_url or self.llm_base_url)


# Global settings instance
settings = Settings()


def reload_settings():
    """Reload settings from .env file."""
    global settings
    settings = Settings()
    return settings
