"""Database models for FinAgent."""

from datetime import datetime

from pydantic import BaseModel, Field


class Setting(BaseModel):
    """Application setting stored in database."""

    id: int | None = None
    key: str = Field(..., description="Setting key (e.g., 'llm_api_key', 'llm_model')")
    value: str = Field(..., description="Setting value")
    category: str = Field(
        default="general", description="Setting category (general, llm, embedding, vector_db)"
    )
    description: str | None = Field(None, description="Setting description")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelConfig(BaseModel):
    """Model configuration stored in database."""

    id: int | None = None
    name: str = Field(
        ..., description="Configuration name (e.g., 'Production LLM', 'Dev Environment')"
    )
    config_type: str = Field(..., description="Config type (llm, embedding)")
    api_key: str = Field(default="", description="API key")
    base_url: str = Field(default="", description="Base URL (empty for OpenAI)")
    model: str = Field(..., description="Model name")
    temperature: float | None = Field(default=0.0, description="Temperature (for LLM only)")
    is_active: bool = Field(default=False, description="Whether this config is currently active")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class History(BaseModel):
    """Query/interaction history."""

    id: int | None = None
    session_id: str | None = Field(None, description="Session identifier")
    query: str = Field(..., description="User query")
    response: str | None = Field(None, description="Agent response")
    model_used: str | None = Field(None, description="Model used for this query")
    tokens_used: int | None = Field(None, description="Total tokens used")
    cost_usd: float | None = Field(None, description="Estimated cost in USD")
    processing_time_seconds: float | None = Field(None, description="Processing time in seconds")
    success: bool = Field(default=True, description="Whether the query was successful")
    error_message: str | None = Field(None, description="Error message if failed")
    metadata: str | None = Field(None, description="Additional metadata (JSON string)")
    created_at: datetime | None = None


class Document(BaseModel):
    """Document metadata stored in database."""

    id: int | None = None
    doc_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Document filename")
    file_path: str = Field(..., description="Full path to document file")
    description: str | None = Field(None, description="Human-readable description")
    document_type: str | None = Field(None, description="Document type (e.g., 裁罰書, 判決書)")
    keywords: list[str] = Field(default_factory=list, description="Keywords/topics")
    document_date: str | None = Field(None, description="Document date (YYYY-MM-DD)")
    issuing_authority: str | None = Field(None, description="Issuing authority (e.g., 金管會)")
    related_institutions: list[str] = Field(default_factory=list, description="Related institutions")
    penalty_amount: str | None = Field(None, description="Penalty amount if applicable")
    violation_types: list[str] = Field(default_factory=list, description="Types of violations")
    custom_fields: dict | None = Field(default_factory=dict, description="Custom metadata")
    indexed: bool = Field(default=False, description="Whether indexed in vector DB")
    chunk_count: int = Field(default=0, description="Number of chunks in vector DB")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Metadata extraction status fields (added 2025-01-19)
    metadata_extracted: bool = Field(default=False, description="Whether metadata has been extracted by LLM")
    metadata_extraction_status: str = Field(default="pending", description="Status: pending, processing, completed, failed, user_edited")
    metadata_extraction_error: str | None = Field(None, description="Error message if extraction failed")
    metadata_extraction_attempts: int = Field(default=0, description="Number of extraction attempts")
    metadata_last_extracted_at: datetime | None = Field(None, description="Timestamp of last extraction")
    metadata_edited_by_user: bool = Field(default=False, description="Whether user manually edited metadata")
    extraction_confidence: float | None = Field(None, description="Extraction confidence score (0-1)")

    # Pipeline monitoring fields (added 2025-11-19)
    pipeline_stage: str = Field(default="uploaded", description="Current pipeline stage")
    pipeline_status: str = Field(default="in_progress", description="Overall pipeline status")
    pipeline_data: str | None = Field(None, description="JSON data with detailed pipeline stage information")
    pipeline_started_at: datetime | None = Field(None, description="Pipeline start time")
    pipeline_completed_at: datetime | None = Field(None, description="Pipeline completion time")


class Concept(BaseModel):
    """Concept/topic extracted from documents for faster retrieval."""

    id: int | None = None
    concept_name: str = Field(..., description="Concept name (e.g., 洗錢防制, 內線交易)")
    concept_type: str | None = Field(None, description="Type: violation_type, institution, authority, topic")
    description: str | None = Field(None, description="Brief description")
    keywords: list[str] = Field(default_factory=list, description="Related keywords")
    document_count: int = Field(default=0, description="Number of documents with this concept")
    metadata: dict | None = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentConcept(BaseModel):
    """Many-to-many mapping between documents and concepts."""

    id: int | None = None
    doc_id: str = Field(..., description="Document ID")
    concept_id: int = Field(..., description="Concept ID")
    relevance_score: float = Field(default=1.0, description="Relevance score (0-1)")
    created_at: datetime | None = None
