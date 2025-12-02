"""Data models for the WikiSearch workflow."""

from enum import Enum
from typing import TypedDict

from langchain_core.documents import Document
from pydantic import BaseModel, Field


class SearchStrategy(str, Enum):
    """Search strategy types."""

    SEMANTIC = "semantic"  # Vector similarity search
    KEYWORD = "keyword"  # Exact keyword matching
    HYBRID = "hybrid"  # Combined BM25 + Vector
    CATEGORY = "category"  # Category-based filtering


class QueryType(str, Enum):
    """Query type classification."""

    FACTUAL = "factual"  # Specific fact lookup
    ANALYTICAL = "analytical"  # Requires analysis
    COMPARATIVE = "comparative"  # Comparing entities
    TEMPORAL = "temporal"  # Time-based queries
    EXPLORATORY = "exploratory"  # Broad browsing


class QueryInsight(BaseModel):
    """Analysis of the user's query."""

    query_type: QueryType = Field(description="Type of query")
    key_entities: list[str] = Field(default_factory=list, description="Key entities mentioned")
    key_topics: list[str] = Field(default_factory=list, description="Key topics/concepts")
    search_strategy: SearchStrategy = Field(description="Recommended search strategy")
    date_range: str | None = Field(default=None, description="Date range if temporal")
    complexity: str = Field(default="medium", description="Query complexity: simple, medium, complex")
    reasoning: str = Field(description="Brief explanation of the analysis")


class SearchTask(BaseModel):
    """A single search task in the retrieval plan."""

    id: int = Field(description="Task ID")
    description: str = Field(description="What to search for")
    tool: str = Field(description="Tool to use: retriever, hard_search, hybrid_search")
    query: str = Field(description="Search query")
    filters: dict = Field(default_factory=dict, description="Optional filters")
    priority: int = Field(default=1, description="Priority 1-5, 1 is highest")


class SearchPlan(BaseModel):
    """Plan for executing multiple searches."""

    tasks: list[SearchTask] = Field(default_factory=list, description="Search tasks to execute")
    strategy: SearchStrategy = Field(description="Overall search strategy")
    max_results_per_task: int = Field(default=5, description="Max results per task")
    merge_strategy: str = Field(default="relevance", description="How to merge results")


class SearchResult(BaseModel):
    """Result from a single search task."""

    task_id: int = Field(description="Task ID")
    tool_used: str = Field(description="Tool that was used")
    query: str = Field(description="Search query")
    documents: list[dict] = Field(default_factory=list, description="Retrieved documents")
    result_count: int = Field(default=0, description="Number of results")
    execution_time_ms: int = Field(default=0, description="Execution time")
    success: bool = Field(default=True, description="Whether search succeeded")
    error: str | None = Field(default=None, description="Error message if failed")


class MergedResult(BaseModel):
    """Merged and deduplicated search results."""

    documents: list[dict] = Field(default_factory=list, description="Merged documents")
    total_unique: int = Field(default=0, description="Total unique documents")
    sources: list[str] = Field(default_factory=list, description="Source tasks")
    relevance_scores: list[float] = Field(default_factory=list, description="Relevance scores")


class WikiCitation(BaseModel):
    """Citation for wiki report."""

    id: int = Field(description="Citation ID")
    source: str = Field(description="Source document name")
    excerpt: str = Field(description="Relevant excerpt")
    relevance: float = Field(default=1.0, description="Relevance score")


class WikiSearchState(TypedDict):
    """State for the WikiSearch workflow."""

    # Input
    input: str

    # Query analysis
    query_insight: dict | None  # QueryInsight as dict

    # Search planning
    search_plan: dict | None  # SearchPlan as dict

    # Search execution
    search_results: list[dict] | None  # List[SearchResult] as dict

    # Result merging
    merged_results: dict | None  # MergedResult as dict

    # Final output
    documents: list[Document]
    response: str
    citations: list[dict] | None  # List[WikiCitation] as dict

    # Progress tracking
    current_stage: str
    progress: int
    error: str | None
