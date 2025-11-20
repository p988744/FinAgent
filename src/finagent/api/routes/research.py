"""Research query endpoints with Celery background processing."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.answers import LegalAnswer
from finagent.models.queries import Query, QueryResponse
from finagent.tasks.research_workflow import (
    execute_research_workflow,
    get_research_status,
    list_research_history,
)

router = APIRouter(prefix="/api/v1/research", tags=["Research"])

# In-memory storage for MVP (will be replaced with database)
query_results: dict[str, LegalAnswer] = {}


# Request/Response models
class ResearchRequest(BaseModel):
    """Research query request."""
    query_text: str


class ResearchResponse(BaseModel):
    """Research query response with session tracking."""
    session_id: str
    celery_task_id: str
    status: str
    message: str


class ResearchStatusResponse(BaseModel):
    """Research session status and progress."""
    session_id: str
    query_text: str
    status: str
    current_agent: Optional[str] = None
    agent_steps: Optional[List[dict]] = None
    todos: Optional[List[dict]] = None
    activity_log: Optional[List[dict]] = None
    research_plan: Optional[dict] = None
    dynamic_plan: Optional[dict] = None
    tool_executions: Optional[dict] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class ResearchHistoryResponse(BaseModel):
    """List of research sessions."""
    sessions: List[dict]
    total: int


@router.post("/query/async", response_model=ResearchResponse, status_code=202)
async def submit_research_async(request: ResearchRequest):
    """
    Submit a research query for async processing with Celery.

    This endpoint immediately returns a session_id and celery_task_id.
    Use the /research/status/{session_id} endpoint to poll for progress.

    Args:
        request: Research request with query_text

    Returns:
        ResearchResponse with session_id and celery_task_id
    """
    # Generate session ID
    session_id = str(uuid.uuid4())

    try:
        # Submit to Celery for background processing
        task = execute_research_workflow.delay(request.query_text, session_id)

        return ResearchResponse(
            session_id=session_id,
            celery_task_id=task.id,
            status="submitted",
            message="Research query submitted for background processing"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit research query: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=ResearchStatusResponse)
async def get_session_status(session_id: str):
    """
    Get research session status and progress.

    Poll this endpoint to monitor progress and retrieve results.

    Args:
        session_id: Session identifier

    Returns:
        ResearchStatusResponse with current status and available data
    """
    try:
        # Get status from database via Celery task
        status_data = get_research_status(session_id)

        if "error" in status_data:
            raise HTTPException(status_code=404, detail=status_data["error"])

        return ResearchStatusResponse(**status_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session status: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse, status_code=202)
async def submit_query(query: Query):
    """
    Submit a legal research query (legacy endpoint - preserved for backward compatibility).

    This endpoint accepts a Traditional Chinese query and initiates
    the multi-agent research process.

    Args:
        query: Query object with text and optional filters

    Returns:
        QueryResponse with query_id for retrieving results
    """
    # Generate unique query ID
    query_id = str(uuid.uuid4())

    try:
        # Process query through agent orchestrator
        orchestrator = AgentOrchestrator()
        answer = await orchestrator.process_query(query)

        # Store result (in production, this would be in a database)
        query_results[query_id] = answer

        return QueryResponse(
            query_id=query_id,
            status="completed",
            message="Query processed successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/query/{query_id}", response_model=LegalAnswer)
async def get_query_result(query_id: str):
    """
    Retrieve results for a query.

    Args:
        query_id: UUID of the query

    Returns:
        LegalAnswer with research results and citations

    Raises:
        HTTPException: If query_id not found
    """
    if query_id not in query_results:
        raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

    return query_results[query_id]


@router.post("/query/sync", response_model=LegalAnswer)
async def submit_query_sync(query: Query):
    """
    Submit a query and wait for results (synchronous).

    This endpoint processes the query and returns results immediately.
    For long-running queries, use the async endpoint instead.

    Args:
        query: Query object with text and optional filters

    Returns:
        LegalAnswer with research results
    """
    try:
        orchestrator = AgentOrchestrator()
        answer = await orchestrator.process_query(query)
        return answer

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/history", response_model=ResearchHistoryResponse)
async def get_research_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    Get research session history.

    Args:
        limit: Maximum number of sessions to return (default: 50)
        offset: Number of sessions to skip for pagination (default: 0)
        status: Optional status filter (completed, failed, in_progress)

    Returns:
        ResearchHistoryResponse with sessions list and total count
    """
    try:
        # Get history from database via Celery task
        history_data = list_research_history(limit, offset, status)

        return ResearchHistoryResponse(**history_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get research history: {str(e)}"
        )
