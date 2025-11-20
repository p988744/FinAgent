# Pipeline Monitoring System - Implementation Guide

**Created:** 2025-11-19
**Purpose:** Track document processing pipeline for debugging and monitoring
**Status:** 🚧 In Progress

---

## Overview

The Pipeline Monitoring System provides real-time visibility into each stage of document processing:

```
📤 Upload → 📝 Parse → 🔍 Index → 🧠 Extract Metadata → 📚 Update Wiki → ✅ Complete
```

Each stage is tracked with:
- **Status**: pending, in_progress, success, failed, skipped
- **Timing**: Start time, end time, duration
- **Details**: Stage-specific information
- **Errors**: Error messages if failed

---

## Architecture

### 1. Data Models ([src/finagent/models/pipeline.py](src/finagent/models/pipeline.py))

**Pipeline Stages**:
- `UPLOADED` - File saved to disk
- `PARSING` - Extracting content
- `PARSED` - Content extracted
- `INDEXING` - Creating embeddings
- `INDEXED` - Stored in Chroma
- `EXTRACTING_METADATA` - LLM extraction
- `METADATA_EXTRACTED` - Metadata complete
- `UPDATING_WIKI` - Building categories
- `WIKI_UPDATED` - Wiki generated
- `COMPLETE` - All done
- `FAILED` - Error occurred

**Pipeline Status**:
- `PENDING` - Not started
- `IN_PROGRESS` - Currently running
- `SUCCESS` - Completed successfully
- `FAILED` - Failed with error
- `SKIPPED` - Skipped (e.g., auto_index=False)

### 2. Database Schema ([src/finagent/database/schema.sql](src/finagent/database/schema.sql#L118-L123))

New fields added to `documents` table:
```sql
pipeline_stage TEXT DEFAULT 'uploaded'
pipeline_status TEXT DEFAULT 'in_progress'
pipeline_data TEXT  -- JSON with detailed stage info
pipeline_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
pipeline_completed_at TIMESTAMP
```

### 3. Document Database ([src/finagent/database/document_db.py](src/finagent/database/document_db.py#L94-L99))

Pipeline fields added to `optional_fields` list for upsert operations.

---

## Usage Examples

### Tracking Pipeline Progress

```python
from finagent.models.pipeline import DocumentPipeline, PipelineStage, PipelineStatus

# Initialize pipeline
pipeline = DocumentPipeline(
    doc_id="doc_123",
    filename="test.txt",
    auto_index=True,
    extract_metadata=True,
    update_wiki=False
)

# Stage 1: Upload
pipeline.update_stage(
    PipelineStage.UPLOADED,
    PipelineStatus.SUCCESS,
    details={"file_size": 1024, "path": "data/documents/test.txt"}
)

# Stage 2: Parsing
pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.IN_PROGRESS)
# ... do parsing ...
pipeline.update_stage(
    PipelineStage.PARSED,
    PipelineStatus.SUCCESS,
    details={"content_length": 5000, "encoding": "utf-8"}
)

# Stage 3: Indexing
pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.IN_PROGRESS)
# ... do indexing ...
pipeline.update_stage(
    PipelineStage.INDEXED,
    PipelineStatus.SUCCESS,
    details={"chunks": 12, "embeddings": 12}
)

# Stage 4: Metadata Extraction
pipeline.update_stage(PipelineStage.EXTRACTING_METADATA, PipelineStatus.IN_PROGRESS)
try:
    # ... extract metadata ...
    pipeline.update_stage(
        PipelineStage.METADATA_EXTRACTED,
        PipelineStatus.SUCCESS,
        details={"confidence": 0.95, "authority": "金管會"}
    )
except Exception as e:
    pipeline.update_stage(
        PipelineStage.METADATA_EXTRACTED,
        PipelineStatus.FAILED,
        error_message=str(e)
    )

# Mark complete
pipeline.mark_complete()

# Get summary
summary = pipeline.to_summary()
print(f"Progress: {pipeline.get_progress_percentage()}%")
print(f"Duration: {pipeline.total_duration_seconds}s")
```

### Saving to Database

```python
import json
from finagent.database.document_db import DocumentDatabase

db = DocumentDatabase()

# Save pipeline data
db.upsert_document(
    doc_id=pipeline.doc_id,
    filename=pipeline.filename,
    file_path="data/documents/test.txt",
    pipeline_stage=pipeline.current_stage.value,
    pipeline_status=pipeline.overall_status.value,
    pipeline_data=json.dumps([s.dict() for s in pipeline.stages]),
    pipeline_completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None
)
```

