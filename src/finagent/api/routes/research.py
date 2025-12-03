"""Research query endpoints with Celery background processing."""

import logging
import sqlite3
import uuid
from pathlib import Path

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

logger = logging.getLogger(__name__)

# Database path
# research.py is at: src/finagent/api/routes/research.py
# parents[4] = project root = /Users/.../finagent/
DB_PATH = Path(__file__).parents[4] / "data" / "finagent.db"


def _create_pending_session(session_id: str, query_text: str) -> None:
    """
    Pre-create a research session with 'pending' status in the database.
    This ensures the session exists before Celery task starts processing.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO research_sessions (
                session_id, query_text, status,
                created_at, updated_at
            )
            VALUES (?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (session_id, query_text)
        )
        conn.commit()
        logger.info(f"Pre-created pending session {session_id}")
    except Exception as e:
        logger.error(f"Failed to pre-create session: {e}")
        raise
    finally:
        conn.close()

router = APIRouter(prefix="/api/v1/research", tags=["Research"])

# In-memory storage for MVP (will be replaced with database)
query_results: dict[str, LegalAnswer] = {}


# Request/Response models
class ResearchRequest(BaseModel):
    """Research query request."""
    query_text: str
    use_deep_agent: bool = False  # If True, use Deep Agent workflow


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
    current_agent: str | None = None
    agent_steps: list[dict] | None = None
    todos: list[dict] | None = None
    activity_log: list[dict] | None = None
    research_plan: dict | None = None
    dynamic_plan: dict | None = None
    tool_executions: dict | None = None
    result: dict | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    processing_time_seconds: float | None = None


class ResearchHistoryResponse(BaseModel):
    """List of research sessions."""
    sessions: list[dict]
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
        # Pre-create session in database with 'pending' status
        # This ensures the session exists before polling starts
        _create_pending_session(session_id, request.query_text)

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


@router.post("/deep-agent/query", response_model=LegalAnswer)
async def submit_deep_agent_query(request: ResearchRequest):
    """
    Submit a query using the Deep Agent workflow (synchronous).

    Deep Agent provides Claude Code-like capabilities:
    - Task planning with write_todos
    - Sub-agent delegation for specialized tasks (RAG researcher, legal analyzer, penalty comparator)
    - Context management

    Args:
        request: Research request with query_text

    Returns:
        LegalAnswer with research results
    """
    try:
        orchestrator = AgentOrchestrator()

        # Create Query object
        from finagent.models.queries import Query
        query = Query(text=request.query_text)

        # Process with Deep Agent
        answer = await orchestrator.process_with_deep_agent(query)
        return answer

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Deep Agent query: {str(e)}"
        )


@router.get("/history", response_model=ResearchHistoryResponse)
async def get_research_history(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None
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
