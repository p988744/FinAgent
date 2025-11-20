# Upload Pipeline Architecture

**Date**: 2025-11-19
**Status**: ✅ HTTP Polling Implemented (No CORS Issues)

## Overview

The current upload system uses **HTTP polling** (Google Drive style) to track upload progress without WebSocket or CORS complications. This document describes the architecture and proposes enhancements for better status monitoring.

---

## Current Implementation

### Backend: HTTP Polling Endpoints

**File**: [src/finagent/api/routes/documents.py](src/finagent/api/routes/documents.py)

#### 1. Upload with Progress Tracking
```python
@router.post("/upload-with-progress")
async def upload_file_with_progress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_index: bool = True,
    extract_metadata: bool = True,
):
    """
    Upload a single file and return a job ID for progress tracking.
    Frontend can poll /upload-progress/{job_id} to get real-time updates.
    """
    job_id = str(uuid.uuid4())
    content = await file.read()

    # Start background processing
    background_tasks.add_task(
        _process_upload_with_progress,
        job_id=job_id,
        filename=file.filename,
        content=content,
        auto_index=auto_index,
        extract_metadata=extract_metadata
    )

    return {"job_id": job_id, "message": f"Upload started for {file.filename}"}
```

#### 2. Progress Polling Endpoint
```python
@router.get("/upload-progress/{job_id}")
async def get_upload_progress(job_id: str):
    """
    Get the current progress of an upload job.
    Frontend polls this endpoint every 500ms to get updates.
    """
    if job_id not in _upload_jobs:
        raise HTTPException(status_code=404, detail="Upload job not found")

    return _upload_jobs[job_id]  # Returns UploadProgress model
```

#### 3. Background Processing Pipeline
```python
async def _process_upload_with_progress(
    job_id: str,
    filename: str,
    content: bytes,
    auto_index: bool,
    extract_metadata: bool
):
    """
    Background task with progress updates at each stage:
    1. UPLOADING (0-10%)    - Initial state
    2. UPLOADED (25%)       - File saved to disk
    3. METADATA_SAVED (40%) - Database entry created
    4. INDEXING (50-60%)    - Vector indexing in progress
    5. INDEXED (90%)        - Vector indexing complete
    6. COMPLETE (100%)      - All done
    """
    # Updates _upload_jobs[job_id] at each stage
    # Tracks: stage, progress, message, chunks, error
```

### Frontend: HTTP Polling Implementation

**File**: [frontend/src/components/documents/DocumentUpload.tsx](frontend/src/components/documents/DocumentUpload.tsx)

#### Upload Flow
```typescript
const uploadFileViaPolling = async (uploadFile: UploadFile): Promise<void> => {
  // Step 1: Upload file and get job ID
  const formData = new FormData()
  formData.append('file', uploadFile.file)
  formData.append('auto_index', 'true')
  formData.append('extract_metadata', 'true')

  const uploadResponse = await fetch(
    'http://localhost:8000/api/v1/documents/upload-with-progress',
    { method: 'POST', body: formData }
  )
  const { job_id } = await uploadResponse.json()

  // Step 2: Poll for progress updates every 500ms
  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      const progressResponse = await fetch(
        `http://localhost:8000/api/v1/documents/upload-progress/${job_id}`
      )
      const progress = await progressResponse.json()

      // Update UI with progress
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? {
                ...f,
                status: progress.stage === 'error' ? 'error' : 'uploading',
                progress: progress.progress,  // 0-100
                stage: progress.stage,         // uploading, indexed, complete
                message: progress.message,     // "正在建立向量索引..."
                chunks: progress.chunks || 0,  // Number of indexed chunks
                error: progress.error,
              }
            : f
        )
      )

      // Check if complete or error
      if (progress.stage === 'complete') {
        clearInterval(pollInterval)
        // Clean up job from server
        await fetch(
          `http://localhost:8000/api/v1/documents/upload-progress/${job_id}`,
          { method: 'DELETE' }
        )
        resolve()
      } else if (progress.stage === 'error') {
        clearInterval(pollInterval)
        reject(new Error(progress.error))
      }
    }, 500) // Poll every 500ms
  })
}
```

---

## Pipeline Stages

### Upload Progress Model
```typescript
interface UploadProgress {
  job_id: string
  filename: string
  stage: 'uploading' | 'uploaded' | 'metadata_saved' | 'indexing' | 'indexed' | 'complete' | 'error'
  progress: number      // 0-100
  message: string       // "正在建立向量索引..."
  chunks?: number       // Number of indexed chunks
  error?: string | null // Error message if stage === 'error'
  document_id?: string  // Available after metadata_saved
}
```

### Stage Progression
```
UPLOADING (10%)       → File upload in progress
   ↓
