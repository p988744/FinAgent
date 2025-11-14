"""Query Memo Logger - Logs query execution details to database for tracking and analysis."""

import json
import logging
import sqlite3
import time
from datetime import datetime
from typing import Any

from finagent.agents.state import AgentState
from finagent.models.answers import LegalAnswer
from finagent.models.queries import Query

logger = logging.getLogger(__name__)


class QueryMemoLogger:
    """
    Logs query execution details to database history table.

    Tracks:
    - Query text and analysis
    - Research plan and tasks
    - Search iterations and strategies
    - Retrieved chunks and citations
    - Processing steps and performance
    - Validation issues
    """

    def __init__(self, db_path: str = "data/finagent.db", session_id: str | None = None):
        """
        Initialize query memo logger.

        Args:
            db_path: Path to SQLite database
            session_id: Optional session ID for grouping related queries
        """
        self.db_path = db_path
        self.session_id = session_id or self._generate_session_id()
        self.start_time = None

    def _generate_session_id(self) -> str:
        """Generate session ID from timestamp."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def start_query(self):
        """Mark query start time."""
        self.start_time = time.time()

    def log_query(
        self,
        query: Query,
        answer: LegalAnswer | None,
        state: AgentState,
        model_used: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> int:
        """
        Log query execution to database.

        Args:
            query: Original query
            answer: Generated answer (if successful)
            state: Final agent state
            model_used: LLM model used
            success: Whether query succeeded
            error_message: Error message if failed

        Returns:
            History record ID
        """
        # Calculate processing time
        processing_time = None
        if self.start_time:
            processing_time = time.time() - self.start_time

        # Extract data from state
        plan_data = state.get("plan")
        plan_analysis = state.get("plan_analysis")
        search_iteration = state.get("search_iteration", 0)
        search_strategy = state.get("search_strategy", "strict")
        retrieved_chunks = state.get("retrieved_chunks", [])
        citations = state.get("citations", [])
        validation_issues = state.get("validation_issues")
        processing_steps = state.get("processing_steps", [])

        # Count chunks by type
        vector_chunks_count = sum(
            1 for chunk in retrieved_chunks if chunk.metadata.get("search_method") != "hard_search"
        )
        hard_chunks_count = sum(
            1 for chunk in retrieved_chunks if chunk.metadata.get("search_method") == "hard_search"
        )

        # Prepare data for database
        data = {
            "session_id": self.session_id,
            "query": query.text,
            "response": answer.detailed_analysis if answer else None,
            "model_used": model_used,
            "tokens_used": None,  # TODO: Calculate from LLM response
            "cost_usd": None,  # TODO: Calculate from tokens
            "processing_time_seconds": processing_time,
            "success": success,
            "error_message": error_message,
            "query_analysis": json.dumps(plan_analysis, ensure_ascii=False) if plan_analysis else None,
            "plan_data": json.dumps(plan_data, ensure_ascii=False) if plan_data else None,
            "search_iterations": search_iteration,
            "search_strategy": search_strategy,
            "vector_chunks_count": vector_chunks_count,
            "hard_chunks_count": hard_chunks_count,
            "total_chunks_count": len(retrieved_chunks),
            "citations_count": len(citations),
            "confidence_level": answer.confidence_score.value if answer and answer.confidence_score else None,
            "validation_issues": json.dumps(validation_issues, ensure_ascii=False)
            if validation_issues
            else None,
            "user_notes": None,  # User can add notes later
            "processing_steps": json.dumps(processing_steps, ensure_ascii=False) if processing_steps else None,
            "metadata": json.dumps(
                {
                    "max_results": query.max_results,
                    "error_count": len(state.get("errors", [])),
                },
                ensure_ascii=False,
            ),
        }

        # Insert into database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO history (
                    session_id, query, response, model_used, tokens_used, cost_usd,
                    processing_time_seconds, success, error_message, metadata,
                    query_analysis, plan_data, search_iterations, search_strategy,
                    vector_chunks_count, hard_chunks_count, total_chunks_count,
                    citations_count, confidence_level, validation_issues,
                    user_notes, processing_steps
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    data["session_id"],
                    data["query"],
                    data["response"],
                    data["model_used"],
                    data["tokens_used"],
                    data["cost_usd"],
                    data["processing_time_seconds"],
                    data["success"],
                    data["error_message"],
                    data["metadata"],
                    data["query_analysis"],
                    data["plan_data"],
                    data["search_iterations"],
                    data["search_strategy"],
                    data["vector_chunks_count"],
                    data["hard_chunks_count"],
                    data["total_chunks_count"],
                    data["citations_count"],
                    data["confidence_level"],
                    data["validation_issues"],
                    data["user_notes"],
                    data["processing_steps"],
                ),
            )

            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Query logged to database with ID {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to log query to database: {e}", exc_info=True)
            return -1

    def add_user_note(self, history_id: int, note: str):
        """
        Add user note to existing history record.

        Args:
            history_id: History record ID
            note: User's note/memo
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE history
                SET user_notes = ?
                WHERE id = ?
                """,
                (note, history_id),
            )

            conn.commit()
            conn.close()

            logger.info(f"Added user note to history record {history_id}")

        except Exception as e:
            logger.error(f"Failed to add user note: {e}", exc_info=True)

    def get_query_history(self, limit: int = 10, session_id: str | None = None) -> list[dict]:
        """
        Retrieve query history.

        Args:
            limit: Maximum number of records to return
            session_id: Filter by session ID (optional)

        Returns:
            List of history records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if session_id:
                cursor.execute(
                    """
                    SELECT *
                    FROM history
                    WHERE session_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (session_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM history
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()
            conn.close()

            # Convert to list of dicts
            records = []
            for row in rows:
                record = dict(row)
                # Parse JSON fields
                for field in ["query_analysis", "plan_data", "validation_issues", "processing_steps", "metadata"]:
                    if record.get(field):
                        try:
                            record[field] = json.loads(record[field])
                        except:
                            pass
                records.append(record)

            return records

        except Exception as e:
            logger.error(f"Failed to retrieve query history: {e}", exc_info=True)
            return []

    def get_query_stats(self) -> dict[str, Any]:
        """
        Get statistics about query history.

        Returns:
            Dictionary with statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total queries
            cursor.execute("SELECT COUNT(*) FROM history")
            total_queries = cursor.fetchone()[0]

            # Success rate
            cursor.execute("SELECT COUNT(*) FROM history WHERE success = 1")
            successful_queries = cursor.fetchone()[0]

            # Average processing time
            cursor.execute("SELECT AVG(processing_time_seconds) FROM history WHERE processing_time_seconds IS NOT NULL")
            avg_time = cursor.fetchone()[0]

            # Hard search usage
            cursor.execute("SELECT COUNT(*) FROM history WHERE hard_chunks_count > 0")
            queries_with_hard_search = cursor.fetchone()[0]

            # Average re-search iterations
            cursor.execute("SELECT AVG(search_iterations) FROM history")
            avg_iterations = cursor.fetchone()[0]

            # Confidence distribution
            cursor.execute("SELECT confidence_level, COUNT(*) FROM history GROUP BY confidence_level")
            confidence_dist = dict(cursor.fetchall())

            conn.close()

            return {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
                "average_processing_time_seconds": avg_time,
                "queries_with_hard_search": queries_with_hard_search,
                "hard_search_usage_rate": queries_with_hard_search / total_queries
                if total_queries > 0
                else 0,
                "average_search_iterations": avg_iterations,
                "confidence_distribution": confidence_dist,
            }

        except Exception as e:
            logger.error(f"Failed to get query stats: {e}", exc_info=True)
            return {}
