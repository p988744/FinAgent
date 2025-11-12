"""Document metadata storage for enhanced document descriptions."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    """Enhanced metadata for a document."""

    doc_id: str
    filename: str
    description: str  # Human-readable description of document content
    document_type: str  # e.g., "裁罰書", "判決書", "法規", "新聞報導"
    keywords: List[str]  # Key topics/entities mentioned
    date: Optional[str] = None  # Document date (e.g., "2020-09-15")
    issuing_authority: Optional[str] = None  # e.g., "金管會", "中央銀行"
    related_institutions: List[str] = []  # Banks/institutions mentioned
    penalty_amount: Optional[str] = None  # If penalty document
    violation_types: List[str] = []  # Types of violations
    custom_fields: Dict[str, Any] = {}  # Additional custom metadata
    created_at: str
    updated_at: str

    class Config:
        arbitrary_types_allowed = True


class DocumentMetadataStore:
    """Stores and retrieves document metadata."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize metadata store.

        Args:
            storage_path: Path to metadata storage file (default: ./data/document_metadata.json)
        """
        self.storage_path = Path(storage_path or "./data/document_metadata.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing metadata
        self.metadata: Dict[str, DocumentMetadata] = {}
        self._load()

    def _load(self):
        """Load metadata from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for doc_id, meta_dict in data.items():
                        self.metadata[doc_id] = DocumentMetadata(**meta_dict)
            except Exception as e:
                print(f"Warning: Failed to load metadata: {e}")

    def _save(self):
        """Save metadata to storage file."""
        try:
            data = {
                doc_id: meta.model_dump()
                for doc_id, meta in self.metadata.items()
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error: Failed to save metadata: {e}")
            raise

    def add_metadata(self, metadata: DocumentMetadata) -> None:
        """
        Add or update document metadata.

        Args:
            metadata: DocumentMetadata object
        """
        metadata.updated_at = datetime.now().isoformat()
        self.metadata[metadata.doc_id] = metadata
        self._save()

    def get_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """
        Get metadata for a document.

        Args:
            doc_id: Document ID

        Returns:
            DocumentMetadata if exists, None otherwise
        """
        return self.metadata.get(doc_id)

    def get_all_metadata(self) -> List[DocumentMetadata]:
        """Get all document metadata."""
        return list(self.metadata.values())

    def search_metadata(
        self,
        keyword: Optional[str] = None,
        document_type: Optional[str] = None,
        institution: Optional[str] = None
    ) -> List[DocumentMetadata]:
        """
        Search metadata by criteria.

        Args:
            keyword: Search in description and keywords
            document_type: Filter by document type
            institution: Filter by related institution

        Returns:
            List of matching DocumentMetadata
        """
        results = []

        for meta in self.metadata.values():
            # Check keyword
            if keyword:
                keyword_lower = keyword.lower()
                if not (
                    keyword_lower in meta.description.lower() or
                    any(keyword_lower in kw.lower() for kw in meta.keywords)
                ):
                    continue

            # Check document type
            if document_type and meta.document_type != document_type:
                continue

            # Check institution
            if institution and institution not in meta.related_institutions:
                continue

            results.append(meta)

        return results

    def delete_metadata(self, doc_id: str) -> bool:
        """
        Delete metadata for a document.

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        if doc_id in self.metadata:
            del self.metadata[doc_id]
            self._save()
            return True
        return False

    def update_metadata(
        self,
        doc_id: str,
        updates: Dict[str, Any]
    ) -> Optional[DocumentMetadata]:
        """
        Update specific fields of document metadata.

        Args:
            doc_id: Document ID
            updates: Dictionary of fields to update

        Returns:
            Updated DocumentMetadata if exists, None otherwise
        """
        if doc_id not in self.metadata:
            return None

        meta = self.metadata[doc_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(meta, key):
                setattr(meta, key, value)

        meta.updated_at = datetime.now().isoformat()
        self._save()

        return meta

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored metadata.

        Returns:
            Dictionary with statistics
        """
        total = len(self.metadata)

        # Count by document type
        type_counts = {}
        for meta in self.metadata.values():
            doc_type = meta.document_type
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        # Count by authority
        authority_counts = {}
        for meta in self.metadata.values():
            if meta.issuing_authority:
                authority = meta.issuing_authority
                authority_counts[authority] = authority_counts.get(authority, 0) + 1

        return {
            "total_documents": total,
            "by_type": type_counts,
            "by_authority": authority_counts,
        }
