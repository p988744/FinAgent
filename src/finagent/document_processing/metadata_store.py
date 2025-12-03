"""Document metadata storage for enhanced document descriptions."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from finagent.database.db import Database
from finagent.database.models import Document


class DocumentMetadata(BaseModel):
    """Enhanced metadata for a document."""

    doc_id: str
    filename: str
    description: str  # Human-readable description of document content
    document_type: str  # e.g., "裁罰書", "判決書", "法規", "新聞報導"
    keywords: list[str]  # Key topics/entities mentioned
    date: str | None = None  # Document date (e.g., "2020-09-15")
    issuing_authority: str | None = None  # e.g., "金管會", "中央銀行"
    related_institutions: list[str] = []  # Banks/institutions mentioned
    penalty_amount: str | None = None  # If penalty document
    violation_types: list[str] = []  # Types of violations
    custom_fields: dict[str, Any] = {}  # Additional custom metadata
    indexed: bool = False  # Whether indexed in vector DB
    chunk_count: int = 0  # Number of chunks in vector DB
    created_at: str
    updated_at: str

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_document(cls, doc: Document) -> "DocumentMetadata":
        """Create DocumentMetadata from database Document model."""
        return cls(
            doc_id=doc.doc_id,
            filename=doc.filename,
            description=doc.description or "",
            document_type=doc.document_type or "",
            keywords=doc.keywords,
            date=doc.document_date,
            issuing_authority=doc.issuing_authority,
            related_institutions=doc.related_institutions,
            penalty_amount=doc.penalty_amount,
            violation_types=doc.violation_types,
            custom_fields=doc.custom_fields or {},
            indexed=doc.indexed,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat(),
            updated_at=doc.updated_at.isoformat() if doc.updated_at else datetime.now().isoformat(),
        )

    def to_document(self, file_path: str = "") -> Document:
        """Convert to database Document model."""
        return Document(
            doc_id=self.doc_id,
            filename=self.filename,
            file_path=file_path,
            description=self.description,
            document_type=self.document_type,
            keywords=self.keywords,
            document_date=self.date,
            issuing_authority=self.issuing_authority,
            related_institutions=self.related_institutions,
            penalty_amount=self.penalty_amount,
            violation_types=self.violation_types,
            custom_fields=self.custom_fields,
            indexed=self.indexed,
            chunk_count=self.chunk_count,
        )


class DocumentMetadataStore:
    """Stores and retrieves document metadata using database backend."""

    def __init__(self, storage_path: str | None = None):
        """
        Initialize metadata store.

        Args:
            storage_path: Legacy parameter (ignored, kept for backwards compatibility)
        """
        # Use database backend instead of JSON file
        self.db = Database()

    def add_metadata(self, metadata: DocumentMetadata, file_path: str = "") -> None:
        """
        Add or update document metadata.

        Args:
            metadata: DocumentMetadata object
            file_path: Full path to document file (optional if updating)
        """
        # Convert to Document model and save to database
        doc = metadata.to_document(file_path=file_path)
        self.db.add_document(doc)

    def get_metadata(self, doc_id: str) -> DocumentMetadata | None:
        """
        Get metadata for a document.

        Args:
            doc_id: Document ID

        Returns:
            DocumentMetadata if exists, None otherwise
        """
        doc = self.db.get_document(doc_id)
        if doc:
            return DocumentMetadata.from_document(doc)
        return None

    def get_all_metadata(self) -> list[DocumentMetadata]:
        """Get all document metadata."""
        docs = self.db.get_all_documents()
        return [DocumentMetadata.from_document(doc) for doc in docs]

    def search_metadata(
        self,
        keyword: str | None = None,
        document_type: str | None = None,
        institution: str | None = None,
    ) -> list[DocumentMetadata]:
        """
        Search metadata by criteria.

        Args:
            keyword: Search in description and keywords
            document_type: Filter by document type
            institution: Filter by related institution

        Returns:
            List of matching DocumentMetadata
        """
        docs = self.db.search_documents(
            keyword=keyword, institution=institution, authority=None
        )

        # Additional filtering for document_type if needed
        if document_type:
            docs = [doc for doc in docs if doc.document_type == document_type]

        return [DocumentMetadata.from_document(doc) for doc in docs]

    def delete_metadata(self, doc_id: str) -> bool:
        """
        Delete metadata for a document.

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        return self.db.delete_document(doc_id)

    def clear_all(self) -> None:
        """
        Clear all metadata from store.

        This removes all stored metadata from the database.
        Useful when doing a full reindex with --clear flag.
        """
        # Delete all documents from database
        all_docs = self.db.get_all_documents()
        for doc in all_docs:
            self.db.delete_document(doc.doc_id)

    def update_metadata(self, doc_id: str, updates: dict[str, Any]) -> DocumentMetadata | None:
        """
        Update specific fields of document metadata.
        If document doesn't exist, creates a new one with the provided fields.

        Args:
            doc_id: Document ID
            updates: Dictionary of fields to update

        Returns:
            Updated DocumentMetadata if exists, newly created if not exists, None on error
        """
        from datetime import datetime

        # Get current document
        doc = self.db.get_document(doc_id)
        if not doc:
            # Document doesn't exist - create a new one with minimal defaults
            now = datetime.now(UTC).isoformat()
            meta = DocumentMetadata(
                doc_id=doc_id,
                filename=updates.get('filename', f'{doc_id}.txt'),
                description=updates.get('description', ''),
                document_type=updates.get('document_type', 'uploaded'),
                keywords=updates.get('keywords', []),
                date=updates.get('date'),
                issuing_authority=updates.get('issuing_authority'),
                related_institutions=updates.get('related_institutions', []),
                penalty_amount=updates.get('penalty_amount'),
                violation_types=updates.get('violation_types', []),
                custom_fields=updates.get('custom_fields', {}),
                indexed=updates.get('indexed', False),
                chunk_count=updates.get('chunk_count', 0),
                created_at=updates.get('created_at', now),
                updated_at=updates.get('updated_at', now),
            )
            # Apply any additional updates
            for key, value in updates.items():
                if hasattr(meta, key) and key not in ['doc_id', 'created_at']:
                    setattr(meta, key, value)

            # Save new metadata
            self.add_metadata(meta, file_path=updates.get('file_path', ''))

            # Now update pipeline fields directly in database (they're not in DocumentMetadata)
            pipeline_fields = {
                'pipeline_stage', 'pipeline_status', 'pipeline_data',
                'pipeline_started_at', 'pipeline_completed_at'
            }
            pipeline_updates = {k: v for k, v in updates.items() if k in pipeline_fields}

            if pipeline_updates:
                # Use Database connection to update pipeline fields
                with self.db.get_connection() as conn:
                    # Build UPDATE SQL
                    set_clauses = []
                    values = []
                    for key, value in pipeline_updates.items():
                        set_clauses.append(f"{key} = ?")
                        values.append(value)

                    if set_clauses:
                        values.append(doc_id)
                        sql = f"UPDATE documents SET {', '.join(set_clauses)} WHERE doc_id = ?"
                        conn.execute(sql, values)
                        conn.commit()

            return meta

        # Convert to DocumentMetadata, update fields, and save back
        meta = DocumentMetadata.from_document(doc)

        # Separate pipeline fields from metadata fields
        pipeline_fields = {
            'pipeline_stage', 'pipeline_status', 'pipeline_data',
            'pipeline_started_at', 'pipeline_completed_at'
        }
        metadata_updates = {k: v for k, v in updates.items() if k not in pipeline_fields}
        pipeline_updates = {k: v for k, v in updates.items() if k in pipeline_fields}

        # Update metadata fields

        for key, value in metadata_updates.items():
            # Use mapped field name if it exists
            meta_key = key
            if hasattr(meta, meta_key):
                setattr(meta, meta_key, value)

        # Save updated metadata back to database
        self.add_metadata(meta, file_path=doc.file_path)

        # Update pipeline fields directly in database
        if pipeline_updates:
            # Use Database connection to update pipeline fields
            with self.db.get_connection() as conn:
                # Build UPDATE SQL
                set_clauses = []
                values = []
                for key, value in pipeline_updates.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(value)

                if set_clauses:
                    values.append(doc_id)
                    sql = f"UPDATE documents SET {', '.join(set_clauses)} WHERE doc_id = ?"
                    conn.execute(sql, values)
                    conn.commit()

        return meta

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about stored metadata.

        Returns:
            Dictionary with statistics
        """
        stats = self.db.get_document_statistics()

        # Map database statistics keys to legacy format for backwards compatibility
        return {
            "total_documents": stats["total_documents"],
            "by_type": stats.get("by_document_type", {}),
            "by_authority": stats.get("by_issuing_authority", {}),
        }
