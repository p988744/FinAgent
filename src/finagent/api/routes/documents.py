"""
Document Management API Routes

Handles document upload, versioning, and indexing operations.
"""

import logging
import os
import uuid
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from enum import Enum

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Form
from pydantic import BaseModel

from finagent.document_processing.metadata_store import DocumentMetadataStore
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.loader import DocumentLoader
from finagent.models.document_types import (
    DocumentCategory,
    DocumentType,
    get_allowed_document_types,
    validate_document_type,
    is_document_type_allowed,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Document storage path
DOCUMENTS_PATH = Path("./data/documents")
DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)

# In-memory version tracking (simple implementation for alpha.5)
# In production, this should be stored in database
_document_versions: dict[str, list[dict[str, Any]]] = {}

# Upload progress tracking (in-memory for now, similar to Google Drive approach)
class UploadStage(str, Enum):
    UPLOADING = "uploading"  # 0-20%
    UPLOADED = "uploaded"  # 20%
    METADATA_SAVED = "metadata_saved"  # 40%
    PROCESSING = "processing"  # 50% - Celery task running
    INDEXING = "indexing"  # 40-80%
    INDEXED = "indexed"  # 80%
    COMPLETE = "complete"  # 100%
    ERROR = "error"

class UploadProgress(BaseModel):
    job_id: str
    filename: str
    stage: UploadStage
    progress: int  # 0-100
    message: str
    chunks: int = 0
    error: str | None = None
    document_id: str | None = None
    celery_task_id: str | None = None  # Celery task ID for status tracking

# In-memory upload progress tracking
_upload_jobs: dict[str, UploadProgress] = {}


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

    # Pipeline monitoring fields
    pipeline_stage: str | None = None
    pipeline_status: str | None = None
    pipeline_started_at: str | None = None
    pipeline_completed_at: str | None = None

    # Metadata extraction status fields
    indexed: bool | None = False
    metadata_extracted: bool | None = False
    metadata_extraction_status: str | None = "pending"  # pending, processing, completed, failed, user_edited
    metadata_extraction_error: str | None = None
    metadata_extraction_attempts: int | None = 0
    metadata_last_extracted_at: str | None = None
    metadata_edited_by_user: bool | None = False
    extraction_confidence: float | None = None

    # Additional metadata fields
    issuing_authority: str | None = None
    related_institutions: list[str] | None = None
    violation_types: list[str] | None = None
    penalty_amount: str | None = None
    keywords: list[str] | None = None


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


# ===== Batch Scan Progress Tracking =====

class BatchScanStage(str, Enum):
    """Batch scan operation stages."""
    SCANNING = "scanning"  # 0-10%
    CLASSIFYING = "classifying"  # 10-30%
    INDEXING = "indexing"  # 30-90%
    EXTRACTING_METADATA = "extracting_metadata"  # 30-90% (parallel with indexing)
    COMPLETE = "complete"  # 100%
    ERROR = "error"


class BatchScanProgress(BaseModel):
    """Batch scan operation progress."""
    model_config = {"validate_assignment": True}  # Allow mutable updates

    job_id: str
    stage: BatchScanStage
    progress: int  # 0-100
    message: str
    total_files: int = 0
    processed_files: int = 0
    indexed_files: int = 0
    failed_files: int = 0
    metadata_extracted: int = 0
    current_file: str | None = None
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class BatchScanStartResponse(BaseModel):
    """Response when starting a batch scan job."""
    job_id: str
    message: str


# In-memory batch scan progress tracking
_batch_scan_jobs: dict[str, BatchScanProgress] = {}


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

    # Get additional metadata fields from database
    store = _get_metadata_store()
    doc = store.db.get_document(metadata.doc_id)

    # Extract metadata status fields from database Document model
    metadata_extracted = doc.metadata_extracted if doc else False
    metadata_extraction_status = doc.metadata_extraction_status if doc else "pending"
    metadata_extraction_error = doc.metadata_extraction_error if doc else None
    metadata_extraction_attempts = doc.metadata_extraction_attempts if doc else 0
    metadata_last_extracted_at = doc.metadata_last_extracted_at.isoformat() if doc and doc.metadata_last_extracted_at else None
    metadata_edited_by_user = doc.metadata_edited_by_user if doc else False
    extraction_confidence = doc.extraction_confidence if doc else None

    # Extract additional metadata fields
    issuing_authority = doc.issuing_authority if doc else metadata.issuing_authority if hasattr(metadata, 'issuing_authority') else None
    related_institutions = doc.related_institutions if doc else metadata.related_institutions if hasattr(metadata, 'related_institutions') else None
    violation_types = doc.violation_types if doc else metadata.violation_types if hasattr(metadata, 'violation_types') else None
    penalty_amount = doc.penalty_amount if doc else metadata.penalty_amount if hasattr(metadata, 'penalty_amount') else None
    keywords = doc.keywords if doc else metadata.keywords if hasattr(metadata, 'keywords') else None

    # Extract pipeline monitoring fields from database Document model
    pipeline_stage = doc.pipeline_stage if doc else None
    pipeline_status = doc.pipeline_status if doc else None

    # Convert pipeline datetime fields to ISO strings
    pipeline_started_at = None
    if doc and doc.pipeline_started_at:
        if isinstance(doc.pipeline_started_at, str):
            pipeline_started_at = doc.pipeline_started_at
        else:
            pipeline_started_at = doc.pipeline_started_at.isoformat()

    pipeline_completed_at = None
    if doc and doc.pipeline_completed_at:
        if isinstance(doc.pipeline_completed_at, str):
            pipeline_completed_at = doc.pipeline_completed_at
        else:
            pipeline_completed_at = doc.pipeline_completed_at.isoformat()

    return DocumentResponse(
        id=metadata.doc_id,
        name=metadata.filename,
        file_path=str(file_path) if file_path else "",
        size_bytes=size_bytes,
        status=status,
        chunk_count=metadata.chunk_count,
        version=version,
        created_at=metadata.created_at if hasattr(metadata, 'created_at') else datetime.now(timezone.utc).isoformat(),
        updated_at=metadata.updated_at if hasattr(metadata, 'updated_at') else datetime.now(timezone.utc).isoformat(),
        description=metadata.description,
        document_type=metadata.document_type,
        # Pipeline monitoring fields
        pipeline_stage=pipeline_stage,
        pipeline_status=pipeline_status,
        pipeline_started_at=pipeline_started_at,
        pipeline_completed_at=pipeline_completed_at,
        # Metadata extraction status fields
        indexed=metadata.indexed,
        metadata_extracted=metadata_extracted,
        metadata_extraction_status=metadata_extraction_status,
        metadata_extraction_error=metadata_extraction_error,
        metadata_extraction_attempts=metadata_extraction_attempts,
        metadata_last_extracted_at=metadata_last_extracted_at,
        metadata_edited_by_user=metadata_edited_by_user,
        extraction_confidence=extraction_confidence,
        # Additional metadata fields
        issuing_authority=issuing_authority,
        related_institutions=related_institutions,
        violation_types=violation_types,
        penalty_amount=penalty_amount,
        keywords=keywords,
    )


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    """Upload a single document (legacy endpoint, kept for backward compatibility)."""
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

    now = datetime.now(timezone.utc).isoformat()
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
        created_at=now,
        updated_at=now,
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


class UploadBatchResponse(BaseModel):
    """Batch upload response."""

    total_files: int
    successful: int
    failed: int
    documents: list[DocumentResponse]
    errors: list[dict[str, str]]


