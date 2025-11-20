# Metadata Status System

## Overview

This document describes the two-tier status system for document processing in FinAgent:

1. **"indexed" status**: Document is in vector DB and filesystem → **searchable**
2. **"metadata_extracted" status**: Metadata analyzed by LLM → **categorized and understood**

## Status Definitions

### Indexed Status (`indexed` column)

**Definition**: Document has been processed into vector embeddings and stored in Chroma vector DB.

**What it means**:
- ✅ Document content loaded from filesystem
- ✅ Content chunked into smaller segments
- ✅ Embeddings generated for each chunk
- ✅ Chunks stored in vector database
- ✅ **Document is searchable** via semantic search

**What it doesn't mean**:
- ❌ Does NOT mean metadata has been extracted
- ❌ Does NOT mean LLM has analyzed the document
- ❌ Does NOT mean document is categorized

**Use case**: Fast indexing without LLM cost, document is immediately searchable

### Metadata Extracted Status (`metadata_extracted` + `metadata_extraction_status`)

**Definition**: Document has been analyzed by LLM to extract structured metadata.

**Extraction Statuses** (`metadata_extraction_status`):
- `pending` - Not yet extracted, waiting in queue
- `processing` - Currently being extracted by LLM
- `completed` - Successfully extracted
- `failed` - Extraction failed (check `metadata_extraction_error`)
- `user_edited` - User manually edited the metadata

**What it means when `completed`**:
- ✅ LLM has analyzed document content
- ✅ Metadata fields populated:
  - `document_type` (裁罰書, 判決書, 法規, etc.)
  - `issuing_authority` (金管會, 中央銀行, etc.)
  - `case_number` (案號)
  - `document_date` (文件日期)
  - `related_institutions` (相關機構 - JSON array)
  - `violation_types` (違規類型 - JSON array)
  - `penalty_amount` (裁罰金額)
  - `keywords` (關鍵詞 - JSON array)
  - `extraction_confidence` (提取信心分數 0-1)
- ✅ **Document appears in wiki categories**
- ✅ **Document can be filtered by type, authority, institution, violation**

**Additional Tracking Fields**:
- `metadata_extraction_error` - Error message if extraction failed
- `metadata_extraction_attempts` - Number of extraction attempts (for retry logic)
- `metadata_last_extracted_at` - Timestamp of last extraction
- `metadata_edited_by_user` - Whether user manually edited metadata

## Workflow Examples

### Example 1: Fast Upload (Indexing Only)

```
User uploads document → Backend processes:
1. Save file to filesystem
2. Create document record (indexed=FALSE, metadata_extraction_status='pending')
3. Index to vector DB (indexed=TRUE)
4. Document is now searchable ✅
5. Metadata extraction NOT run (fast, no LLM cost)
```

**Result**:
- Document searchable immediately
- No LLM cost
- No categories yet
- User can trigger extraction later

### Example 2: Full Upload (Indexing + Metadata Extraction)

```
User uploads document with extract_metadata=true → Backend processes:
1. Save file to filesystem
2. Create document record (indexed=FALSE, metadata_extraction_status='pending')
3. Update status (metadata_extraction_status='processing')
4. Index to vector DB (indexed=TRUE)
5. Call LLM to extract metadata
6. Save extracted metadata to database
7. Update status (metadata_extracted=TRUE, metadata_extraction_status='completed')
```

**Result**:
- Document searchable ✅
- Metadata extracted ✅
- Appears in wiki categories ✅
- Cost: ~$0.001 USD per document

### Example 3: Re-Extract Metadata

```
User clicks "Re-extract metadata" on document:
1. Check current status
2. Update status (metadata_extraction_status='processing')
3. Increment metadata_extraction_attempts
4. Call LLM to extract metadata
5. Overwrite existing metadata
6. Update status (metadata_extracted=TRUE, metadata_extraction_status='completed', metadata_last_extracted_at=NOW())
```

**Use cases**:
- Initial extraction failed
- Extraction confidence was low
- LLM model improved
- User wants fresh analysis

### Example 4: User Edit Metadata

```
User manually edits metadata in UI:
1. User changes document_type from "uploaded" to "裁罰書"
2. User adds institutions: ["玉山銀行", "金管會"]
3. Backend saves changes
4. Update metadata_edited_by_user=TRUE
5. Update metadata_extraction_status='user_edited'
6. Do NOT overwrite on re-index unless user requests
```

