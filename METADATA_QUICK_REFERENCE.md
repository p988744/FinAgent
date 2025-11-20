# Metadata System Quick Reference

## Two-Tier Status System

### Tier 1: Indexed (`indexed` column)
- **Means**: Document in vector DB + filesystem
- **Result**: Searchable via semantic search ✅
- **Speed**: ~0.5 seconds
- **Cost**: $0

### Tier 2: Metadata Extracted (`metadata_extracted` + `metadata_extraction_status`)
- **Means**: LLM analyzed document structure and content
- **Result**: Categorized in wiki, filterable by type/authority/institution/violation ✅
- **Speed**: ~5-15 seconds
- **Cost**: ~$0.001 USD per document

## Status Values

| Status | Description |
|--------|-------------|
| `pending` | Waiting for metadata extraction |
| `processing` | LLM currently analyzing |
| `completed` | Successfully extracted |
| `failed` | Extraction failed (see `metadata_extraction_error`) |
| `user_edited` | User manually edited metadata |

## Database Schema

**New columns added** (Migration 001):
```sql
metadata_extracted              BOOLEAN DEFAULT 0
metadata_extraction_status      TEXT DEFAULT 'pending'
metadata_extraction_error       TEXT
metadata_extraction_attempts    INTEGER DEFAULT 0
metadata_last_extracted_at      TIMESTAMP
metadata_edited_by_user         BOOLEAN DEFAULT 0
```

## Current State

```bash
# Check migration status
uv run python -m finagent.database.migrate status

# View document status distribution
sqlite3 data/finagent.db "SELECT indexed, metadata_extracted, metadata_extraction_status, COUNT(*) FROM documents GROUP BY indexed, metadata_extracted, metadata_extraction_status;"

# Find documents needing extraction
sqlite3 data/finagent.db "SELECT doc_id, filename FROM documents WHERE indexed=1 AND metadata_extraction_status='pending' LIMIT 10;"

# Find failed extractions
sqlite3 data/finagent.db "SELECT doc_id, filename, metadata_extraction_error FROM documents WHERE metadata_extraction_status='failed';"
```

## Frontend Status

**Metadata extraction enabled**: [DocumentUpload.tsx:104](../frontend/src/components/documents/DocumentUpload.tsx#L104)
```typescript
formData.append('extract_metadata', 'true')  // ✅ Enabled
```

All new uploads will automatically extract metadata.

## Testing

```bash
# Run metadata extraction E2E test
cd frontend
npx playwright test alpha6-metadata-extraction.spec.ts --headed

# Check results
sqlite3 ../data/finagent.db "SELECT filename, document_type, issuing_authority, metadata_extraction_status FROM documents ORDER BY created_at DESC LIMIT 5;"
```

## Next Steps (API Implementation)

### 1. Monitor Metadata Status
```bash
curl http://localhost:8000/api/v1/documents/metadata/status
```

### 2. Re-extract Single Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/{doc_id}/metadata/extract
```

### 3. Batch Re-extract
```bash
curl -X POST http://localhost:8000/api/v1/documents/metadata/extract-batch \
  -H "Content-Type: application/json" \
  -d '{"status_filter": "failed"}'
```

### 4. User Edit Metadata
```bash
curl -X PATCH http://localhost:8000/api/v1/documents/{doc_id}/metadata \
  -H "Content-Type: application/json" \
  -d '{"document_type": "裁罰書", "issuing_authority": "金管會"}'
```

### 5. Reset to LLM Extraction
```bash
curl -X POST http://localhost:8000/api/v1/documents/{doc_id}/metadata/reset
```

## Documentation

- **Full System Design**: [METADATA_STATUS_SYSTEM.md](./METADATA_STATUS_SYSTEM.md)
- **Implementation Guide**: [METADATA_EXTRACTION_GUIDE.md](./METADATA_EXTRACTION_GUIDE.md)
- **Implementation Summary**: [METADATA_IMPLEMENTATION_SUMMARY.md](./METADATA_IMPLEMENTATION_SUMMARY.md)

## Key Concepts

**Indexed = Searchable**
```
indexed=TRUE → Document chunks in vector DB → Semantic search works
```

**Metadata Extracted = Categorized**
```
metadata_extracted=TRUE → Wiki categories populated → Filter by type/authority/institution
```

**Upload Workflow**
```
Upload → Save → Index (searchable ✅) → Extract (categorize ✅) → Complete
        ↓       ↓                      ↓                        ↓
    pending  indexed               processing              completed
```

## Troubleshooting

**No metadata in wiki?**
```sql
-- Check if extraction ran
SELECT metadata_extraction_status, COUNT(*)
FROM documents
GROUP BY metadata_extraction_status;

-- If all 'pending', metadata extraction hasn't run yet
-- Check if extract_metadata=true in upload
-- Check backend logs for LLM errors
```

**Failed extractions?**
```sql
-- Find failed documents
SELECT doc_id, filename, metadata_extraction_error, metadata_extraction_attempts
FROM documents
WHERE metadata_extraction_status='failed'
ORDER BY metadata_extraction_attempts DESC;

-- Trigger re-extraction (API endpoint needed)
```

**User edits not saving?**
```sql
-- Check user edit flag
SELECT doc_id, filename, metadata_edited_by_user, metadata_extraction_status
FROM documents
WHERE metadata_edited_by_user=1;

-- User edits should have status='user_edited'
```

## Performance

**Indexing only** (fast mode):
- 100 documents × 0.5s = 50 seconds
- Cost: $0

**Full extraction** (with metadata):
- 100 documents × 10s = 1,000 seconds (~16 minutes)
- Cost: 100 × $0.001 = $0.10 USD

**Recommendation**:
- Index all documents first (searchable immediately)
- Extract metadata in background or on-demand
- Batch process during off-peak hours
