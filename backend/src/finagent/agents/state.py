"""Agent state definitions for LangGraph workflow."""

from typing import TypedDict, Optional, List, Dict, Any
from finagent.models.queries import Query
from finagent.models.answers import LegalAnswer
from finagent.models.citations import LegalCitation
from finagent.document_processing.retriever import RetrievedChunk


class AgentState(TypedDict):
    """
    State schema for the multi-agent legal research workflow.

    This state is passed through the LangGraph workflow and updated by each agent.
    """
    # Input
    query: Query

    # Planning Agent outputs
    plan: Optional[Dict[str, Any]]
    research_tasks: Optional[List[str]]

    # Action Agent outputs
    retrieved_chunks: Optional[List[RetrievedChunk]]
    citations: Optional[List[LegalCitation]]

    # Validation Agent outputs
    validation_passed: bool
    validation_issues: Optional[List[str]]

    # Answer Agent outputs
    answer: Optional[LegalAnswer]

    # Metadata
    processing_steps: List[str]
    errors: List[str]
