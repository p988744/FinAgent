# Full Content Storage for Wiki Display

**Date:** 2025-11-18
**Status:** ✅ Implemented and tested
**Last Updated:** 2025-11-18 (Added MIME type handling for multiple file types)

## Overview

Added `full_content` field to the documents table to store complete document text in the database for text files. Added `mime_type` field to distinguish between text files (display in browser) and binary files (download via file_path). This enables fast wiki display for text documents while supporting proper download handling for PDFs, Word documents, and other binary formats.

## Why This Change?

When users browse the document wiki, they need to:
1. **View full document content** - For text files, display in browser; for binary files, provide download
2. **Access content reliably** - Even if original files are moved/deleted
3. **Fast retrieval** - No file I/O latency for text display
4. **API-friendly** - Serve text content directly from database, provide download URLs for binary files
5. **Support multiple file types** - Text (.txt, .html), PDF (.pdf), Word (.doc, .docx)

## Implementation

### 1. Database Migrations ✅

**Migration 002:** [src/finagent/database/migrations/002_add_full_content.sql](src/finagent/database/migrations/002_add_full_content.sql)

```sql
ALTER TABLE documents ADD COLUMN full_content TEXT;
```

**Migration 003:** [src/finagent/database/migrations/003_add_mime_type.sql](src/finagent/database/migrations/003_add_mime_type.sql)

```sql
-- Add mime_type field for file type identification
ALTER TABLE documents ADD COLUMN mime_type TEXT DEFAULT 'text/plain';

-- Update existing documents based on file extensions
UPDATE documents SET mime_type = 'text/plain' WHERE filename LIKE '%.txt';
UPDATE documents SET mime_type = 'application/pdf' WHERE filename LIKE '%.pdf';
UPDATE documents SET mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' WHERE filename LIKE '%.docx';
UPDATE documents SET mime_type = 'application/msword' WHERE filename LIKE '%.doc';
```

**Applied:**
```bash
sqlite3 data/finagent.db < src/finagent/database/migrations/002_add_full_content.sql
sqlite3 data/finagent.db < src/finagent/database/migrations/003_add_mime_type.sql
```

### 2. DocumentIndexer Update ✅

**File:** [src/finagent/document_processing/indexer.py](src/finagent/document_processing/indexer.py)

Updated `index_document()` to detect MIME type and conditionally store full content:

```python
# Detect MIME type and conditionally store full_content
# Only text files store full_content for browser display
# Binary files (PDF, Word) will be downloaded via file_path
mime_type = "text/plain"  # Default
full_content = None

if filename.endswith(".txt"):
    mime_type = "text/plain"
    full_content = document.content  # Store for browser display
elif filename.endswith(".pdf"):
    mime_type = "application/pdf"
    # Binary file: full_content stays None, use file_path for download
elif filename.endswith(".docx"):
    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
elif filename.endswith(".doc"):
    mime_type = "application/msword"
elif filename.endswith(".html") or filename.endswith(".htm"):
    mime_type = "text/html"
    full_content = document.content

self.document_db.upsert_document(
    doc_id=document.id,
    filename=filename,
    file_path=file_path,
    content_preview=content_preview,
    full_content=full_content,  # Only for text files
    mime_type=mime_type,
    file_size=file_size,
    custom_fields=document.metadata,
)
```

### 3. DocumentDatabase Enhancement ✅

**File:** [src/finagent/database/document_db.py](src/finagent/database/document_db.py)

**Added to optional_fields list:**
```python
"full_content",  # Full document content for wiki display (text files only)
"mime_type",     # MIME type for file type identification
```

**New method for retrieving content:**
```python
def get_full_content(self, doc_id: str) -> str | None:
    """Get full content of a document for wiki display."""
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT full_content FROM documents WHERE doc_id = ?",
            (doc_id,),
        )
        row = cursor.fetchone()
        return row["full_content"] if row else None
    finally:
        conn.close()
```

### 4. Backfill Script ✅

