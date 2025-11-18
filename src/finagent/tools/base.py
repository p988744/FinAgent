"""Base tool interface and models."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolCapability(BaseModel):
    """Describes what a tool can do."""

    name: str = Field(..., description="Tool name (e.g., 'vector_search')")
    description: str = Field(..., description="What this tool does")

    # Query intent matching
    supported_intents: list[str] = Field(
        ...,
        description="Query intents this tool can handle (e.g., 'temporal', 'comparison', 'specific_file')",
    )

    # Required query features
    required_features: list[str] = Field(
        default_factory=list,
        description="Features needed in query (e.g., 'entity_name', 'date_range', 'filename')",
    )

    # Execution characteristics
    execution_time_estimate: str = Field(
        ..., description="Estimated execution time (e.g., 'fast', 'medium', 'slow')"
    )

    cost_estimate: str = Field(
        ..., description="Resource cost (e.g., 'low', 'medium', 'high')"
    )

    # Limitations
    limitations: list[str] = Field(
        default_factory=list, description="Known limitations of this tool"
    )


class ToolInput(BaseModel):
    """Standardized input for all tools."""

    query: str = Field(..., description="User query")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific parameters"
    )


class ToolOutput(BaseModel):
    """Standardized output from all tools."""

    success: bool = Field(..., description="Whether execution succeeded")
    results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved results (documents, metadata, etc.)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Execution metadata (time, cost, etc.)"
    )
    error: str | None = Field(None, description="Error message if failed")


class BaseTool(ABC):
    """Base class for all tools."""

    @abstractmethod
    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        pass

    @abstractmethod
    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Execute the tool."""
        pass

    @abstractmethod
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate input parameters."""
        pass
