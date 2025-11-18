"""Database operations for wiki management."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WikiDatabase:
    """Handles all database operations for wiki features."""

    def __init__(self, db_path: str = "data/finagent.db"):
        """
        Initialize wiki database.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ============================================================================
    # Wiki Categories
    # ============================================================================

    def create_category(
        self,
        name: str,
        category_type: str,
        parent_id: int | None = None,
        description: str | None = None,
        icon: str | None = None,
        display_order: int = 0,
    ) -> int:
        """
        Create a new wiki category.

        Args:
            name: Category name
            category_type: Type (authority, institution, violation, document_type)
            parent_id: Parent category ID (None for root)
            description: Optional description
            icon: Optional icon (emoji or identifier)
            display_order: Display order within parent

        Returns:
            Category ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO wiki_categories (name, category_type, parent_id, description, icon, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, category_type, parent_id, description, icon, display_order),
            )
            conn.commit()
            category_id = cursor.lastrowid
            logger.info(f"Created category: {name} (ID: {category_id})")
            return category_id

        except sqlite3.IntegrityError:
            # Category already exists
            cursor.execute(
                "SELECT id FROM wiki_categories WHERE name = ? AND category_type = ?",
                (name, category_type),
            )
            result = cursor.fetchone()
            return result["id"] if result else None
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating category: {e}")
            raise
        finally:
            conn.close()

    def get_category(self, category_id: int) -> dict | None:
        """Get category by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM wiki_categories WHERE id = ?",
                (category_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_categories(
        self,
        category_type: str | None = None,
        parent_id: int | None = None,
    ) -> list[dict]:
        """
        List categories with optional filters.

        Args:
            category_type: Filter by type
            parent_id: Filter by parent (None = root categories)

        Returns:
            List of categories
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM wiki_categories WHERE 1=1"
            params = []

            if category_type:
                query += " AND category_type = ?"
                params.append(category_type)

            if parent_id is not None:
                query += " AND parent_id = ?"
                params.append(parent_id)
            else:
                # Root categories (parent_id IS NULL)
                query += " AND parent_id IS NULL"

            query += " ORDER BY display_order, name"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def update_category_count(self, category_id: int, count: int):
        """Update document count for a category."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE wiki_categories
                SET document_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (count, category_id),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating category count: {e}")
            raise
        finally:
            conn.close()

    def delete_category(self, category_id: int) -> bool:
        """
        Delete a category and its subcategories (cascade).

        Args:
            category_id: Category ID to delete

        Returns:
            True if deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM wiki_categories WHERE id = ?", (category_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting category: {e}")
            raise
        finally:
            conn.close()

    # ============================================================================
    # Document Relationships
    # ============================================================================

    def create_relationship(
        self,
        doc_id_1: str,
        doc_id_2: str,
        relationship_type: str,
        strength: float = 0.5,
        metadata: dict | None = None,
    ) -> int:
        """
        Create a relationship between two documents.

        Args:
            doc_id_1: First document ID
            doc_id_2: Second document ID
            relationship_type: Type (related, supersedes, amendment, references, similar)
            strength: Relationship strength (0-1)
            metadata: Optional metadata dictionary

        Returns:
            Relationship ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None

            cursor.execute(
                """
                INSERT OR REPLACE INTO document_relationships
                (doc_id_1, doc_id_2, relationship_type, strength, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (doc_id_1, doc_id_2, relationship_type, strength, metadata_json),
            )
            conn.commit()
            return cursor.lastrowid

        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating relationship: {e}")
            raise
        finally:
            conn.close()

    def get_related_documents(
        self,
        doc_id: str,
        relationship_type: str | None = None,
        min_strength: float = 0.0,
    ) -> list[dict]:
        """
        Get documents related to a given document.

        Args:
            doc_id: Document ID
            relationship_type: Filter by type
            min_strength: Minimum relationship strength

        Returns:
            List of related documents with relationship info
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT
                    CASE
                        WHEN doc_id_1 = ? THEN doc_id_2
                        ELSE doc_id_1
                    END as related_doc_id,
                    relationship_type,
                    strength,
                    metadata
                FROM document_relationships
                WHERE (doc_id_1 = ? OR doc_id_2 = ?)
                    AND strength >= ?
            """
            params = [doc_id, doc_id, doc_id, min_strength]

            if relationship_type:
                query += " AND relationship_type = ?"
                params.append(relationship_type)

            query += " ORDER BY strength DESC"

            cursor.execute(query, params)

            relationships = []
            for row in cursor.fetchall():
                rel = dict(row)
                if rel.get("metadata"):
                    try:
                        rel["metadata"] = json.loads(rel["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                relationships.append(rel)

            return relationships

        finally:
            conn.close()

    def delete_relationships(self, doc_id: str):
        """Delete all relationships for a document."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM document_relationships WHERE doc_id_1 = ? OR doc_id_2 = ?",
                (doc_id, doc_id),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting relationships: {e}")
            raise
        finally:
            conn.close()

    # ============================================================================
    # Wiki Statistics
    # ============================================================================

    def save_statistic(
        self,
        stat_type: str,
        stat_key: str | None,
        stat_value: int,
        metadata: dict | None = None,
    ):
        """
        Save a wiki statistic.

        Args:
            stat_type: Type (total_docs, by_authority, by_year, etc.)
            stat_key: Optional key (e.g., '2020', '金管會')
            stat_value: Statistic value (count)
            metadata: Optional metadata
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None

            # Delete old statistics of same type/key
            if stat_key:
                cursor.execute(
                    "DELETE FROM wiki_statistics WHERE stat_type = ? AND stat_key = ?",
                    (stat_type, stat_key),
                )
            else:
                cursor.execute(
                    "DELETE FROM wiki_statistics WHERE stat_type = ? AND stat_key IS NULL",
                    (stat_type,),
                )

            # Insert new statistic
            cursor.execute(
                """
                INSERT INTO wiki_statistics (stat_type, stat_key, stat_value, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (stat_type, stat_key, stat_value, metadata_json),
            )

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving statistic: {e}")
            raise
        finally:
            conn.close()

    def get_statistics(self, stat_type: str | None = None) -> list[dict]:
        """
        Get wiki statistics.

        Args:
            stat_type: Optional filter by type

        Returns:
            List of statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if stat_type:
                cursor.execute(
                    """
                    SELECT * FROM wiki_statistics
                    WHERE stat_type = ?
                    ORDER BY stat_key
                    """,
                    (stat_type,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM wiki_statistics ORDER BY stat_type, stat_key"
                )

            stats = []
            for row in cursor.fetchall():
                stat = dict(row)
                if stat.get("metadata"):
                    try:
                        stat["metadata"] = json.loads(stat["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                stats.append(stat)

            return stats

        finally:
            conn.close()

    def clear_statistics(self, stat_type: str | None = None):
        """
        Clear wiki statistics.

        Args:
            stat_type: Optional - clear only this type, or all if None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if stat_type:
                cursor.execute(
                    "DELETE FROM wiki_statistics WHERE stat_type = ?",
                    (stat_type,),
                )
            else:
                cursor.execute("DELETE FROM wiki_statistics")

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Error clearing statistics: {e}")
            raise
        finally:
            conn.close()
