# Pipeline "Complete" Status Fix

**Date**: 2025-11-19
**Issue**: All pipelines stop at "元數據生成完成" (metadata_extracted), never reaching "完成" (complete)

---

## Root Cause

Documents have two different paths for processing:

### Path 1: Upload via Web UI (✅ Works Correctly)
When users upload files through the web interface:

1. File upload → `uploaded` stage
2. File parsing → `parsed` stage
3. Vector indexing → `indexed` stage
4. Metadata extraction → `metadata_extracted` stage
5. **`pipeline.mark_complete()` is called** → `complete` stage ✅

**File**: [src/finagent/api/routes/documents.py:1018](src/finagent/api/routes/documents.py#L1018)
```python
# Stage 5: Complete
pipeline.mark_complete()

# Save final pipeline state
store.update_metadata(doc_id, {
    "pipeline_stage": pipeline.current_stage.value,  # 'complete'
    "pipeline_status": pipeline.overall_status.value,  # 'success'
    "pipeline_data": json.dumps([...]),
    "pipeline_completed_at": pipeline.completed_at.isoformat()
})
```

This path **correctly** marks the pipeline as `complete`.

---

### Path 2: Metadata Extraction Script (❌ Bug)
When metadata is extracted via the background script (e.g., for bulk processing):

1. Documents already indexed (stage = `indexed`)
2. Script extracts metadata → sets `pipeline_stage = 'metadata_extracted'`
3. **Script never calls `mark_complete()`** → stays at `metadata_extracted` ❌

**File**: [scripts/extract_metadata.py:124](scripts/extract_metadata.py#L124) (BEFORE fix)
```python
cursor.execute("""
    UPDATE documents
    SET
        ...
        pipeline_stage = 'metadata_extracted',  # ❌ Stops here!
        updated_at = CURRENT_TIMESTAMP
    WHERE doc_id = ?
""", ...)
```

This is the bug - the script sets stage to `'metadata_extracted'` but never transitions to `'complete'`.

---

## Why This Happened

Looking at the upload workflow, the pipeline progression is:

1. `uploaded` → File saved to disk
2. `parsed` → File content read and parsed
3. `indexed` → Vector embeddings created and stored in Chroma
4. `metadata_extracted` → LLM extracts structured metadata (title, authority, violations, etc.)
5. `complete` → **All processing finished**

The metadata extraction script handles **step 4** but was missing **step 5**.

---

## Impact

### Database State
Before fix:
```sql
SELECT pipeline_stage, COUNT(*) FROM documents GROUP BY pipeline_stage;
```
Result:
- `metadata_extracted`: 28 documents (stuck here)
- `uploaded`: 4 documents (still processing)

### Frontend Display
According to [DocumentList.tsx:119](frontend/src/components/documents/DocumentList.tsx#L119):

```typescript
{doc.pipeline_stage && doc.pipeline_stage !== 'complete' && (
  <div className="mt-2">
    {/* Progress bar shown here */}
  </div>
)}
```

**Issue**: Documents with `pipeline_stage = 'metadata_extracted'` still show the progress bar, even though they're actually done processing. The UI displays:
- ✅ Progress: 90% (correct for metadata_extracted stage)
- ✅ Label: "元數據生成完成" (correct)
- ❌ But progress bar never disappears (should hide when complete)

---

## The Fix

### 1. Update Metadata Extraction Script

**File**: [scripts/extract_metadata.py:124-127](scripts/extract_metadata.py#L124-L127)

**Before**:
```python
pipeline_stage = 'metadata_extracted',
updated_at = CURRENT_TIMESTAMP
```

**After**:
```python
pipeline_stage = 'complete',
pipeline_status = 'success',
pipeline_completed_at = CURRENT_TIMESTAMP,
updated_at = CURRENT_TIMESTAMP
```

**Rationale**: After metadata extraction succeeds, the document is fully processed. Mark it as `'complete'` to match the upload workflow behavior.

---

### 2. Migrate Existing Documents

Updated all documents stuck at `metadata_extracted` to `complete`:

```sql
UPDATE documents
SET
    pipeline_stage = 'complete',
    pipeline_status = 'success',
    pipeline_completed_at = CURRENT_TIMESTAMP
WHERE pipeline_stage = 'metadata_extracted';
```

**Result**: 28 documents updated from `'metadata_extracted'` to `'complete'`

---

## Verification

### Database After Fix
```sql
SELECT pipeline_stage, COUNT(*) FROM documents GROUP BY pipeline_stage;
```
Result:
- `complete`: 28 documents ✅
- `uploaded`: 4 documents (still processing)

### API Response After Fix
```json
{
  "id": "doc_ae56d355",
  "name": "004_20120120_證券期貨局_...",
  "pipeline_stage": "complete",
  "pipeline_status": "success",
  "pipeline_started_at": "2025-11-19T07:13:42",
  "pipeline_completed_at": "2025-11-19T08:13:51",
  "metadata_extracted": true,
  "extraction_confidence": 0.95
}
```
✅ Correct: `pipeline_stage = 'complete'`
✅ Correct: `pipeline_completed_at` is set

### Frontend After Fix

**Documents with `pipeline_stage = 'complete'`**:
- ❌ Progress bar is **hidden** (correct - matches the `!== 'complete'` condition)
- ✅ Status badge shows "已索引" (indexed)
- ✅ All action buttons work (View, Versions, Reindex, Delete, Pipeline Details)

**Documents still processing** (uploaded, parsing, indexing, extracting_metadata):
- ✅ Progress bar **shown** with appropriate percentage and label
- ✅ Auto-updates every 2 seconds via polling

---

## Pipeline Stage Progression

Complete pipeline flow with percentages:

| Stage | Progress | Label (繁體中文) | Description |
|-------|----------|-----------------|-------------|
| `uploaded` | 20% | 文件已上傳 | File saved to disk |
| `parsing` | 30% | 文件解析中 | Parsing in progress |
| `parsed` | 40% | 文件解析完成 | Parsing complete |
| `indexing` | 50% | 文件索引中 | Vector indexing in progress |
| `indexed` | 70% | 文件索引完成 | Vector embeddings created |
| `extracting_metadata` | 80% | 生成元數據中 | LLM extraction in progress |
| `metadata_extracted` | 90% | 元數據生成完成 | Metadata extraction complete |
| `updating_wiki` | 95% | 更新Wiki中 | Updating wiki (batch upload only) |
| **`complete`** | **100%** | **處理完成** | **All processing finished** ✅ |

**Key Point**: The `complete` stage (100%) is essential to:
1. Signal that no more processing is needed
2. Hide the progress bar in the UI
3. Mark `pipeline_completed_at` timestamp
4. Set `pipeline_status = 'success'`

---

## Why Two Code Paths Exist

### Upload Workflow (`_process_upload_with_progress`)
- Used by: Web UI file upload
- Handles: Single file upload with real-time progress
- Controls: All stages from upload → complete
- Location: [src/finagent/api/routes/documents.py:796-1062](src/finagent/api/routes/documents.py#L796-L1062)

### Metadata Extraction Script (`extract_metadata.py`)
- Used by: Batch processing, re-extraction, CLI tools
- Handles: Only metadata extraction (assumes indexing already done)
- Controls: Only the `metadata_extracted` stage
- Location: [scripts/extract_metadata.py](scripts/extract_metadata.py)

The script was originally designed to just extract metadata, not handle the full pipeline. But since metadata extraction is the **last step** before completion, it should also mark the pipeline as complete.

---

## Best Practices Going Forward

### Rule: Last Stage Should Mark Complete

Any code path that completes the final processing step should:
1. Set `pipeline_stage = 'complete'`
2. Set `pipeline_status = 'success'` (or `'failed'` if errors)
3. Set `pipeline_completed_at = CURRENT_TIMESTAMP`

### Future-Proofing

If we add new processing stages in the future (e.g., "wiki_updated", "analysis_generated"), ensure that:
- The **last** stage in the sequence marks the pipeline as `'complete'`
- All code paths (upload, batch scripts, CLI) consistently use the same logic

---

## Testing

### Test Case 1: New Upload via Web UI
1. Upload a file via http://localhost:5173
2. Watch pipeline progress: 20% → 40% → 70% → 90% → 100%
3. Verify final state: `pipeline_stage = 'complete'`
4. Verify progress bar disappears when complete

**Result**: ✅ Works correctly (always did)

### Test Case 2: Bulk Metadata Extraction
1. Run `uv run python scripts/extract_metadata.py`
2. Check document that was processed
3. Verify final state: `pipeline_stage = 'complete'` (not `'metadata_extracted'`)
4. Verify `pipeline_completed_at` is set

**Result**: ✅ Fixed (was broken, now works)

### Test Case 3: Existing Documents
1. Check documents that were stuck at `'metadata_extracted'`
2. Verify they show `pipeline_stage = 'complete'` after migration
3. Verify progress bar is hidden in UI

**Result**: ✅ Fixed via SQL UPDATE

---

## Summary

### The Bug
Metadata extraction script set `pipeline_stage = 'metadata_extracted'` but never transitioned to `'complete'`, causing 28 documents to appear "stuck" at 90% progress.

### The Fix
1. **Script update**: Change `pipeline_stage = 'metadata_extracted'` to `'complete'`
2. **Database migration**: Update existing documents from `'metadata_extracted'` to `'complete'`

### The Result
All fully-processed documents now correctly show:
- ✅ `pipeline_stage = 'complete'`
- ✅ `pipeline_status = 'success'`
- ✅ Progress bar hidden (100% complete)
- ✅ Pipeline modal shows "處理完成" when viewing details

**Status**: Fully resolved 🎉