---

## API Endpoints (To Be Implemented)

### GET /api/v1/documents/{doc_id}/pipeline
Get pipeline status for a specific document.

**Response**:
```json
{
  "doc_id": "doc_123",
  "filename": "test.txt",
  "current_stage": "metadata_extracted",
  "overall_status": "in_progress",
  "progress_percentage": 75.0,
  "total_duration_seconds": 8.5,
  "stages": [
    {
      "stage": "uploaded",
      "status": "success",
      "duration": 0.1,
      "details": {"file_size": 1024}
    },
    {
      "stage": "parsed",
      "status": "success",
      "duration": 0.2,
      "details": {"content_length": 5000}
    },
    {
      "stage": "indexed",
      "status": "success",
      "duration": 2.5,
      "details": {"chunks": 12}
    },
    {
      "stage": "metadata_extracted",
      "status": "success",
      "duration": 5.7,
      "details": {"confidence": 0.95}
    },
    {
      "stage": "wiki_updated",
      "status": "pending"
    }
  ]
}
```

### GET /api/v1/documents/pipeline/stats
Get pipeline statistics across all documents.

**Response**:
```json
{
  "total_documents": 100,
  "by_status": {
    "in_progress": 5,
    "success": 90,
    "failed": 5
  },
  "by_stage": {
    "uploaded": 2,
    "parsing": 1,
    "indexing": 2,
    "extracting_metadata": 0,
    "complete": 95
  },
  "avg_duration_seconds": 12.3,
  "failed_documents": [
    {
      "doc_id": "doc_456",
      "filename": "failed.txt",
      "failed_stage": "indexing",
      "error": "Connection timeout"
    }
  ]
}
```

---

## Frontend UI Components (To Be Implemented)

### 1. Pipeline Progress Bar

Visual progress indicator showing current stage:

```
📤 Upload ✓ → 📝 Parse ✓ → 🔍 Index ⏳ → 🧠 Metadata ⏸️ → 📚 Wiki ⏸️ → ✅ Complete
     [█████████████████████████░░░░░░░░░░░░░░░░░] 60%
```

### 2. Pipeline Timeline

Detailed timeline view:

```
Stage              Status    Duration    Details
----------------   -------   ---------   --------------------------
📤 Uploaded        ✅ Success  0.1s       Size: 1.2 KB
📝 Parsed          ✅ Success  0.2s       Length: 5,000 chars
🔍 Indexed         ✅ Success  2.5s       Chunks: 12, Embeddings: 12
🧠 Metadata        ⏳ Running  5.7s       LLM: ollama/gpt-oss:20b
📚 Wiki            ⏸️ Pending  -          Waiting...
```

### 3. Error Details Panel

When a stage fails, show detailed error information:

```
❌ Pipeline Failed at: Indexing Stage

Error Message:
  Connection to Chroma vector database failed: timeout after 30s

Stack Trace:
  File "indexer.py", line 152, in index_document
  File "chromadb/client.py", line 88, in add_embeddings

Retry Options:
  [Retry Indexing]  [Skip & Continue]  [View Logs]
```

---

## Integration Points

### 1. Upload Endpoint ([documents.py](src/finagent/api/routes/documents.py))

```python
from finagent.models.pipeline import DocumentPipeline, PipelineStage, PipelineStatus

async def _process_upload_with_progress(...):
    # Initialize pipeline
    pipeline = DocumentPipeline(
        doc_id=doc_id,
        filename=file.filename,
        auto_index=auto_index,
        extract_metadata=extract_metadata
    )

    try:
        # Upload stage
        pipeline.update_stage(PipelineStage.UPLOADED, PipelineStatus.SUCCESS)

        # Parse stage
        pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.IN_PROGRESS)
        document = loader.load_txt(file_path.name)
        pipeline.update_stage(PipelineStage.PARSED, PipelineStatus.SUCCESS)

        # Index stage
        if auto_index:
            pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.IN_PROGRESS)
            num_chunks = await indexer.index_document(document)
            pipeline.update_stage(
                PipelineStage.INDEXED,
                PipelineStatus.SUCCESS,
                details={"chunks": num_chunks}
            )

        # Save pipeline to database
        store.update_metadata(doc_id, {
            "pipeline_stage": pipeline.current_stage.value,
            "pipeline_status": pipeline.overall_status.value,
            "pipeline_data": json.dumps([s.dict() for s in pipeline.stages])
        })

    except Exception as e:
        pipeline.update_stage(
            pipeline.current_stage,
            PipelineStatus.FAILED,
            error_message=str(e)
        )
```