@router.post("/upload-batch")
async def upload_documents_batch(
    files: list[UploadFile] = File(...),
    auto_index: bool = True,
    extract_metadata: bool = True,
) -> UploadBatchResponse:
    """
    Upload multiple documents in a single request.

    Args:
        files: List of files to upload
        auto_index: If True, automatically index documents after upload (default: True)
        extract_metadata: If True, extract LLM metadata during indexing (default: True, requires auto_index=True)
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    successful = []
    errors = []

    for file in files:
        try:
            if not file.filename:
                errors.append({"filename": "unknown", "error": "No filename provided"})
                continue

            # Only support TXT files
            if not file.filename.endswith(".txt"):
                errors.append({
                    "filename": file.filename,
                    "error": "Only .txt files are supported",
                })
                continue

            # Generate document ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"

            # Save file to disk
            file_path = DOCUMENTS_PATH / file.filename
            content = await file.read()

            # Handle duplicate filenames
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = file_path.stem
                suffix = file_path.suffix
                file_path = DOCUMENTS_PATH / f"{stem}_{timestamp}{suffix}"

            with open(file_path, "wb") as f:
                f.write(content)

            # Create metadata
            from finagent.document_processing.metadata_store import DocumentMetadata

            now = datetime.now(timezone.utc).isoformat()
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
                created_at=now,
                updated_at=now,
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

            # Auto-index if requested
            if auto_index:
                try:
                    logger.info(f"Auto-indexing document {doc_id}: {file.filename}")
                    loader = DocumentLoader()
                    # Pass just the filename - loader will prepend base_path
                    document = loader.load_txt(file_path.name)

                    indexer = DocumentIndexer(extract_metadata=extract_metadata)
                    num_chunks = await indexer.index_document(document)

                    # Update metadata
                    store.update_metadata(
                        doc_id,
                        {
                            "indexed": True,
                            "chunk_count": num_chunks,
                        },
                    )
                    metadata.indexed = True
                    metadata.chunk_count = num_chunks
                    logger.info(f"Auto-indexed {doc_id} with {num_chunks} chunks")
                except Exception as e:
                    logger.error(f"Failed to auto-index {doc_id}: {e}")
                    # Don't fail the upload if indexing fails

            successful.append(_metadata_to_response(metadata, str(file_path)))

        except Exception as e:
            errors.append({
                "filename": file.filename if file.filename else "unknown",
                "error": str(e),
            })

    # Auto-rebuild wiki if documents were successfully uploaded
    if len(successful) > 0 and auto_index:
        try:
            logger.info(f"Auto-rebuilding wiki after uploading {len(successful)} documents")
            from finagent.wiki.generator import WikiGenerator
            wiki_gen = WikiGenerator()
            wiki_result = wiki_gen.generate_wiki(
                clear_existing=False,
                include_relationships=True,
                relationship_threshold=0.3,
            )
            logger.info(f"Wiki rebuild complete: {wiki_result.get('total_duration_seconds', 0):.2f}s")
        except Exception as e:
            logger.error(f"Failed to auto-rebuild wiki: {e}")
            # Don't fail the upload if wiki rebuild fails

    return UploadBatchResponse(
        total_files=len(files),
        successful=len(successful),
        failed=len(errors),
        documents=successful,
        errors=errors,
    )


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


# =============================================================================
# Directory Scanning and Auto-Discovery APIs
# =============================================================================


class DirectoryInfo(BaseModel):
    """Information about a subdirectory."""
    name: str
    path: str
    file_count: int
    total_size_bytes: int
    subdirectories: list["DirectoryInfo"] = []


class ScanRequest(BaseModel):
    """Request to scan directory for new documents."""
    extract_metadata: bool = False
    index_new: bool = True
    auto_classify: bool = True  # Auto-classify document type based on path/content
    use_llm_classification: bool = False  # Use LLM for classification (slower but more accurate)


class ClassifiedFile(BaseModel):
    """Information about a classified file."""
    path: str
    filename: str
    document_type: str  # category name
    document_type_zh: str  # Chinese name
    confidence: float
    reasoning: str


class ScanResult(BaseModel):
    """Result of directory scan."""
    total_files_found: int
    new_files: int
    existing_files: int
    indexed_files: int
    failed_files: int
    directories_scanned: int
    new_file_list: list[str]
    classified_files: list[ClassifiedFile] = []  # Files with classification info
    directory_structure: list[DirectoryInfo]
    message: str


class DirectoryStructureResponse(BaseModel):
    """Response containing directory structure."""
    base_path: str
    directories: list[DirectoryInfo]
    total_files: int
    total_size_bytes: int


def _scan_directory_recursive(
    base_path: Path,
    current_path: Path,
    pattern: str = "*.txt"
) -> tuple[list[Path], DirectoryInfo]:
    """
    Recursively scan directory and return files and structure info.

    Args:
        base_path: The root documents directory
        current_path: Current directory being scanned
        pattern: File pattern to match (default: *.txt)

    Returns:
        Tuple of (list of file paths, DirectoryInfo for current directory)
    """
    files: list[Path] = []
    subdirs: list[DirectoryInfo] = []
    total_size = 0

    # Get direct files in this directory
    for file_path in current_path.glob(pattern):
        if file_path.is_file():
            files.append(file_path)
            total_size += file_path.stat().st_size

    # Recursively scan subdirectories
    for subdir in sorted(current_path.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith('.'):
            sub_files, sub_info = _scan_directory_recursive(base_path, subdir, pattern)
            files.extend(sub_files)
            subdirs.append(sub_info)
            total_size += sub_info.total_size_bytes

    # Create info for current directory
    relative_path = str(current_path.relative_to(base_path)) if current_path != base_path else ""
    dir_info = DirectoryInfo(
        name=current_path.name if current_path != base_path else "root",
        path=relative_path,
        file_count=len([f for f in current_path.glob(pattern) if f.is_file()]),
        total_size_bytes=total_size,
        subdirectories=subdirs
    )

    return files, dir_info


@router.get("/directory-structure")
async def get_directory_structure() -> DirectoryStructureResponse:
    """
    Get the directory structure of the documents folder.

    Returns a tree structure showing all subdirectories and file counts.
    Users can organize documents in subdirectories for categorization.
    """
    docs_dir = DOCUMENTS_PATH
    if not docs_dir.exists():
        return DirectoryStructureResponse(
            base_path=str(docs_dir),
            directories=[],
            total_files=0,
            total_size_bytes=0
        )

    all_files, root_info = _scan_directory_recursive(docs_dir, docs_dir)

    return DirectoryStructureResponse(
        base_path=str(docs_dir),
        directories=root_info.subdirectories,
        total_files=len(all_files),
        total_size_bytes=root_info.total_size_bytes
    )


@router.post("/scan")
async def scan_directory(
    request: ScanRequest | None = None,
    background_tasks: BackgroundTasks = None
) -> ScanResult:
    """
    Scan documents directory for new files and optionally index them.

    This endpoint:
    1. Scans the documents directory recursively
    2. Identifies files not yet in the database
    3. Auto-classifies documents by type (法規, 裁罰資料, 知識)
    4. Optionally indexes new files to the knowledge base

    Args:
        request: Scan options (extract_metadata, index_new, auto_classify, use_llm_classification)

    Returns:
        Scan results including new files found, classifications, and directory structure
    """
    from finagent.document_processing.loader import DocumentLoader
    from finagent.document_processing.indexer import DocumentIndexer
    from finagent.models.document_types import (
        classify_document_by_path,
        classify_document_with_llm,
        ALLOWED_DOCUMENT_TYPES,
        DocumentCategory,
    )

    if request is None:
        request = ScanRequest()

    docs_dir = DOCUMENTS_PATH
    store = _get_metadata_store()

    if not docs_dir.exists():
        return ScanResult(
            total_files_found=0,
            new_files=0,
            existing_files=0,
            indexed_files=0,
            failed_files=0,
            directories_scanned=0,
            new_file_list=[],
            classified_files=[],
            directory_structure=[],
            message=f"Documents directory not found: {docs_dir}"
        )

    # Scan directory
    all_files, root_info = _scan_directory_recursive(docs_dir, docs_dir)

    # Check which files are already in database
    existing_docs = {doc.file_path: doc for doc in store.db.get_all_documents()}
    existing_paths = set(existing_docs.keys())

    new_files = []
    existing_count = 0

    for file_path in all_files:
        str_path = str(file_path)
        if str_path in existing_paths:
            existing_count += 1
        else:
            new_files.append(str_path)

    # Count directories
    def count_dirs(info: DirectoryInfo) -> int:
        return 1 + sum(count_dirs(sub) for sub in info.subdirectories)

    dirs_scanned = count_dirs(root_info) if root_info.subdirectories else 1

    # Classify new files
    classified_files: list[ClassifiedFile] = []
    file_classifications: dict[str, DocumentCategory] = {}

    if request.auto_classify and new_files:
        loader = DocumentLoader()

        for file_path in new_files:
            try:
                abs_path = str(Path(file_path).resolve())
                filename = Path(file_path).name

                if request.use_llm_classification:
                    # LLM-based classification (more accurate but slower)
                    document = loader.load_txt(abs_path)
                    result = await classify_document_with_llm(
                        content=document.content,
                        filename=file_path,
                    )
                    category = result.category
                    confidence = result.confidence
                    reasoning = result.reasoning
                else:
                    # Rule-based classification (fast)
                    category = classify_document_by_path(file_path)
                    confidence = 0.9 if category != DocumentCategory.OTHER else 0.5
                    reasoning = f"根據路徑分類: {Path(file_path).parent.name}/{filename}"

                doc_type = ALLOWED_DOCUMENT_TYPES.get(category, ALLOWED_DOCUMENT_TYPES[DocumentCategory.OTHER])
                classified_files.append(ClassifiedFile(
                    path=file_path,
                    filename=filename,
                    document_type=category.value,
                    document_type_zh=doc_type.name_zh,
                    confidence=confidence,
                    reasoning=reasoning,
                ))
                file_classifications[file_path] = category

            except Exception as e:
                logger.warning(f"Failed to classify {file_path}: {e}")
                # Default to OTHER if classification fails
                doc_type = ALLOWED_DOCUMENT_TYPES[DocumentCategory.OTHER]
                classified_files.append(ClassifiedFile(
                    path=file_path,
                    filename=Path(file_path).name,
                    document_type=DocumentCategory.OTHER.value,
                    document_type_zh=doc_type.name_zh,
                    confidence=0.0,
                    reasoning=f"分類失敗: {str(e)[:50]}",
                ))
                file_classifications[file_path] = DocumentCategory.OTHER

    # Index new files if requested
    indexed_count = 0
    failed_count = 0

    if request.index_new and new_files:
        loader = DocumentLoader()
        indexer = DocumentIndexer(extract_metadata=request.extract_metadata)

        for file_path in new_files:
            try:
                # Convert to absolute path since file_path is like "data/documents/..."
                # and DocumentLoader.load_txt expects either absolute or relative to base_path
                abs_path = str(Path(file_path).resolve())

                # Load document using load_txt method with absolute path
                document = loader.load_txt(abs_path)
                if document:
                    # Add classification to document metadata
                    if file_path in file_classifications:
                        category = file_classifications[file_path]
                        doc_type = ALLOWED_DOCUMENT_TYPES.get(category, ALLOWED_DOCUMENT_TYPES[DocumentCategory.OTHER])
                        document.metadata["document_type"] = doc_type.name_zh
                        document.metadata["document_category"] = category.value

                    # Index document (async method)
                    num_chunks = await indexer.index_document(document)
                    if num_chunks > 0:
                        indexed_count += 1
                        logger.info(f"Indexed {file_path} with {num_chunks} chunks")
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                failed_count += 1

    return ScanResult(
        total_files_found=len(all_files),
        new_files=len(new_files),
        existing_files=existing_count,
        indexed_files=indexed_count,
        classified_files=classified_files,
        failed_files=failed_count,
        directories_scanned=dirs_scanned,
        new_file_list=new_files,
        directory_structure=root_info.subdirectories,
        message=f"掃描完成：發現 {len(new_files)} 個新檔案" if new_files else "目錄已同步，無新檔案"
    )


@router.post("/scan-preview")
async def scan_preview() -> ScanResult:
    """
    Preview scan results without indexing.

    Performs a dry-run scan to show what new files would be indexed.
    """
    return await scan_directory(ScanRequest(index_new=False, extract_metadata=False))


# ===== Batch Scan with Progress Tracking =====

@router.post("/scan-with-progress", response_model=BatchScanStartResponse)
async def scan_with_progress(
    request: ScanRequest = None,
) -> BatchScanStartResponse:
    """
    Start a batch scan operation with progress tracking.

    This endpoint:
    1. Starts a background task to scan and index documents
    2. Returns a job_id immediately
    3. Frontend can poll /scan-progress/{job_id} to get real-time updates

    Args:
        request: Scan options (extract_metadata, index_new, auto_classify)

    Returns:
        BatchScanStartResponse with job_id
    """
    import asyncio

    if request is None:
        request = ScanRequest()

    # Generate job ID
    job_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    # Initialize progress tracking
    _batch_scan_jobs[job_id] = BatchScanProgress(
        job_id=job_id,
        stage=BatchScanStage.SCANNING,
        progress=0,
        message="開始掃描目錄...",
        started_at=started_at,
    )

    # Start background task using asyncio.create_task for true async execution
    # This ensures the response is returned immediately without waiting
    asyncio.create_task(_process_batch_scan_with_progress(job_id, request))

    return BatchScanStartResponse(
        job_id=job_id,
        message="批次掃描已啟動，請使用 job_id 查詢進度"
    )


@router.get("/scan-progress/{job_id}", response_model=BatchScanProgress)
async def get_scan_progress(job_id: str) -> BatchScanProgress:
    """
    Get the current progress of a batch scan job.

    Frontend polls this endpoint every 500ms-1s to get updates.
    """
    if job_id not in _batch_scan_jobs:
        raise HTTPException(status_code=404, detail="Scan job not found")

    return _batch_scan_jobs[job_id]


@router.delete("/scan-progress/{job_id}")
async def clear_scan_progress(job_id: str):
    """Clear a completed scan job from memory."""
    if job_id in _batch_scan_jobs:
        del _batch_scan_jobs[job_id]
        return {"message": "Scan job cleared"}
    raise HTTPException(status_code=404, detail="Scan job not found")


async def _process_batch_scan_with_progress(
    job_id: str,
    request: ScanRequest,
) -> None:
    """
    Background task to process batch scan with progress updates.

    Updates _batch_scan_jobs[job_id] as it progresses.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[BatchScan] Starting background task for job {job_id}")

    try:
        from finagent.document_processing.loader import DocumentLoader
        from finagent.document_processing.indexer import DocumentIndexer
        from finagent.models.document_types import (
            classify_document_by_path,
            classify_document_with_llm,
            ALLOWED_DOCUMENT_TYPES,
            DocumentCategory,
        )
        logger.info(f"[BatchScan] Imports successful")
    except Exception as import_error:
        logger.error(f"[BatchScan] Import error: {import_error}")
        if job_id in _batch_scan_jobs:
            _batch_scan_jobs[job_id].stage = BatchScanStage.ERROR
            _batch_scan_jobs[job_id].error = f"Import error: {import_error}"
        return

    progress = _batch_scan_jobs[job_id]
    logger.info(f"[BatchScan] Got progress object, starting processing")

    try:
        # Stage 1: Scanning (0-10%)
        progress.stage = BatchScanStage.SCANNING
        progress.progress = 5
        progress.message = "掃描目錄中..."

        docs_dir = DOCUMENTS_PATH
        store = _get_metadata_store()

        if not docs_dir.exists():
            progress.stage = BatchScanStage.ERROR
            progress.error = f"Documents directory not found: {docs_dir}"
            progress.message = "錯誤：文件目錄不存在"
            return

        # Scan directory
        all_files, root_info = _scan_directory_recursive(docs_dir, docs_dir)
        progress.total_files = len(all_files)
        progress.progress = 10
        progress.message = f"發現 {len(all_files)} 個檔案"

        # Check which files are already in database
        existing_count = 0
        new_files = []
        for file_path in all_files:
            str_path = str(file_path)
            if store.get_metadata(str_path.replace("/", "_").replace(".", "_")):
                existing_count += 1
            else:
                new_files.append(str_path)

        progress.total_files = len(new_files)
        progress.progress = 15
        progress.message = f"發現 {len(new_files)} 個新檔案需要處理"

        if not new_files:
            progress.stage = BatchScanStage.COMPLETE
            progress.progress = 100
            progress.message = "目錄已同步，無新檔案"
            progress.completed_at = datetime.now(timezone.utc).isoformat()
            return

        # Stage 2: Classifying (10-30%)
        progress.stage = BatchScanStage.CLASSIFYING
        file_classifications: dict[str, DocumentCategory] = {}

        if request.auto_classify:
            loader = DocumentLoader()
            for i, file_path in enumerate(new_files):
                try:
                    progress.current_file = Path(file_path).name
                    progress.progress = 15 + int((i / len(new_files)) * 15)
                    progress.message = f"分類中: {progress.current_file}"

                    filename = Path(file_path).name

                    if request.use_llm_classification:
                        abs_path = str(Path(file_path).resolve())
                        document = loader.load_txt(abs_path)
                        result = await classify_document_with_llm(
                            content=document.content,
                            filename=file_path,
                        )
                        category = result.category
                    else:
                        category = classify_document_by_path(file_path)

                    file_classifications[file_path] = category

                except Exception as e:
                    logger.warning(f"Failed to classify {file_path}: {e}")
                    file_classifications[file_path] = DocumentCategory.OTHER

        progress.progress = 30
        progress.message = f"分類完成，準備索引 {len(new_files)} 個檔案"

        # Stage 3: Indexing (30-90%)
        if request.index_new:
            progress.stage = BatchScanStage.INDEXING
            loader = DocumentLoader()
            indexer = DocumentIndexer(extract_metadata=request.extract_metadata)

            for i, file_path in enumerate(new_files):
                try:
                    progress.current_file = Path(file_path).name
                    progress.processed_files = i
                    base_progress = 30 + int((i / len(new_files)) * 60)
                    progress.progress = min(base_progress, 89)

                    if request.extract_metadata:
                        progress.message = f"索引並提取 metadata: {progress.current_file} ({i+1}/{len(new_files)})"
                    else:
                        progress.message = f"索引中: {progress.current_file} ({i+1}/{len(new_files)})"

                    abs_path = str(Path(file_path).resolve())
                    document = loader.load_txt(abs_path)

                    if document:
                        # Add classification to document metadata
                        if file_path in file_classifications:
                            category = file_classifications[file_path]
                            doc_type = ALLOWED_DOCUMENT_TYPES.get(category, ALLOWED_DOCUMENT_TYPES[DocumentCategory.OTHER])
                            document.metadata["document_type"] = doc_type.name_zh
                            document.metadata["document_category"] = category.value

                        # Index document (async method)
                        num_chunks = await indexer.index_document(document)
                        if num_chunks > 0:
                            progress.indexed_files += 1
                            if request.extract_metadata:
                                progress.metadata_extracted += 1
                            logger.info(f"Indexed {file_path} with {num_chunks} chunks")

                except Exception as e:
                    logger.error(f"Failed to index {file_path}: {e}")
                    progress.failed_files += 1

            progress.processed_files = len(new_files)

        # Stage 4: Complete
        progress.stage = BatchScanStage.COMPLETE
        progress.progress = 100
        progress.current_file = None
        progress.completed_at = datetime.now(timezone.utc).isoformat()

        if request.extract_metadata:
            progress.message = f"完成：索引 {progress.indexed_files} 個檔案，提取 {progress.metadata_extracted} 個 metadata，{progress.failed_files} 個失敗"
        else:
            progress.message = f"完成：索引 {progress.indexed_files} 個檔案，{progress.failed_files} 個失敗"

    except Exception as e:
        logger.error(f"Batch scan failed: {e}")
        progress.stage = BatchScanStage.ERROR
        progress.error = str(e)
        progress.message = f"錯誤：{str(e)}"
        progress.completed_at = datetime.now(timezone.utc).isoformat()


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


