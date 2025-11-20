# Unimplemented Tasks Report

Generated: 2025-11-19 via Playwright UI exploration

## Summary

Found **8 missing features on Documents page** and **6 missing features on Wiki page**, plus **2 API issues**.

Total: **16 unimplemented tasks**

---

## Documents Page Issues (8 tasks)

### 1. Missing Metadata Status Indicators ⚠️ HIGH PRIORITY

**Current State**: Document cards do not show metadata extraction status

**Expected**:
- Status badges showing: `pending` / `processing` / `completed` / `failed` / `user_edited`
- Visual indicators:
  - ⏳ 元數據: 待處理 (Metadata: Pending)
  - 🔄 元數據: 處理中 (Metadata: Processing)
  - ✅ 元數據: 已提取 (Metadata: Extracted)
  - ❌ 元數據: 失敗 (Metadata: Failed)
  - ✏️ 元數據: 使用者編輯 (Metadata: User Edited)

**Files to modify**:
- `frontend/src/components/documents/DocumentList.tsx`
- `frontend/src/components/documents/DocumentCard.tsx` (if exists)
- `frontend/src/types/documents.ts` (add metadata status fields)

---

### 2. Missing Re-extract Metadata Button ⚠️ HIGH PRIORITY

**Current State**: No button to trigger metadata re-extraction

**Expected**:
- "重新提取元數據" button on each document
- Shows for documents with status: `failed` or `pending`
- Triggers API: `POST /api/v1/documents/{doc_id}/metadata/extract`

**Implementation**:
```tsx
<button onClick={() => handleReextract(doc.id)}>
  重新提取元數據
</button>
```

**Files to modify**:
- `frontend/src/components/documents/DocumentList.tsx`

---

### 3. Missing Batch Operations ⚠️ MEDIUM PRIORITY

**Current State**: No batch re-extraction functionality

**Expected**:
- "批次重新提取" button above document list
- Triggers API: `POST /api/v1/documents/metadata/extract-batch`
- Options:
  - Extract all pending
  - Extract all failed
  - Extract selected documents

**Files to modify**:
- `frontend/src/components/documents/DocumentList.tsx`
- New component: `frontend/src/components/documents/BatchOperations.tsx`

---

### 4. Missing Metadata Editor ⚠️ HIGH PRIORITY

**Current State**: No UI to view/edit document metadata

**Expected**: Modal or detail page showing:
- document_type (dropdown: 裁罰書/判決書/法規/新聞報導)
- issuing_authority (dropdown: 金管會/中央銀行/公平會)
- related_institutions (tags input)
- violation_types (tags input)
- penalty_amount (text input)
- keywords (tags input)
- Edit and Save buttons

**Implementation**:
```tsx
<MetadataEditorModal
  docId={selectedDoc.id}
  metadata={selectedDoc.metadata}
  onSave={handleMetadataSave}
  onClose={() => setShowEditor(false)}
/>
```

**Files to create**:
- `frontend/src/components/documents/MetadataEditorModal.tsx`
- API endpoint: `PATCH /api/v1/documents/{doc_id}/metadata`

---

### 5. Missing Extraction Confidence Score ⚠️ LOW PRIORITY

**Current State**: No display of metadata extraction confidence

**Expected**:
- Confidence score shown for each document
- Format: "信心分數: 0.95" or "95%"
- Color coding:
  - Green (>0.8): High confidence
  - Yellow (0.5-0.8): Medium confidence
  - Red (<0.5): Low confidence

**Files to modify**:
- `frontend/src/components/documents/DocumentList.tsx`
- `frontend/src/types/documents.ts` (add `extraction_confidence` field)

---

### 6. Missing Indexed Status Display ⚠️ MEDIUM PRIORITY

**Current State**: Document cards don't show if document is indexed (searchable)

**Expected**:
- Badge showing "✅ 已索引" or "Indexed"
- Badge showing "⏳ 索引中" if indexing in progress

**Note**: This is separate from metadata status. Indexed = searchable, Metadata = categorized.

