"""Celery task for processing document uploads."""

import asyncio
import logging
import traceback

from celery import Task

from finagent.celery_app import celery_app
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.loader import DocumentLoader
from finagent.document_processing.metadata_store import DocumentMetadataStore
from finagent.models.pipeline import DocumentPipeline, PipelineStage, PipelineStatus

logger = logging.getLogger(__name__)


class DocumentProcessingTask(Task):
    """Custom task class with retry configuration."""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 5}  # Retry after 5s, 10s, 20s
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=DocumentProcessingTask,
    name="finagent.tasks.process_document_upload",
    track_started=True,
)
def process_document_upload(
    self,
    doc_id: str,
    filename: str,
    file_path: str,
    auto_index: bool = True,
    extract_metadata: bool = True,
) -> dict:
    """
    Process an uploaded document: load, index, extract metadata.

    Args:
        doc_id: Document ID
        filename: Original filename
        file_path: Path to saved file (relative to project root)
        auto_index: Whether to automatically index the document
        extract_metadata: Whether to extract metadata using LLM

    Returns:
        dict with processing results (chunk_count, metadata, etc.)

    Raises:
        Retry: If processing fails and should be retried
    """
    from datetime import datetime

    # Initialize log collection
    task_logs = []

    def add_log(level: str, message: str):
        """Add a log entry with timestamp."""
        # Use local time with timezone for user-friendly display
        timestamp = datetime.now().astimezone().isoformat()
        task_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        logger.log(getattr(logging, level), f"[CELERY TASK] {message}")

    add_log('INFO', f"Starting processing for {filename} (doc_id={doc_id})")

    # Initialize components
    store = DocumentMetadataStore()
    pipeline = DocumentPipeline(
        doc_id=doc_id,
        filename=filename,
        auto_index=auto_index,
        extract_metadata=extract_metadata
    )

    try:

        # Load document
        add_log('INFO', f"Loading document: {filename}")
        pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.IN_PROGRESS, details={'logs': task_logs})

        loader = DocumentLoader()
        try:
            document = loader.load_txt(filename)
        except FileNotFoundError:
            error_msg = f"File not found: {filename}"
            add_log('ERROR', error_msg)
            pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.FAILED, error_message=error_msg, details={'logs': task_logs})
            _save_failed_state(store, doc_id, pipeline, error_msg, task_logs)
            raise ValueError(error_msg)
        except Exception as load_err:
            error_msg = f"Failed to load document: {str(load_err)}"
            add_log('ERROR', error_msg)
            pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.FAILED, error_message=error_msg, details={'logs': task_logs})
            _save_failed_state(store, doc_id, pipeline, error_msg, task_logs)
            raise ValueError(error_msg)

        # Validate document content
        if not document or not document.content or len(document.content.strip()) == 0:
            error_msg = "Document content is empty or invalid"
            add_log('ERROR', error_msg)
            pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.FAILED, error_message=error_msg, details={'logs': task_logs})
            _save_failed_state(store, doc_id, pipeline, error_msg, task_logs)
            raise ValueError(error_msg)

        add_log('INFO', f"Document loaded successfully: {len(document.content)} characters")
        pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.SUCCESS, details={'logs': task_logs})

        # Update progress (25% - parsing complete)
        self.update_state(state='PROGRESS', meta={'progress': 25, 'status': 'Document loaded', 'logs': task_logs})

        # Index document if requested
        chunk_count = 0
        if auto_index:
            add_log('INFO', f"Starting indexing for document: {filename}")
            pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.IN_PROGRESS, details={'logs': task_logs})

            indexer = DocumentIndexer(extract_metadata=False)  # Metadata extraction is separate

            try:
                # Run async indexing in event loop
                add_log('INFO', "Creating embeddings and storing in vector database...")
                chunk_count = asyncio.run(indexer.index_document(document))

                # Validate indexing result
                if chunk_count == 0:
                    error_msg = "Indexing failed - no chunks created"
                    add_log('ERROR', error_msg)
                    pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.FAILED, error_message=error_msg, details={'logs': task_logs})
                    _save_failed_state(store, doc_id, pipeline, error_msg, task_logs)
                    raise ValueError(error_msg)

                add_log('INFO', f"Indexed successfully: {chunk_count} chunks created")
                pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.SUCCESS, details={'logs': task_logs, 'chunk_count': chunk_count})

                # Update progress (50% - indexing complete)
                self.update_state(state='PROGRESS', meta={'progress': 50, 'status': f'Indexed {chunk_count} chunks', 'logs': task_logs})

            except Exception as index_err:
                error_msg = f"Indexing failed: {str(index_err)}"
                add_log('ERROR', error_msg)
                add_log('ERROR', f"Traceback: {traceback.format_exc()}")
                pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.FAILED, error_message=error_msg, details={'logs': task_logs})
                _save_failed_state(store, doc_id, pipeline, error_msg, task_logs)
                raise ValueError(error_msg)
        else:
            add_log('INFO', "Indexing skipped (auto_index=false)")
            pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.SKIPPED, details={'logs': task_logs})

        # Extract metadata if requested
        metadata = None
        if extract_metadata:
            add_log('INFO', f"Starting metadata extraction: {filename}")
            pipeline.update_stage(PipelineStage.EXTRACTING_METADATA, PipelineStatus.IN_PROGRESS, details={'logs': task_logs})

            # Update progress (75% - starting metadata extraction)
            self.update_state(state='PROGRESS', meta={'progress': 75, 'status': 'Extracting metadata', 'logs': task_logs})

            indexer = DocumentIndexer(extract_metadata=True)

            try:
                # Run async metadata extraction in event loop
                add_log('INFO', "Using LLM to extract metadata fields...")
                metadata = asyncio.run(indexer.metadata_extractor.extract_metadata(document.content, filename))

                if metadata:
                    add_log('INFO', f"Metadata extracted successfully: {len(metadata)} fields")
                    pipeline.update_stage(PipelineStage.EXTRACTING_METADATA, PipelineStatus.SUCCESS, details={'logs': task_logs, 'metadata_fields': list(metadata.keys())})
                else:
                    add_log('WARNING', "No metadata extracted from document")
                    pipeline.update_stage(PipelineStage.EXTRACTING_METADATA, PipelineStatus.SUCCESS, details={'logs': task_logs})

            except Exception as meta_err:
                error_msg = f"Metadata extraction failed: {str(meta_err)}"
                add_log('ERROR', error_msg)
                add_log('ERROR', f"Traceback: {traceback.format_exc()}")
                # Don't fail the entire task if only metadata extraction fails
                pipeline.update_stage(PipelineStage.EXTRACTING_METADATA, PipelineStatus.FAILED, error_message=error_msg, details={'logs': task_logs})
        else:
            add_log('INFO', "Metadata extraction skipped (extract_metadata=false)")
            pipeline.update_stage(PipelineStage.EXTRACTING_METADATA, PipelineStatus.SKIPPED, details={'logs': task_logs})

        # Mark pipeline as complete
        add_log('INFO', f"All stages completed successfully for {filename}")
        pipeline.mark_complete()

        # Save final state to database
        _save_success_state(store, doc_id, pipeline, chunk_count, metadata, task_logs)

        # Update progress (100% - complete)
        self.update_state(state='SUCCESS', meta={'progress': 100, 'status': 'Processing complete', 'logs': task_logs})

        add_log('INFO', f"Processing complete for {filename} (doc_id={doc_id})")

        return {
            'doc_id': doc_id,
            'filename': filename,
            'chunk_count': chunk_count,
            'metadata': metadata,
            'pipeline_stage': 'complete',
            'pipeline_status': 'success',
            'logs': task_logs,
        }

    except Exception as e:
        error_msg = f"Unexpected error processing {filename}: {str(e)}"
        add_log('ERROR', error_msg)
        add_log('ERROR', f"Traceback: {traceback.format_exc()}")

        # Mark as failed
        pipeline.update_stage(pipeline.current_stage, PipelineStatus.FAILED, error_message=error_msg, details={'logs': task_logs})
        _save_failed_state(store, doc_id, pipeline, error_msg, task_logs)

        # Retry if this is a retriable error
        if self.request.retries < self.max_retries:
            add_log('INFO', f"Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        # Max retries exceeded
        add_log('ERROR', f"Max retries exceeded for {filename}")
        raise


def _save_success_state(
    store: DocumentMetadataStore,
    doc_id: str,
    pipeline: DocumentPipeline,
    chunk_count: int,
    metadata: dict | None,
    task_logs: list,
) -> None:
    """Save successful pipeline state to database."""
    import json
    from datetime import datetime

    update_data = {
        'filename': pipeline.filename,  # Include filename for document creation
        'indexed': 1,
        'chunk_count': chunk_count,
        'pipeline_stage': pipeline.current_stage.value,
        'pipeline_status': pipeline.overall_status.value,
        'pipeline_started_at': pipeline.started_at.isoformat() if pipeline.started_at else None,
        'pipeline_completed_at': datetime.now().astimezone().isoformat(),
        'pipeline_data': json.dumps([
            {
                'stage': stage.stage.value,
                'status': stage.status.value,
                'started_at': stage.started_at.isoformat() if stage.started_at else None,
                'completed_at': stage.completed_at.isoformat() if stage.completed_at else None,
                'duration': stage.duration_seconds,
                'error_message': stage.error_message,
                'details': stage.details,  # Include details (which contains logs)
            }
            for stage in pipeline.stages
        ]),
    }

    if metadata:
        update_data.update(metadata)

    store.update_metadata(doc_id, update_data)
    logger.info(f"[CELERY TASK] Saved success state to database for {doc_id}")


def _save_failed_state(
    store: DocumentMetadataStore,
    doc_id: str,
    pipeline: DocumentPipeline,
    error_message: str,
    task_logs: list,
) -> None:
    """Save failed pipeline state to database."""
    import json
    from datetime import datetime

    update_data = {
        'filename': pipeline.filename,  # Include filename for document creation
        'pipeline_stage': pipeline.current_stage.value,
        'pipeline_status': 'failed',
        'pipeline_started_at': pipeline.started_at.isoformat() if pipeline.started_at else None,
        'pipeline_completed_at': datetime.now().astimezone().isoformat(),
        'pipeline_data': json.dumps([
            {
                'stage': stage.stage.value,
                'status': stage.status.value,
                'started_at': stage.started_at.isoformat() if stage.started_at else None,
                'completed_at': stage.completed_at.isoformat() if stage.completed_at else None,
                'duration': stage.duration_seconds,
                'error_message': stage.error_message,
                'details': stage.details,  # Include details (which contains logs)
            }
            for stage in pipeline.stages
        ]),
    }

    store.update_metadata(doc_id, update_data)
    logger.info(f"[CELERY TASK] Saved failed state to database for {doc_id}: {error_message}")
