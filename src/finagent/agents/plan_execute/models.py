"""Data models for the Plan-and-Execute agent flow."""

from typing import Annotated, Any, List, Optional, TypedDict, Union

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class PlanTask(BaseModel):
    """A single task in the research plan."""

    id: int = Field(description="Unique identifier for the task")
    description: str = Field(description="Description of what needs to be done")
    tool: str = Field(description="The tool to use for this task (e.g., 'retriever', 'hard_search')")
    args: dict = Field(default_factory=dict, description="Arguments for the tool")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed, failed")
    result: Optional[str] = Field(default=None, description="Result of the task execution")


class Plan(BaseModel):
    """The research plan containing a list of tasks."""

    tasks: List[PlanTask] = Field(default_factory=list, description="List of tasks to execute")


class PlanExecuteState(TypedDict):
    """State for the Plan-and-Execute workflow."""

    input: str
    plan: Plan
    past_steps: Annotated[List[tuple], "List of (task, result) tuples"]
    response: Optional[str]
    scratchpad: List[Any]  # For internal agent reasoning if needed
