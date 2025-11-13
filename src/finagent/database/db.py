"""Database connection and operations for FinAgent."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .models import History, ModelConfig, Setting


class Database:
    """SQLite database manager for FinAgent."""

    def __init__(self, db_path: str = "./data/finagent.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ==================== Settings Operations ====================

    def get_setting(self, key: str) -> Setting | None:
        """Get a setting by key.

        Args:
            key: Setting key

        Returns:
            Setting object or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return Setting(**dict(row))
            return None

    def get_all_settings(self, category: str | None = None) -> list[Setting]:
        """Get all settings, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of Setting objects
        """
        with self.get_connection() as conn:
            if category:
                cursor = conn.execute(
                    "SELECT * FROM settings WHERE category = ? ORDER BY key",
                    (category,),
                )
            else:
                cursor = conn.execute("SELECT * FROM settings ORDER BY category, key")

            return [Setting(**dict(row)) for row in cursor.fetchall()]

    def set_setting(
        self,
        key: str,
        value: str,
        category: str = "general",
        description: str | None = None,
    ) -> Setting:
        """Set a setting value (insert or update).

        Args:
            key: Setting key
            value: Setting value
            category: Setting category
            description: Optional description

        Returns:
            Updated Setting object
        """
        with self.get_connection() as conn:
            # Check if setting exists
            existing = self.get_setting(key)

            if existing:
                conn.execute(
                    """
                    UPDATE settings
                    SET value = ?, category = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE key = ?
                    """,
                    (value, category, description, key),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO settings (key, value, category, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, value, category, description),
                )

            conn.commit()
            return self.get_setting(key)

    def delete_setting(self, key: str) -> bool:
        """Delete a setting.

        Args:
            key: Setting key

        Returns:
            True if deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM settings WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0

    def get_settings_as_dict(self, category: str | None = None) -> dict[str, str]:
        """Get settings as a dictionary.

        Args:
            category: Optional category filter

        Returns:
            Dictionary mapping keys to values
        """
        settings = self.get_all_settings(category)
        return {s.key: s.value for s in settings}

    # ==================== Model Config Operations ====================

    def get_model_config(self, config_id: int) -> ModelConfig | None:
        """Get a model config by ID.

        Args:
            config_id: Configuration ID

        Returns:
            ModelConfig object or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM model_configs WHERE id = ?", (config_id,))
            row = cursor.fetchone()
            if row:
                return ModelConfig(**dict(row))
            return None

    def get_active_model_config(self, config_type: str) -> ModelConfig | None:
        """Get the active model config for a given type.

        Args:
            config_type: 'llm' or 'embedding'

        Returns:
            Active ModelConfig or None
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM model_configs WHERE config_type = ? AND is_active = 1",
                (config_type,),
            )
            row = cursor.fetchone()
            if row:
                return ModelConfig(**dict(row))
            return None

    def get_all_model_configs(self, config_type: str | None = None) -> list[ModelConfig]:
        """Get all model configs, optionally filtered by type.

        Args:
            config_type: Optional type filter ('llm' or 'embedding')

        Returns:
            List of ModelConfig objects
        """
        with self.get_connection() as conn:
            if config_type:
                cursor = conn.execute(
                    "SELECT * FROM model_configs WHERE config_type = ? ORDER BY created_at DESC",
                    (config_type,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM model_configs ORDER BY config_type, created_at DESC"
                )

            return [ModelConfig(**dict(row)) for row in cursor.fetchall()]

    def save_model_config(
        self,
        name: str,
        config_type: str,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float | None = 0.0,
        is_active: bool = False,
    ) -> ModelConfig:
        """Save a new model configuration.

        Args:
            name: Configuration name
            config_type: 'llm' or 'embedding'
            api_key: API key
            base_url: Base URL
            model: Model name
            temperature: Temperature (LLM only)
            is_active: Whether to set as active

        Returns:
            Created ModelConfig object
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO model_configs
                (name, config_type, api_key, base_url, model, temperature, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, config_type, api_key, base_url, model, temperature, is_active),
            )
            conn.commit()
            return self.get_model_config(cursor.lastrowid)

    def update_model_config(self, config_id: int, **kwargs) -> ModelConfig | None:
        """Update a model configuration.

        Args:
            config_id: Configuration ID
            **kwargs: Fields to update

        Returns:
            Updated ModelConfig or None if not found
        """
        allowed_fields = {
            "name",
            "api_key",
            "base_url",
            "model",
            "temperature",
            "is_active",
        }
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return self.get_model_config(config_id)

        set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
        values = list(update_fields.values()) + [config_id]

        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE model_configs SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values,
            )
            conn.commit()
            return self.get_model_config(config_id)

    def set_active_model_config(self, config_id: int) -> ModelConfig | None:
        """Set a model config as active (deactivates others of same type).

        Args:
            config_id: Configuration ID

        Returns:
            Updated ModelConfig or None if not found
        """
        return self.update_model_config(config_id, is_active=True)

    def delete_model_config(self, config_id: int) -> bool:
        """Delete a model configuration.

        Args:
            config_id: Configuration ID

        Returns:
            True if deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM model_configs WHERE id = ?", (config_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== History Operations ====================

    def add_history(
        self,
        query: str,
        response: str | None = None,
        session_id: str | None = None,
        model_used: str | None = None,
        tokens_used: int | None = None,
        cost_usd: float | None = None,
        processing_time_seconds: float | None = None,
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> History:
        """Add a history entry.

        Args:
            query: User query
            response: Agent response
            session_id: Session identifier
            model_used: Model used
            tokens_used: Total tokens used
            cost_usd: Estimated cost in USD
            processing_time_seconds: Processing time
            success: Whether query was successful
            error_message: Error message if failed
            metadata: Additional metadata

        Returns:
            Created History object
        """
        metadata_json = json.dumps(metadata) if metadata else None

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO history
                (session_id, query, response, model_used, tokens_used, cost_usd,
                 processing_time_seconds, success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    query,
                    response,
                    model_used,
                    tokens_used,
                    cost_usd,
                    processing_time_seconds,
                    success,
                    error_message,
                    metadata_json,
                ),
            )
            conn.commit()

            # Fetch the created history entry
            cursor = conn.execute("SELECT * FROM history WHERE id = ?", (cursor.lastrowid,))
            row = cursor.fetchone()
            return History(**dict(row))

    def get_history(
        self,
        limit: int = 100,
        session_id: str | None = None,
        success_only: bool = False,
    ) -> list[History]:
        """Get history entries.

        Args:
            limit: Maximum number of entries to return
            session_id: Optional session filter
            success_only: Only return successful queries

        Returns:
            List of History objects
        """
        with self.get_connection() as conn:
            query = "SELECT * FROM history"
            conditions = []
            params = []

            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)

            if success_only:
                conditions.append("success = 1")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [History(**dict(row)) for row in cursor.fetchall()]

    def get_history_stats(self) -> dict[str, Any]:
        """Get statistics about query history.

        Returns:
            Dictionary with statistics
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost_usd) as total_cost_usd,
                    AVG(processing_time_seconds) as avg_processing_time,
                    COUNT(DISTINCT session_id) as total_sessions
                FROM history
                """
            )
            row = cursor.fetchone()
            return dict(row)

    def clear_history(self, older_than_days: int | None = None) -> int:
        """Clear history entries.

        Args:
            older_than_days: Only clear entries older than this many days (None = all)

        Returns:
            Number of entries deleted
        """
        with self.get_connection() as conn:
            if older_than_days:
                cursor = conn.execute(
                    """
                    DELETE FROM history
                    WHERE created_at < datetime('now', '-' || ? || ' days')
                    """,
                    (older_than_days,),
                )
            else:
                cursor = conn.execute("DELETE FROM history")

            conn.commit()
            return cursor.rowcount


# Global database instance
_db: Database | None = None


def get_db() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