**File:** [scripts/backfill_full_content.py](scripts/backfill_full_content.py)

Populates `full_content` for existing documents by reading from original files:

```bash
# Preview
uv run python scripts/backfill_full_content.py --dry-run

# Execute
uv run python scripts/backfill_full_content.py
```

**Results:**
```
✓ Success: 2 documents
⚠ Missing files: 10 documents (old test data)
```

The 2 real documents ([玉山銀行_洗錢防制裁罰_2020.txt](data/documents/玉山銀行_洗錢防制裁罰_2020.txt), [國泰世華銀行_內線交易_2021.txt](data/documents/國泰世華銀行_內線交易_2021.txt)) now have full content stored.

## File Type Handling Strategy

### Supported File Types

| File Type | Extension | MIME Type | full_content | Display Method |
|-----------|-----------|-----------|--------------|----------------|
| **Text** | .txt | text/plain | ✅ Stored | Show in browser |
| **HTML** | .html, .htm | text/html | ✅ Stored | Show in browser |
| **PDF** | .pdf | application/pdf | ❌ Not stored | Download via file_path |
| **Word (Modern)** | .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document | ❌ Not stored | Download via file_path |
| **Word (Legacy)** | .doc | application/msword | ❌ Not stored | Download via file_path |

### Design Rationale

1. **Text Files (.txt, .html)**
   - Store `full_content` in database for instant display
   - Users can view, copy, and search content directly in browser
   - No additional file serving logic needed

2. **Binary Files (.pdf, .doc, .docx)**
   - Do NOT store `full_content` (would be meaningless text extraction)
   - Store `file_path` for serving original binary file
   - Users download the original file to view with proper applications
   - Preserves formatting, images, and layout

### API Behavior (Checkpoint 4)

```python
# GET /api/wiki/documents/{doc_id}
{
    "doc_id": "doc_123",
    "filename": "玉山銀行_洗錢防制裁罰_2020.txt",
    "mime_type": "text/plain",
    "full_content": "金融監督管理委員會裁罰書...",  # For text files
    "file_path": null  # Not needed for text files
}

# GET /api/wiki/documents/{doc_id}
{
    "doc_id": "doc_456",
    "filename": "裁罰書_2020.pdf",
    "mime_type": "application/pdf",
    "full_content": null,  # Binary files don't have full_content
    "file_path": "/data/documents/裁罰書_2020.pdf",  # For download
    "download_url": "/api/documents/doc_456/download"  # Endpoint to serve file
}
```

### Frontend Behavior (Checkpoint 5)

```tsx
// Document viewer component
const DocumentViewer = ({ doc }) => {
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

### Check stored content:
```bash
sqlite3 data/finagent.db "SELECT doc_id, filename, LENGTH(full_content) as size FROM documents WHERE full_content IS NOT NULL;"
```

**Output:**
```
doc_玉山銀行_洗錢防制裁罰_2020_1da27f67|玉山銀行_洗錢防制裁罰_2020.txt|1821
doc_國泰世華銀行_內線交易_2021_d47d5d4c|國泰世華銀行_內線交易_2021.txt|2270
```

### View content preview:
```bash
sqlite3 data/finagent.db "SELECT SUBSTR(full_content, 1, 200) FROM documents WHERE doc_id = 'doc_玉山銀行_洗錢防制裁罰_2020_1da27f67';"
```

**Output:**
```
金融監督管理委員會裁罰書

受處分人：玉山商業銀行股份有限公司
裁罰文號：金管銀法字第10900123456號
裁罰日期：民國109年9月15日

主文

玉山商業銀行股份有限公司因違反洗錢防制法第6條及銀行法相關規定，處新臺幣貳億伍仟萬元罰鍰。
```

✅ Full content stored correctly!

## Usage in Wiki

### Backend API (Future - Checkpoint 4)

```python
from finagent.database.document_db import DocumentDatabase

db = DocumentDatabase()

# Get full content for display
content = db.get_full_content("doc_玉山銀行_洗錢防制裁罰_2020_1da27f67")