class DeleteResponse(BaseModel):
    """Document deletion response."""

    status: str
    message: str
    chunks_deleted: int
    file_deleted: bool


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> DeleteResponse:
    """Delete a document, its index, and trigger wiki rebuild."""
    store = _get_metadata_store()
    metadata = store.get_metadata(document_id)

    if not metadata:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Get file path before deletion
    doc = store.db.get_document(document_id)
    file_path = Path(doc.file_path) if doc else None
    file_deleted = False

    # Delete from vector database (Chroma) and metadata store (SQLite)
    indexer = DocumentIndexer()
    chunks_deleted = indexer.delete_document(document_id)

    # Delete physical file
    if file_path and file_path.exists():
        try:
            file_path.unlink()
            file_deleted = True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")

    # Clean up version history
    if document_id in _document_versions:
        del _document_versions[document_id]

    return DeleteResponse(
        status="success",
        message=f"Document {document_id} deleted successfully",
        chunks_deleted=chunks_deleted,
        file_deleted=file_deleted,
    )


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
    # Pass just filename if path is relative, or full path if absolute
    document = loader.load_txt(file_path.name if not file_path.is_absolute() else str(file_path))

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

            # Pass just filename - loader will prepend base_path for relative paths
            file_path = Path(doc.file_path)
            document = loader.load_txt(file_path.name if not file_path.is_absolute() else str(file_path))
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


