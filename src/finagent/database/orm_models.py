"""SQLAlchemy ORM models for Alembic migrations."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Document(Base):
    """Document table."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Text, nullable=False, unique=True, index=True)
    filename = Column(Text, nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    description = Column(Text)
    document_type = Column(Text, index=True)
    keywords = Column(Text)  # JSON array
    document_date = Column(Text)
    issuing_authority = Column(Text, index=True)
    related_institutions = Column(Text)  # JSON array
    penalty_amount = Column(Text)
    violation_types = Column(Text)  # JSON array
    custom_fields = Column(Text)  # JSON object
    indexed = Column(Boolean, default=False, index=True)
    chunk_count = Column(Integer, default=0)

    # Metadata extraction status fields
    metadata_extracted = Column(Boolean, default=False)
    metadata_extraction_status = Column(Text, default="pending")
    metadata_extraction_error = Column(Text)
    metadata_extraction_attempts = Column(Integer, default=0)
    metadata_last_extracted_at = Column(DateTime)
    metadata_edited_by_user = Column(Boolean, default=False)
    extraction_confidence = Column(Float)

    # Pipeline monitoring fields
    pipeline_stage = Column(Text, default="uploaded")
    pipeline_status = Column(Text, default="in_progress")
    pipeline_data = Column(Text)  # JSON data
    pipeline_started_at = Column(DateTime, default=func.now())
    pipeline_completed_at = Column(DateTime)

    # Wiki-related fields
    title = Column(Text)
    category_id = Column(Integer, ForeignKey("wiki_categories.id"))
    content_preview = Column(Text)
    full_content = Column(Text)  # Complete document content for wiki display
    extraction_method = Column(Text, default="none")
    case_number = Column(Text)
    language = Column(Text, default="zh-TW")
    document_status = Column(Text, default="active")
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class WikiCategory(Base):
    """Wiki categories table."""

    __tablename__ = "wiki_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    category_type = Column(
        Text,
        nullable=False,
        index=True,
    )
    parent_id = Column(Integer, ForeignKey("wiki_categories.id"), index=True)
    description = Column(Text)
    icon = Column(Text)
    document_count = Column(Integer, default=0, index=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id_1 = Column(Text, nullable=False, index=True)
    doc_id_2 = Column(Text, nullable=False, index=True)
    relationship_type = Column(Text, nullable=False, index=True)
    strength = Column(Float, default=0.5, index=True)
    relationship_metadata = Column("metadata", Text)  # JSON - using column name 'metadata' but attribute 'relationship_metadata'
    created_at = Column(DateTime, default=func.now())

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_type = Column(Text, nullable=False, index=True)
    stat_key = Column(Text, index=True)
    stat_value = Column(Integer, nullable=False)
    stat_metadata = Column("metadata", Text)  # JSON - using column name 'metadata' but attribute 'stat_metadata'
    calculated_at = Column(DateTime, default=func.now(), index=True)


class Setting(Base):
    """Application settings table."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(Text, nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    category = Column(Text, default="general", index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ModelConfigTable(Base):
    """Model configurations table."""

    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    config_type = Column(Text, nullable=False, index=True)
    api_key = Column(Text, default="")
    base_url = Column(Text, default="")
    model = Column(Text, nullable=False)
    temperature = Column(Float)
    is_active = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class History(Base):
    """Query history table."""

    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text)
    model_used = Column(Text)
    tokens_used = Column(Integer)
    cost_usd = Column(Float)
    processing_time_seconds = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now(), index=True)


class Concept(Base):
    """Concepts table."""

    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    concept_type = Column(Text, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DocumentConcept(Base):
    """Document-Concept relationship table."""

    __tablename__ = "document_concepts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Text, nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("doc_id", "concept_id", name="uq_doc_concept"),)