**Files to modify**:
- `frontend/src/components/documents/DocumentList.tsx`
- `frontend/src/types/documents.ts` (ensure `indexed` field exists)

---

### 7. Missing Metadata Status in Document Cards ⚠️ HIGH PRIORITY

**Current State**: Document card HTML does not include metadata extraction status

**Expected**: Each document card shows both:
1. Indexed status (searchable or not)
2. Metadata status (pending/processing/completed/failed/user_edited)

**Example**:
```
📄 yushan_aml_penalty.txt
   [✅ 已索引] [✅ 元數據: 已提取] (信心: 0.95)
   123 個區塊 | 2025-01-19
```

**Files to modify**:
- `frontend/src/components/documents/DocumentList.tsx`

---

### 8. Missing Metadata Extraction Monitor Dashboard ⚠️ MEDIUM PRIORITY

**Current State**: No dashboard showing extraction progress across all documents

**Expected**: Dashboard card showing:
```
元數據提取狀態
━━━━━━━━━━━━━━━━━━━
總文件數: 100
已索引: 100 (100%)
已提取元數據: 45 (45%)

狀態明細:
  ⏳ 待處理: 40
  🔄 處理中: 5
  ✅ 已完成: 45
  ❌ 失敗: 10

[批次重新提取失敗的文件]
```

**Files to create**:
- `frontend/src/components/documents/MetadataMonitor.tsx`
- API endpoint: `GET /api/v1/documents/metadata/status`

---

## Wiki Page Issues (6 tasks)

### 9. Missing Category Breakdown UI ⚠️ HIGH PRIORITY

**Current State**: No visual breakdown by document type, authority, institution, violation

**Expected**: Category cards showing:
```
依文件類型
裁罰書: 50
判決書: 30
法規: 20
新聞報導: 15

依發文機關
金管會: 60
中央銀行: 25
公平會: 15

依相關機構
玉山銀行: 10
中國信託: 8
國泰世華: 6

依違規類型
洗錢防制: 15
內部控制: 12
資訊揭露: 8
```

**Files to modify**:
- `frontend/src/pages/WikiPage.tsx`
- Create: `frontend/src/components/wiki/CategoryBreakdown.tsx`

---

### 10. Missing Metadata Extraction Statistics ⚠️ MEDIUM PRIORITY

**Current State**: No display of extraction progress/coverage

**Expected**: Stats card showing:
```
元數據提取統計
━━━━━━━━━━━━━━━━
總文件數: 100
已提取元數據: 45
未提取元數據: 55
提取覆蓋率: 45%

平均信心分數: 0.87
低信心文件: 5
使用者編輯: 3
```

**Files to modify**:
- `frontend/src/pages/WikiPage.tsx`
- API: Enhance `/api/v1/wiki/overview` response

---

### 11. Missing Search/Filter Functionality ⚠️ MEDIUM PRIORITY

**Current State**: No search box to filter wiki entries

**Expected**:
- Search input to filter by category name, institution, violation type
- Real-time filtering as user types
- Clear button to reset filter

**Files to create**:
- Add search input to `frontend/src/pages/WikiPage.tsx`
- Implement client-side filtering or API-based search

---

### 12. Missing Clickable Category Navigation ⚠️ HIGH PRIORITY

**Current State**: Categories are not clickable/interactive

**Expected**:
- Click "金管會" → Show all documents from 金管會
- Click "洗錢防制" → Show all documents about AML violations
- Click category → Navigate to filtered document list or query page

**Implementation**:
```tsx
<button onClick={() => handleCategoryClick('authority', '金管會')}>
  金管會 (60)
</button>
```

**Files to modify**:
- `frontend/src/pages/WikiPage.tsx`
- May integrate with query page or document list with filters

---

### 13. Missing Timeline/Date Filtering ⚠️ LOW PRIORITY

**Current State**: No way to filter documents by date range or year

**Expected**:
- Timeline showing document counts by year/quarter
- Date range picker
- Trend visualization

**Example**:
```
2018: ████ 10
2019: ██████ 15
2020: ████████████ 25
2021: ██████████████ 30
2022: ████████ 20
```

