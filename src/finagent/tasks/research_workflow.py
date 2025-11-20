"""Celery tasks for research workflow execution."""

import asyncio
import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.celery_app import celery_app
from finagent.models.queries import Query

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parents[3] / "data" / "finagent.db"


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(str(DB_PATH))


def create_research_session(session_id: str, query_text: str, celery_task_id: str) -> int:
    """
    Create a new research session in the database.

    Args:
        session_id: Unique session identifier
        query_text: User's research query
        celery_task_id: Celery task ID

    Returns:
        Database row ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO research_sessions (
                session_id, query_text, status, celery_task_id,
                started_at, created_at, updated_at
            )
            VALUES (?, ?, 'in_progress', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (session_id, query_text, celery_task_id)
        )
        conn.commit()
        row_id = cursor.lastrowid
        logger.info(f"Created research session {session_id} (row_id={row_id})")
        return row_id
    finally:
        conn.close()


def update_research_session(session_id: str, updates: Dict[str, Any]):
    """
    Update research session with new data.

    Args:
        session_id: Session identifier
        updates: Dictionary of fields to update
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build UPDATE query dynamically
        set_clauses = []
        values = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            # Convert dict/list to JSON string
            if isinstance(value, (dict, list)):
                values.append(json.dumps(value, ensure_ascii=False))
            else:
                values.append(value)

        # Always update updated_at (but trigger will also do this)
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE research_sessions
            SET {', '.join(set_clauses)}
            WHERE session_id = ?
        """
        values.append(session_id)

        cursor.execute(query, values)
        conn.commit()
        logger.debug(f"Updated session {session_id}: {list(updates.keys())}")
    finally:
        conn.close()


class SessionProgressCallback:
    """Callback handler for UI progress updates that persists to database."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.steps = {}
        self.todos = []
        self.activity_log = []
        self.plan = None
        self.dynamic_plan = None
        self.tool_executions = {}

    async def on_step_update(self, step: str, status: str, data: Dict[str, Any] = None):
        """Handle agent step updates."""
        self.steps[step] = {
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

        # Update database
        update_research_session(self.session_id, {
            "current_agent": step,
            "agent_steps": list(self.steps.values())
        })

    async def on_todo_update(self, todos: list):
        """Handle todo list updates."""
        self.todos = todos
        update_research_session(self.session_id, {"todos": todos})

    async def on_activity_log(self, level: str, message: str):
        """Handle activity log entries."""
        entry = {
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.activity_log.append(entry)
        update_research_session(self.session_id, {"activity_log": self.activity_log})

    async def on_plan_created(self, plan: Dict[str, Any]):
        """Handle research plan creation."""
        self.plan = plan
        update_research_session(self.session_id, {"research_plan": plan})

    async def on_dynamic_plan(self, dynamic_plan: Dict[str, Any]):
        """Handle dynamic plan analysis."""
        self.dynamic_plan = dynamic_plan
        update_research_session(self.session_id, {"dynamic_plan": dynamic_plan})

    async def on_tool_execution(self, tool_name: str, status: Dict[str, Any]):
        """Handle tool execution updates."""
        self.tool_executions[tool_name] = status
        update_research_session(self.session_id, {"tool_executions": self.tool_executions})


@celery_app.task(bind=True, name="finagent.tasks.execute_research_workflow")
def execute_research_workflow(self, query_text: str, session_id: str = None):
    """
    Execute research workflow in background using LangGraph multi-agent system.

    Args:
        query_text: User's research query
        session_id: Optional session ID (generated if not provided)

    Returns:
        Dict with session_id, result, and metadata
    """
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting research workflow for session {session_id}")

    try:
        # Create session in database
        create_research_session(session_id, query_text, task_id)

        # Create progress callback
        callback = SessionProgressCallback(session_id)

        # Create orchestrator with callback
        orchestrator = AgentOrchestrator(
            enable_query_logging=True,
            ui_callback=callback
        )

        # Create query object
        query = Query(
            text=query_text,
            session_id=session_id,
            timestamp=datetime.now()
        )

        # Execute workflow (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(orchestrator.process_query(query))
        finally:
            loop.close()

        # Convert result to dict
        result_dict = {
            "executive_summary": result.executive_summary,
            "key_findings": result.key_findings,
            "detailed_analysis": result.detailed_analysis,
            "confidence": {
                "level": result.confidence_level.value if result.confidence_level else "MEDIUM",
                "justification": result.confidence_justification
            },
            "citations": [
                {
                    "source": cite.source_document,
                    "page": cite.page_number,
                    "excerpt": cite.excerpt,
                    "authority_level": cite.authority_level.value if cite.authority_level else "SECONDARY",
                    "citation_type": cite.citation_type.value if cite.citation_type else "SUPPORT"
                }
                for cite in (result.citations or [])
            ],
            "processing_time_ms": result.processing_time_ms,
            "tokens_used": getattr(result, 'tokens_used', None),
            "cost_usd": getattr(result, 'cost_usd', None)
        }

        # Update session with completion
        update_research_session(session_id, {
            "status": "completed",
            "result": result_dict,
            "completed_at": datetime.now().isoformat(),
            "processing_time_seconds": result.processing_time_ms / 1000.0 if result.processing_time_ms else None,
            "tokens_used": getattr(result, 'tokens_used', None),
            "cost_usd": getattr(result, 'cost_usd', None)
        })

        logger.info(f"[Task {task_id}] Research workflow completed for session {session_id}")

        return {
            "session_id": session_id,
            "status": "completed",
            "result": result_dict
        }

    except Exception as e:
        logger.error(f"[Task {task_id}] Research workflow failed: {e}", exc_info=True)

        # Update session with error
        try:
            update_research_session(session_id, {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now().isoformat()
            })
        except Exception as db_error:
            logger.error(f"Failed to update session error: {db_error}")

        # Re-raise exception for Celery
        raise


@celery_app.task(name="finagent.tasks.get_research_status")
def get_research_status(session_id: str):
    """
    Get research session status and progress.

    Args:
        session_id: Session identifier

    Returns:
        Dict with session status and data
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                session_id, query_text, status, celery_task_id,
                current_agent, agent_steps, todos, activity_log,
                research_plan, dynamic_plan, tool_executions,
                result, error_message,
                started_at, completed_at, processing_time_seconds,
                tokens_used, cost_usd, created_at, updated_at
            FROM research_sessions
            WHERE session_id = ?
            """,
            (session_id,)
        )

        row = cursor.fetchone()
        if not row:
            return {"error": "Session not found", "session_id": session_id}

        # Parse JSON fields
        def safe_json_parse(value):
            if value is None:
                return None
            try:
                return json.loads(value) if isinstance(value, str) else value
            except:
                return value

        return {
            "session_id": row[0],
            "query_text": row[1],
            "status": row[2],
            "celery_task_id": row[3],
            "current_agent": row[4],
            "agent_steps": safe_json_parse(row[5]),
            "todos": safe_json_parse(row[6]),
            "activity_log": safe_json_parse(row[7]),
            "research_plan": safe_json_parse(row[8]),
            "dynamic_plan": safe_json_parse(row[9]),
            "tool_executions": safe_json_parse(row[10]),
            "result": safe_json_parse(row[11]),
            "error_message": row[12],
            "started_at": row[13],
            "completed_at": row[14],
            "processing_time_seconds": row[15],
            "tokens_used": row[16],
            "cost_usd": row[17],
            "created_at": row[18],
            "updated_at": row[19]
        }
    finally:
        conn.close()


@celery_app.task(name="finagent.tasks.list_research_history")
def list_research_history(limit: int = 50, offset: int = 0, status_filter: str = None):
    """
    List research session history.

    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        status_filter: Optional status filter (completed, failed, in_progress)

    Returns:
        Dict with sessions list and total count
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query with optional status filter
        where_clause = ""
        params = []

        if status_filter:
            where_clause = "WHERE status = ?"
            params.append(status_filter)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM research_sessions {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Get sessions with pagination
        params.extend([limit, offset])
        query = f"""
            SELECT
                session_id, query_text, status, celery_task_id,
                started_at, completed_at, processing_time_seconds,
                is_bookmarked, created_at
            FROM research_sessions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        sessions = []
        for row in rows:
            sessions.append({
                "session_id": row[0],
                "query_text": row[1],
                "status": row[2],
                "celery_task_id": row[3],
                "started_at": row[4],
                "completed_at": row[5],
                "processing_time_seconds": row[6],
                "is_bookmarked": bool(row[7]),
                "created_at": row[8]
            })

        return {
            "sessions": sessions,
            "total": total
        }
    finally:
        conn.close()
