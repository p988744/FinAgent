"""
Wiki API Response Schemas

Pydantic models for wiki API endpoints.
"""

from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Category Schemas
# ============================================================================


class CategorySummary(BaseModel):
    """Summary of a single category."""

    id: int
    name: str
    type: str  # authority, institution, violation, doc_type
    document_count: int
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class CategoryDetail(BaseModel):
    """Detailed category information with metadata."""

    id: int
    name: str
    type: str
    document_count: int
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None


class CategoryTree(BaseModel):
    """Hierarchical category tree."""

    type: str  # authority, institution, violation, doc_type
    total_count: int
    categories: list[CategorySummary]


# ============================================================================
# Document Schemas
# ============================================================================


class DocumentSummary(BaseModel):
    """Brief document information for lists."""

    doc_id: str
    filename: str
    document_type: str | None = None
    issuing_authority: str | None = None
    date: str | None = None
    related_institutions: list[str] = Field(default_factory=list)
    violation_types: list[str] = Field(default_factory=list)
    extraction_confidence: float | None = None


class DocumentDetail(BaseModel):
    """Full document metadata."""

    doc_id: str
    filename: str
    file_path: str
    document_type: str | None = None
    issuing_authority: str | None = None
    date: str | None = None
    case_number: str | None = None
    related_institutions: list[str] = Field(default_factory=list)
    violation_types: list[str] = Field(default_factory=list)
    penalty_amount: str | None = None
    keywords: list[str] = Field(default_factory=list)
    extraction_confidence: float | None = None
    full_content: str | None = None
    chunk_count: int = 0
    indexed: bool = False
    file_size: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    related_documents: list["RelatedDocument"] = Field(default_factory=list)


class RelatedDocument(BaseModel):
    """Related document with relationship strength."""

    doc_id: str
    filename: str
    relationship_type: str  # related, temporal, citation
    strength: float  # 0.0-1.0
    reason: str | None = None


class DocumentList(BaseModel):
    """Paginated document list."""

    total: int
    offset: int
    limit: int
    documents: list[DocumentSummary]


# ============================================================================
# Statistics Schemas
# ============================================================================


class DocumentStats(BaseModel):
    """Overall document statistics."""

    total_documents: int
    with_metadata: int
    without_metadata: int
    by_type: dict[str, int] = Field(default_factory=dict)
    by_authority: dict[str, int] = Field(default_factory=dict)
    avg_confidence: float | None = None


class TimelineDataPoint(BaseModel):
    """Single data point for timeline."""

    period: str  # e.g., "2020", "2020-01", "2020-01-15"
    count: int
    label: str | None = None


class TimelineStats(BaseModel):
    """Timeline statistics."""

    granularity: str  # year, month, day
    data: list[TimelineDataPoint]
    total_count: int
    date_range: dict[str, str | None] = Field(
        default_factory=lambda: {"earliest": None, "latest": None}
    )


class TopEntity(BaseModel):
    """Top entity (institution or violation) with count."""

    name: str
    count: int
    percentage: float


class TopEntitiesStats(BaseModel):
    """Top entities statistics."""

    institutions: list[TopEntity]
    violations: list[TopEntity]
    authorities: list[TopEntity]


# ============================================================================
# Wiki Overview Schemas
# ============================================================================


class WikiOverview(BaseModel):
    """Complete wiki overview."""

    total_documents: int
    total_categories: int
    categories_by_type: dict[str, int] = Field(default_factory=dict)
    document_stats: DocumentStats
    recent_documents: list[DocumentSummary] = Field(default_factory=list)
    top_entities: TopEntitiesStats
    generated_at: str | None = None


# ============================================================================
# Search Schemas
# ============================================================================


class SearchFilters(BaseModel):
    """Search filter parameters."""

    document_type: str | None = None
    authority: str | None = None
    institution: str | None = None
    violation: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    min_confidence: float | None = None


class SearchResult(BaseModel):
    """Single search result."""

    doc_id: str
    filename: str
    document_type: str | None = None
    relevance_score: float
    snippet: str | None = None
    highlights: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Search results response."""

    query: str
    total_results: int
    offset: int
    limit: int
    results: list[SearchResult]
    filters_applied: SearchFilters | None = None


# ============================================================================
# Operation Response Schemas
# ============================================================================


class WikiRebuildResponse(BaseModel):
    """Wiki rebuild operation response."""

    success: bool
    rebuild_time_ms: int
    categories_created: int
    documents_categorized: int
    relationships_detected: int
    statistics_updated: bool
    message: str


class StatsRefreshResponse(BaseModel):
    """Statistics refresh response."""

    success: bool
    statistics_updated: bool
    cached_at: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_type: str | None = None
    error_code: str | None = None


# Update forward references
DocumentDetail.model_rebuild()
