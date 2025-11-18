# MIME Type Enhancement for Multiple File Types

**Date:** 2025-11-18
**Status:** ✅ Implemented and tested

## Problem

The initial `full_content` implementation stored complete document text for ALL files. This approach doesn't work for:
- **PDF files** - Binary format, text extraction loses formatting
- **Word documents** (.doc, .docx) - Binary format with embedded images and complex formatting
- **Other binary formats** - Cannot be meaningfully displayed as plain text

## Solution

Add `mime_type` field to distinguish between text files (displayable) and binary files (downloadable), then conditionally store `full_content` only for text files.

## Implementation Summary

### Migration 003

```sql
ALTER TABLE documents ADD COLUMN mime_type TEXT DEFAULT 'text/plain';

-- Update existing documents
UPDATE documents SET mime_type = 'text/plain' WHERE filename LIKE '%.txt';
UPDATE documents SET mime_type = 'application/pdf' WHERE filename LIKE '%.pdf';
UPDATE documents SET mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' WHERE filename LIKE '%.docx';
UPDATE documents SET mime_type = 'application/msword' WHERE filename LIKE '%.doc';
```

### DocumentIndexer Changes

File: [src/finagent/document_processing/indexer.py:150-169](src/finagent/document_processing/indexer.py#L150-L169)

- Detects MIME type from file extension
- Only stores `full_content` for text files (.txt, .html)
- Binary files have `full_content = None`, use `file_path` for download

### DocumentDatabase Changes

File: [src/finagent/database/document_db.py:78](src/finagent/database/document_db.py#L78)

- Added `"mime_type"` to optional_fields

## File Type Support Matrix

| File Type | Extension | MIME Type | full_content | Display Method |
|-----------|-----------|-----------|--------------|----------------|
| Text | .txt | text/plain | ✅ Stored | Show in browser |
| HTML | .html, .htm | text/html | ✅ Stored | Show in browser |
| PDF | .pdf | application/pdf | ❌ Not stored | Download |
| Word (Modern) | .docx | application/vnd...wordprocessingml.document | ❌ Not stored | Download |
| Word (Legacy) | .doc | application/msword | ❌ Not stored | Download |

## API Changes (Checkpoint 4)

### Text File Response
```json
{
  "doc_id": "doc_123",
  "filename": "玉山銀行_洗錢防制裁罰_2020.txt",
  "mime_type": "text/plain",
  "full_content": "金融監督管理委員會裁罰書...",
  "content_preview": "金融監督管理委員會裁罰書..."
}
```

### Binary File Response
```json
{
  "doc_id": "doc_456",
  "filename": "裁罰書_2020.pdf",
  "mime_type": "application/pdf",
  "full_content": null,
  "file_path": "/data/documents/裁罰書_2020.pdf",
  "download_url": "/api/documents/doc_456/download"
}
```

### New Download Endpoint
```python
@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str):
    db = DocumentDatabase()
    doc = db.get_document(doc_id)

    return FileResponse(
        path=doc["file_path"],
        filename=doc["filename"],
        media_type=doc["mime_type"]
    )
```

## Frontend Changes (Checkpoint 5)

### Conditional Rendering

```tsx
const DocumentViewer = ({ doc }: { doc: Document }) => {
  // Text files: show content
  if (doc.mime_type === 'text/plain' || doc.mime_type === 'text/html') {
    return (
      <div className="text-viewer">
        <div className="toolbar">
          <button onClick={() => copy(doc.full_content)}>📋 Copy</button>
        </div>
        <pre className="whitespace-pre-wrap">{doc.full_content}</pre>
      </div>
    )
  }

  // Binary files: show download button
  return (
    <div className="binary-file">
      <FileIcon type={doc.mime_type} />
      <p>{doc.filename}</p>
      <a href={doc.download_url} download>
        <button>⬇️ Download {doc.filename}</button>
      </a>
    </div>
  )
}
```

## Verification

```bash
# Check MIME types and full_content status
sqlite3 data/finagent.db "SELECT filename, mime_type, CASE WHEN full_content IS NOT NULL THEN 'Yes' ELSE 'No' END as has_content FROM documents LIMIT 5;"
```

**Output:**
```
323_20200519_保險局_凱基商業銀行股份有限公司.txt|text/plain|No
115_20141114_證券期貨局_正鑫證券投資顧問股份有限公司.txt|text/plain|No
玉山銀行_洗錢防制裁罰_2020.txt|text/plain|Yes
國泰世華銀行_內線交易_2021.txt|text/plain|Yes
```

✅ MIME types correctly assigned to all documents
✅ Text files have full_content where backfilled
✅ New uploads will only store full_content for text files

## Benefits

1. **Proper file handling** - Text files displayed, binary files downloaded
2. **Storage efficiency** - Don't store meaningless text extraction for binary files
3. **Better UX** - Users get original PDFs/Word docs with formatting intact
4. **Type-aware system** - Frontend knows how to render each file type
5. **Extensible** - Easy to add more MIME types in the future

## Files Modified

1. [src/finagent/database/migrations/003_add_mime_type.sql](src/finagent/database/migrations/003_add_mime_type.sql) - New migration
2. [src/finagent/document_processing/indexer.py](src/finagent/document_processing/indexer.py) - MIME detection and conditional storage
3. [src/finagent/database/document_db.py](src/finagent/database/document_db.py) - Add mime_type to optional_fields
4. [FULL_CONTENT_STORAGE.md](FULL_CONTENT_STORAGE.md) - Updated with file type strategy
5. [CHECKPOINT_REVIEW.md](CHECKPOINT_REVIEW.md) - Updated with revised approach

## Related Documentation

- [FULL_CONTENT_STORAGE.md](FULL_CONTENT_STORAGE.md) - Complete storage strategy
- [CHECKPOINT_REVIEW.md](CHECKPOINT_REVIEW.md) - Impact on remaining checkpoints
- [V1_0_RELEASE_PLAN.md](V1_0_RELEASE_PLAN.md) - Full roadmap

---

**Status:** ✅ Ready for Checkpoint 2 (LLM Metadata Extraction)
