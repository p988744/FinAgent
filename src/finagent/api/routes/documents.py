"""
Document Management API Routes

Handles document upload, versioning, and indexing operations.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from finagent.document_processing.metadata_store import DocumentMetadataStore
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.loader import DocumentLoader

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Document storage path
DOCUMENTS_PATH = Path("./data/documents")
DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)

# In-memory version tracking (simple implementation for alpha.5)
# In production, this should be stored in database
_document_versions: dict[str, list[dict[str, Any]]] = {}


class DocumentResponse(BaseModel):
    """Document metadata response."""

    id: str
    name: str
    file_path: str
    size_bytes: int
    status: str  # pending, indexed, error
    chunk_count: int
    version: int
    created_at: str
    updated_at: str
    description: str | None = None
    document_type: str | None = None


class DocumentVersion(BaseModel):
    """Document version history entry."""

    version: int
    file_path: str
    size_bytes: int
    created_at: str


class IndexStatus(BaseModel):
    """Overall index status."""

    total_documents: int
    indexed_documents: int
    pending_documents: int
    error_documents: int
    total_chunks: int
    last_indexed_at: str | None


class ReindexProgress(BaseModel):
    """Reindex operation progress."""

    status: str
    total: int
    processed: int
    failed: int
    message: str
    metadata_extracted: int = 0


class ReindexRequest(BaseModel):
    """Reindex operation request parameters."""

    extract_metadata: bool = False
    clear_existing: bool = False


def _get_metadata_store() -> DocumentMetadataStore:
    """Get singleton metadata store instance."""
    return DocumentMetadataStore()


def _metadata_to_response(metadata: Any, file_path: str = "") -> DocumentResponse:
    """Convert internal metadata to API response."""
    # Determine status based on indexed flag
    if metadata.indexed:
        status = "indexed"
    else:
        status = "pending"

    # Get file size
    size_bytes = 0
    if file_path and Path(file_path).exists():
        size_bytes = Path(file_path).stat().st_size
    elif hasattr(metadata, "file_path") and Path(metadata.file_path).exists():
        size_bytes = Path(metadata.file_path).stat().st_size

    # Get version from in-memory store
    version = 1
    if metadata.doc_id in _document_versions:
        version = len(_document_versions[metadata.doc_id])

    return DocumentResponse(
        id=metadata.doc_id,
        name=metadata.filename,
        file_path=str(file_path) if file_path else "",
        size_bytes=size_bytes,
        status=status,
        chunk_count=metadata.chunk_count,
        version=version,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        description=metadata.description,
        document_type=metadata.document_type,
    )


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    """Upload a new document."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Only support TXT files for now
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported in alpha.5",
        )

    # Generate document ID
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    # Save file to disk
    file_path = DOCUMENTS_PATH / file.filename
    content = await file.read()

    # Handle duplicate filenames
    if file_path.exists():
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = file_path.stem
        suffix = file_path.suffix
        file_path = DOCUMENTS_PATH / f"{stem}_{timestamp}{suffix}"

    with open(file_path, "wb") as f:
        f.write(content)

    # Create metadata
    from finagent.document_processing.metadata_store import DocumentMetadata

    metadata = DocumentMetadata(
        doc_id=doc_id,
        filename=file.filename,
        description=f"Uploaded file: {file.filename}",
        document_type="uploaded",
        keywords=[],
        date=None,
        issuing_authority=None,
        related_institutions=[],
        penalty_amount=None,
        violation_types=[],
        custom_fields={},
        indexed=False,
        chunk_count=0,
    )

    # Save metadata
    store = _get_metadata_store()
    store.add_metadata(metadata, str(file_path))

    # Initialize version history
    _document_versions[doc_id] = [
        {
            "version": 1,
            "file_path": str(file_path),
            "size_bytes": len(content),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ]

    return _metadata_to_response(metadata, str(file_path))


@router.get("/")
async def list_documents() -> list[DocumentResponse]:
    """List all documents with metadata."""
    store = _get_metadata_store()
    all_metadata = store.get_all_metadata()

    result = []
    for metadata in all_metadata:
        # Try to get file path from database
        doc = store.db.get_document(metadata.doc_id)
        file_path = doc.file_path if doc else ""
        result.append(_metadata_to_response(metadata, file_path))

    return result


@router.get("/status")
async def get_index_status() -> IndexStatus:
    """Get overall index status."""
    store = _get_metadata_store()
    all_metadata = store.get_all_metadata()

    total = len(all_metadata)
    indexed = sum(1 for m in all_metadata if m.indexed)
    pending = sum(1 for m in all_metadata if not m.indexed)
    total_chunks = sum(m.chunk_count for m in all_metadata)

    return IndexStatus(
        total_documents=total,
        indexed_documents=indexed,
        pending_documents=pending,
        error_documents=0,
        total_chunks=total_chunks,
        last_indexed_at=datetime.now(timezone.utc).isoformat() if indexed > 0 else None,
    )


@router.get("/{document_id}")
async def get_document(document_id: str) -> DocumentResponse:
    """Get single document details."""
    store = _get_metadata_store()
    metadata = store.get_metadata(document_id)

    if not metadata:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    doc = store.db.get_document(document_id)
    file_path = doc.file_path if doc else ""

    return _metadata_to_response(metadata, file_path)


@router.get("/{document_id}/content")
async def get_document_content(document_id: str) -> dict[str, Any]:
    """Get document content (text)."""
    store = _get_metadata_store()
    doc = store.db.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Document file not found: {file_path}")

    # Read file content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "id": document_id,
        "content": content,
        "size_chars": len(content),
        "file_path": str(file_path),
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> dict[str, str]:
    """Delete a document and its index."""
    store = _get_metadata_store()
    metadata = store.get_metadata(document_id)

    if not metadata:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Delete from metadata store (this will also delete from database)
    success = store.delete_metadata(document_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document metadata")

    # Clean up version history
    if document_id in _document_versions:
        del _document_versions[document_id]

    # Note: In production, we should also clean up the vector DB chunks
    # This would require the DocumentIndexer to have a delete_document method

    return {
        "status": "success",
        "message": f"Document {document_id} deleted",
    }


@router.post("/{document_id}/reindex")
async def reindex_single_document(
    document_id: str, request: ReindexRequest | None = None
) -> DocumentResponse:
    """Reindex a single document with optional metadata extraction."""
    extract_metadata = request.extract_metadata if request else False

    store = _get_metadata_store()
    doc = store.db.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Document file not found: {file_path}")

    # Load document
    loader = DocumentLoader()
    document = loader.load_txt(str(file_path))

    # Index document with optional metadata extraction (async)
    indexer = DocumentIndexer(extract_metadata=extract_metadata)
    num_chunks = await indexer.index_document(document)

    # Update metadata to mark as indexed
    metadata = store.get_metadata(document_id)
    if metadata:
        store.update_metadata(
            document_id,
            {
                "indexed": True,
                "chunk_count": num_chunks,
            },
        )
        metadata.indexed = True
        metadata.chunk_count = num_chunks

    return _metadata_to_response(metadata, str(file_path))


@router.post("/reindex-all")
async def reindex_all_documents(request: ReindexRequest | None = None) -> ReindexProgress:
    """Reindex all documents with optional metadata extraction (batch operation)."""
    extract_metadata = request.extract_metadata if request else False
    clear_existing = request.clear_existing if request else False

    store = _get_metadata_store()
    all_metadata = store.get_all_metadata()

    total = len(all_metadata)
    processed = 0
    failed = 0
    metadata_extracted = 0

    loader = DocumentLoader()
    indexer = DocumentIndexer(extract_metadata=extract_metadata)

    # Clear existing vector DB if requested
    if clear_existing:
        indexer.clear_collection()

    for metadata in all_metadata:
        try:
            doc = store.db.get_document(metadata.doc_id)
            if not doc or not Path(doc.file_path).exists():
                failed += 1
                continue

            document = loader.load_txt(doc.file_path)
            num_chunks = await indexer.index_document(document)

            # Check if metadata was extracted
            if extract_metadata:
                # Verify metadata was stored
                updated_doc = store.db.get_document(metadata.doc_id)
                if updated_doc and updated_doc.get("extraction_confidence"):
                    metadata_extracted += 1

            store.update_metadata(
                metadata.doc_id,
                {
                    "indexed": True,
                    "chunk_count": num_chunks,
                },
            )
            processed += 1

        except Exception as e:
            print(f"Failed to index {metadata.doc_id}: {e}")
            failed += 1

    message = f"Reindexed {processed}/{total} documents, {failed} failed"
    if extract_metadata:
        message += f", {metadata_extracted} with metadata extracted"

    return ReindexProgress(
        status="completed",
        total=total,
        processed=processed,
        failed=failed,
        metadata_extracted=metadata_extracted,
        message=message,
    )


@router.post("/{document_id}/versions")
async def upload_new_version(
    document_id: str, file: UploadFile = File(...)
) -> DocumentResponse:
    """Upload a new version of an existing document."""
    store = _get_metadata_store()
    metadata = store.get_metadata(document_id)

    if not metadata:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Save new version
    content = await file.read()
    version_num = len(_document_versions.get(document_id, [])) + 1

    # Create versioned filename
    stem = Path(file.filename).stem
    suffix = Path(file.filename).suffix
    versioned_filename = f"{stem}_v{version_num}{suffix}"
    file_path = DOCUMENTS_PATH / versioned_filename

    with open(file_path, "wb") as f:
        f.write(content)

    # Update version history
    if document_id not in _document_versions:
        _document_versions[document_id] = []

    _document_versions[document_id].append(
        {
            "version": version_num,
            "file_path": str(file_path),
            "size_bytes": len(content),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Update metadata
    store.update_metadata(
        document_id,
        {
            "indexed": False,  # Needs reindexing
            "chunk_count": 0,
        },
    )

    # Update file path in database
    doc = store.db.get_document(document_id)
    if doc:
        doc.file_path = str(file_path)
        store.db.add_document(doc)

    # Refresh metadata
    metadata = store.get_metadata(document_id)

    return _metadata_to_response(metadata, str(file_path))


@router.get("/{document_id}/versions")
async def get_version_history(document_id: str) -> list[DocumentVersion]:
    """Get version history for a document."""
    store = _get_metadata_store()
    metadata = store.get_metadata(document_id)

    if not metadata:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    versions = _document_versions.get(document_id, [])

    # If no version history, create one from current state
    if not versions:
        doc = store.db.get_document(document_id)
        if doc:
            size_bytes = 0
            if Path(doc.file_path).exists():
                size_bytes = Path(doc.file_path).stat().st_size

            versions = [
                {
                    "version": 1,
                    "file_path": doc.file_path,
                    "size_bytes": size_bytes,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ]

    return [
        DocumentVersion(
            version=v["version"],
            file_path=v["file_path"],
            size_bytes=v["size_bytes"],
            created_at=v["created_at"],
        )
        for v in versions
    ]
