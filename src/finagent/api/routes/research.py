"""Research query endpoints."""

import uuid
from fastapi import APIRouter, HTTPException
from typing import Dict

from finagent.models.queries import Query, QueryResponse
from finagent.models.answers import LegalAnswer
from finagent.agents.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/v1/research", tags=["Research"])

# In-memory storage for MVP (will be replaced with database)
query_results: Dict[str, LegalAnswer] = {}


@router.post("/query", response_model=QueryResponse, status_code=202)
async def submit_query(query: Query):
    """
    Submit a legal research query.

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
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


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
        raise HTTPException(
            status_code=404,
            detail=f"Query {query_id} not found"
        )

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
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