# ===== HTTP Polling-Based Upload Progress (Google Drive Style) =====

async def _process_upload_with_progress(
    job_id: str,
    filename: str,
    content: bytes,
    auto_index: bool,
    extract_metadata: bool,
    duplicate_action: str = "version",
    document_type: str = "penalty",
):
    """
    Process file upload and enqueue Celery task for async processing.
    This function handles file saving and initial metadata, then hands off to Celery.
    """
    from finagent.models.pipeline import DocumentPipeline, PipelineStage, PipelineStatus
    from finagent.tasks.document_processing import process_document_upload
    import json

    print(f"[UPLOAD] Background task started for job {job_id}, filename: {filename}", flush=True)

    pipeline = None
    doc_id = None

    try:
        # Generate doc_id early for pipeline tracking
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        print(f"[UPLOAD] Generated doc_id: {doc_id}", flush=True)

        # Initialize pipeline monitoring
        print(f"[UPLOAD] Initializing pipeline for {doc_id}", flush=True)
        pipeline = DocumentPipeline(
            doc_id=doc_id,
            filename=filename,
            auto_index=auto_index,
            extract_metadata=extract_metadata,
            update_wiki=False  # Wiki update happens in batch upload
        )
        print(f"[UPLOAD] Pipeline created successfully, current stage: {pipeline.current_stage}", flush=True)

        # Stage 1: Uploading (simulate - already uploaded in request)
        print(f"[UPLOAD] Setting initial upload progress", flush=True)
        _upload_jobs[job_id] = UploadProgress(
            job_id=job_id,
            filename=filename,
            stage=UploadStage.UPLOADING,
            progress=10,
            message="上傳文件中..."
        )
        pipeline.update_stage(PipelineStage.UPLOADED, PipelineStatus.IN_PROGRESS)
        await asyncio.sleep(0.1)  # Small delay for UI

        # Stage 2: File saved
        print(f"[UPLOAD] Stage 2: Saving file to disk", flush=True)
        file_path = DOCUMENTS_PATH / filename

        # Handle duplicate filenames based on action
        if file_path.exists():
            if duplicate_action == "skip":
                # Skip upload - file already exists
                error_msg = f"文件 {filename} 已存在，已跳過上傳"
                logger.info(error_msg)
                pipeline.update_stage(PipelineStage.UPLOADED, PipelineStatus.SKIPPED, error_message=error_msg)
                _upload_jobs[job_id].stage = UploadStage.ERROR
                _upload_jobs[job_id].error = error_msg
                return
            elif duplicate_action == "replace":
                # Treat as new file - add unique ID suffix to keep both
                stem = file_path.stem
                suffix = file_path.suffix

                # Generate short unique ID (8 chars from UUID)
                unique_id = str(uuid.uuid4())[:8]
                file_path = DOCUMENTS_PATH / f"{stem}_{unique_id}{suffix}"

                filename = file_path.name  # Update filename for pipeline
                logger.info(f"Duplicate filename detected, treating as new file: {filename}")
            elif duplicate_action == "version":
                # Create new version
                stem = file_path.stem
                suffix = file_path.suffix
                version = 1

                # Find next available version number
                while file_path.exists():
                    file_path = DOCUMENTS_PATH / f"{stem}_v{version}{suffix}"
                    version += 1

                filename = file_path.name  # Update filename for pipeline
                logger.info(f"Duplicate filename detected, renamed to: {filename}")

        with open(file_path, "wb") as f:
            f.write(content)

        print(f"[UPLOAD] File saved to {file_path}", flush=True)
        _upload_jobs[job_id].filename = filename  # Update filename in progress tracker
        _upload_jobs[job_id].stage = UploadStage.UPLOADED
        _upload_jobs[job_id].progress = 25
        _upload_jobs[job_id].message = "文件已儲存"

        pipeline.update_stage(
            PipelineStage.UPLOADED,
            PipelineStatus.SUCCESS,
            details={"file_size": len(content), "path": str(file_path)}
        )
        print(f"[UPLOAD] Pipeline updated to UPLOADED SUCCESS", flush=True)

        await asyncio.sleep(0.1)

        # Stage 3: Create and save initial metadata
        print(f"[UPLOAD] Stage 3: Creating and saving metadata", flush=True)
        from finagent.document_processing.metadata_store import DocumentMetadata

        pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.IN_PROGRESS)
        print(f"[UPLOAD] Pipeline updated to PARSING IN_PROGRESS", flush=True)

        now = datetime.now(timezone.utc).isoformat()
        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=filename,
            description=f"Uploaded file: {filename}",
            document_type=document_type,  # Use the user-specified document type
            keywords=[],
            date=None,
            issuing_authority=None,
            related_institutions=[],
            penalty_amount=None,
            violation_types=[],
            custom_fields={},
            indexed=False,
            chunk_count=0,
            created_at=now,
            updated_at=now,
        )

        store = _get_metadata_store()

        # Save initial metadata with pipeline data
        print(f"[UPLOAD] Saving initial metadata for {doc_id}", flush=True)
        store.add_metadata(metadata, str(file_path))

        store.update_metadata(doc_id, {
            "pipeline_stage": pipeline.current_stage.value,
            "pipeline_status": pipeline.overall_status.value,
            "pipeline_data": json.dumps([s.model_dump(mode='json') for s in pipeline.stages], ensure_ascii=False),
            "pipeline_started_at": pipeline.started_at.isoformat()
        })

        _upload_jobs[job_id].stage = UploadStage.METADATA_SAVED
        _upload_jobs[job_id].progress = 40
        _upload_jobs[job_id].message = "元數據已儲存"
        _upload_jobs[job_id].document_id = doc_id

        # Stage 4: Enqueue Celery task for processing
        print(f"[UPLOAD] Enqueueing Celery task for {doc_id}", flush=True)
        _upload_jobs[job_id].progress = 50
        _upload_jobs[job_id].message = "開始處理文件..."

        # Enqueue Celery task - this returns immediately
        relative_path = str(file_path.relative_to(DOCUMENTS_PATH.parent))
        task_result = process_document_upload.delay(
            doc_id=doc_id,
            filename=filename,
            file_path=relative_path,
            auto_index=auto_index,
            extract_metadata=extract_metadata
        )

        # Store Celery task ID for status tracking
        _upload_jobs[job_id].celery_task_id = task_result.id
        _upload_jobs[job_id].stage = UploadStage.PROCESSING
        _upload_jobs[job_id].progress = 60
        _upload_jobs[job_id].message = f"處理中 (任務ID: {task_result.id[:8]}...)"

        print(f"[UPLOAD] Celery task enqueued: {task_result.id}", flush=True)
        logger.info(f"Upload initiated for {doc_id} - Celery task: {task_result.id}")

        # Update upload job to indicate processing is in Celery
        _upload_jobs[job_id].stage = UploadStage.COMPLETE
        _upload_jobs[job_id].progress = 100
        _upload_jobs[job_id].message = "上傳完成，處理中..."

    except Exception as e:
        logger.error(f"Upload job {job_id} failed: {e}", exc_info=True)

        # Update pipeline with failure
        if pipeline and doc_id:
            pipeline.update_stage(
                pipeline.current_stage,
                PipelineStatus.FAILED,
                error_message=str(e)
            )
            try:
                store = _get_metadata_store()
                store.update_metadata(doc_id, {
                    "pipeline_stage": pipeline.current_stage.value,
                    "pipeline_status": PipelineStatus.FAILED.value,
                    "pipeline_data": json.dumps([s.model_dump(mode='json') for s in pipeline.stages], ensure_ascii=False)
                })
            except Exception as save_error:
                logger.error(f"Failed to save error pipeline state: {save_error}")

        _upload_jobs[job_id] = UploadProgress(
            job_id=job_id,
            filename=filename,
            stage=UploadStage.ERROR,
            progress=0,
            message="上傳失敗",
            error=str(e)
        )