UPLOADED (25%)        → File saved to data/documents/
   ↓
METADATA_SAVED (40%)  → Database entry created with doc_id
   ↓
INDEXING (50-60%)     → Vector embeddings being created
   ↓
INDEXED (90%)         → Vector indexing complete
   ↓
COMPLETE (100%)       → All pipeline stages finished
```

---

## Current Issues

### 1. No Auto-Refresh After Upload
**Problem**: After upload completes, document list doesn't automatically refresh

**Current Behavior**:
- User uploads file → Progress shows 100%
- Document list still shows old data
- User must manually click "Refresh" or navigate away and back

**Code Location**: [DocumentUpload.tsx:214-224](frontend/src/components/documents/DocumentUpload.tsx#L214-L224)
```typescript
// Upload all files via HTTP polling (parallel)
await Promise.all(pendingFiles.map((f) => uploadFileViaPolling(f)))

// Note: onUpload callback removed to prevent duplicate document list entries
// The document list will refresh automatically via polling or user refresh

setGlobalError(null)
```

### 2. No Interval Polling for Document List
**Problem**: Document list only refreshes on page load or manual action

**Missing Feature**: Periodic polling to show:
- Upload pipeline status updates
- Metadata extraction progress
- Pipeline completion status

---

## Proposed Enhancements

### Enhancement 1: Auto-Refresh After Upload
**Add callback to refresh document list after all uploads complete**

```typescript
// In DocumentUpload.tsx
const handleUploadAll = useCallback(async () => {
  const pendingFiles = uploadFiles.filter((f) => f.status === 'pending')
  if (pendingFiles.length === 0) return

  try {
    // Mark all as uploading
    setUploadFiles((prev) =>
      prev.map((f) =>
        f.status === 'pending' ? { ...f, status: 'uploading', progress: 0 } : f
      )
    )

    // Upload all files via HTTP polling (parallel)
    await Promise.all(pendingFiles.map((f) => uploadFileViaPolling(f)))

    // ✅ NEW: Trigger document list refresh
    if (onUpload) {
      await onUpload([])  // Empty array since files already processed
    }

    setGlobalError(null)
  } catch (err) {
    console.error('Upload error:', err)
  }
}, [uploadFiles, uploadFileViaPolling, onUpload])
```

### Enhancement 2: Interval Polling for Document List
**Add periodic polling with manual refresh button**

```typescript
// In DocumentsPage.tsx
export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([])
  const [isPollingEnabled, setIsPollingEnabled] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch(API_BASE)
      if (!res.ok) throw new Error('Failed to fetch documents')
      const data = await res.json()
      setDocuments(data)
      setLastRefresh(new Date())
    } catch (err) {
      showError('無法載入文件列表')
      console.error(err)
    }
  }, [])

  // ✅ NEW: Interval polling (every 5 seconds when enabled)
  useEffect(() => {
    if (!isPollingEnabled) return

    const interval = setInterval(() => {
      fetchDocuments()
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(interval)
  }, [isPollingEnabled, fetchDocuments])

  // ✅ NEW: Manual refresh handler
  const handleManualRefresh = useCallback(async () => {
    setIsPollingEnabled(false) // Pause auto-polling
    await fetchDocuments()
    setTimeout(() => setIsPollingEnabled(true), 2000) // Resume after 2s
  }, [fetchDocuments])

  return (
    <div className="space-y-6">
      {/* ... existing UI ... */}

      {/* ✅ NEW: Refresh control */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={handleManualRefresh}
            className="inline-flex items-center px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4 mr-1.5" />
            手動刷新
          </button>
          <span className="text-xs text-gray-500">
            上次更新: {lastRefresh.toLocaleTimeString()}
          </span>
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={isPollingEnabled}
            onChange={(e) => setIsPollingEnabled(e.target.checked)}
          />
          自動刷新 (每5秒)
        </label>
      </div>

      {/* ... rest of UI ... */}
    </div>
  )
}
```

### Enhancement 3: Smart Polling Based on Pipeline Status
**Only poll when documents are in processing states**

```typescript
// In DocumentsPage.tsx
const [processingCount, setProcessingCount] = useState(0)

const fetchDocuments = useCallback(async () => {
  try {
    const res = await fetch(API_BASE)
    if (!res.ok) throw new Error('Failed to fetch documents')
    const data = await res.json()
    setDocuments(data)

    // ✅ NEW: Count documents in processing states
    const processing = data.filter((doc: DocumentResponse) =>
      doc.pipeline_status === 'in_progress' ||
      doc.metadata_extraction_status === 'processing'
    ).length
    setProcessingCount(processing)

    setLastRefresh(new Date())
  } catch (err) {
    showError('無法載入文件列表')
    console.error(err)
  }
}, [])

// ✅ NEW: Smart polling interval
useEffect(() => {
  if (!isPollingEnabled) return

  // Poll faster when documents are processing
  const interval = processingCount > 0 ? 2000 : 10000 // 2s vs 10s

  const timer = setInterval(() => {
    fetchDocuments()
  }, interval)

  return () => clearInterval(timer)
}, [isPollingEnabled, processingCount, fetchDocuments])
```

---

## Benefits of HTTP Polling Approach

✅ **No CORS Issues**: All endpoints on same origin
✅ **Simple Implementation**: Standard HTTP requests
✅ **Reliable**: Works through firewalls and proxies
✅ **Familiar Pattern**: Similar to Google Drive uploads
✅ **Easy Debugging**: Can test with curl/Postman
✅ **Stateless**: No connection management complexity

---

## Implementation Priority

### High Priority (Immediate)
1. **Auto-refresh after upload** - Users see their uploads immediately
2. **Manual refresh button** - Users can force update anytime
3. **Last refresh timestamp** - Users know when data was updated

### Medium Priority (Next)
1. **Smart interval polling** - Poll faster during processing
2. **Processing indicator** - Show active pipeline count
3. **Pause/resume polling** - User control over auto-refresh

### Low Priority (Future)
1. **Server-sent events (SSE)** - Alternative to polling for real-time updates
2. **Optimistic UI updates** - Show uploads before server confirms
3. **Background sync** - Update in background tab

---

## Code Locations

### Backend
- **Upload endpoints**: [documents.py:1040-1104](src/finagent/api/routes/documents.py#L1040-L1104)
- **Background processing**: [documents.py:766-1032](src/finagent/api/routes/documents.py#L766-L1032)
- **Pipeline monitoring**: [documents.py:1475-1626](src/finagent/api/routes/documents.py#L1475-L1626)

### Frontend
- **Upload component**: [DocumentUpload.tsx](frontend/src/components/documents/DocumentUpload.tsx)
- **Documents page**: [DocumentsPage.tsx](frontend/src/pages/DocumentsPage.tsx)
- **Pipeline progress**: [PipelineProgress.tsx](frontend/src/components/documents/PipelineProgress.tsx)

---

## Testing Checklist

- [ ] Upload single file → Progress shows stages → Document appears in list
- [ ] Upload multiple files → All tracked separately → All complete
- [ ] Manual refresh → Updates immediately → Timestamp updates
- [ ] Auto-refresh enabled → Polls every 5s → Shows processing status
- [ ] Auto-refresh disabled → No polling → Manual refresh works
- [ ] Upload error → Shows error message → Can retry
- [ ] Pipeline failure → Error visible → Can view details

---

## Next Steps

1. Implement auto-refresh after upload completion
2. Add manual refresh button with timestamp
3. Add auto-refresh toggle with interval polling
4. Test all upload scenarios end-to-end
5. Document user-facing features

**Status**: Ready for implementation 🚀
