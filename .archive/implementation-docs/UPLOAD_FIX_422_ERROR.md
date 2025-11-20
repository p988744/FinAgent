# Upload 422 Error Fix

**Date**: 2025-11-19
**Status**: ✅ Fixed

## Problem

After implementing the HTTP polling-based upload system and progress bar enhancements, users encountered a 422 error when uploading documents:

```
POST http://localhost:5173/api/v1/documents/upload-batch?auto_index=true&extract_metadata=true
422 (Unprocessable Entity)
```

**Error Location**: [DocumentsPage.tsx:133](frontend/src/pages/DocumentsPage.tsx#L133)

---

## Root Cause

The `handleUpload` function in `DocumentsPage.tsx` was designed for the old batch upload workflow, but the `DocumentUpload` component now handles uploads internally via the new HTTP polling system.

**Workflow Mismatch**:

1. **New Flow (polling-based)**:
   - `DocumentUpload` component uploads files via `uploadFileViaPolling()`
   - After completion, calls `onUpload([])` with an **empty array** to trigger parent refresh

2. **Old Flow (batch upload)**:
   - `handleUpload` function expects **actual File objects** in the files array
   - Tries to upload these files to `/api/v1/documents/upload-batch` endpoint
   - **Error**: When it receives empty array `[]`, FormData is empty, causing 422 error

---

## Solution

Modified `handleUpload` to detect when it's being called as a refresh callback (empty files array) versus actual batch upload:

### Code Changes

**File**: [frontend/src/pages/DocumentsPage.tsx:125-170](frontend/src/pages/DocumentsPage.tsx#L125-L170)

```typescript
const handleUpload = async (files: File[]) => {
  // DocumentUpload component now handles uploads internally via polling
  // and calls this callback with an empty array to trigger refresh
  if (files.length === 0) {
    // Just refresh the document list
    await Promise.all([fetchDocuments(), fetchIndexStatus()])
    return
  }

  // Legacy batch upload support (if needed in future)
  setIsUploading(true)
  try {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    const res = await fetch(`${API_BASE}/upload-batch?auto_index=true&extract_metadata=true`, {
      method: 'POST',
      body: formData,
    })

    if (!res.ok) {
      const error = await res.json()
      throw new Error(error.detail || '上傳失敗')
    }

    const result = await res.json()
    await Promise.all([fetchDocuments(), fetchIndexStatus()])

    if (result.successful > 0) {
      showSuccess(
        `成功上傳 ${result.successful} 個文件${
          result.failed > 0 ? `，${result.failed} 個失敗` : ''
        }`
      )
    } else {
      showError('所有文件上傳失敗')
    }
  } catch (err) {
    showError(err instanceof Error ? err.message : '上傳失敗')
    throw err
  } finally {
    setIsUploading(false)
  }
}
```

### Key Changes

**Lines 126-132**: Added early return for empty array
```typescript
if (files.length === 0) {
  // Just refresh the document list
  await Promise.all([fetchDocuments(), fetchIndexStatus()])
  return
}
```

**Why This Works**:
- When `DocumentUpload` completes polling-based uploads, it calls `onUpload([])`
- `handleUpload` detects empty array and just refreshes the document list
- No attempt to call batch upload endpoint with empty FormData
- Legacy batch upload code preserved for future use if needed

---

## Upload Flow After Fix

### 1. User Uploads Files

```
User selects files → DocumentUpload component
                          ↓
                  Upload via polling
                          ↓
            uploadFileViaPolling(file) for each file
                          ↓
            Poll /api/v1/documents/upload-progress/{job_id}
                          ↓
            Track progress: 0% → 100%
                          ↓
            All uploads complete
                          ↓
            Call onUpload([])  ← Empty array!
                          ↓
            DocumentsPage.handleUpload([])
                          ↓
            Detect files.length === 0
                          ↓
            fetchDocuments() + fetchIndexStatus()
                          ↓
            Document list refreshes with new files ✅
```

### 2. What Happens Now

✅ Files upload successfully via polling
✅ Progress bars show during upload
✅ After completion, `onUpload([])` triggers refresh
✅ `handleUpload` detects empty array
✅ Document list refreshes to show new documents
✅ No 422 error

---

## Testing Results

### Test 1: Single File Upload
1. ✅ User uploads single .txt file
2. ✅ Progress shows: uploading → parsing → indexing → extracting metadata → complete
3. ✅ Progress bar updates in DocumentUpload component
4. ✅ After completion, document list refreshes automatically
5. ✅ New document appears in "最近上傳" section
6. ✅ No 422 error

### Test 2: Multiple File Upload
1. ✅ User uploads 3 files simultaneously
2. ✅ Each file shows individual progress
3. ✅ All files complete at different times
4. ✅ After all complete, document list refreshes once
5. ✅ All 3 documents appear in list
6. ✅ No 422 error

### Test 3: Auto-Refresh Integration
1. ✅ Upload file via polling
2. ✅ Document appears in list after refresh
3. ✅ Smart polling detects processing document
4. ✅ Polling interval changes to 2s (fast mode)
5. ✅ Progress bars update every 2 seconds
6. ✅ When processing complete, interval returns to 10s
7. ✅ No 422 error

---

## Technical Details

### Why Empty Array?

The `DocumentUpload` component calls `onUpload([])` with an empty array because:

1. **Files already processed**: Uploads handled internally via polling
2. **No duplicate work**: Parent doesn't need to re-upload
3. **Trigger refresh**: Empty array signals "refresh the list"
4. **Clean API**: Simple callback interface

### Why Not Remove Batch Upload Code?

The batch upload code (lines 134-169) is preserved for:

1. **Future flexibility**: May want to support both upload methods
2. **Backward compatibility**: Existing code that passes actual File objects
3. **Testing**: Useful for testing batch upload endpoint directly
4. **Documentation**: Shows how batch upload worked

### Alternative Approaches Considered

**Option 1: Separate refresh callback**
```typescript
onUploadComplete?: () => Promise<void>
```
❌ More complex API, two callbacks instead of one

**Option 2: Remove handleUpload entirely**
```typescript
<DocumentUpload onUpload={undefined} />
```
❌ Loses batch upload capability, breaks interface

**Option 3: Check inside DocumentUpload**
```typescript
if (onUpload && files.length > 0) {
  await onUpload(files)
}
```
❌ Requires changing DocumentUpload, less flexible

**✅ Chosen: Early return in handleUpload**
- Simple, clean, preserves existing behavior
- No breaking changes to component interfaces
- Easy to understand and maintain

---

## Files Modified

1. **[frontend/src/pages/DocumentsPage.tsx](frontend/src/pages/DocumentsPage.tsx)** (lines 125-170)
   - Added empty array check
   - Added early return for refresh-only case
   - Preserved legacy batch upload code

---

## Related Documentation

- [UPLOAD_PIPELINE_ARCHITECTURE.md](UPLOAD_PIPELINE_ARCHITECTURE.md) - Overall polling architecture
- [UPLOAD_ENHANCEMENTS_COMPLETE.md](UPLOAD_ENHANCEMENTS_COMPLETE.md) - Auto-refresh implementation
- [PROGRESS_BAR_ENHANCEMENT.md](PROGRESS_BAR_ENHANCEMENT.md) - Progress bar implementation
- [DocumentUpload.tsx](frontend/src/components/documents/DocumentUpload.tsx) - Upload component source

---

## Success Criteria

✅ Upload completes successfully via polling
✅ No 422 error when upload finishes
✅ Document list refreshes automatically after upload
✅ Progress bars work during upload
✅ Auto-refresh polling works (2s/10s intervals)
✅ Processing count updates correctly
✅ Manual refresh button works
✅ Legacy batch upload code preserved

**Status**: Complete and tested 🎉

---

## Before and After

### Before (Broken)
```typescript
const handleUpload = async (files: File[]) => {
  setIsUploading(true)
  // ... always tries to upload to batch endpoint
  const formData = new FormData()
  files.forEach((file) => {  // files = [] → empty FormData!
    formData.append('files', file)
  })
  // 422 error: "No files provided"
}
```

### After (Fixed)
```typescript
const handleUpload = async (files: File[]) => {
  // Check if this is a refresh callback
  if (files.length === 0) {
    await Promise.all([fetchDocuments(), fetchIndexStatus()])
    return  // ✅ No batch upload attempt
  }

  // Legacy batch upload for actual files
  setIsUploading(true)
  // ... rest of code
}
```

---

## Known Limitations

1. **No upload queue UI**: Only see active uploads in DocumentUpload component
2. **Single upload flow**: Polling-based only, batch upload unused
3. **No duplicate detection**: User can upload same file multiple times

These are not bugs - they're known design choices. May be addressed in future enhancements.

---

## Deployment Notes

**No backend changes required!** This is a frontend-only fix.

**To deploy**:
1. Frontend will hot-reload automatically (Vite HMR)
2. No need to restart backend server
3. Existing uploaded documents unaffected
4. No database migrations needed

**Services Running**:
- ✅ Backend: http://localhost:8000 (uvicorn with --reload)
- ✅ Frontend: http://localhost:5173 (Vite dev server)

---

## Future Improvements

### Could Add (Not Implemented)
1. **Upload queue visualization**: Show all pending/active uploads
2. **Duplicate file detection**: Warn before uploading same file
3. **Retry failed uploads**: Automatic retry mechanism
4. **Upload history**: Track all uploads, show failures
5. **Batch upload UI**: Allow user to choose polling vs batch

None of these are critical - current system works well for typical usage.
