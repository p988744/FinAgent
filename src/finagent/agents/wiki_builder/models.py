"""Data models for the WikiBuilder workflow."""

from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field


class ProcessingStage(str, Enum):
    """Processing stages for the WikiBuilder workflow."""

    LOADING = "loading"
    EXTRACTING_METADATA = "extracting_metadata"
    EXTRACTING_CONCEPTS = "extracting_concepts"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    BUILDING_CATEGORIES = "building_categories"
    COMPLETE = "complete"
    ERROR = "error"


class Concept(BaseModel):
    """A concept extracted from a document."""

    name: str = Field(description="Concept name (e.g., '洗錢防制', '玉山銀行')")
    concept_type: str = Field(description="Type: entity, topic, regulation, institution")
    confidence: float = Field(default=1.0, description="Extraction confidence 0-1")
    source_text: str | None = Field(default=None, description="Source text snippet")


class ExtractedMetadata(BaseModel):
    """Metadata extracted from a document."""

    title: str = Field(description="Document title")
    description: str = Field(description="2-3 sentence summary")
    document_type: str = Field(description="裁罰書, 判決書, 法規, etc.")
    issuing_authority: str | None = Field(default=None, description="發文機關")
    case_number: str | None = Field(default=None, description="案號")
    document_date: str | None = Field(default=None, description="YYYY-MM-DD")
    related_institutions: list[str] = Field(default_factory=list, description="金融機構")
    violation_types: list[str] = Field(default_factory=list, description="違規類型")
    penalty_amount: str | None = Field(default=None, description="裁罰金額")
    keywords: list[str] = Field(default_factory=list, description="關鍵詞")
    extraction_confidence: float = Field(default=0.0, description="Confidence 0-1")


class TextChunk(BaseModel):
    """A text chunk from a document."""

    chunk_id: int = Field(description="Chunk index within document")
    text: str = Field(description="Chunk text content")
    start_char: int = Field(description="Start character position")
    end_char: int = Field(description="End character position")
    metadata: dict = Field(default_factory=dict, description="Chunk metadata")


class CategoryUpdate(BaseModel):
    """Category update from document processing."""

    category_type: str = Field(description="authority, institution, violation, doc_type")
    category_name: str = Field(description="Category name")
    doc_count: int = Field(description="Number of documents in category")


class WikiBuilderState(TypedDict):
    """State for the WikiBuilder workflow."""

    # Input
    file_path: str
    filename: str
    content: str

    # Document processing
    doc_id: str | None
    document_loaded: bool

    # Metadata extraction
    metadata: dict | None  # ExtractedMetadata as dict
    metadata_extracted: bool

    # Concept extraction
    concepts: list[dict] | None  # List[Concept] as dict
    concepts_extracted: bool

    # Chunking
    chunks: list[dict] | None  # List[TextChunk] as dict
    chunk_count: int

    # Indexing
    indexed: bool
    index_success: bool

    # Category building
    categories_updated: list[dict] | None  # List[CategoryUpdate] as dict

    # Progress tracking
    current_stage: str  # ProcessingStage value
    progress: int  # 0-100
    error: str | None

    # Timing
    started_at: str | None
    completed_at: str | None


class WikiBuilderProgress(BaseModel):
    """Progress update for WebSocket streaming."""

    doc_id: str
    filename: str
    stage: ProcessingStage
    progress: int
    message: str
    chunk_count: int = 0
    categories_count: int = 0
    error: str | None = None


class WikiBuilderResult(BaseModel):
    """Final result of the WikiBuilder workflow."""

    success: bool
    doc_id: str
    filename: str
    metadata: ExtractedMetadata | None = None
    concepts: list[Concept] = Field(default_factory=list)
    chunk_count: int = 0
    categories_updated: list[CategoryUpdate] = Field(default_factory=list)
    processing_time_ms: int = 0
    error: str | None = None
