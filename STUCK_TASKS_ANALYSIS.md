# Stuck Tasks Analysis & Fix

**Date**: 2025-11-19
**Issue**: 5 documents stuck at `uploaded` stage with `in_progress` status

---

## Root Cause

Documents were uploaded via the `/upload-with-progress` endpoint which uses FastAPI's `BackgroundTasks` to process files asynchronously. The background processing tasks were killed when the server reloaded during development, leaving documents in an incomplete state.

### Timeline
1. User uploads files via web UI → POST `/api/v1/documents/upload-with-progress`
2. Endpoint returns immediately with `job_id`
3. Background task `_process_upload_with_progress()` starts processing
4. **Server reloads (due to code changes)** → Background tasks killed
5. Documents stuck at `pipeline_stage='uploaded'`, `full_content=NULL`

---

## Affected Documents

| Doc ID | Filename | Issue |
|--------|----------|-------|
| doc_8b2d8ae7 | 011_20120229_銀行局_渣打國際商業銀行.txt | Background task killed |
| doc_720caadd | 007_20120209_銀行局_未指定.txt | Background task killed |
| doc_6ef787df | 009_20120209_銀行局_未指定.txt | Background task killed |
| doc_1b27c45d | test_pipeline_progress.txt | Background task killed |
| doc_0768f6da | 012_20120329_銀行局_台北富邦商業銀行.txt | Background task killed |

All files existed on disk (validated with `ls data/documents/`).

---

## Resolution

### Step 1: Content Recovery
**Script**: [scripts/reprocess_stuck_uploads.py](scripts/reprocess_stuck_uploads.py)

**What it does**:
1. Finds documents with `pipeline_stage='uploaded'` AND `pipeline_status='in_progress'` AND `full_content IS NULL`
2. Reads file content from disk
3. **Validates content** (not empty, valid UTF-8)
4. Updates database with `full_content` and sets `pipeline_stage='parsed'`
5. **Marks as failed** if file missing, empty, or has encoding issues

**Error handling added**:
- ❌ File not found → Mark as `failed`
- ❌ Empty content → Mark as `failed`
- ❌ UTF-8 decode error → Mark as `failed`
- ✅ Valid content → Mark as `parsed`

### Step 2: Complete Processing
**Script**: [scripts/complete_stuck_documents.py](scripts/complete_stuck_documents.py)

**What it does**:
1. Finds documents with `pipeline_stage='parsed'`
2. Loads document using `DocumentLoader`
3. **Validates document object** (not None, has content)
4. Indexes document (creates vector embeddings)
5. **Validates indexing result** (chunk_count > 0)
6. Extracts metadata using LLM
7. Marks as `pipeline_stage='complete'`
8. **Marks as failed** if any step fails

**Error handling added**:
- ❌ File load fails → Mark as `failed`, stay at `parsed`
- ❌ Document empty → Mark as `failed`, stay at `parsed`
- ❌ Indexing produces 0 chunks → Mark as `failed`, stay at `parsed`
- ❌ Any exception → Mark as `failed`, stay at `parsed`
- ✅ All steps succeed → Mark as `complete`

---

## Upload Endpoint Improvements

