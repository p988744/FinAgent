"""Todo item model for tracking query execution tasks."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class TodoItem(BaseModel):
    """Represents a task in the query execution plan."""

    id: str = Field(..., description="Unique identifier for the todo item")
    content: str = Field(..., description="Imperative form: 'Retrieve documents'")
    active_form: str = Field(
        ..., description="Present continuous: 'Retrieving documents'"
    )
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        default="pending", description="Current execution status"
    )
    category: Literal["analysis", "retrieval", "validation", "synthesis"] = Field(
        ..., description="Task category"
    )
    can_parallel: bool = Field(
        default=False, description="Can run in parallel with other tasks"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="IDs of tasks that must complete first"
    )
    result: Optional[Any] = Field(default=None, description="Result data from execution")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: Optional[datetime] = Field(default=None, description="Task start time")
    completed_at: Optional[datetime] = Field(
        default=None, description="Task completion time"
    )
    progress_percentage: int = Field(
        default=0, description="Progress percentage (0-100)", ge=0, le=100
    )
    substeps: Optional[list[str]] = Field(
        default=None, description="List of substeps for this task"
    )
    current_substep: Optional[str] = Field(
        default=None, description="Currently executing substep"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "retrieval_1",
                "content": "Retrieve documents via vector search",
                "active_form": "Retrieving documents via vector search",
                "status": "in_progress",
                "category": "retrieval",
                "can_parallel": True,
                "dependencies": ["analysis_1"],
                "progress_percentage": 60,
                "current_substep": "Searching vector database",
            }
        }

    def mark_started(self):
        """Mark task as started."""
        self.status = "in_progress"
        self.started_at = datetime.now()
        self.progress_percentage = 0

    def update_progress(self, percentage: int, substep: Optional[str] = None):
        """Update progress percentage and current substep."""
        self.progress_percentage = min(100, max(0, percentage))
        if substep:
            self.current_substep = substep

    def mark_completed(self, result: Any = None):
        """Mark task as completed."""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.progress_percentage = 100
        self.current_substep = None
        if result is not None:
            self.result = result

    def mark_failed(self, error: str):
        """Mark task as failed."""
        self.status = "failed"
        self.completed_at = datetime.now()
        self.error = error

    def is_ready_to_execute(self, completed_ids: set[str]) -> bool:
        """Check if all dependencies are completed."""
        if self.status != "pending":
            return False
        return all(dep in completed_ids for dep in self.dependencies)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
