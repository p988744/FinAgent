"""Data models for the WikiBuilder workflow."""

from enum import Enum
from typing import Any, List, Optional, TypedDict

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
    source_text: Optional[str] = Field(default=None, description="Source text snippet")


class ExtractedMetadata(BaseModel):
    """Metadata extracted from a document."""

    title: str = Field(description="Document title")
    description: str = Field(description="2-3 sentence summary")
    document_type: str = Field(description="裁罰書, 判決書, 法規, etc.")
    issuing_authority: Optional[str] = Field(default=None, description="發文機關")
    case_number: Optional[str] = Field(default=None, description="案號")
    document_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    related_institutions: List[str] = Field(default_factory=list, description="金融機構")
    violation_types: List[str] = Field(default_factory=list, description="違規類型")
    penalty_amount: Optional[str] = Field(default=None, description="裁罰金額")
    keywords: List[str] = Field(default_factory=list, description="關鍵詞")
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
    doc_id: Optional[str]
    document_loaded: bool

    # Metadata extraction
    metadata: Optional[dict]  # ExtractedMetadata as dict
    metadata_extracted: bool

    # Concept extraction
    concepts: Optional[List[dict]]  # List[Concept] as dict
    concepts_extracted: bool

    # Chunking
    chunks: Optional[List[dict]]  # List[TextChunk] as dict
    chunk_count: int

    # Indexing
    indexed: bool
    index_success: bool

    # Category building
    categories_updated: Optional[List[dict]]  # List[CategoryUpdate] as dict

    # Progress tracking
    current_stage: str  # ProcessingStage value
    progress: int  # 0-100
    error: Optional[str]

    # Timing
    started_at: Optional[str]
    completed_at: Optional[str]


class WikiBuilderProgress(BaseModel):
    """Progress update for WebSocket streaming."""

    doc_id: str
    filename: str
    stage: ProcessingStage
    progress: int
    message: str
    chunk_count: int = 0
    categories_count: int = 0
    error: Optional[str] = None


class WikiBuilderResult(BaseModel):
    """Final result of the WikiBuilder workflow."""

    success: bool
    doc_id: str
    filename: str
    metadata: Optional[ExtractedMetadata] = None
    concepts: List[Concept] = Field(default_factory=list)
    chunk_count: int = 0
    categories_updated: List[CategoryUpdate] = Field(default_factory=list)
    processing_time_ms: int = 0
    error: Optional[str] = None
