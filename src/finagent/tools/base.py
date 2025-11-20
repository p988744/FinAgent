"""Base tool interface and models."""

import json
import logging
import sqlite3
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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

    async def execute_with_tracking(
        self, tool_input: ToolInput, query_id: str
    ) -> ToolOutput:
        """
        Execute tool with execution tracking.

        Args:
            tool_input: Tool input parameters
            query_id: Associated query/research session ID

        Returns:
            ToolOutput with execution results
        """
        capability = self.get_capability()
        tool_name = capability.name

        # Validate input
        if not self.validate_input(tool_input):
            error_msg = f"Invalid input parameters for tool: {tool_name}"
            logger.error(error_msg)
            return ToolOutput(success=False, results=[], metadata={}, error=error_msg)

        # Track execution time
        start_time = time.time()

        try:
            # Execute tool
            output = await self.execute(tool_input)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Add execution time to metadata
            if output.metadata:
                output.metadata["execution_time_ms"] = execution_time_ms
            else:
                output.metadata = {"execution_time_ms": execution_time_ms}

            # Store execution record in database
            self._store_execution(
                query_id=query_id,
                tool_name=tool_name,
                tool_input=tool_input,
                output=output,
                execution_time_ms=execution_time_ms,
            )

            logger.info(
                f"Tool '{tool_name}' executed successfully in {execution_time_ms}ms"
            )

            return output

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Tool execution failed: {str(e)}"

            logger.error(f"Tool '{tool_name}' failed after {execution_time_ms}ms: {e}")

            # Store failed execution
            self._store_execution(
                query_id=query_id,
                tool_name=tool_name,
                tool_input=tool_input,
                output=ToolOutput(
                    success=False, results=[], metadata={}, error=error_msg
                ),
                execution_time_ms=execution_time_ms,
            )

            return ToolOutput(
                success=False,
                results=[],
                metadata={"execution_time_ms": execution_time_ms},
                error=error_msg,
            )

    def _store_execution(
        self,
        query_id: str,
        tool_name: str,
        tool_input: ToolInput,
        output: ToolOutput,
        execution_time_ms: int,
    ) -> None:
        """
        Store tool execution record in database.

        Args:
            query_id: Associated query ID
            tool_name: Name of the tool
            tool_input: Tool input parameters
            output: Tool execution output
            execution_time_ms: Execution time in milliseconds
        """
        try:
            # Get database path
            db_path = Path("data/finagent.db")
            if not db_path.exists():
                logger.warning(
                    f"Database not found at {db_path}, skipping execution tracking"
                )
                return

            # Prepare data for storage
            parameters_json = json.dumps(tool_input.parameters, ensure_ascii=False)

            # Get sample results (top 3)
            sample_results = output.results[:3] if output.results else []
            sample_results_json = json.dumps(sample_results, ensure_ascii=False)

            # Get metadata
            metadata_json = json.dumps(output.metadata, ensure_ascii=False)

            # Store in database
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO tool_executions (
                        query_id, tool_name, parameters, execution_time_ms,
                        results_count, sample_results, metadata, success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        query_id,
                        tool_name,
                        parameters_json,
                        execution_time_ms,
                        len(output.results),
                        sample_results_json,
                        metadata_json,
                        1 if output.success else 0,
                        output.error,
                    ),
                )
                conn.commit()

            logger.debug(
                f"Stored execution record for tool '{tool_name}' (query_id={query_id})"
            )

        except Exception as e:
            logger.error(f"Failed to store tool execution record: {e}")
