# Metadata Extraction Implementation Guide

## Overview

This document explains how metadata extraction works in FinAgent's document upload system, following a background task pattern similar to Google Drive's upload progress tracking.

## Key Changes Made

### 1. Frontend: Enable Metadata Extraction (DocumentUpload.tsx)

**File**: `/Users/weifanliao/PycharmProjects/finagent/frontend/src/components/documents/DocumentUpload.tsx`

**Change**: Line 104
```typescript
// Before:
formData.append('extract_metadata', 'false')

// After:
formData.append('extract_metadata', 'true')
```

This enables LLM-based metadata extraction during document upload.

## How It Works

### Upload Flow with Metadata Extraction

```
1. User selects file → Frontend uploads to backend
2. Backend creates upload job with job_id
3. Frontend polls progress every 500ms
4. Backend processes in background:
   a. Stage 1: File upload (10% progress)
   b. Stage 2: File saved (25% progress)
   c. Stage 3: Metadata created (40% progress)
   d. Stage 4: Vector indexing (50-60% progress)
      - If extract_metadata=true: LLM extraction runs here
   e. Stage 5: Indexed (90% progress)
   f. Stage 6: Complete (100% progress)
```

### Backend Implementation

**File**: `/Users/weifanliao/PycharmProjects/finagent/src/finagent/document_processing/indexer.py`

**Key Functions**:

1. **`index_document()` (Lines 86-258)**
   - Checks if `extract_metadata=True`
   - Calls LLM to extract metadata (lines 100-122)
   - Stores extracted metadata in database (lines 225-244)

2. **Extracted Fields**:
   - `document_type` - e.g., "裁罰書", "判決書", "法規"
   - `issuing_authority` - e.g., "金管會", "中央銀行"
   - `case_number` - Case/reference number
   - `document_date` - Document date
   - `related_institutions` - JSON array of institutions (e.g., ["玉山銀行", "中國信託"])
   - `violation_types` - JSON array of violations (e.g., ["洗錢防制", "內部控制"])
   - `penalty_amount` - Penalty amount if applicable
   - `keywords` - Extracted keywords
   - `extraction_confidence` - Confidence score (0-1)

### Database Schema

**File**: `/Users/weifanliao/PycharmProjects/finagent/src/finagent/database/schema.sql`

**Relevant Tables**:

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    description TEXT,
    document_type TEXT,           -- Extracted by LLM
    keywords TEXT,                -- Extracted by LLM (JSON array)
    document_date TEXT,           -- Extracted by LLM
    issuing_authority TEXT,       -- Extracted by LLM
    related_institutions TEXT,    -- Extracted by LLM (JSON array)
    penalty_amount TEXT,          -- Extracted by LLM
    violation_types TEXT,         -- Extracted by LLM (JSON array)
    custom_fields TEXT,
    indexed BOOLEAN DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Wiki Integration

**File**: `/Users/weifanliao/PycharmProjects/finagent/src/finagent/api/routes/wiki.py`

The wiki endpoint aggregates metadata to provide:
- **Total documents**: Count of all indexed documents
- **Documents by type**: Breakdown by `document_type` (裁罰書, 判決書, etc.)
- **Documents by authority**: Breakdown by `issuing_authority` (金管會, 中央銀行, etc.)
- **Top entities**:
  - `institutions`: Most mentioned institutions (from `related_institutions`)
  - `violations`: Most common violation types (from `violation_types`)
  - `authorities`: Most common authorities (from `issuing_authority`)

## Testing

### E2E Test: Metadata Extraction

**File**: `/Users/weifanliao/PycharmProjects/finagent/frontend/e2e/alpha6-metadata-extraction.spec.ts`

**Test Cases**:

1. **Upload with Metadata Extraction**
   - Creates realistic test document (金管會裁罰書)
   - Uploads via frontend
   - Waits for completion (up to 2 minutes for LLM)
   - Verifies chunk count displayed
   - Navigates to wiki
   - Checks for metadata indicators (金管會, 玉山, 洗錢防制, 裁罰書)

2. **Wiki API Verification**
   - Calls `/api/v1/wiki/overview`
   - Checks `with_metadata` count
   - Verifies categories populated:
     - `by_type` (document types)
     - `by_authority` (authorities)
     - `top_entities.institutions`
     - `top_entities.violations`

3. **Document Details Check**
   - Fetches document list
   - Finds test document
   - Verifies extracted fields:
     - `document_type` != "uploaded"
     - `issuing_authority` present
     - `related_institutions` present
     - `violation_types` present
     - `penalty_amount` present

**Run Test**:
```bash
cd frontend
npx playwright test alpha6-metadata-extraction.spec.ts --headed
```

## Performance

### LLM Extraction Costs

- **Model**: GPT-4o-mini (default)
- **Average Time**: 5-15 seconds per document
- **Average Cost**: ~$0.001 USD per document
- **Token Usage**: ~1,000 tokens average

### Background Processing

- Metadata extraction runs as FastAPI BackgroundTask
- Frontend polls progress every 500ms
- User sees real-time progress updates:
  - "上傳文件中..." (Uploading)
  - "文件已儲存" (File saved)
  - "元數據已儲存" (Metadata saved)
  - "正在建立向量索引..." (Indexing)
  - "分析文件內容..." (Analyzing)
  - "索引完成 (N 個區塊)" (Complete with chunk count)

## Troubleshooting

### Metadata Not Extracted

1. **Check Frontend Setting**:
   - Verify `extract_metadata='true'` in DocumentUpload.tsx (Line 104)

2. **Check Backend Logs**:
   ```bash
   # Look for LLM extraction logs
   grep "Extracting metadata" logs/backend.log
   grep "Metadata extracted" logs/backend.log
   ```

3. **Check LLM API Key**:
   ```bash
   # Ensure OpenAI API key is configured
   cat .env | grep LLM_API_KEY
   ```

4. **Check Database**:
   ```bash
   # Connect to database
   sqlite3 data/finagent.db

   # Check if metadata populated
   SELECT doc_id, filename, document_type, issuing_authority
   FROM documents
   WHERE document_type IS NOT NULL AND document_type != 'uploaded';
   ```

### Wiki Not Showing Categories

1. **Wait for Extraction**: LLM extraction can take 5-15 seconds per document

2. **Refresh Wiki Page**: The wiki aggregates on-the-fly from database

3. **Check Wiki API**:
   ```bash
   curl http://localhost:8000/api/v1/wiki/overview | jq
   ```

4. **Verify Metadata Exists**:
   ```bash
   curl http://localhost:8000/api/v1/documents | jq '.[0]'
   ```

## Future Enhancements

1. **Batch Metadata Extraction**: Process multiple documents in parallel
2. **Progress for Metadata**: Separate progress indicator for LLM extraction
3. **Retry Failed Extractions**: Auto-retry if LLM extraction fails
4. **Custom Extraction Prompts**: Allow users to customize extraction rules
5. **Extraction History**: Track extraction attempts and results

## References

- [LangGraph Multi-Agent Architecture](LANGGRAPH_IMPLEMENTATION.md)
- [Database Schema](src/finagent/database/schema.sql)
- [Document Indexer](src/finagent/document_processing/indexer.py)
- [Upload Progress API](src/finagent/api/routes/documents.py)
- [Wiki API](src/finagent/api/routes/wiki.py)