**File**: [src/finagent/api/routes/documents.py](src/finagent/api/routes/documents.py#L956-L973)

### Added Validation

```python
# Validate document content (line 960-962)
if not document or not document.content or len(document.content.strip()) == 0:
    raise ValueError("Document content is empty or invalid")

# Validate indexing result (line 971-973)
if num_chunks == 0:
    raise ValueError("Indexing failed - no chunks created")
```

**Why this matters**:
- Prevents silent failures where documents appear "uploaded" but have no searchable content
- Catches empty files, corrupted files, or files with unsupported encoding early
- Provides clear error messages to users instead of leaving documents stuck

### Existing Error Handling (Already Good)

```python
except Exception as e:
    logger.error(f"Failed to auto-index {doc_id}: {e}")
    pipeline.update_stage(
        PipelineStage.INDEXING,
        PipelineStatus.FAILED,
        error_message=str(e)
    )
    # Save failed pipeline state
    store.update_metadata(doc_id, {
        "pipeline_stage": pipeline.current_stage.value,
        "pipeline_status": pipeline.overall_status.value,
        "pipeline_data": json.dumps([...])
    })
    # Don't fail the upload if indexing fails
    _upload_jobs[job_id].message = f"索引失敗: {str(e)}"
```

This ensures:
- Pipeline status is saved to database even on failure
- User can see the error in the upload progress modal
- Upload doesn't completely fail - file is still saved

---

## Results

### Before Fix
```sql
SELECT pipeline_stage, pipeline_status, COUNT(*) FROM documents
WHERE pipeline_status = 'in_progress';
```
Result: 5 documents stuck at `uploaded` with `in_progress`

### After Fix
```sql
SELECT pipeline_stage, COUNT(*) FROM documents GROUP BY pipeline_stage;
```
Result: 33 documents at `complete` ✅

### Processing Summary
- ✅ Loaded content from disk (all 5 files)
- ✅ Indexed successfully (19 total chunks: 4, 5, 5, 1, 4)
- ✅ Metadata extracted with 95% confidence
- ✅ Marked as `pipeline_stage='complete'`

---

## Best Practices Going Forward

### 1. Validate at Every Stage

```python
# ❌ BAD: Assume content exists
document = loader.load_txt(filename)
indexer.index_document(document)

# ✅ GOOD: Validate before proceeding
document = loader.load_txt(filename)
if not document or not document.content:
    raise ValueError("Document is empty")

num_chunks = await indexer.index_document(document)
if num_chunks == 0:
    raise ValueError("No chunks created")
```

### 2. Always Mark Failed State

```python
# ❌ BAD: Silent failure
try:
    process_document()
except Exception as e:
    logger.error(f"Error: {e}")
    # No database update!

# ✅ GOOD: Update pipeline status
try:
    process_document()
except Exception as e:
    logger.error(f"Error: {e}")
    cursor.execute("""
        UPDATE documents
        SET pipeline_stage = 'current_stage',
            pipeline_status = 'failed'
        WHERE doc_id = ?
    """, (doc_id,))
```

### 3. Handle Background Task Failures

**Problem**: `BackgroundTasks` in FastAPI are fire-and-forget. If the server restarts, they're lost.

**Solutions**:
1. **Short-term**: Periodic cleanup script to find and retry stuck tasks
2. **Long-term**: Use a persistent task queue (Celery, RQ, or database-backed queue)
3. **Monitoring**: Track `pipeline_status='in_progress'` for > 5 minutes as potential stuck tasks

### 4. Provide User Feedback

Frontend should show:
- ✅ `pipeline_status='success'` → Green checkmark, hide progress bar
- ⏳ `pipeline_status='in_progress'` → Blue spinner, show progress bar
- ❌ `pipeline_status='failed'` → Red error icon, show error message with retry button

---

## Testing Recovery Scripts

### Test Empty File
```bash
# Create empty file
touch data/documents/test_empty.txt

# Upload via API
curl -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@data/documents/test_empty.txt"

# Kill server mid-upload (simulate crash)
pkill -f uvicorn

# Run recovery
uv run python scripts/reprocess_stuck_uploads.py
```

**Expected**: Document marked as `failed` with error "File is empty"

### Test Missing File
```bash
# Create database entry without file
sqlite3 data/finagent.db "INSERT INTO documents (doc_id, filename, pipeline_stage, pipeline_status) VALUES ('test_missing', 'missing.txt', 'uploaded', 'in_progress');"

# Run recovery
uv run python scripts/reprocess_stuck_uploads.py
```

**Expected**: Document marked as `failed` with error "File not found"

### Test Invalid UTF-8
```bash
# Create file with invalid UTF-8
echo -e '\xFF\xFE' > data/documents/test_encoding.txt

# Upload and simulate crash
# Run recovery
uv run python scripts/reprocess_stuck_uploads.py
```

**Expected**: Document marked as `failed` with error "File encoding error"

---

## Monitoring Query

Run this daily to find potentially stuck tasks:

```sql
SELECT doc_id, filename, pipeline_stage, pipeline_status,
       ROUND((JULIANDAY('now') - JULIANDAY(pipeline_started_at)) * 24 * 60) as minutes_stuck
FROM documents
WHERE pipeline_status = 'in_progress'
  AND pipeline_started_at < datetime('now', '-5 minutes')
ORDER BY pipeline_started_at;
```

If any results: investigate and run recovery scripts.

---

## Summary

**Problem**: Background tasks killed by server reload, leaving 5 documents stuck
**Solution**: 2-step recovery process with comprehensive validation and error handling
**Prevention**: Added validation to upload endpoint + monitoring for stuck tasks
**Result**: All 33 documents now at `complete` stage ✅

**Key Takeaway**: Always validate data at every pipeline stage and mark failures explicitly in the database, never leave documents in indeterminate states.
