"""Database helpers for LangGraph checkpointing and query history.

This module provides:
1. CheckpointDatabase - Connection pool and helper methods
2. get_checkpoint_db() - Global singleton instance

Usage:
    from finagent.database.checkpoint_db import get_checkpoint_db

    db = get_checkpoint_db()
    checkpointer = db.get_checkpointer()  # For LangGraph
    query_id = db.create_query_record("User query")
    db.update_query_result(query_id, response="Final answer")
"""

import json
import logging
import os
import uuid
from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


class CheckpointDatabase:
    """Manage PostgreSQL connections for LangGraph checkpoints and query history."""

    def __init__(self, db_uri: str | None = None):
        """
        Initialize database connection pool.

        Args:
            db_uri: PostgreSQL connection string. If None, uses LANGGRAPH_CHECKPOINT_DB env var.

        Raises:
            ValueError: If db_uri is None and LANGGRAPH_CHECKPOINT_DB is not set.
        """
        self.db_uri = db_uri or os.getenv('LANGGRAPH_CHECKPOINT_DB')

        if not self.db_uri:
            raise ValueError(
                "LANGGRAPH_CHECKPOINT_DB environment variable not set. "
                "Please set it in .env file: "
                "LANGGRAPH_CHECKPOINT_DB=postgresql://user:pass@localhost:5432/finagent"
            )

        # Connection pool configuration
        self.connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        }

        # Create connection pool
        try:
            self.pool = ConnectionPool(
                conninfo=self.db_uri,
                max_size=20,
                kwargs=self.connection_kwargs
            )
            logger.info(f"Checkpoint database pool created: {self._safe_uri(self.db_uri)}")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    def _safe_uri(self, uri: str) -> str:
        """Return URI with password masked for logging."""
        if '@' in uri:
            # postgresql://user:PASSWORD@host:port/db
            parts = uri.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                return f"{user_pass[0]}:****@{parts[1]}"
        return uri

    def get_checkpointer(self) -> PostgresSaver:
        """
        Get PostgresSaver checkpointer instance for LangGraph.

        Returns:
            PostgresSaver: LangGraph checkpointer that uses this connection pool.

        Example:
            checkpointer = db.get_checkpointer()
            orchestrator = AgentOrchestrator(checkpointer=checkpointer)
        """
        return PostgresSaver(self.pool)

    def setup_tables(self):
        """
        Setup checkpoint tables and query history table.

        This method:
        1. Creates LangGraph checkpoint tables (via checkpointer.setup())
        2. Creates query_history table (via SQL file)

        Safe to call multiple times (uses IF NOT EXISTS).
        """
        # Setup LangGraph checkpoint tables
        checkpointer = self.get_checkpointer()
        checkpointer.setup()
        logger.info("✅ LangGraph checkpoint tables created/verified")

        # Setup query history table
        schema_file = os.path.join(
            os.path.dirname(__file__),
            'query_history_schema.sql'
        )

        if os.path.exists(schema_file):
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    with open(schema_file) as f:
                        schema_sql = f.read()
                        cur.execute(schema_sql)
            logger.info("✅ Query history table created/verified")
        else:
            logger.warning(f"Schema file not found: {schema_file}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            Connection: PostgreSQL connection from pool

        Example:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        """
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    def create_query_record(
        self,
        query_text: str,
        thread_id: str | None = None,
        query_type: str | None = None,
        use_plan_execute: bool = True,
        user_id: str | None = None,
        session_id: str | None = None
    ) -> str:
        """
        Create a new query history record.

        Args:
            query_text: The user's query
            thread_id: LangGraph thread ID (creates new UUID if None)
            query_type: Query type (factual, analytical, comparative)
            use_plan_execute: Whether using plan-and-execute workflow
            user_id: User identifier (optional)
            session_id: Session identifier (optional)

        Returns:
            str: query_id (UUID)

        Example:
            query_id = db.create_query_record("玉山銀行洗錢防制裁罰")
        """
        query_id = str(uuid.uuid4())
        thread_id = thread_id or str(uuid.uuid4())

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO query_history (
                        query_id, thread_id, query_text, query_type,
                        use_plan_execute, user_id, session_id, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                    RETURNING query_id
                    """,
                    (query_id, thread_id, query_text, query_type,
                     use_plan_execute, user_id, session_id)
                )
                result = cur.fetchone()
                conn.commit()

        logger.info(f"Created query record: {query_id}")
        return result['query_id']

    def update_query_status(
        self,
        query_id: str,
        status: str,
        error_message: str | None = None
    ):
        """
        Update query status.

        Args:
            query_id: Query UUID
            status: New status (pending, running, completed, failed)
            error_message: Error message if status is 'failed'

        Example:
            db.update_query_status(query_id, 'running')
            db.update_query_status(query_id, 'failed', str(exception))
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if status == 'completed':
                    cur.execute(
                        """
                        UPDATE query_history
                        SET status = %s, error_message = %s,
                            completed_at = NOW(), updated_at = NOW()
                        WHERE query_id = %s
                        """,
                        (status, error_message, query_id)
                    )
                else:
                    cur.execute(
                        """
                        UPDATE query_history
                        SET status = %s, error_message = %s, updated_at = NOW()
                        WHERE query_id = %s
                        """,
                        (status, error_message, query_id)
                    )
                conn.commit()

        logger.debug(f"Updated query {query_id} status: {status}")

    def update_query_result(
        self,
        query_id: str,
        query_insight: dict | None = None,
        plan: dict | None = None,
        past_steps: list | None = None,
        response: str | None = None,
        total_tokens: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        llm_cost_usd: float | None = None,
        execution_time: float | None = None
    ):
        """
        Update query with execution results.

        Args:
            query_id: Query UUID
            query_insight: QueryInsight from analyzer (dict)
            plan: Plan from planner (dict)
            past_steps: Execution steps (list)
            response: Final response text
            total_tokens: Total LLM tokens used
            prompt_tokens: Prompt tokens
            completion_tokens: Completion tokens
            llm_cost_usd: Estimated cost in USD
            execution_time: Execution time in seconds

        Example:
            db.update_query_result(
                query_id,
                response="Final answer...",
                execution_time=45.2
            )
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE query_history
                    SET
                        query_insight = %s,
                        plan = %s,
                        past_steps = %s,
                        response = %s,
                        total_tokens = %s,
                        prompt_tokens = %s,
                        completion_tokens = %s,
                        llm_cost_usd = %s,
                        execution_time_seconds = %s,
                        status = 'completed',
                        completed_at = NOW(),
                        updated_at = NOW()
                    WHERE query_id = %s
                    """,
                    (
                        json.dumps(query_insight) if query_insight else None,
                        json.dumps(plan) if plan else None,
                        json.dumps(past_steps) if past_steps else None,
                        response,
                        total_tokens,
                        prompt_tokens,
                        completion_tokens,
                        llm_cost_usd,
                        execution_time,
                        query_id
                    )
                )
                conn.commit()

        logger.info(f"Updated query result: {query_id}")

    def get_query_by_id(self, query_id: str) -> dict | None:
        """
        Get query record by ID.

        Args:
            query_id: Query UUID

        Returns:
            dict: Query record or None if not found

        Example:
            record = db.get_query_by_id(query_id)
            if record:
                print(f"Status: {record['status']}")
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM query_history WHERE query_id = %s",
                    (query_id,)
                )
                return cur.fetchone()

    def get_query_history(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        status: str | None = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Get query history with optional filters.

        Args:
            user_id: Filter by user ID
            session_id: Filter by session ID
            status: Filter by status
            limit: Maximum number of records to return

        Returns:
            list: List of query records (most recent first)

        Example:
            # Get last 10 queries for a user
            history = db.get_query_history(user_id='user123', limit=10)

            # Get all completed queries
            completed = db.get_query_history(status='completed', limit=50)
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Build query with filters
                where_clauses = []
                params = []

                if user_id:
                    where_clauses.append("user_id = %s")
                    params.append(user_id)

                if session_id:
                    where_clauses.append("session_id = %s")
                    params.append(session_id)

                if status:
                    where_clauses.append("status = %s")
                    params.append(status)

                where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
                params.append(limit)

                cur.execute(
                    f"""
                    SELECT * FROM query_history
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    params
                )

                return cur.fetchall()

    def close(self):
        """Close connection pool."""
        self.pool.close()
        logger.info("Checkpoint database pool closed")


# Global instance
_checkpoint_db: CheckpointDatabase | None = None


def get_checkpoint_db() -> CheckpointDatabase:
    """
    Get global checkpoint database instance (singleton).

    Returns:
        CheckpointDatabase: Global instance

    Example:
        db = get_checkpoint_db()
        checkpointer = db.get_checkpointer()

    Note:
        This creates a single connection pool shared across the application.
        Call db.close() only when shutting down the application.
    """
    global _checkpoint_db
    if _checkpoint_db is None:
        _checkpoint_db = CheckpointDatabase()
    return _checkpoint_db
