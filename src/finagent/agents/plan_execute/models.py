"""Data models for the Plan-and-Execute agent flow."""

from operator import add
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


class QueryInsight(BaseModel):
    """Analysis of the user's query before planning."""

    query_type: str = Field(description="Type of query (e.g., factual, analytical, comparative, temporal)")
    key_entities: List[str] = Field(default_factory=list, description="Key entities mentioned (banks, dates, amounts, regulations)")
    search_strategy: str = Field(description="Recommended search strategy (semantic, keyword, hybrid)")
    complexity: str = Field(description="Query complexity (simple, medium, complex)")
    reasoning: str = Field(description="Brief explanation of the analysis")


def replace_plan(left: Optional[Plan], right: Plan) -> Plan:
    """Replace plan state (use latest value only)."""
    return right


class PlanExecuteState(TypedDict):
    """State for the Plan-and-Execute workflow."""

    input: str
    query_insight: Optional[QueryInsight]  # Analysis of the query before planning
    plan: Annotated[Plan, replace_plan]  # Use Annotated to handle single-value updates
    past_steps: Annotated[List[tuple], add]
    response: Optional[str]
    scratchpad: List[Any]  # For internal agent reasoning if needed

    # Human-in-the-loop confirmation fields
    confirmation_request: Optional[dict]  # Request sent to user
    plan_approved: Optional[bool]  # True=approved, False=rejected/modified, None=pending
    user_modifications: Optional[dict]  # Modifications from user
    user_feedback: Optional[str]  # Feedback from user if rejected
    confirmation_requested_at: Optional[str]  # ISO timestamp
    confirmation_received_at: Optional[str]  # ISO timestamp