**Files to create**:
- `frontend/src/components/wiki/Timeline.tsx`

---

### 14. Missing Metadata Quality Indicators ⚠️ LOW PRIORITY

**Current State**: No indication of extraction quality or confidence

**Expected**: Quality indicators showing:
- Average confidence score across all documents
- Number of low-confidence extractions (<0.5)
- User edit count
- Failed extraction count

**Files to modify**:
- `frontend/src/pages/WikiPage.tsx`
- API: Enhance `/api/v1/wiki/overview` with quality metrics

---

## API Issues (2 tasks)

### 15. ✅ COMPLETED - Metadata Status Fields in Documents API Response

**Status**: IMPLEMENTED ✅ (2025-11-19)

**What was done**:
- Updated `DocumentResponse` model with all metadata status fields
- Updated `_metadata_to_response()` function to populate fields from database
- Verified API returns all required fields correctly

**Files modified**:
- ✅ `src/finagent/api/routes/documents.py` - Updated `DocumentResponse` model (lines 74-82)
- ✅ `src/finagent/api/routes/documents.py` - Updated `_metadata_to_response()` function (lines 135-202)

**Test Results**:
```
✅ All metadata status fields present in DocumentResponse:
  - metadata_extracted: bool
  - metadata_extraction_status: str (pending/processing/completed/failed/user_edited)
  - metadata_extraction_error: str | None
  - metadata_extraction_attempts: int
  - metadata_last_extracted_at: str | None
  - metadata_edited_by_user: bool
  - extraction_confidence: float | None
  - issuing_authority: str | None
  - related_institutions: list[str] | None
  - violation_types: list[str] | None
  - penalty_amount: str | None
  - keywords: list[str] | None
```

---

### 16. ✅ COMPLETED - Metadata Status Monitoring API Endpoint

**Status**: IMPLEMENTED ✅ (2025-11-19)

**What was done**:
- Created `MetadataStatusResponse` and `FailedDocument` models
- Implemented `GET /api/v1/documents/metadata/status` endpoint
- Calculates statistics across all documents
- Returns status breakdown, failed documents, and confidence metrics

**Files modified**:
- ✅ `src/finagent/api/routes/documents.py` - Added endpoint (lines 915-1014)

**Test Results**:
```
✅ Endpoint: GET /api/v1/documents/metadata/status
✅ Status Code: 200
✅ Response includes:
  - total_documents: 29
  - indexed: 29 (100%)
  - metadata_extracted: 0 (0%)
  - by_status: {pending: 29, processing: 0, completed: 0, failed: 0, user_edited: 0}
  - failed_documents: []
  - average_confidence: null
  - low_confidence_count: 0
```

---

## Additional API Endpoints Needed

These were specified in documentation but not yet implemented:

### 17. ✅ COMPLETED - Re-extract Single Document API

**Status**: IMPLEMENTED ✅ (2025-11-19)

**Endpoint**: `POST /api/v1/documents/{document_id}/metadata/extract`

**What was done**:
- Created `MetadataExtractRequest` and `MetadataExtractResponse` models
- Implemented extraction workflow with status tracking
- Added `extract_metadata()` wrapper to MetadataExtractor
- Updates status: pending → processing → completed/failed
- Tracks attempts and errors

**Files modified**:
- ✅ `src/finagent/api/routes/documents.py` (lines 1052-1181)
- ✅ `src/finagent/document_processing/metadata_extractor.py` (lines 478-517)
- ✅ `src/finagent/database/db.py` (lines 471-526)

### 18. Batch Re-extract
- **Endpoint**: `POST /api/v1/documents/metadata/extract-batch`
- **Purpose**: Batch metadata extraction with filters
- **Priority**: MEDIUM
- **Status**: NOT IMPLEMENTED (can be added later if needed)

### 19. ✅ COMPLETED - User Edit Metadata API

**Status**: IMPLEMENTED ✅ (2025-11-19)

**Endpoint**: `PATCH /api/v1/documents/{document_id}/metadata`

