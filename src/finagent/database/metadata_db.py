"""Database for document metadata."""

import logging
import sqlite3
from pathlib import Path
from typing import Any

from finagent.models.document_metadata import ExtendedDocumentMetadata

logger = logging.getLogger(__name__)


class MetadataDB:
    """Database for document metadata with filtering and querying capabilities."""

    def __init__(self, db_path: str = "./data/finagent.db"):
        self.db_path = db_path
        self._ensure_database_dir()
        self._init_schema()

    def _ensure_database_dir(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize metadata table schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    entity_normalized TEXT NOT NULL,
                    penalty_type TEXT NOT NULL,
                    penalty_amount REAL,
                    date TEXT NOT NULL,
                    year_roc INTEGER,
                    year_ad INTEGER,
                    jurisdiction TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    case_number TEXT,
                    content_length INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # Create indexes for fast querying
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entity ON document_metadata(entity)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_date ON document_metadata(date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_penalty_type ON document_metadata(penalty_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jurisdiction ON document_metadata(jurisdiction)"
            )

            conn.commit()
            logger.info("Metadata database schema initialized")

    async def insert(self, metadata: ExtendedDocumentMetadata):
        """Insert document metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO document_metadata
                (filename, file_path, entity, entity_normalized, penalty_type,
                 penalty_amount, date, year_roc, year_ad, jurisdiction,
                 document_type, case_number, content_length, chunk_count,
                 indexed_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metadata.filename,
                    metadata.file_path,
                    metadata.entity,
                    metadata.entity_normalized,
                    metadata.penalty_type,
                    metadata.penalty_amount,
                    metadata.date,
                    metadata.year_roc,
                    metadata.year_ad,
                    metadata.jurisdiction,
                    metadata.document_type,
                    metadata.case_number,
                    metadata.content_length,
                    metadata.chunk_count,
                    metadata.indexed_at,
                    metadata.updated_at,
                ),
            )
            conn.commit()
            logger.debug(f"Inserted metadata for: {metadata.filename}")

    async def search(self, filters: dict[str, Any]) -> list[dict]:
        """
        Search metadata with filters.

        Args:
            filters: Dictionary of filter criteria
                - entity: str (partial match)
                - date_from: str (YYYY-MM-DD)
                - date_to: str (YYYY-MM-DD)
                - penalty_type: str (partial match)
                - jurisdiction: str (exact match)
                - year_ad: int

        Returns:
            List of matching documents as dictionaries
        """
        query = "SELECT * FROM document_metadata WHERE 1=1"
        params = []

        if entity := filters.get("entity"):
            query += " AND (entity LIKE ? OR entity_normalized LIKE ?)"
            params.append(f"%{entity}%")
            params.append(f"%{entity}%")

        if date_from := filters.get("date_from"):
            query += " AND date >= ?"
            params.append(date_from)

        if date_to := filters.get("date_to"):
            query += " AND date <= ?"
            params.append(date_to)

        if penalty_type := filters.get("penalty_type"):
            query += " AND penalty_type LIKE ?"
            params.append(f"%{penalty_type}%")

        if jurisdiction := filters.get("jurisdiction"):
            query += " AND jurisdiction = ?"
            params.append(jurisdiction)

        if year_ad := filters.get("year_ad"):
            query += " AND year_ad = ?"
            params.append(year_ad)

        # Sort by date DESC by default
        query += " ORDER BY date DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]

        logger.debug(f"Metadata search returned {len(results)} results")
        return results

    async def list_all(
        self, entity: str | None = None, penalty_type: str | None = None
    ) -> list[dict]:
        """
        List all documents matching criteria.

        Args:
            entity: Entity name (optional)
            penalty_type: Penalty type (optional)

        Returns:
            List of all matching documents
        """
        filters = {}
        if entity:
            filters["entity"] = entity
        if penalty_type:
            filters["penalty_type"] = penalty_type

        return await self.search(filters)

    async def get_file_path(self, filename: str) -> str | None:
        """Get file path by filename."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT file_path FROM document_metadata WHERE filename = ?",
                (filename,),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    async def get_metadata(self, filename: str) -> dict | None:
        """Get metadata by filename."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM document_metadata WHERE filename = ?", (filename,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    async def count_documents(self) -> int:
        """Get total number of documents in metadata DB."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM document_metadata")
            return cursor.fetchone()[0]

    async def delete_by_filename(self, filename: str) -> bool:
        """
        Delete metadata by filename.

        Args:
            filename: Document filename

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM document_metadata WHERE filename = ?", (filename,)
            )
            conn.commit()
            return cursor.rowcount > 0
