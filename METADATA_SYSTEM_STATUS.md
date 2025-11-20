# Metadata System Implementation Status

⚠️ **NOTE**: This is a supporting reference for **Checkpoint 6.2.1** in [V1_0_RELEASE_PLAN.md](V1_0_RELEASE_PLAN.md)

**Source of Truth**: [V1_0_RELEASE_PLAN.md](V1_0_RELEASE_PLAN.md) - Checkpoint 6.2.1

**Last Updated**: 2025-11-19
**Backend Progress**: 4/4 tasks (100% complete)
**Frontend Progress**: 0/16 tasks (0% complete)

---

## Quick Summary

### ✅ Completed (4 tasks)
1. **Backend API**: Metadata status fields in DocumentResponse
2. **Backend API**: Metadata status monitoring endpoint
3. **Backend API**: Single document metadata extraction endpoint
4. **Backend API**: User metadata editing endpoint

### 🚧 In Progress (0 tasks)
None

### ⏳ Remaining (16 tasks)
- 8 Frontend UI tasks (Documents page)
- 6 Frontend UI tasks (Wiki page)
- 2 Backend API tasks (lower priority)

---

## Phase 1: Backend Foundation ✅ COMPLETE

### Database Schema ✅
**File**: `src/finagent/database/schema.sql`
**Status**: Migrated successfully

Added 7 columns to `documents` table:
```sql
metadata_extracted BOOLEAN DEFAULT 0
metadata_extraction_status TEXT DEFAULT 'pending'
metadata_extraction_error TEXT
metadata_extraction_attempts INTEGER DEFAULT 0
metadata_last_extracted_at TIMESTAMP
metadata_edited_by_user BOOLEAN DEFAULT 0
extraction_confidence REAL
```

### Database Models ✅
**File**: `src/finagent/database/models.py` (lines 76-83)
**Status**: Complete

Updated `Document` model with metadata status fields.

### Database Operations ✅
**File**: `src/finagent/database/db.py` (lines 471-526)
**Status**: Complete

Updated `add_document()` to handle metadata status fields in INSERT and UPDATE.

