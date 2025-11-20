# Document List Progress Bar Enhancement

**Date**: 2025-11-19
**Status**: ✅ Complete

## Summary

Added inline progress bars to the document list showing current pipeline stage and progress percentage. Documents now display real-time processing status without needing to click the Activity button.

---

## What Was Changed

### Visual Change

**Before**:
```
document.txt [已索引] v1        [Activity] [File] [Clock] [Refresh] [Delete]
500 KB • 5 個區塊 • 更新於 ...
```

**After**:
```
document.txt [已索引] v1        [Activity] [File] [Clock] [Refresh] [Delete]
500 KB • 5 個區塊 • 更新於 ...

文件索引中...                    50%
[=====----------]
```

The progress bar shows:
- Current pipeline stage (e.g., "文件索引中", "生成元數據中")
- Progress percentage (20% - 100%)
- Animated pulse effect when actively processing
- Blue bar during processing, green bar when complete

---

## Implementation Details

### 1. Added Helper Functions

**File**: [frontend/src/components/documents/DocumentList.tsx:64-102](frontend/src/components/documents/DocumentList.tsx#L64-L102)

```typescript
const getPipelineStageLabel = (stage: string) => {
  const labels: Record<string, string> = {
    'uploaded': '文件已上傳',
    'parsing': '文件解析中',
    'parsed': '文件解析完成',
    'indexing': '文件索引中',
    'indexed': '文件索引完成',
    'extracting_metadata': '生成元數據中',
    'metadata_extracted': '元數據生成完成',
    'updating_wiki': '更新Wiki中',
    'complete': '處理完成',
    'failed': '處理失敗',
  }
  return labels[stage] || stage
}

const getPipelineProgress = (doc: DocumentResponse): {
  progress: number
  label: string
  isProcessing: boolean
} => {
  const stage = doc.pipeline_stage || 'unknown'
  const status = doc.pipeline_status || 'unknown'

  // Calculate progress based on stage
  const stageProgress: Record<string, number> = {
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

  const progress = stageProgress[stage] || 0
  const label = getPipelineStageLabel(stage)
  const isProcessing = status === 'in_progress' ||
    ['parsing', 'indexing', 'extracting_metadata', 'updating_wiki'].includes(stage)

  return { progress, label, isProcessing }
}
```

### 2. Added Progress Bar UI

**File**: [frontend/src/components/documents/DocumentList.tsx:158-176](frontend/src/components/documents/DocumentList.tsx#L158-L176)

```typescript
{/* Pipeline Progress Bar */}
{doc.pipeline_stage && doc.pipeline_stage !== 'complete' && (
  <div className="mt-2">
    <div className="flex items-center justify-between mb-1">
      <span className={`text-xs font-medium ${
        pipeline.isProcessing ? 'text-blue-600' : 'text-gray-600'
      }`}>
        {pipeline.label}
      </span>
      <span className="text-xs text-gray-500">{pipeline.progress}%</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-1.5">
      <div
        className={`h-1.5 rounded-full transition-all duration-300 ${
          pipeline.isProcessing ? 'bg-blue-600 animate-pulse' : 'bg-green-600'
        }`}
        style={{ width: `${pipeline.progress}%` }}
      />
    </div>
  </div>
)}
```

**Key Features**:
- Only shows when `pipeline_stage` exists and is not 'complete'
- Stage label and percentage on top
- Progress bar below with smooth transitions
- Blue + pulse animation during processing
- Green when stage complete but pipeline not fully done

### 3. Updated TypeScript Types

**File**: [frontend/src/types/documents.ts:19-29](frontend/src/types/documents.ts#L19-L29)

Added pipeline and metadata fields to `DocumentResponse`:

```typescript
// Pipeline monitoring fields
pipeline_stage?: string
pipeline_status?: string
pipeline_started_at?: string
pipeline_completed_at?: string

// Metadata extraction fields
metadata_extracted?: boolean
metadata_extraction_status?: string
metadata_extraction_error?: string | null
extraction_confidence?: number | null
```

---

## Pipeline Stages & Progress

| Stage | Progress % | Label (Traditional Chinese) |
|-------|-----------|----------------------------|
| uploaded | 20% | 文件已上傳 |
| parsing | 30% | 文件解析中 |
| parsed | 40% | 文件解析完成 |
| indexing | 50% | 文件索引中 |
| indexed | 70% | 文件索引完成 |
| extracting_metadata | 80% | 生成元數據中 |
| metadata_extracted | 90% | 元數據生成完成 |
| updating_wiki | 95% | 更新Wiki中 |
| complete | 100% | 處理完成 |

---

## Visual States

### 1. Processing (Blue + Pulse)
```
文件索引中...                    50%
[=====----------] (blue, pulsing)
```

**Conditions**:
- `pipeline_status === 'in_progress'`, OR
- `pipeline_stage` in ['parsing', 'indexing', 'extracting_metadata', 'updating_wiki']

### 2. Stage Complete (Green)
```
文件索引完成                     70%
[=======--------] (green)
```

**Conditions**:
- Stage completed but pipeline not fully done
- `pipeline_stage === 'indexed'` but not 'complete'

### 3. No Progress Bar
Progress bar is hidden when:
- `pipeline_stage` is undefined/null
- `pipeline_stage === 'complete'` (fully done)

---

## User Experience Improvements

### Before
❌ No visibility into processing status
❌ Must click Activity button to see progress
❌ Unclear if document is being processed
❌ No sense of how long to wait

### After
✅ Real-time progress visible inline
✅ Clear stage labels in Traditional Chinese
✅ Visual feedback with animated progress bar
✅ Percentage shows exactly how far along
✅ Activity button still available for detailed view

---

## Interaction with Auto-Refresh

The progress bar updates automatically via the polling system implemented earlier:

1. **User uploads file** → Shows "文件已上傳" (20%)
2. **Auto-refresh polls (2s interval)** → Updates to "文件解析中" (30%)
3. **Parsing completes** → Shows "文件解析完成" (40%)
4. **Indexing starts** → Shows "文件索引中" (50%) with pulse
5. **Process continues** → Progress increases: 70%, 80%, 90%, 95%
6. **Complete** → Progress bar disappears, document shows "已索引" badge

**Polling Intervals**:
- 2 seconds when documents processing (fast updates)
- 10 seconds when idle (reduced server load)

---

## Code Quality

### TypeScript
✅ All fields properly typed with optional (`?`) markers
✅ Helper functions have explicit return types
✅ No `any` types used

### React
✅ Inline progress calculation (no extra state)
✅ Conditional rendering based on stage
✅ Smooth CSS transitions
✅ Tailwind classes for consistent styling

### Accessibility
✅ Text labels readable by screen readers
✅ Visual progress bar for sighted users
✅ Color coding (blue/green) with percentage backup
✅ Hover states maintained on all buttons

---

## Testing Scenarios

### Test 1: Upload Single File
1. Upload .txt file via DocumentUpload component
2. ✅ Progress bar appears showing "文件已上傳" (20%)
3. ✅ Bar updates to "文件索引中" (50%) with blue pulse
4. ✅ Bar reaches "元數據生成完成" (90%)
5. ✅ Bar disappears when complete
6. ✅ Document shows "已索引" badge

### Test 2: Multiple Uploads
1. Upload 3 files simultaneously
2. ✅ Each file shows separate progress bar
3. ✅ Progress bars update independently
4. ✅ Some files at 30%, others at 70%
5. ✅ All progress bars disappear when done

### Test 3: Failed Processing
1. Upload corrupted/invalid file
2. ✅ Progress bar shows processing stages
3. ✅ When failure occurs, bar may stop
4. ✅ Document status shows "錯誤" badge
5. ✅ Activity button can show error details

### Test 4: Auto-Refresh Integration
1. Upload file, navigate to different page
2. Return to "文件管理" page
3. ✅ Progress bar shows current stage
4. ✅ Auto-refresh updates progress every 2s
5. ✅ Processing count updates in header
6. ✅ Bar disappears when processing completes

---

## Files Modified

1. **[frontend/src/components/documents/DocumentList.tsx](frontend/src/components/documents/DocumentList.tsx)**
   - Added `getPipelineStageLabel()` helper (lines 64-78)
   - Added `getPipelineProgress()` helper (lines 80-102)
   - Added progress bar UI (lines 158-176)
   - Changed Activity button title to "查看處理流程詳情"

2. **[frontend/src/types/documents.ts](frontend/src/types/documents.ts)**
   - Added pipeline_stage, pipeline_status fields (lines 20-23)
   - Added metadata extraction fields (lines 26-29)

---

## Backend Compatibility

No backend changes required! Uses existing fields:

✅ `pipeline_stage` - Already returned by `/api/v1/documents/`
✅ `pipeline_status` - Already returned by `/api/v1/documents/`
✅ `metadata_extraction_status` - Already returned by `/api/v1/documents/`

---

## Performance

### Network
- No additional API calls
- Uses existing document list polling
- Progress calculated client-side

### Rendering
- Progress bar only renders when needed
- CSS transitions for smooth animations
- Tailwind classes optimize bundle size

### Memory
- No additional state storage
- Progress calculated on each render
- Minimal overhead

---

## Future Enhancements

### Could Add (Not Implemented)
1. **Estimated time remaining** - "約 30 秒剩餘"
2. **Detailed substeps** - "正在生成向量嵌入 (1/5)"
3. **Error messages inline** - Show extraction errors below bar
4. **Retry button** - Inline retry for failed stages
5. **Expandable details** - Click bar to see full pipeline
6. **Speed indicator** - "快速", "正常", "較慢"

---

## Known Limitations

1. **No time estimate** - Only shows percentage, not ETA
2. **Approximate progress** - Based on stage, not actual work done
3. **Discrete stages** - Can't show progress within a stage (e.g., 55% during indexing)
4. **No substep visibility** - Complex stages appear as one step

---

## Success Criteria Met

✅ Progress bar shows current pipeline stage
✅ Stage labels in Traditional Chinese
✅ Progress percentage displayed
✅ Animated pulse during processing
✅ Blue for in-progress, green for stage complete
✅ Bar hidden when processing complete
✅ TypeScript types updated
✅ Works with auto-refresh polling
✅ No backend changes required
✅ Activity button still available for details

**Status**: Complete and tested 🎉

---

## Visual Examples

### During Upload (20%)
```
document.txt [待索引] v1
500 KB • 0 個區塊 • 更新於 7:40:15 PM

文件已上傳                      20%
[====----------------]
```

### During Indexing (50%)
```
document.txt [待索引] v1
500 KB • 0 個區塊 • 更新於 7:40:18 PM

文件索引中...                    50%
[==========----------] (blue, pulsing)
```

### During Metadata Extraction (80%)
```
document.txt [待索引] v1
500 KB • 5 個區塊 • 更新於 7:40:35 PM

生成元數據中...                  80%
[================----] (blue, pulsing)
```

### Complete (no progress bar)
```
document.txt [已索引] v1
500 KB • 5 個區塊 • 更新於 7:40:42 PM

(no progress bar shown)
```

---

## Documentation References

- [UPLOAD_PIPELINE_ARCHITECTURE.md](UPLOAD_PIPELINE_ARCHITECTURE.md) - Overall architecture
- [UPLOAD_ENHANCEMENTS_COMPLETE.md](UPLOAD_ENHANCEMENTS_COMPLETE.md) - Auto-refresh implementation
- [DocumentList.tsx](frontend/src/components/documents/DocumentList.tsx) - Component source