# Return in API response
{
    "doc_id": "doc_玉山銀行_洗錢防制裁罰_2020_1da27f67",
    "filename": "玉山銀行_洗錢防制裁罰_2020.txt",
    "content": content,  # Full document text
    "content_preview": content[:500]  # First 500 chars for list view
}
```

### Frontend Wiki (Future - Checkpoint 5)

```typescript
// Document detail page
const DocumentViewer = ({ docId }: { docId: string }) => {
  const [content, setContent] = useState<string>('')

  useEffect(() => {
    fetch(`/api/wiki/documents/${docId}`)
      .then(res => res.json())
      .then(data => setContent(data.content))
  }, [docId])

  return (
    <div className="document-viewer">
      <pre className="whitespace-pre-wrap">{content}</pre>
    </div>
  )
}
```

## Storage Considerations

### Database Size Impact

**Per Document:**
- Average legal document: ~5 KB (玉山銀行: 1.8 KB, 國泰世華: 2.2 KB)
- 1000 documents: ~5 MB
- 10,000 documents: ~50 MB

**SQLite Limits:**
- TEXT field: Up to 1 GB
- Database size: Up to 281 TB (practical limit: hardware)

**Conclusion:** ✅ Storage is negligible for legal documents

### Alternatives Considered

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **1. File system only** | No duplication | File I/O latency, reliability issues | ❌ Rejected |
| **2. Chroma reconstruction** | No duplication | Complex, chunk ordering issues | ❌ Rejected |
| **3. Database storage** | Fast, reliable, API-friendly | Storage overhead (~5 MB per 1000 docs) | ✅ **Selected** |
| **4. Object storage (S3)** | Scalable | Added complexity, cost, latency | ❌ Overkill for v1.0 |

## Benefits

1. ✅ **Fast Wiki Display** - No file I/O
2. ✅ **Reliable Access** - Works even if files deleted
3. ✅ **API-Ready** - Serve content directly via REST API
4. ✅ **Search-Friendly** - Can index full_content for full-text search
5. ✅ **Backup-Friendly** - Single database file contains everything
6. ✅ **Deployment-Friendly** - No need to sync file system

## Future Enhancements

### Full-Text Search (Optional)

SQLite FTS5 for full-text search:

```sql
-- Create FTS virtual table
CREATE VIRTUAL TABLE documents_fts USING fts5(doc_id, full_content);

-- Populate from documents table
INSERT INTO documents_fts (doc_id, full_content)
SELECT doc_id, full_content FROM documents WHERE full_content IS NOT NULL;

-- Search across full content
SELECT doc_id FROM documents_fts WHERE full_content MATCH '洗錢防制';
```

### Content Compression (Optional)

For very large documents (>100 KB):

```python
import zlib
import base64

# Compress before storage
compressed = base64.b64encode(zlib.compress(content.encode('utf-8'))).decode('ascii')

# Decompress when retrieving
content = zlib.decompress(base64.b64decode(compressed)).decode('utf-8')
```

## Files Modified

1. `src/finagent/database/migrations/002_add_full_content.sql` - New migration
2. `src/finagent/document_processing/indexer.py` - Store full_content
3. `src/finagent/database/document_db.py` - Add get_full_content() method
4. `scripts/backfill_full_content.py` - New backfill script
5. `FULL_CONTENT_STORAGE.md` - This document

## Summary

✅ Full content storage is implemented and working
✅ New documents will automatically store full content
✅ Existing documents can be backfilled with the script
✅ Wiki can now display complete documents without file system access
✅ Ready for use in Checkpoint 4 (Wiki REST API) and Checkpoint 5 (Wiki Frontend UI)

---

**Related:**
- [CHECKPOINT_1_COMPLETE.md](CHECKPOINT_1_COMPLETE.md) - Database Integration
- [V1_0_RELEASE_PLAN.md](V1_0_RELEASE_PLAN.md) - Full roadmap
- [PROJECT_VISION.md](PROJECT_VISION.md) - Product vision
