"""Database models for FinAgent."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Setting(BaseModel):
    """Application setting stored in database."""

    id: Optional[int] = None
    key: str = Field(..., description="Setting key (e.g., 'llm_api_key', 'llm_model')")
    value: str = Field(..., description="Setting value")
    category: str = Field(default="general", description="Setting category (general, llm, embedding, vector_db)")
    description: Optional[str] = Field(None, description="Setting description")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ModelConfig(BaseModel):
    """Model configuration stored in database."""

    id: Optional[int] = None
    name: str = Field(..., description="Configuration name (e.g., 'Production LLM', 'Dev Environment')")
    config_type: str = Field(..., description="Config type (llm, embedding)")
    api_key: str = Field(default="", description="API key")
    base_url: str = Field(default="", description="Base URL (empty for OpenAI)")
    model: str = Field(..., description="Model name")
    temperature: Optional[float] = Field(default=0.0, description="Temperature (for LLM only)")
    is_active: bool = Field(default=False, description="Whether this config is currently active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class History(BaseModel):
    """Query/interaction history."""

    id: Optional[int] = None
    session_id: Optional[str] = Field(None, description="Session identifier")
    query: str = Field(..., description="User query")
    response: Optional[str] = Field(None, description="Agent response")
    model_used: Optional[str] = Field(None, description="Model used for this query")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time in seconds")
    success: bool = Field(default=True, description="Whether the query was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[str] = Field(None, description="Additional metadata (JSON string)")
    created_at: Optional[datetime] = None
