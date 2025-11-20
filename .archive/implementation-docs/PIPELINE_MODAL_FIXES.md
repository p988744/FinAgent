# Pipeline Modal Fixes

**Date**: 2025-11-19
**Status**: ✅ Both Issues Fixed

## Problems Reported

User reported two issues with the Pipeline Modal (處理進度):

1. **Background color is black** - User wanted blur effect instead of solid black
2. **Progress never changes** - Progress is static, not updating

---

## Issue 1: Black Background → Blur Effect ✅

### Problem
The modal overlay was using `bg-black bg-opacity-50`, which creates a solid black background with 50% opacity. This looks harsh and doesn't match modern UI patterns.

### Solution
Changed to blur effect with Tailwind CSS backdrop utilities:

**File**: [frontend/src/components/documents/PipelineModal.tsx:63](frontend/src/components/documents/PipelineModal.tsx#L63)

**Before**:
```typescript
<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
```

**After**:
```typescript
<div className="fixed inset-0 backdrop-blur-sm bg-black/30 flex items-center justify-center z-50 p-4">
```

### What Changed
- `backdrop-blur-sm` - Adds subtle blur effect to background
- `bg-black/30` - Modern Tailwind opacity syntax (30% black instead of 50%)
- Result: Softer, more elegant modal overlay

---

## Issue 2: Static Progress (Not Updating) ✅

### Problem
The Pipeline Modal was fetching data every 2 seconds via auto-refresh, but the API endpoint was returning 500 errors. The progress appeared static because the API calls were failing.

### Root Cause
The backend endpoint `/api/v1/documents/{doc_id}/pipeline` was returning datetime objects for `started_at` and `completed_at` fields, but the Pydantic model expected string values.

**Error**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for PipelineStatusResponse
started_at
  Input should be a valid string [type=string_type, input_value=datetime.datetime(2025, 11, 19, 6, 30, 28), input_type=datetime]
```

### Solution
Convert datetime objects to ISO format strings before returning the response.

**File**: [src/finagent/api/routes/documents.py:1525-1552](src/finagent/api/routes/documents.py#L1525-L1552)

**Before**:
```python
return PipelineStatusResponse(
    doc_id=document_id,
    filename=doc.filename,
    current_stage=doc.pipeline_stage or "unknown",
    overall_status=doc.pipeline_status or "unknown",
    progress_percentage=progress,
    total_duration_seconds=total_duration,
    stages=stages,
    started_at=doc.pipeline_started_at if isinstance(doc.pipeline_started_at, str) else None,
    completed_at=doc.pipeline_completed_at if isinstance(doc.pipeline_completed_at, str) else None
)
```

**After**:
```python
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
```

### What Changed
1. **Proper datetime handling**: Check if field is datetime object or string
2. **Convert to ISO format**: Use `.isoformat()` for datetime objects
3. **Preserve strings**: If already a string, use as-is
4. **Result**: API returns 200 OK with properly formatted timestamps

---

## How Auto-Refresh Works

The Pipeline Modal has built-in auto-refresh functionality:

**File**: [frontend/src/components/documents/PipelineModal.tsx:21-58](frontend/src/components/documents/PipelineModal.tsx#L21-L58)

```typescript
const [autoRefresh, setAutoRefresh] = useState(true);

useEffect(() => {
  if (!isOpen || !docId) return;

  const fetchPipeline = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE}/api/v1/documents/${docId}/pipeline`);

      if (!response.ok) {
        throw new Error(`Failed to fetch pipeline: ${response.statusText}`);
      }

      const data = await response.json();
      setPipeline(data);

      // Stop auto-refresh if pipeline is complete or failed
      if (data.overall_status === 'success' || data.overall_status === 'failed') {
        setAutoRefresh(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pipeline status');
    } finally {
      setLoading(false);
    }
  };

  fetchPipeline();

  // Auto-refresh every 2 seconds if still in progress
  const interval = autoRefresh
    ? setInterval(fetchPipeline, 2000)
    : undefined;

  return () => {
    if (interval) clearInterval(interval);
  };
}, [docId, isOpen, autoRefresh]);
```

**Key Features**:
- ✅ Polls every 2 seconds when modal is open
- ✅ Automatically stops when status is 'success' or 'failed'
- ✅ Shows loading spinner on first load
- ✅ Displays errors if API fails
- ✅ Cleanup interval on unmount

---

## Testing Results

### Before Fixes
❌ Modal background: Solid black, harsh appearance
❌ Progress: Static, no updates
❌ API calls: 500 errors every 2 seconds
❌ Console: ValidationError for datetime fields

### After Fixes
✅ Modal background: Blur effect, elegant appearance
✅ Progress: Live updates every 2 seconds
✅ API calls: 200 OK responses
✅ Console: No errors
✅ Auto-refresh: Stops when complete

### Test Scenario: View Pipeline for Indexed Document

1. ✅ User opens document list (文件管理 page)
2. ✅ User clicks Activity button (處理進度) on any document
3. ✅ Modal opens with blur background
4. ✅ Pipeline data loads immediately
5. ✅ Progress bar shows current stage
6. ✅ Auto-refresh polls every 2 seconds
7. ✅ Progress updates in real-time
8. ✅ When status = 'success', auto-refresh stops
9. ✅ User can close modal

---

## Visual Comparison

### Background Effect

**Before (Black)**:
```css
bg-black bg-opacity-50
/* Result: Solid black with 50% opacity */
```

**After (Blur)**:
```css
backdrop-blur-sm bg-black/30
/* Result: Blurred background with 30% black overlay */
```

### API Response

**Before (Error)**:
```json
{
  "detail": [
    {
      "type": "string_type",
      "msg": "Input should be a valid string",
      "input": "datetime.datetime(2025, 11, 19, 6, 30, 28)"
    }
  ]
}
```

**After (Success)**:
```json
{
  "doc_id": "doc_7e2dc5f2",
  "filename": "document.txt",
  "current_stage": "complete",
  "overall_status": "success",
  "progress_percentage": 100,
  "total_duration_seconds": 45.3,
  "stages": [...],
  "started_at": "2025-11-19T06:30:28",
  "completed_at": "2025-11-19T06:31:13"
}
```

---

## Files Modified

### Frontend
1. **[frontend/src/components/documents/PipelineModal.tsx](frontend/src/components/documents/PipelineModal.tsx)** (line 63)
   - Changed background from `bg-black bg-opacity-50` to `backdrop-blur-sm bg-black/30`

### Backend
2. **[src/finagent/api/routes/documents.py](src/finagent/api/routes/documents.py)** (lines 1525-1552)
   - Added datetime to ISO string conversion
   - Fixed `started_at` and `completed_at` field handling

---

## Related Components

The Pipeline Modal uses these child components:

1. **[PipelineProgress.tsx](frontend/src/components/documents/PipelineProgress.tsx)**
   - Shows progress bar with percentage
   - Displays stage icons (✅ ⏳ ❌)
   - Color-coded status badges

2. **[PipelineTimeline.tsx](frontend/src/components/documents/PipelineTimeline.tsx)**
   - Shows detailed timeline of all stages
   - Timing information for each stage
   - Error messages if any stage failed

---

## Backend Logs Confirmation

**Before Fix** (500 errors):
```
INFO:     127.0.0.1:60982 - "GET /api/v1/documents/doc_xxx/pipeline HTTP/1.1" 500 Internal Server Error
pydantic_core._pydantic_core.ValidationError: 1 validation error for PipelineStatusResponse
started_at
  Input should be a valid string [type=string_type, input_value=datetime.datetime(...)]
```

**After Fix** (200 OK):
```
INFO:     127.0.0.1:61546 - "GET /api/v1/documents/doc_7e2dc5f2/pipeline HTTP/1.1" 200 OK
INFO:     127.0.0.1:61612 - "GET /api/v1/documents/doc_xxx/pipeline HTTP/1.1" 200 OK
INFO:     127.0.0.1:61623 - "GET /api/v1/documents/doc_xxx/pipeline HTTP/1.1" 200 OK
```

---

## User Experience Improvements

### Issue 1: Background
**Before**: Harsh black overlay, feels dated
**After**: Modern blur effect, elegant and professional

### Issue 2: Progress Updates
**Before**: Static progress, appears broken
**After**: Live updates every 2 seconds, shows real-time status

---

## Technical Details

### Tailwind Backdrop Blur
- `backdrop-blur-sm` - Applies 4px blur to background
- Requires backdrop-filter support (modern browsers)
- Fallback: `bg-black/30` provides solid color if blur unsupported

### ISO Format Datetime
- `.isoformat()` - Converts datetime to ISO 8601 format
- Example: `2025-11-19T06:30:28` (without timezone)
- Example: `2025-11-19T06:30:28+00:00` (with timezone)
- Compatible with JavaScript `Date.parse()` and `new Date()`

### Auto-Refresh Logic
- Polls every 2 seconds while `autoRefresh === true`
- Stops polling when:
  - Modal closes (`isOpen === false`)
  - Document ID changes
  - Status becomes 'success' or 'failed'
- Cleanup: `clearInterval()` on unmount prevents memory leaks

---

## Known Limitations

1. **No manual refresh button**: User must close and reopen modal to force refresh
2. **Fixed 2-second interval**: Not configurable (could add user preference)
3. **No offline handling**: Doesn't detect network errors vs API errors

These are not critical issues - current implementation works well for typical usage.

---

## Success Criteria

✅ Modal background uses blur effect (not solid black)
✅ Pipeline API returns 200 OK (no ValidationError)
✅ Progress updates every 2 seconds
✅ Auto-refresh stops when complete
✅ Frontend HMR applied changes automatically
✅ Backend auto-reloaded after code change
✅ No breaking changes to other components

**Status**: Both issues completely resolved 🎉

---

## Deployment Notes

**Services Reloaded Automatically**:
- ✅ Frontend: Vite HMR detected changes, hot-reloaded PipelineModal.tsx
- ✅ Backend: Uvicorn detected changes, reloaded documents.py

**No manual restarts needed!**

**Browser**: No hard refresh required, changes applied immediately

---

## Future Enhancements (Not Implemented)

Could add in future:
1. **Manual refresh button**: Force refresh without closing modal
2. **Configurable poll interval**: User preference for refresh speed
3. **Pause/Resume button**: Stop auto-refresh without closing
4. **Progress notifications**: Alert when pipeline completes
5. **Retry failed stages**: Button to retry if stage fails
6. **Stage duration chart**: Visual timeline of stage durations

None of these are urgent - current implementation meets requirements.
