"""Query and task models."""

from enum import Enum

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Type of research task."""

    SEARCH = "搜尋"  # Search for documents/cases
    RETRIEVAL = "檢索"  # Retrieve specific documents
    ANALYSIS = "分析"  # Analyze documents
    COMPARISON = "比較"  # Compare cases
    VALIDATION = "驗證"  # Validate information


class Task(BaseModel):
    """
    Research task with legal-specific context.

    Represents a single step in the research plan.
    """

    id: int = Field(..., description="Task ID")
    description: str = Field(..., description="Task description")
    task_type: TaskType = Field(..., description="Type of task")
    done: bool = Field(default=False, description="Whether task is completed")

    # Legal-specific fields
    jurisdiction: str | None = Field(None, description="Jurisdiction (e.g., '金管會')")
    required_sources: list[str] = Field(
        default_factory=list, description="Required source types (e.g., ['主要來源'])"
    )
    dependencies: list[int] = Field(
        default_factory=list, description="Task IDs that must be completed first"
    )

    # Execution tracking
    tool_name: str | None = Field(None, description="Tool to use for this task")
    result: str | None = Field(None, description="Task result")
    error: str | None = Field(None, description="Error message if task failed")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "description": "搜尋金管會對玉山銀行於2019-2020年間的裁罰記錄",
                "task_type": "搜尋",
                "done": False,
                "jurisdiction": "金管會",
                "required_sources": ["主要來源"],
            }
        }


class Query(BaseModel):
    """User query for legal research."""

    text: str = Field(
        ..., min_length=1, max_length=2000, description="Query text in Traditional Chinese"
    )
    max_results: int = Field(default=5, ge=1, le=50, description="Maximum number of results")
    include_full_documents: bool = Field(
        default=False, description="Whether to include full document text"
    )

    # Optional filters
    regulator: str | None = Field(None, description="Filter by regulator (e.g., '金管會')")
    start_date: str | None = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: str | None = Field(None, description="End date (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "玉山銀行在2020年因洗錢防制違規受到什麼處分？",
                "max_results": 5,
                "include_full_documents": False,
                "regulator": "金管會",
            }
        }


class QueryResponse(BaseModel):
    """Response to a query containing query ID and status."""

    query_id: str = Field(..., description="Unique query identifier")
    status: str = Field(..., description="Query processing status")
    message: str = Field(default="Query submitted successfully")