### API Endpoints ✅

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/documents/` | GET | List documents with metadata status | ✅ |
| `/api/v1/documents/{id}` | GET | Get single document with metadata status | ✅ |
| `/api/v1/documents/metadata/status` | GET | Metadata extraction statistics | ✅ |
| `/api/v1/documents/{id}/metadata/extract` | POST | Extract metadata via LLM | ✅ |
| `/api/v1/documents/{id}/metadata` | PATCH | Edit metadata manually | ✅ |

---

## Phase 2: Frontend UI (Documents Page) ⏳ NOT STARTED

**Priority**: HIGH
**Estimated Effort**: 2-3 days

### Task 1: Metadata Status Badges
**Priority**: HIGH
**Files**: `frontend/src/components/documents/DocumentList.tsx`

Add status badges to document cards:
- ⏳ Pending (gray)
- 🔄 Processing (blue)
- ✅ Completed (green)
- ❌ Failed (red)
- ✏️ User Edited (purple)

**API Used**: Document fields from existing endpoints

---

### Task 2: Re-extract Button
**Priority**: HIGH
**Files**: `frontend/src/components/documents/DocumentList.tsx`

Add "重新提取元數據" button:
- Show only for documents with status: `pending` or `failed`
- Calls: `POST /api/v1/documents/{id}/metadata/extract`
- Updates UI after extraction completes

**Implementation**:
```tsx
{(doc.metadata_extraction_status === 'pending' ||
  doc.metadata_extraction_status === 'failed') && (
  <button onClick={() => handleReextract(doc.id)}>
    🔄 重新提取元數據
  </button>
)}
```

---

### Task 3: Metadata Editor Modal
**Priority**: HIGH
**Files**: `frontend/src/components/documents/MetadataEditorModal.tsx` (NEW)

Create modal with form fields:
- `document_type`: Dropdown (裁罰書, 判決書, 法規, 新聞, 研究報告, 其他)
- `issuing_authority`: Dropdown (金管會, 銀行局, 證券期貨局, 保險局, 中央銀行, 公平會)
- `related_institutions`: Tags input (多個機構名稱)
- `violation_types`: Tags input (違規類型)
- `penalty_amount`: Text input
- `keywords`: Tags input
- Save/Cancel buttons

**API Used**: `PATCH /api/v1/documents/{id}/metadata`

---

### Task 4: Indexed Status Display
**Priority**: MEDIUM
**Files**: `frontend/src/components/documents/DocumentList.tsx`

Add badge showing indexing status:
- ✅ 已索引 (indexed = true, green)
- ⏳ 未索引 (indexed = false, gray)

**Note**: Separate from metadata extraction status.

---

### Task 5: Confidence Score Display
**Priority**: LOW
**Files**: `frontend/src/components/documents/DocumentList.tsx`

Show extraction confidence:
- Format: "信心分數: 0.95" or "95%"
- Color coding:
  - Green (>0.8): High confidence
  - Yellow (0.5-0.8): Medium confidence
  - Red (<0.5): Low confidence

---

### Task 6: Batch Operations Panel
**Priority**: MEDIUM
**Files**: `frontend/src/components/documents/BatchOperations.tsx` (NEW)

Add panel above document list:
- Select multiple documents (checkboxes)
- "批次重新提取" button
- Options: Extract all pending, Extract all failed, Extract selected

---

### Task 7: Metadata Monitor Dashboard
**Priority**: MEDIUM
**Files**: `frontend/src/components/documents/MetadataMonitor.tsx` (NEW)

Dashboard card showing:
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

**API Used**: `GET /api/v1/documents/metadata/status`

---

### Task 8: Extraction Attempt Counter
**Priority**: LOW
**Files**: `frontend/src/components/documents/DocumentList.tsx`

Show extraction attempts for failed documents:
- Format: "嘗試次數: 3"
- Only show for `failed` status

---

## Phase 3: Frontend UI (Wiki Page) ⏳ NOT STARTED

**Priority**: HIGH
**Estimated Effort**: 2-3 days

### Task 9: Category Breakdown UI
**Priority**: HIGH
**Files**: `frontend/src/pages/WikiPage.tsx`, `frontend/src/components/wiki/CategoryBreakdown.tsx` (NEW)

Display categories with counts:
```
依文件類型
裁罰書: 50
判決書: 30
法規: 20

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

**Data Source**: Aggregate from `GET /api/v1/documents/` response

---

### Task 10: Clickable Categories
**Priority**: HIGH
**Files**: `frontend/src/pages/WikiPage.tsx`

Make categories interactive:
- Click "金管會" → Filter documents by issuing_authority
- Click "洗錢防制" → Filter documents by violation_type
- Navigation options:
  - Show filtered list in modal
  - Navigate to Documents page with filter
  - Open query page with pre-filled search

---

### Task 11: Metadata Extraction Statistics
**Priority**: MEDIUM
**Files**: `frontend/src/pages/WikiPage.tsx`

Stats card on Wiki page:
```
元數據提取統計
━━━━━━━━━━━━━━━━
總文件數: 100
已提取元數據: 45
提取覆蓋率: 45%

平均信心分數: 0.87
低信心文件: 5
使用者編輯: 3
```

**API Used**: `GET /api/v1/documents/metadata/status`

---

### Task 12: Search/Filter on Wiki
**Priority**: MEDIUM
**Files**: `frontend/src/pages/WikiPage.tsx`

Add search input:
- Filter by category name, institution, violation type
- Real-time filtering as user types
- Clear button to reset

---

### Task 13: Timeline/Date Filtering
**Priority**: LOW
**Files**: `frontend/src/components/wiki/Timeline.tsx` (NEW)

Timeline showing document counts by year:
```
2018: ████ 10
2019: ██████ 15
2020: ████████████ 25
2021: ██████████████ 30
2022: ████████ 20
```

---

### Task 14: Quality Indicators
**Priority**: LOW
**Files**: `frontend/src/pages/WikiPage.tsx`

Show metadata quality metrics:
- Average confidence score
- Number of low-confidence extractions (<0.5)
- User edit count
- Failed extraction count