**Protection**:
- User edits are preserved
- Re-indexing won't overwrite user edits
- User can choose to "Reset to LLM extraction"

## API Endpoints

### Monitor Metadata Extraction

**GET `/api/v1/documents/metadata/status`**

Returns overview of metadata extraction status across all documents.

**Response**:
```json
{
  "total_documents": 100,
  "indexed": 100,
  "metadata_extracted": 45,
  "by_status": {
    "pending": 40,
    "processing": 5,
    "completed": 45,
    "failed": 10,
    "user_edited": 5
  },
  "failed_documents": [
    {
      "doc_id": "abc123",
      "filename": "test.txt",
      "error": "LLM API timeout",
      "attempts": 3,
      "last_attempted_at": "2025-01-19T01:00:00Z"
    }
  ]
}
```

### Re-Extract Single Document

**POST `/api/v1/documents/{doc_id}/metadata/extract`**

Triggers metadata re-extraction for a single document.

**Parameters**:
- `force`: boolean - Force re-extraction even if user_edited=true (default: false)

**Response**:
```json
{
  "doc_id": "abc123",
  "status": "processing",
  "message": "Metadata extraction started"
}
```

### Batch Re-Extract

**POST `/api/v1/documents/metadata/extract-batch`**

Triggers metadata extraction for multiple documents.

**Request Body**:
```json
{
  "doc_ids": ["abc123", "def456"],  // Optional: specific documents
  "status_filter": "failed",         // Optional: only failed|pending
  "force": false                     // Force re-extraction of completed
}
```

**Response**:
```json
{
  "queued": 25,
  "already_processing": 2,
  "skipped_user_edited": 3,
  "message": "25 documents queued for extraction"
}
```

### Edit Metadata (User)

**PATCH `/api/v1/documents/{doc_id}/metadata`**

Allows user to manually edit metadata.

**Request Body**:
```json
{
  "document_type": "裁罰書",
  "issuing_authority": "金管會",
  "related_institutions": ["玉山銀行"],
  "violation_types": ["洗錢防制"],
  "penalty_amount": "500萬元",
  "keywords": ["洗錢", "防制", "客戶盡職調查"]
}
```

**Response**:
```json
{
  "doc_id": "abc123",
  "metadata_edited_by_user": true,
  "metadata_extraction_status": "user_edited",
  "message": "Metadata updated successfully"
}
```

### Reset to LLM Extraction

**POST `/api/v1/documents/{doc_id}/metadata/reset`**

Resets user edits and re-extracts with LLM.

**Response**:
```json
{
  "doc_id": "abc123",
  "metadata_edited_by_user": false,
  "metadata_extraction_status": "processing",
  "message": "Metadata reset, re-extraction started"
}
```

## UI Components

### Document List - Status Indicators

Each document shows:
```
📄 document.txt
   [✅ Indexed] [⏳ Metadata: Pending]
   [✅ Indexed] [✅ Metadata: Extracted] (confidence: 0.95)
   [✅ Indexed] [❌ Metadata: Failed] → Show error, offer retry
   [✅ Indexed] [✏️ Metadata: User Edited]
```

### Metadata Extraction Monitor

Dashboard showing:
- Total documents
- Indexing status (for search)
- Metadata extraction status (for categories)
- Failed extractions with retry button
- Queue status (X documents processing)

### Document Detail - Metadata Tab

```
Document Type: 裁罰書 [Edit] [Re-extract]
Issuing Authority: 金管會 [Edit]
Related Institutions: 玉山銀行, 中國信託 [Edit]
Violation Types: 洗錢防制, 內部控制 [Edit]

Status: User Edited ✏️
Last Extracted: 2025-01-19 10:00:00
Extraction Confidence: 0.95
Attempts: 1

[Reset to LLM Extraction] [Save Manual Edits]
```

## Database Queries

### Find documents needing metadata extraction
```sql
SELECT doc_id, filename
FROM documents
WHERE indexed = 1
  AND (metadata_extracted = 0 OR metadata_extraction_status = 'pending')
ORDER BY created_at DESC;
```

### Find failed extractions
```sql
SELECT doc_id, filename, metadata_extraction_error, metadata_extraction_attempts
FROM documents
WHERE metadata_extraction_status = 'failed'
ORDER BY metadata_extraction_attempts DESC, created_at DESC;
```

### Find user-edited metadata
```sql
SELECT doc_id, filename, document_type, issuing_authority
FROM documents
WHERE metadata_edited_by_user = 1
ORDER BY updated_at DESC;
```

