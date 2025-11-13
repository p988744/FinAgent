"""Document metadata storage for enhanced document descriptions."""

from datetime import datetime
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

        Args:
            doc_id: Document ID
            updates: Dictionary of fields to update

        Returns:
            Updated DocumentMetadata if exists, None otherwise
        """
        # Get current document
        doc = self.db.get_document(doc_id)
        if not doc:
            return None

        # Convert to DocumentMetadata, update fields, and save back
        meta = DocumentMetadata.from_document(doc)

        # Update fields (map field names from DocumentMetadata to Document model)
        field_mapping = {
            "date": "document_date",  # DocumentMetadata.date -> Document.document_date
        }

        for key, value in updates.items():
            # Use mapped field name if it exists
            meta_key = key
            if hasattr(meta, meta_key):
                setattr(meta, meta_key, value)

        # Save updated metadata back to database
        self.add_metadata(meta, file_path=doc.file_path)

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