---

## Phase 4: Backend Enhancements ⏳ OPTIONAL

### Task 15: Batch Re-extract API
**Priority**: MEDIUM
**Endpoint**: `POST /api/v1/documents/metadata/extract-batch`

Extract metadata for multiple documents:
- Request: `{ doc_ids: [...], filter: "pending" | "failed" | "all" }`
- Response: Job ID for tracking progress
- Use background task processing

---

### Task 16: Reset to LLM Extraction API
**Priority**: LOW
**Endpoint**: `POST /api/v1/documents/{id}/metadata/reset`

Reset user edits and re-extract:
- Clears `metadata_edited_by_user` flag
- Resets status to `pending`
- Optionally triggers immediate re-extraction

---

## Implementation Order (Recommended)

### Week 1: Documents Page UI (HIGH Priority)
1. ✅ Metadata status badges (Task 1)
2. ✅ Re-extract button (Task 2)
3. ✅ Metadata editor modal (Task 3)
4. ✅ Indexed status display (Task 4)

### Week 2: Wiki Page UI (HIGH Priority)
5. ✅ Category breakdown (Task 9)
6. ✅ Clickable categories (Task 10)
7. ✅ Metadata extraction statistics (Task 11)
8. ✅ Search/filter (Task 12)

### Week 3: Enhancements (MEDIUM/LOW Priority)
9. ✅ Confidence score display (Task 5)
10. ✅ Batch operations (Task 6)
11. ✅ Metadata monitor dashboard (Task 7)
12. ✅ Quality indicators (Task 14)

### Week 4: Optional (LOW Priority)
13. ✅ Timeline/date filtering (Task 13)
14. ✅ Extraction attempt counter (Task 8)
15. ✅ Batch re-extract API (Task 15)
16. ✅ Reset API (Task 16)

---

## Testing Checklist

### Backend API Tests ✅
- [x] GET /api/v1/documents/ returns metadata status fields
- [x] GET /api/v1/documents/metadata/status returns statistics
- [x] POST /api/v1/documents/{id}/metadata/extract extracts metadata
- [x] PATCH /api/v1/documents/{id}/metadata updates metadata
- [x] Database properly persists metadata status fields

### Frontend UI Tests ⏳
- [ ] Status badges display correctly
- [ ] Re-extract button triggers extraction
- [ ] Metadata editor modal saves changes
- [ ] Category breakdown shows correct counts
- [ ] Clickable categories filter documents
- [ ] Search/filter works on Wiki page

---

## Current Database State

**Total Documents**: 29
**Indexed**: 29 (100%)
**Metadata Extracted**: 1 (3.4%)
**Status Breakdown**:
- Pending: 28
- Processing: 0
- Completed: 0
- Failed: 0
- User Edited: 1

---

## Quick Reference: API Endpoints

### Get Documents with Metadata Status
```bash
GET /api/v1/documents/
```

### Get Metadata Statistics
```bash
GET /api/v1/documents/metadata/status
```

### Extract Metadata (Single Document)
```bash
POST /api/v1/documents/{id}/metadata/extract
Content-Type: application/json

{
  "force": false
}
```

### Edit Metadata Manually
```bash
PATCH /api/v1/documents/{id}/metadata
Content-Type: application/json

{
  "document_type": "裁罰書",
  "issuing_authority": "金管會",
  "keywords": ["洗錢防制", "內控"]
}
```

---

## Files Modified (Backend)

1. `src/finagent/database/schema.sql` - Added metadata status columns
2. `src/finagent/database/models.py` - Updated Document model
3. `src/finagent/database/db.py` - Updated add_document() upsert
4. `src/finagent/api/routes/documents.py` - Added 3 new endpoints
5. `src/finagent/document_processing/metadata_extractor.py` - Added extract_metadata() wrapper

---

## Next Action

**Start with Frontend Task 1**: Add metadata status badges to document cards

This provides immediate visual feedback and enables all other UI features.

**File to Modify**: `frontend/src/components/documents/DocumentList.tsx`

**API Data Already Available**: All document endpoints now return `metadata_extraction_status` field.
