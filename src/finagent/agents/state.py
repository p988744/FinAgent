"""Agent state definitions for LangGraph workflow."""

from typing import Any, TypedDict

from finagent.document_processing.retriever import RetrievedChunk
from finagent.models.answers import LegalAnswer
from finagent.models.citations import LegalCitation
from finagent.models.queries import Query
from finagent.models.todo_item import TodoItem


class AgentState(TypedDict):
    """
    State schema for the multi-agent legal research workflow.

    This state is passed through the LangGraph workflow and updated by each agent.
    """

    # Input
    query: Query

    # Query Analysis Agent outputs (runs before planning)
    clarification_request: dict[str, Any] | None  # Clarification request details
    clarification_response: str | None  # User's clarification response
    query_intent: str | None  # Understood user intent

    # Planning Agent outputs
    plan: dict[str, Any] | None
    plan_analysis: dict[str, Any] | None  # Query analysis results
    research_tasks: list[str] | None

    # Action Agent outputs
    retrieved_chunks: list[RetrievedChunk] | None
    citations: list[LegalCitation] | None

    # Validation Agent outputs
    validation_passed: bool
    validation_issues: list[str] | None

    # Answer Agent outputs
    answer: LegalAnswer | None

    # Re-search tracking
    search_iteration: int  # Current iteration (0 = first search, 1-2 = re-search)
    max_search_iterations: int  # Maximum iterations allowed (default: 2)
    search_strategy: str  # Current search strategy: "strict", "relaxed", "broad"

    # Todo tracking (Phase 5)
    todos: list[TodoItem] | None  # Task tracking with real-time status updates

    # Metadata
    processing_steps: list[str]
    errors: list[str]
