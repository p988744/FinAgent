"""Agent state definitions for LangGraph workflow."""

from typing import Any, TypedDict

from finagent.document_processing.retriever import RetrievedChunk
from finagent.models.answers import LegalAnswer
from finagent.models.citations import LegalCitation
from finagent.models.queries import Query


class AgentState(TypedDict):
    """
    State schema for the multi-agent legal research workflow.

    This state is passed through the LangGraph workflow and updated by each agent.
    """

    # Input
    query: Query

    # Planning Agent outputs
    plan: dict[str, Any] | None
    research_tasks: list[str] | None

    # Action Agent outputs
    retrieved_chunks: list[RetrievedChunk] | None
    citations: list[LegalCitation] | None

    # Validation Agent outputs
    validation_passed: bool
    validation_issues: list[str] | None

    # Answer Agent outputs
    answer: LegalAnswer | None

    # Metadata
    processing_steps: list[str]
    errors: list[str]
