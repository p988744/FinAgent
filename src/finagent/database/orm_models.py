"""SQLAlchemy ORM models for Alembic migrations."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    """Document table."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    document_type: Mapped[str | None] = mapped_column(Text, index=True)
    keywords: Mapped[str | None] = mapped_column(Text)  # JSON array
    mime_type: Mapped[str | None] = mapped_column(Text, default="text/plain")
    file_size: Mapped[int | None] = mapped_column(Integer)
    document_date: Mapped[str | None] = mapped_column(Text)
    issuing_authority: Mapped[str | None] = mapped_column(Text, index=True)
    related_institutions: Mapped[str | None] = mapped_column(Text)  # JSON array
    penalty_amount: Mapped[str | None] = mapped_column(Text)
    violation_types: Mapped[str | None] = mapped_column(Text)  # JSON array
    custom_fields: Mapped[str | None] = mapped_column(Text)  # JSON object
    indexed: Mapped[bool | None] = mapped_column(Boolean, default=False, index=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Metadata extraction status fields
    metadata_extracted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    metadata_extraction_status: Mapped[str | None] = mapped_column(Text, default="pending")
    metadata_extraction_error: Mapped[str | None] = mapped_column(Text)
    metadata_extraction_attempts: Mapped[int | None] = mapped_column(Integer, default=0)
    metadata_last_extracted_at: Mapped[datetime | None] = mapped_column(DateTime)
    metadata_edited_by_user: Mapped[bool | None] = mapped_column(Boolean, default=False)
    extraction_confidence: Mapped[float | None] = mapped_column(Float)

    # Wiki-related fields
    title: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("wiki_categories.id"))
    content_preview: Mapped[str | None] = mapped_column(Text)
    full_content: Mapped[str | None] = mapped_column(Text)  # Complete document content for wiki display
    extraction_method: Mapped[str | None] = mapped_column(Text, default="none")
    case_number: Mapped[str | None] = mapped_column(Text)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime)
    access_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class DocumentPipeline(Base):
    """Document pipeline status table."""

    __tablename__ = "document_pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    stage: Mapped[str | None] = mapped_column(Text, default="uploaded")
    status: Mapped[str | None] = mapped_column(Text, default="in_progress", index=True)
    data: Mapped[str | None] = mapped_column(Text)  # JSON data
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class WikiCategory(Base):
    """Wiki categories table."""

    __tablename__ = "wiki_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("wiki_categories.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(Text)
    document_count: Mapped[int | None] = mapped_column(Integer, default=0, index=True)
    display_order: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", "category_type", name="uq_wiki_category_name_type"),
        CheckConstraint(
            "category_type IN ('authority', 'institution', 'violation', 'document_type')",
            name="ck_wiki_category_type",
        ),
    )


class DocumentRelationship(Base):
    """Document relationships table."""

    __tablename__ = "document_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id_1: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    doc_id_2: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    strength: Mapped[float | None] = mapped_column(Float, default=0.5, index=True)
    relationship_metadata: Mapped[str | None] = mapped_column("metadata", Text)  # JSON - using column name 'metadata' but attribute 'relationship_metadata'
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("doc_id_1", "doc_id_2", "relationship_type", name="uq_doc_rel"),
        CheckConstraint(
            "relationship_type IN ('related', 'supersedes', 'amendment', 'references', 'similar')",
            name="ck_relationship_type",
        ),
        CheckConstraint("strength >= 0 AND strength <= 1", name="ck_relationship_strength"),
    )


class WikiStatistic(Base):
    """Wiki statistics table."""

    __tablename__ = "wiki_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    stat_key: Mapped[str | None] = mapped_column(Text, index=True)
    stat_value: Mapped[int] = mapped_column(Integer, nullable=False)
    stat_metadata: Mapped[str | None] = mapped_column("metadata", Text)  # JSON - using column name 'metadata' but attribute 'stat_metadata'
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), index=True)


class Setting(Base):
    """Application settings table."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text, default="general", index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ModelConfigTable(Base):
    """Model configurations table."""

    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    config_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    api_key: Mapped[str | None] = mapped_column(Text, default="")
    base_url: Mapped[str | None] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(Text, nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class History(Base):
    """Query history table."""

    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(Text, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(Text)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    processing_time_seconds: Mapped[float | None] = mapped_column(Float)
    success: Mapped[bool | None] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata: Mapped[str | None] = mapped_column(Text)  # JSON string for additional data
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), index=True)


class Concept(Base):
    """Concepts table."""

    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    concept_type: Mapped[str | None] = mapped_column(Text, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)  # JSON array
    document_count: Mapped[int | None] = mapped_column(Integer, default=0)
    metadata: Mapped[str | None] = mapped_column(Text)  # JSON object
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class DocumentConcept(Base):
    """Document-Concept relationship table."""

    __tablename__ = "document_concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("document_id", "concept_id", name="uq_doc_concept"),)


class ResearchSession(Base):
    """Research workflow sessions table."""

    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", index=True)
    celery_task_id: Mapped[str | None] = mapped_column(Text, index=True)
    result: Mapped[str | None] = mapped_column(Text)  # JSON string
    error_message: Mapped[str | None] = mapped_column(Text)

    # Agent workflow tracking
    current_agent: Mapped[str | None] = mapped_column(Text)
    agent_steps: Mapped[str | None] = mapped_column(Text)  # JSON array
    todos: Mapped[str | None] = mapped_column(Text)  # JSON array
    activity_log: Mapped[str | None] = mapped_column(Text)  # JSON array
    research_plan: Mapped[str | None] = mapped_column(Text)  # JSON object
    dynamic_plan: Mapped[str | None] = mapped_column(Text)  # JSON object
    tool_executions: Mapped[str | None] = mapped_column(Text)  # JSON object
    step_history: Mapped[str | None] = mapped_column(Text)  # JSON array

    # Performance metrics
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    processing_time_seconds: Mapped[float | None] = mapped_column(Float)
    model_used: Mapped[str | None] = mapped_column(Text)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Float)

    # User interaction
    user_id: Mapped[str | None] = mapped_column(Text, index=True)
    is_bookmarked: Mapped[bool | None] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ToolExecution(Base):
    """Tool executions tracking table."""

    __tablename__ = "tool_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    parameters: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_results: Mapped[str | None] = mapped_column(Text)  # JSON string
    metadata: Mapped[str | None] = mapped_column(Text)  # JSON string
    success: Mapped[bool | None] = mapped_column(Boolean, default=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now(), index=True)