### 2. Indexer ([indexer.py](src/finagent/document_processing/indexer.py))

```python
async def index_document(self, document, pipeline: DocumentPipeline = None):
    # Update pipeline if provided
    if pipeline:
        if self.extract_metadata:
            pipeline.update_stage(
                PipelineStage.EXTRACTING_METADATA,
                PipelineStatus.IN_PROGRESS
            )

    # Extract metadata
    if self.extract_metadata:
        try:
            result = await self.metadata_extractor.extract_new(...)
            if pipeline:
                pipeline.update_stage(
                    PipelineStage.METADATA_EXTRACTED,
                    PipelineStatus.SUCCESS,
                    details={"confidence": result.metadata.extraction_confidence}
                )
        except Exception as e:
            if pipeline:
                pipeline.update_stage(
                    PipelineStage.METADATA_EXTRACTED,
                    PipelineStatus.FAILED,
                    error_message=str(e)
                )
```

---

## Benefits

1. **🐛 Debugging**: Quickly identify which stage failed and why
2. **📊 Monitoring**: Track processing performance and bottlenecks
3. **🔍 Transparency**: Users see real-time progress
4. **📈 Analytics**: Aggregate stats on success rates, durations
5. **🚨 Alerting**: Detect and notify on failures
6. **🔄 Retry Logic**: Intelligently retry failed stages

---

## Implementation Status

- ✅ Data models created ([pipeline.py](src/finagent/models/pipeline.py))
- ✅ Database schema updated ([schema.sql](src/finagent/database/schema.sql))
- ✅ Database fields added ([document_db.py](src/finagent/database/document_db.py))
- ⏸️ Upload endpoint integration
- ⏸️ Indexer integration
- ⏸️ API endpoints
- ⏸️ Frontend UI components
- ⏸️ Testing & validation

---

## Next Steps

1. **Integrate into upload flow**:
   - Update `_process_upload_with_progress` to track pipeline
   - Pass pipeline object to indexer

2. **Create API endpoints**:
   - `GET /api/v1/documents/{doc_id}/pipeline`
   - `GET /api/v1/documents/pipeline/stats`

3. **Build frontend UI**:
   - Progress bar component
   - Timeline view
   - Error details panel

4. **Add monitoring**:
   - Dashboard with pipeline stats
   - Failed document list
   - Performance metrics

5. **Testing**:
   - Unit tests for pipeline models
   - Integration tests for full workflow
   - E2E tests with UI

---

## Example: Full Pipeline Flow

```python
# 1. Upload initiated
pipeline = DocumentPipeline(doc_id="doc_789", filename="report.txt")
pipeline.update_stage(PipelineStage.UPLOADED, PipelineStatus.SUCCESS)

# 2. Parsing
pipeline.update_stage(PipelineStage.PARSING, PipelineStatus.IN_PROGRESS)
content = parse_file("report.txt")
pipeline.update_stage(PipelineStage.PARSED, PipelineStatus.SUCCESS,
                     details={"length": len(content)})

# 3. Indexing
pipeline.update_stage(PipelineStage.INDEXING, PipelineStatus.IN_PROGRESS)
chunks = create_embeddings(content)
pipeline.update_stage(PipelineStage.INDEXED, PipelineStatus.SUCCESS,
                     details={"chunks": len(chunks)})

# 4. Metadata extraction
pipeline.update_stage(PipelineStage.EXTRACTING_METADATA, PipelineStatus.IN_PROGRESS)
metadata = await extract_metadata(content)  # Takes 7 seconds with Ollama
pipeline.update_stage(PipelineStage.METADATA_EXTRACTED, PipelineStatus.SUCCESS,
                     details={"confidence": 0.95, "authority": "金管會"})

# 5. Wiki update
pipeline.update_stage(PipelineStage.UPDATING_WIKI, PipelineStatus.IN_PROGRESS)
build_wiki_categories(metadata)
pipeline.update_stage(PipelineStage.WIKI_UPDATED, PipelineStatus.SUCCESS,
                     details={"categories_added": 3})

# 6. Complete
pipeline.mark_complete()

# Result:
# - Total time: 12.5 seconds
# - Progress: 100%
# - Status: SUCCESS
# - All stages: ✅
```

---

**This pipeline monitoring system will make debugging document processing issues trivial!** 🎉