**What was done**:
- Created `MetadataUpdateRequest` and `MetadataUpdateResponse` models
- Implements partial updates (only non-None fields updated)
- Automatically marks as "user_edited" status
- Returns list of updated fields

**Files modified**:
- ✅ `src/finagent/api/routes/documents.py` (lines 1184-1289)
- ✅ `src/finagent/database/db.py` (updated add_document upsert)

**Test Results**:
```
✅ PATCH /api/v1/documents/{id}/metadata
✅ Updated 3 fields successfully
✅ Status changed to "user_edited"
✅ User edited flag set to True
```

### 20. Reset to LLM Extraction
- **Endpoint**: `POST /api/v1/documents/{doc_id}/metadata/reset`
- **Purpose**: Reset user edits and re-extract with LLM
- **Priority**: LOW

---

## Priority Summary

### 🔴 HIGH PRIORITY (10 tasks)

1. Metadata status indicators in document cards
2. Re-extract metadata button
3. Metadata editor modal
4. Metadata status in document cards
5. Category breakdown UI on wiki
6. Clickable category navigation
7. Add metadata status fields to Documents API
8. Implement metadata status API endpoint
9. Implement re-extract single document API
10. Implement user edit metadata API

### 🟡 MEDIUM PRIORITY (5 tasks)

11. Batch operations UI
12. Indexed status display
13. Metadata extraction monitor dashboard
14. Metadata extraction statistics on wiki
15. Search/filter functionality on wiki
16. Implement batch re-extract API

### 🟢 LOW PRIORITY (5 tasks)

17. Extraction confidence score display
18. Timeline/date filtering
19. Metadata quality indicators
20. Reset to LLM extraction API

---

## Implementation Order Recommendation

### Phase 1: Backend API Foundation (Week 1)
1. Add metadata status fields to Documents API response (#15)
2. Implement metadata status monitoring API (#16)
3. Implement re-extract single document API (#17)
4. Implement user edit metadata API (#19)

### Phase 2: Document Page UI (Week 2)
5. Add metadata status indicators to document cards (#1, #7)
6. Add re-extract button (#2)
7. Create metadata editor modal (#4)
8. Add indexed status display (#6)

### Phase 3: Wiki Page UI (Week 3)
9. Add category breakdown UI (#9)
10. Make categories clickable (#12)
11. Add metadata extraction statistics (#10)
12. Add search/filter functionality (#11)

### Phase 4: Advanced Features (Week 4)
13. Batch operations (#3)
14. Metadata monitor dashboard (#8)
15. Confidence score display (#5)
16. Quality indicators (#14)
17. Timeline/date filtering (#13)

---

## Testing Recommendations

### E2E Tests Needed

1. **test-metadata-status-display.spec.ts**
   - Verify status badges appear
   - Check status transitions (pending → processing → completed)

2. **test-metadata-reextract.spec.ts**
   - Click re-extract button
   - Verify status changes to processing
   - Wait for completion

3. **test-metadata-editor.spec.ts**
   - Open editor modal
   - Edit metadata fields
   - Save and verify API call
   - Check status changes to user_edited

4. **test-wiki-categories.spec.ts**
   - Verify categories display
   - Click category
   - Verify filtered results

5. **test-batch-operations.spec.ts**
   - Select multiple documents
   - Click batch re-extract
   - Monitor progress

---

## Screenshots Captured

Playwright test captured screenshots showing current state:

1. `test-results/documents-page-full.png` - Full documents page
2. `test-results/wiki-page-full.png` - Full wiki page

Review these to understand current UI layout before implementing changes.

---

## Notes

- ✅ No browser console errors found - UI is stable
- ⚠️ Wiki API returns `with_metadata: undefined` - may need backend fix
- ✅ Documents API working (29 documents)
- ✅ Backend migration successful (new columns exist in database)
- ⚠️ All 29 documents are indexed but 0 have metadata extracted (all status: pending)

**Action needed**: Need to trigger metadata extraction for existing documents to populate wiki categories.