### Get extraction statistics
```sql
SELECT
  metadata_extraction_status,
  COUNT(*) as count,
  AVG(extraction_confidence) as avg_confidence
FROM documents
WHERE indexed = 1
GROUP BY metadata_extraction_status;
```

## Background Job Processing

### Job Queue for Metadata Extraction

Use FastAPI BackgroundTasks or Celery for async processing:

```python
@router.post("/documents/metadata/extract-all")
async def extract_all_metadata(background_tasks: BackgroundTasks):
    """Extract metadata for all pending documents."""
    docs = db.query("SELECT * FROM documents WHERE indexed=1 AND metadata_extraction_status='pending'")

    for doc in docs:
        background_tasks.add_task(extract_metadata_task, doc.doc_id)

    return {"queued": len(docs)}

async def extract_metadata_task(doc_id: str):
    """Background task to extract metadata for one document."""
    # Update status to 'processing'
    db.update(doc_id, metadata_extraction_status='processing')

    try:
        # Load document content
        content = load_document_content(doc_id)

        # Call LLM
        metadata = await llm_extract_metadata(content)

        # Save to database
        db.update(doc_id,
            metadata_extracted=True,
            metadata_extraction_status='completed',
            document_type=metadata.document_type,
            issuing_authority=metadata.issuing_authority,
            # ... other fields
            metadata_last_extracted_at=datetime.now()
        )

    except Exception as e:
        # Mark as failed
        db.update(doc_id,
            metadata_extraction_status='failed',
            metadata_extraction_error=str(e),
            metadata_extraction_attempts=db.get_attempts(doc_id) + 1
        )
```

## Retry Logic

### Automatic Retry for Failed Extractions

```python
async def retry_failed_extractions(max_attempts=3):
    """Retry failed extractions up to max_attempts."""
    failed = db.query(
        "SELECT * FROM documents WHERE metadata_extraction_status='failed' AND metadata_extraction_attempts < ?",
        (max_attempts,)
    )

    for doc in failed:
        await extract_metadata_task(doc.doc_id)
```

### Exponential Backoff

```python
async def retry_with_backoff(doc_id: str, attempt: int):
    """Retry with exponential backoff."""
    delay = 2 ** attempt  # 2s, 4s, 8s, 16s...
    await asyncio.sleep(delay)
    await extract_metadata_task(doc_id)
```

## Migration Notes

### Migrating Existing Documents

After adding the new columns, existing documents will have:
- `metadata_extracted=0`
- `metadata_extraction_status='pending'`

Documents that already have metadata (from old system) are automatically updated:
```sql
UPDATE documents
SET metadata_extracted = 1,
    metadata_extraction_status = 'completed',
    metadata_last_extracted_at = updated_at
WHERE document_type IS NOT NULL
  AND document_type != ''
  AND document_type != 'uploaded';
```

## Testing

### Test Scenarios

1. **Upload without extraction** → `indexed=TRUE`, `metadata_extracted=FALSE`
2. **Upload with extraction** → `indexed=TRUE`, `metadata_extracted=TRUE`
3. **Failed extraction** → `metadata_extraction_status='failed'`, error saved
4. **Retry extraction** → `attempts` incremented, status updated
5. **User edit** → `metadata_edited_by_user=TRUE`, status='user_edited'
6. **Reset user edit** → Triggers re-extraction, clears user_edited flag

## Performance Considerations

### Cost

- **Indexing only**: No LLM cost, ~0.1s per document
- **Metadata extraction**: ~$0.001 USD per document, ~5-15s per document

### Throughput

- **Parallel extraction**: Process N documents simultaneously (configured limit)
- **Queue management**: Background jobs with priority queue
- **Rate limiting**: Respect LLM API rate limits

### Monitoring

- Track extraction success rate
- Monitor average extraction time
- Alert on high failure rate
- Dashboard for queue status

## Summary

**Key Principles**:
1. **Separate concerns**: Indexing (search) vs Metadata (categories)
2. **User control**: Allow manual editing, protect user edits
3. **Retry-able**: Failed extractions can be retried
4. **Monitorable**: Clear status for each document
5. **Cost-effective**: User chooses when to extract (LLM cost)

**Status Flow**:
```
Upload → indexed:TRUE, metadata:pending
     ↓
  Extract? (user choice)
     ↓
   YES → processing → completed/failed
     ↓                    ↓
  Categories work    Retry available

   NO → Stay pending (fast, no cost)
```
