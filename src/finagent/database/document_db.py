"""Database operations for document management."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentDatabase:
    """Handles all database operations for documents."""

    def __init__(self, db_path: str = "data/finagent.db"):
        """
        Initialize document database.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        # Ensure database exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def upsert_document(
        self,
        doc_id: str,
        filename: str,
        file_path: str,
        **kwargs,
    ) -> int:
        """
        Insert or update document metadata.

        Args:
            doc_id: Unique document identifier
            filename: Document filename
            file_path: Full path to document file
            **kwargs: Additional fields (title, description, document_type, etc.)

        Returns:
            Document ID (integer primary key)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Prepare fields
            fields = {
                "doc_id": doc_id,
                "filename": filename,
                "file_path": file_path,
            }

            # Add optional fields
            optional_fields = [
                "title",
                "description",
                "document_type",
                "category_id",
                "issuing_authority",
                "case_number",
                "document_date",
                "related_institutions",  # JSON
                "violation_types",  # JSON
                "penalty_amount",
                "keywords",  # JSON
                "content_preview",
                "full_content",  # Full document content for wiki display (text files only)
                "mime_type",  # MIME type for file type identification
                "indexed",
                "chunk_count",
                "file_size",
                "language",
                "extraction_method",
                "extraction_confidence",
                "document_status",
                "custom_fields",  # JSON
                # Metadata extraction status fields
                "metadata_extracted",
                "metadata_extraction_status",
                "metadata_extraction_error",
                "metadata_extraction_attempts",
                "metadata_last_extracted_at",
                "metadata_edited_by_user",
                # Pipeline monitoring fields
                "pipeline_stage",
                "pipeline_status",
                "pipeline_data",  # JSON
                "pipeline_started_at",
                "pipeline_completed_at",
            ]

            for field in optional_fields:
                if field in kwargs:
                    value = kwargs[field]
                    # Convert lists to JSON strings
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False)
                    fields[field] = value

            # Check if document exists
            cursor.execute("SELECT id FROM documents WHERE doc_id = ?", (doc_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing document
                set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
                values = list(fields.values())
                values.append(doc_id)  # For WHERE clause

                cursor.execute(
                    f"UPDATE documents SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE doc_id = ?",
                    values,
                )
                doc_pk = existing["id"]
                logger.info(f"Updated document: {doc_id}")
            else:
                # Insert new document
                columns = ", ".join(fields.keys())
                placeholders = ", ".join(["?" for _ in fields])
                values = list(fields.values())

                cursor.execute(
                    f"INSERT INTO documents ({columns}) VALUES ({placeholders})",
                    values,
                )
                doc_pk = cursor.lastrowid
                logger.info(f"Inserted document: {doc_id}")

            conn.commit()
            return doc_pk

        except Exception as e:
            conn.rollback()
            logger.error(f"Error upserting document {doc_id}: {e}")
            raise
        finally:
            conn.close()

    def get_full_content(self, doc_id: str) -> str | None:
        """
        Get full content of a document for wiki display.

        Args:
            doc_id: Document identifier

        Returns:
            Full document content or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT full_content FROM documents WHERE doc_id = ?",
                (doc_id,),
            )
            row = cursor.fetchone()
            return row["full_content"] if row else None
        finally:
            conn.close()

    def get_document(self, doc_id: str) -> dict | None:
        """
        Get document metadata by doc_id.

        Args:
            doc_id: Document identifier

        Returns:
            Dictionary with document data or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT *
                FROM documents
                WHERE doc_id = ?
                """,
                (doc_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            doc = dict(row)

            # Parse JSON fields
            json_fields = [
                "keywords",
                "related_institutions",
                "violation_types",
                "custom_fields",
            ]
            for field in json_fields:
                if doc.get(field):
                    try:
                        doc[field] = json.loads(doc[field])
                    except (json.JSONDecodeError, TypeError):
                        pass

            return doc

        finally:
            conn.close()

    def list_documents(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC",
    ) -> list[dict]:
        """
        List documents with optional filters.

        Args:
            filters: Dictionary of field:value filters
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: ORDER BY clause (default: newest first)

        Returns:
            List of document dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            where_clauses = []
            values = []

            if filters:
                for field, value in filters.items():
                    if value is not None:
                        where_clauses.append(f"{field} = ?")
                        values.append(value)

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            query = f"""
                SELECT *
                FROM documents
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """

            values.extend([limit, offset])

            cursor.execute(query, values)
            rows = cursor.fetchall()

            documents = []
            for row in rows:
                doc = dict(row)

                # Parse JSON fields
                json_fields = [
                    "keywords",
                    "related_institutions",
                    "violation_types",
                    "custom_fields",
                ]
                for field in json_fields:
                    if doc.get(field):
                        try:
                            doc[field] = json.loads(doc[field])
                        except (json.JSONDecodeError, TypeError):
                            pass

                documents.append(doc)

            return documents

        finally:
            conn.close()

    def mark_as_indexed(self, doc_id: str, chunk_count: int):
        """
        Mark document as indexed with chunk count.

        Args:
            doc_id: Document identifier
            chunk_count: Number of chunks created
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE documents
                SET indexed = 1,
                    chunk_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
                """,
                (chunk_count, doc_id),
            )
            conn.commit()
            logger.info(f"Marked document as indexed: {doc_id} ({chunk_count} chunks)")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error marking document as indexed: {e}")
            raise
        finally:
            conn.close()

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document from database.

        Args:
            doc_id: Document identifier

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

            if deleted:
                logger.info(f"Deleted document: {doc_id}")
            else:
                logger.warning(f"Document not found for deletion: {doc_id}")

            return deleted

        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting document: {e}")
            raise
        finally:
            conn.close()

    def count_documents(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count documents matching filters.

        Args:
            filters: Optional filters

        Returns:
            Document count
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            where_clauses = []
            values = []

            if filters:
                for field, value in filters.items():
                    if value is not None:
                        where_clauses.append(f"{field} = ?")
                        values.append(value)

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            cursor.execute(
                f"SELECT COUNT(*) as count FROM documents WHERE {where_clause}",
                values,
            )

            result = cursor.fetchone()
            return result["count"] if result else 0

        finally:
            conn.close()

    def increment_access_count(self, doc_id: str):
        """
        Increment access count and update last_accessed timestamp.

        Args:
            doc_id: Document identifier
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE documents
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE doc_id = ?
                """,
                (doc_id,),
            )
            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Error incrementing access count: {e}")
            raise
        finally:
            conn.close()

    def get_documents_by_category(
        self, category_id: int, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """
        Get all documents in a category.

        Args:
            category_id: Wiki category ID
            limit: Maximum results
            offset: Results to skip

        Returns:
            List of documents
        """
        return self.list_documents(
            filters={"category_id": category_id},
            limit=limit,
            offset=offset,
        )

    def get_indexed_documents(self) -> list[dict]:
        """
        Get all indexed documents.

        Returns:
            List of indexed documents
        """
        return self.list_documents(filters={"indexed": 1}, limit=10000)

    def get_statistics(self) -> dict[str, Any]:
        """
        Get overall document statistics.

        Returns:
            Dictionary with statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            stats = {}

            # Total documents
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            stats["total_documents"] = cursor.fetchone()["count"]

            # Indexed documents
            cursor.execute("SELECT COUNT(*) as count FROM documents WHERE indexed = 1")
            stats["indexed_documents"] = cursor.fetchone()["count"]

            # By document type
            cursor.execute(
                """
                SELECT document_type, COUNT(*) as count
                FROM documents
                WHERE document_type IS NOT NULL
                GROUP BY document_type
                ORDER BY count DESC
                """
            )
            stats["by_type"] = [
                {"type": row["document_type"], "count": row["count"]}
                for row in cursor.fetchall()
            ]

            # By authority
            cursor.execute(
                """
                SELECT issuing_authority, COUNT(*) as count
                FROM documents
                WHERE issuing_authority IS NOT NULL
                GROUP BY issuing_authority
                ORDER BY count DESC
                """
            )
            stats["by_authority"] = [
                {"authority": row["issuing_authority"], "count": row["count"]}
                for row in cursor.fetchall()
            ]

            # Total chunks
            cursor.execute("SELECT SUM(chunk_count) as total FROM documents")
            result = cursor.fetchone()
            stats["total_chunks"] = result["total"] if result["total"] else 0

            return stats

        finally:
            conn.close()