class UploadWithProgressResponse(BaseModel):
    """Response for upload with progress tracking."""
    job_id: str
    message: str


class DuplicateDetectedResponse(BaseModel):
    """Response when duplicate file is detected."""
    status: str = "duplicate_detected"
    message: str
    duplicate_info: dict
    options: dict


@router.post("/upload-with-progress")
async def upload_file_with_progress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_index: bool = Form(True),
    extract_metadata: bool = Form(True),
    duplicate_action: str = Form("ask"),  # "ask", "version", "replace", "skip"
    document_type: str = Form("penalty"),  # Document type classification
):
    """
    Upload a single file and return a job ID for progress tracking.
    Frontend can poll /upload-progress/{job_id} to get real-time updates.

    This is similar to how Google Drive handles file uploads.

    Args:
        file: The file to upload
        auto_index: Whether to automatically index the document
        extract_metadata: Whether to extract metadata using LLM
        duplicate_action: How to handle duplicates
            - "ask": Check for duplicates and ask user (default)
            - "version": Automatically create new version
            - "replace": Replace existing file
            - "skip": Skip upload if file exists
        document_type: Document type classification (required)
            - "penalty": 裁罰書 - Regulatory penalty documents
            - "legal_provision": 法條 - Legal provisions
            - "court_judgment": 判決書 - Court judgments
            - "regulatory_notice": 監管公告 - Regulatory announcements
            - "knowledge_base": 知識文件 - Knowledge base documents
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    # Validate document type
    if not is_document_type_allowed(document_type):
        allowed_types = ", ".join([dt.name_zh for dt in get_allowed_document_types()])
        raise HTTPException(
            status_code=400,
            detail=f"文件類型 '{document_type}' 不允許上傳。允許的類型：{allowed_types}"
        )

    # Read file content
    content = await file.read()

    # Check for duplicate if action is "ask"
    if duplicate_action == "ask":
        file_path = DOCUMENTS_PATH / file.filename
        if file_path.exists():
            # File exists - return duplicate info
            file_size = file_path.stat().st_size
            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()

            return DuplicateDetectedResponse(
                status="duplicate_detected",
                message=f"文件 {file.filename} 已存在",
                duplicate_info={
                    "filename": file.filename,
                    "size": file_size,
                    "modified": modified_time,
                    "path": str(file_path)
                },
                options={
                    "version": "建立新版本 (推薦)",
                    "replace": "覆蓋現有文件",
                    "skip": "取消上傳"
                }
            )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Start background processing
    print(f"[ENDPOINT] Adding background task for job {job_id}, file: {file.filename}, type: {document_type}", flush=True)
    background_tasks.add_task(
        _process_upload_with_progress,
        job_id=job_id,
        filename=file.filename,
        content=content,
        auto_index=auto_index,
        extract_metadata=extract_metadata,
        duplicate_action=duplicate_action,
        document_type=document_type,
    )
    print(f"[ENDPOINT] Background task added successfully", flush=True)

    return UploadWithProgressResponse(
        job_id=job_id,
        message=f"Upload started for {file.filename}"
    )


@router.get("/upload-progress/{job_id}", response_model=UploadProgress)
async def get_upload_progress(job_id: str):
    """
    Get the current progress of an upload job.
    Frontend polls this endpoint every 500ms to get updates.

    This is the HTTP polling approach used by Google Drive and similar services.
    """
    if job_id not in _upload_jobs:
        raise HTTPException(status_code=404, detail="Upload job not found")

    return _upload_jobs[job_id]


@router.delete("/upload-progress/{job_id}")
async def clear_upload_progress(job_id: str):
    """Clear a completed upload job from memory."""
    if job_id in _upload_jobs:
        del _upload_jobs[job_id]
        return {"message": "Upload job cleared"}
    raise HTTPException(status_code=404, detail="Upload job not found")


# ===== Celery Task Status Monitoring =====

class CeleryTaskStatus(BaseModel):
    """Celery task status response."""
    task_id: str
    state: str  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    status: str | None = None  # Custom status message
    progress: int = 0  # 0-100
    result: dict | None = None  # Task result when complete
    error: str | None = None  # Error message if failed


@router.get("/tasks/{task_id}/status", response_model=CeleryTaskStatus)
async def get_celery_task_status(task_id: str):
    """
    Get the current status of a Celery task.
    Frontend can poll this to track document processing progress.
    """
    from finagent.celery_app import celery_app
    from celery.result import AsyncResult

    task_result = AsyncResult(task_id, app=celery_app)

    # Build response based on task state
    response = CeleryTaskStatus(
        task_id=task_id,
        state=task_result.state,
        status=None,
        progress=0,
        result=None,
        error=None
    )

    if task_result.state == 'PENDING':
        # Task is waiting in queue
        response.status = '等待處理...'
        response.progress = 0

    elif task_result.state == 'STARTED':
        # Task has started
        response.status = '處理中...'
        response.progress = 10

    elif task_result.state == 'PROGRESS':
        # Task is running with custom progress
        info = task_result.info or {}
        response.status = info.get('status', '處理中...')
        response.progress = info.get('progress', 50)

    elif task_result.state == 'SUCCESS':
        # Task completed successfully
        response.status = '處理完成'
        response.progress = 100
        response.result = task_result.result

    elif task_result.state == 'FAILURE':
        # Task failed
        response.status = '處理失敗'
        response.progress = 0
        response.error = str(task_result.info) if task_result.info else 'Unknown error'

    elif task_result.state == 'RETRY':
        # Task is being retried
        response.status = '重試中...'
        response.progress = 0

    return response


# ===== Metadata Status Monitoring =====

class FailedDocument(BaseModel):
    """Failed document details."""
    doc_id: str
    filename: str
    error: str | None
    attempts: int
    last_attempted_at: str | None


class MetadataStatusResponse(BaseModel):
    """Metadata extraction status statistics."""
    total_documents: int
    indexed: int
    metadata_extracted: int
    by_status: dict[str, int]
    failed_documents: list[FailedDocument]
    average_confidence: float | None
    low_confidence_count: int


@router.get("/metadata/status")
async def get_metadata_status() -> MetadataStatusResponse:
    """
    Get metadata extraction status statistics across all documents.

    Returns:
        - Total document counts
        - Breakdown by extraction status (pending/processing/completed/failed/user_edited)
        - List of failed documents with error details
        - Average confidence score
        - Count of low-confidence extractions (<0.5)
    """
    store = _get_metadata_store()
    all_metadata = store.get_all_metadata()

    # Initialize counters
    total_documents = len(all_metadata)
    indexed_count = 0
    metadata_extracted_count = 0
    status_counts = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
        "user_edited": 0,
    }
    failed_docs = []
    confidence_scores = []
    low_confidence_count = 0

    # Process each document
    for metadata in all_metadata:
        # Get full document from database
        doc = store.db.get_document(metadata.doc_id)
        if not doc:
            continue

        # Count indexed
        if doc.indexed:
            indexed_count += 1

        # Count metadata extracted
        if doc.metadata_extracted:
            metadata_extracted_count += 1

        # Count by status
        status = doc.metadata_extraction_status or "pending"
        if status in status_counts:
            status_counts[status] += 1

        # Collect failed documents
        if status == "failed":
            failed_docs.append(FailedDocument(
                doc_id=doc.doc_id,
                filename=doc.filename,
                error=doc.metadata_extraction_error,
                attempts=doc.metadata_extraction_attempts,
                last_attempted_at=doc.metadata_last_extracted_at.isoformat() if doc.metadata_last_extracted_at else None,
            ))

        # Collect confidence scores
        if doc.extraction_confidence is not None:
            confidence_scores.append(doc.extraction_confidence)
            if doc.extraction_confidence < 0.5:
                low_confidence_count += 1

    # Calculate average confidence
    average_confidence = None
    if confidence_scores:
        average_confidence = sum(confidence_scores) / len(confidence_scores)

    return MetadataStatusResponse(
        total_documents=total_documents,
        indexed=indexed_count,
        metadata_extracted=metadata_extracted_count,
        by_status=status_counts,
        failed_documents=failed_docs,
        average_confidence=average_confidence,
        low_confidence_count=low_confidence_count,
    )


# ===== Metadata Extraction Operations =====

class MetadataExtractRequest(BaseModel):
    """Request to extract metadata for a document."""
    force: bool = False  # Force re-extraction even if already extracted


class MetadataExtractResponse(BaseModel):
    """Response from metadata extraction."""
    doc_id: str
    filename: str
    status: str  # success, failed, already_extracted
    message: str
    extraction_confidence: float | None = None
    metadata_extracted: bool = False
    error: str | None = None


@router.post("/{document_id}/metadata/extract")
async def extract_document_metadata(
    document_id: str,
    request: MetadataExtractRequest | None = None,
) -> MetadataExtractResponse:
    """
    Trigger metadata extraction for a single document.

    This endpoint:
    1. Loads the document content
    2. Calls LLM to extract metadata (document_type, issuing_authority, etc.)
    3. Saves extracted metadata to database
    4. Updates extraction status and confidence score

    Args:
        document_id: Document ID to extract metadata for
        request.force: If True, re-extract even if already extracted (default: False)

    Returns:
        Extraction result with status and confidence score
    """
    force = request.force if request else False

    store = _get_metadata_store()
    doc = store.db.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Check if already extracted (unless force=True)
    if doc.metadata_extracted and not force:
        return MetadataExtractResponse(
            doc_id=document_id,
            filename=doc.filename,
            status="already_extracted",
            message="Metadata already extracted. Use force=true to re-extract.",
            extraction_confidence=doc.extraction_confidence,
            metadata_extracted=True,
        )

    # Verify file exists
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Document file not found: {file_path}")

    try:
        # Update status to processing
        doc_copy = doc.model_copy()
        doc_copy.metadata_extraction_status = "processing"
        doc_copy.metadata_extraction_attempts = doc.metadata_extraction_attempts + 1
        store.db.add_document(doc_copy)

        # Load document content
        loader = DocumentLoader()
        document = loader.load_txt(file_path.name if not file_path.is_absolute() else str(file_path))

        # Extract metadata using LLM
        from finagent.document_processing.metadata_extractor import MetadataExtractor

        extractor = MetadataExtractor()
        extracted_metadata = await extractor.extract_metadata(document.content, document.metadata.filename)

        # Update document with extracted metadata
        now = datetime.now(timezone.utc)
        doc_updated = doc.model_copy()
        doc_updated.document_type = extracted_metadata.get("document_type")
        doc_updated.issuing_authority = extracted_metadata.get("issuing_authority")
        doc_updated.related_institutions = extracted_metadata.get("related_institutions", [])
        doc_updated.violation_types = extracted_metadata.get("violation_types", [])
        doc_updated.penalty_amount = extracted_metadata.get("penalty_amount")
        doc_updated.keywords = extracted_metadata.get("keywords", [])
        doc_updated.metadata_extracted = True
        doc_updated.metadata_extraction_status = "completed"
        doc_updated.metadata_last_extracted_at = now
        doc_updated.extraction_confidence = extracted_metadata.get("confidence", 0.8)
        doc_updated.metadata_extraction_error = None

        store.db.add_document(doc_updated)

        return MetadataExtractResponse(
            doc_id=document_id,
            filename=doc.filename,
            status="success",
            message="Metadata extracted successfully",
            extraction_confidence=extracted_metadata.get("confidence", 0.8),
            metadata_extracted=True,
        )

    except Exception as e:
        logger.error(f"Failed to extract metadata for {document_id}: {e}")

        # Update status to failed
        doc_failed = doc.model_copy()
        doc_failed.metadata_extraction_status = "failed"
        doc_failed.metadata_extraction_error = str(e)
        doc_failed.metadata_last_extracted_at = datetime.now(timezone.utc)
        store.db.add_document(doc_failed)

        return MetadataExtractResponse(
            doc_id=document_id,
            filename=doc.filename,
            status="failed",
            message=f"Metadata extraction failed: {str(e)}",
            error=str(e),
        )


# ===== Metadata Editing =====

class MetadataUpdateRequest(BaseModel):
    """Request to update document metadata."""
    description: str | None = None
    document_type: str | None = None
    issuing_authority: str | None = None
    related_institutions: list[str] | None = None
    violation_types: list[str] | None = None
    penalty_amount: str | None = None
    keywords: list[str] | None = None


class MetadataUpdateResponse(BaseModel):
    """Response from metadata update."""
    doc_id: str
    filename: str
    message: str
    updated_fields: list[str]


@router.patch("/{document_id}/metadata")
async def update_document_metadata(
    document_id: str,
    request: MetadataUpdateRequest,
) -> MetadataUpdateResponse:
    """
    Update document metadata manually.

    This endpoint allows users to edit metadata fields that were either:
    - Extracted by LLM (to correct errors)
    - Not extracted (to add missing information)

    When metadata is updated via this endpoint, the document is marked as
    'user_edited' to indicate manual intervention.

    Args:
        document_id: Document ID to update
        request: Metadata fields to update (only non-None fields are updated)

    Returns:
        Update result with list of updated fields
    """
    store = _get_metadata_store()
    doc = store.db.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Build update dictionary with only non-None fields
    update_data = {}
    updated_fields = []

    if request.description is not None:
        update_data["description"] = request.description
        updated_fields.append("description")

    if request.document_type is not None:
        update_data["document_type"] = request.document_type
        updated_fields.append("document_type")

    if request.issuing_authority is not None:
        update_data["issuing_authority"] = request.issuing_authority
        updated_fields.append("issuing_authority")

    if request.related_institutions is not None:
        update_data["related_institutions"] = request.related_institutions
        updated_fields.append("related_institutions")

    if request.violation_types is not None:
        update_data["violation_types"] = request.violation_types
        updated_fields.append("violation_types")

    if request.penalty_amount is not None:
        update_data["penalty_amount"] = request.penalty_amount
        updated_fields.append("penalty_amount")

    if request.keywords is not None:
        update_data["keywords"] = request.keywords
        updated_fields.append("keywords")

    # Mark as user edited if any fields were updated
    if update_data:
        # Get current document and update fields
        doc_copy = doc.model_copy()

        for key, value in update_data.items():
            setattr(doc_copy, key, value)

        # Mark as user edited
        doc_copy.metadata_edited_by_user = True
        doc_copy.metadata_extraction_status = "user_edited"
        doc_copy.updated_at = datetime.now(timezone.utc)

        # Update database (add_document does upsert)
        store.db.add_document(doc_copy)

        logger.info(f"User updated metadata for {document_id}: {updated_fields}")

        return MetadataUpdateResponse(
            doc_id=document_id,
            filename=doc.filename,
            message=f"Updated {len(updated_fields)} metadata field(s)",
            updated_fields=updated_fields,
        )
    else:
        return MetadataUpdateResponse(
            doc_id=document_id,
            filename=doc.filename,
            message="No fields updated (all values were None)",
            updated_fields=[],
        )


# ===== Pipeline Status Monitoring =====

class PipelineStageInfo(BaseModel):
    """Information about a single pipeline stage."""
    stage: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration: float | None = None
    details: dict | None = None
    error_message: str | None = None


class PipelineStatusResponse(BaseModel):
    """Pipeline status for a specific document."""
    doc_id: str
    filename: str
    current_stage: str
    overall_status: str
    progress_percentage: float
    total_duration_seconds: float | None
    stages: list[PipelineStageInfo]
    started_at: str | None
    completed_at: str | None


@router.get("/{document_id}/pipeline")
async def get_document_pipeline_status(document_id: str) -> PipelineStatusResponse:
    """
    Get pipeline status for a specific document.

    Returns detailed information about each pipeline stage:
    - uploaded → parsing → indexed → metadata_extracted → complete

    Each stage includes:
    - Status (pending/in_progress/success/failed/skipped)
    - Timing information
    - Stage-specific details
    - Error messages if failed
    """
    store = _get_metadata_store()
    doc = store.db.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Parse pipeline data from JSON
    stages = []
    if doc.pipeline_data:
        try:
            import json
            stages_data = json.loads(doc.pipeline_data)
            stages = [PipelineStageInfo(**stage) for stage in stages_data]
        except Exception as e:
            logger.error(f"Failed to parse pipeline_data for {document_id}: {e}")

    # Calculate progress percentage
    from finagent.models.pipeline import PipelineStage, PipelineStatus

    # If we have detailed stages, use them
    if stages:
        # Count completed stages
        completed_count = sum(1 for s in stages if s.status == PipelineStatus.SUCCESS.value)
        # Total possible stages (excluding FAILED and intermediate states)
        total_stages = len([s for s in PipelineStage if s.value not in ['uploading', 'parsing', 'indexing', 'extracting_metadata', 'updating_wiki', 'failed']])
        progress = (completed_count / total_stages * 100) if total_stages > 0 else 0
    else:
        # Fallback: use pipeline_stage to estimate progress
        stage_progress_map = {
            'uploaded': 20,
            'parsing': 30,
            'parsed': 40,
            'indexing': 50,
            'indexed': 70,
            'extracting_metadata': 80,
            'metadata_extracted': 90,
            'updating_wiki': 95,
            'complete': 100,
        }
        current_stage = doc.pipeline_stage or 'uploaded'
        progress = stage_progress_map.get(current_stage, 0)

    # Calculate total duration
    total_duration = None
    if doc.pipeline_started_at and doc.pipeline_completed_at:
        from datetime import datetime
        try:
            # Handle both datetime objects and ISO strings
            if isinstance(doc.pipeline_started_at, str):
                start = datetime.fromisoformat(doc.pipeline_started_at.replace('Z', '+00:00'))
            else:
                start = doc.pipeline_started_at

            if isinstance(doc.pipeline_completed_at, str):
                end = datetime.fromisoformat(doc.pipeline_completed_at.replace('Z', '+00:00'))
            else:
                end = doc.pipeline_completed_at

            total_duration = (end - start).total_seconds()
        except Exception as e:
            logger.error(f"Failed to calculate duration for {document_id}: {e}")

    # Convert datetime objects to ISO format strings
    started_at_str = None
    if doc.pipeline_started_at:
        if isinstance(doc.pipeline_started_at, str):
            started_at_str = doc.pipeline_started_at
        else:
            # Convert datetime to ISO format string
            started_at_str = doc.pipeline_started_at.isoformat()

    completed_at_str = None
    if doc.pipeline_completed_at:
        if isinstance(doc.pipeline_completed_at, str):
            completed_at_str = doc.pipeline_completed_at
        else:
            # Convert datetime to ISO format string
            completed_at_str = doc.pipeline_completed_at.isoformat()

    return PipelineStatusResponse(
        doc_id=document_id,
        filename=doc.filename,
        current_stage=doc.pipeline_stage or "unknown",
        overall_status=doc.pipeline_status or "unknown",
        progress_percentage=progress,
        total_duration_seconds=total_duration,
        stages=stages,
        started_at=started_at_str,
        completed_at=completed_at_str
    )


class PipelineStatsResponse(BaseModel):
    """Aggregate pipeline statistics across all documents."""
    total_documents: int
    by_status: dict[str, int]  # {in_progress: 5, success: 90, failed: 5}
    by_stage: dict[str, int]  # {uploaded: 2, indexing: 3, complete: 95}
    avg_duration_seconds: float | None
    failed_documents: list[dict]  # [{doc_id, filename, failed_stage, error}]


@router.get("/pipeline/stats")
async def get_pipeline_stats() -> PipelineStatsResponse:
    """
    Get aggregate pipeline statistics across all documents.

    Returns:
    - Total document count
    - Breakdown by overall status (in_progress/success/failed)
    - Breakdown by current stage
    - Average processing duration
    - List of failed documents with error details
    """
    store = _get_metadata_store()
    all_metadata = store.get_all_metadata()

    total_documents = len(all_metadata)
    status_counts: dict[str, int] = {}
    stage_counts: dict[str, int] = {}
    durations: list[float] = []
    failed_docs: list[dict] = []

    for metadata in all_metadata:
        doc = store.db.get_document(metadata.doc_id)
        if not doc:
            continue

        # Count by status
        status = doc.pipeline_status or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

        # Count by stage
        stage = doc.pipeline_stage or "unknown"
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # Collect durations
        if doc.pipeline_started_at and doc.pipeline_completed_at:
            from datetime import datetime
            try:
                start = datetime.fromisoformat(doc.pipeline_started_at.replace('Z', '+00:00'))
                end = datetime.fromisoformat(doc.pipeline_completed_at.replace('Z', '+00:00'))
                duration = (end - start).total_seconds()
                durations.append(duration)
            except Exception:
                pass

        # Collect failed documents
        if doc.pipeline_status == "failed":
            # Parse pipeline data to find error
            error_message = None
            failed_stage = doc.pipeline_stage
            if doc.pipeline_data:
                try:
                    import json
                    stages_data = json.loads(doc.pipeline_data)
                    # Find the failed stage
                    for stage_info in stages_data:
                        if stage_info.get('status') == 'failed':
                            error_message = stage_info.get('error_message')
                            failed_stage = stage_info.get('stage', failed_stage)
                            break
                except Exception:
                    pass

            failed_docs.append({
                "doc_id": doc.doc_id,
                "filename": doc.filename,
                "failed_stage": failed_stage,
                "error": error_message
            })

    # Calculate average duration
    avg_duration = sum(durations) / len(durations) if durations else None

    return PipelineStatsResponse(
        total_documents=total_documents,
        by_status=status_counts,
        by_stage=stage_counts,
        avg_duration_seconds=avg_duration,
        failed_documents=failed_docs
    )


# ===== Document Type Classification Endpoints =====

class DocumentTypeResponse(BaseModel):
    """Document type information for frontend."""
    category: str
    name_zh: str
    name_en: str
    description: str
    allowed: bool
    requires_authority: bool
    requires_date: bool
    example_filename_pattern: str | None = None


class AllowedDocumentTypesResponse(BaseModel):
    """List of allowed document types for upload."""
    allowed_types: list[DocumentTypeResponse]
    total_count: int


@router.get("/types/allowed")
async def get_allowed_types() -> AllowedDocumentTypesResponse:
    """
    Get list of document types allowed for upload.

    This endpoint returns all document categories that users can upload.
    Use this to populate document type selector in the upload form.

    Allowed types:
    - 裁罰書 (penalty) - Regulatory penalty documents
    - 法條 (legal_provision) - Legal provisions/articles
    - 判決書 (court_judgment) - Court judgments
    - 監管公告 (regulatory_notice) - Regulatory announcements
    - 知識文件 (knowledge_base) - Knowledge base documents

    Not allowed:
    - 新聞報導 (news) - Secondary source
    - 分析報告 (analysis) - Secondary source
    - 銀行聲明 (bank_statement) - Biased source
    - 其他 (other) - Requires review
    """
    allowed_types = get_allowed_document_types()

    return AllowedDocumentTypesResponse(
        allowed_types=[
            DocumentTypeResponse(
                category=dt.category.value,
                name_zh=dt.name_zh,
                name_en=dt.name_en,
                description=dt.description,
                allowed=dt.allowed,
                requires_authority=dt.requires_authority,
                requires_date=dt.requires_date,
                example_filename_pattern=dt.example_filename_pattern,
            )
            for dt in allowed_types
        ],
        total_count=len(allowed_types),
    )


class DocumentTypeValidationRequest(BaseModel):
    """Request to validate a document type before upload."""
    category: str
    issuing_authority: str | None = None
    document_date: str | None = None


class DocumentTypeValidationResponse(BaseModel):
    """Response from document type validation."""
    valid: bool
    category: str | None = None
    name_zh: str | None = None
    error_message: str | None = None
    warnings: list[str] = []


@router.post("/types/validate")
async def validate_type(request: DocumentTypeValidationRequest) -> DocumentTypeValidationResponse:
    """
    Validate a document type before upload.

    This endpoint checks:
    1. Whether the category is valid
    2. Whether the category is allowed for upload
    3. Whether required fields are provided (warnings if missing)

    Use this endpoint before uploading to ensure the document type is accepted.
    """
    result = validate_document_type(
        category=request.category,
        issuing_authority=request.issuing_authority,
        document_date=request.document_date,
    )

    return DocumentTypeValidationResponse(
        valid=result.valid,
        category=result.category.value if result.category else None,
        name_zh=result.document_type.name_zh if result.document_type else None,
        error_message=result.error_message,
        warnings=result.warnings,
    )
