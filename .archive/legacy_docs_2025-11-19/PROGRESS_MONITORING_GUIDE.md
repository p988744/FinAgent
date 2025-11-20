# Progress Monitoring Guide

**Created:** 2025-11-18
**Status:** ✅ Implemented

---

## Overview

The FinAgent document upload system now includes comprehensive progress monitoring via WebSocket, allowing real-time visibility into:

1. **File Upload** - Track file transfer progress
2. **Document Indexing** - Monitor vector database indexing
3. **Metadata Extraction** - Track LLM metadata generation (if enabled)

---

## Architecture

### WebSocket Endpoint

**URL:** `ws://localhost:8000/api/v1/ws/upload`

**Message Protocol:**

```typescript
// Client → Server: Start upload
{
  "type": "upload_start",
  "filename": "document.txt",
  "content": "base64_encoded_content",
  "auto_index": true,
  "extract_metadata": false
}

// Server → Client: Progress updates
{
  "type": "progress",
  "timestamp": "2025-11-18T10:30:00Z",
  "payload": {
    "stage": "uploading" | "uploaded" | "metadata_saved" | "indexing" | "indexed",
    "message": "上傳文件: document.txt",
    "progress": 0-100,
    "chunks": 10  // (optional, only for "indexed" stage)
  }
}

// Server → Client: Complete
{
  "type": "upload_complete",
  "timestamp": "2025-11-18T10:30:05Z",
  "payload": {
    "document": {
      "id": "doc_12345678",
      "name": "document.txt",
      "status": "indexed",
      "chunk_count": 10,
      "indexed": true,
      "created_at": "2025-11-18T10:30:00Z"
    },
    "message": "上傳完成!",
    "progress": 100
  }
}

// Server → Client: Error
{
  "type": "error",
  "timestamp": "2025-11-18T10:30:01Z",
  "payload": {
    "message": "Only .txt files are supported"
  }
}
```

---

## Progress Stages

### Stage 1: Uploading (0-25%)
- **Stage:** `"uploading"`
- **Message:** `"上傳文件: {filename}"`
- **Progress:** `0%`
- **Action:** Receiving and decoding base64 content

### Stage 2: Uploaded (25%)
- **Stage:** `"uploaded"`
- **Message:** `"文件已儲存: {filename}"`
- **Progress:** `25%`
- **Action:** File written to `data/documents/`

### Stage 3: Metadata Saved (40%)
- **Stage:** `"metadata_saved"`
- **Message:** `"元數據已儲存"`
- **Progress:** `40%`
- **Action:** Document metadata stored in SQLite

### Stage 4: Indexing Start (50%)
- **Stage:** `"indexing"`
- **Message:** `"正在建立向量索引..."`
- **Progress:** `50%`
- **Action:** Starting DocumentIndexer

### Stage 5: Indexing In Progress (60%)
- **Stage:** `"indexing"`
- **Message:** `"分析文件內容..."`
- **Progress:** `60%`
- **Action:** Creating vector embeddings and chunks

### Stage 6: Indexed (80%)
- **Stage:** `"indexed"`
- **Message:** `"索引完成 ({chunks} 個區塊)"`
- **Progress:** `80%`
- **Payload:** `{"chunks": 10}`
- **Action:** Chunks stored in Chroma vector database

### Stage 7: Complete (100%)
- **Type:** `"upload_complete"`
- **Message:** `"上傳完成!"` or `"上傳完成 (未索引)"`
- **Progress:** `100%`
- **Action:** Ready for querying

---

## Usage Examples

### Python Client

```python
import asyncio
import base64
import json
import websockets

async def upload_with_progress(filename: str, content: str):
    """Upload a document with real-time progress monitoring."""

    # Encode content
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    # Connect to WebSocket
    uri = "ws://localhost:8000/api/v1/ws/upload"
    async with websockets.connect(uri) as websocket:

        # Send upload request
        await websocket.send(json.dumps({
            "type": "upload_start",
            "filename": filename,
            "content": content_b64,
            "auto_index": True,
            "extract_metadata": False,
        }))

        # Receive progress updates
        while True:
            message = await websocket.recv()
            data = json.dumps(message)

            if data["type"] == "progress":
                stage = data["payload"]["stage"]
                progress = data["payload"]["progress"]
                message_text = data["payload"]["message"]
                print(f"[{progress:3d}%] {stage}: {message_text}")

            elif data["type"] == "upload_complete":
                document = data["payload"]["document"]
                print(f"✅ Upload complete: {document['id']}")
                print(f"   Status: {document['status']}")
                print(f"   Chunks: {document['chunk_count']}")
                break

            elif data["type"] == "error":
                print(f"❌ Error: {data['payload']['message']}")
                break

# Run
asyncio.run(upload_with_progress("test.txt", "測試內容..."))
```

### JavaScript/TypeScript Client

```typescript
async function uploadWithProgress(filename: string, content: string) {
  // Encode content to base64
  const contentB64 = btoa(unescape(encodeURIComponent(content)));

  // Connect to WebSocket
  const ws = new WebSocket('ws://localhost:8000/api/v1/ws/upload');

  ws.onopen = () => {
    // Send upload request
    ws.send(JSON.stringify({
      type: 'upload_start',
      filename,
      content: contentB64,
      auto_index: true,
      extract_metadata: false,
    }));
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'progress') {
      const { stage, progress, message } = data.payload;
      console.log(`[${progress}%] ${stage}: ${message}`);

      // Update UI progress bar
      updateProgressBar(progress, message);
    }
    else if (data.type === 'upload_complete') {
      const { document, message } = data.payload;
      console.log(`✅ ${message}`, document);
      ws.close();
    }
    else if (data.type === 'error') {
      console.error(`❌ Error: ${data.payload.message}`);
      ws.close();
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
}

// Usage
uploadWithProgress('test.txt', '測試內容...');
```

---

## Frontend Integration

### React Component Example

```tsx
import { useState, useEffect } from 'react';

interface UploadProgress {
  stage: string;
  message: string;
  progress: number;
  chunks?: number;
}

function DocumentUploadWithProgress() {
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const handleUpload = async (file: File) => {
    // Read file content
    const content = await file.text();
    const contentB64 = btoa(unescape(encodeURIComponent(content)));

    // Connect WebSocket
    const websocket = new WebSocket('ws://localhost:8000/api/v1/ws/upload');

    websocket.onopen = () => {
      websocket.send(JSON.stringify({
        type: 'upload_start',
        filename: file.name,
        content: contentB64,
        auto_index: true,
        extract_metadata: false,
      }));
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'progress') {
        setProgress(data.payload);
      }
      else if (data.type === 'upload_complete') {
        setProgress({ ...data.payload, progress: 100 });
        setTimeout(() => websocket.close(), 1000);
      }
      else if (data.type === 'error') {
        console.error(data.payload.message);
        websocket.close();
      }
    };

    setWs(websocket);
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />

      {progress && (
        <div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
          <p>{progress.message}</p>
          {progress.chunks && <p>已索引 {progress.chunks} 個區塊</p>}
        </div>
      )}
    </div>
  );
}
```

---

## Testing

### Test Script

See [tests/test_websocket_upload.py](tests/test_websocket_upload.py) for a complete test example.

**Run test:**

```bash
# Start backend server
uv run python -m uvicorn finagent.main:app --reload --port 8000

# Run WebSocket upload test
uv run python tests/test_websocket_upload.py
```

**Expected output:**

```
🔌 Connecting to WebSocket...
✅ Connected!

📤 Sending upload request for: test_websocket_upload.txt

📊 Progress updates:
------------------------------------------------------------
[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0% | uploading       | 上傳文件: test_websocket_upload.txt
[███████░░░░░░░░░░░░░░░░░░░░░░░]  25% | uploaded        | 文件已儲存: test_websocket_upload.txt
[████████████░░░░░░░░░░░░░░░░░░]  40% | metadata_saved  | 元數據已儲存
[███████████████░░░░░░░░░░░░░░░]  50% | indexing        | 正在建立向量索引...
[██████████████████░░░░░░░░░░░░]  60% | indexing        | 分析文件內容...
[████████████████████████░░░░░░]  80% | indexed         | 索引完成 (5 個區塊)
[██████████████████████████████] 100% | complete        | 上傳完成!
------------------------------------------------------------

✅ 上傳完成!

📄 Document Details:
   ID: doc_abc12345
   Name: test_websocket_upload.txt
   Status: indexed
   Chunks: 5
   Indexed: True

🏁 Test complete!
```

---

## Implementation Details

### Backend Code

**File:** [src/finagent/api/routes/websocket.py](src/finagent/api/routes/websocket.py)

**Key functions:**
- `websocket_upload_endpoint()` - Main WebSocket handler (lines 351-567)
- Progress stages: uploading → uploaded → metadata_saved → indexing → indexed → complete
- Error handling: Graceful degradation if indexing fails

**Auto-indexing logic:**
- Uses `DocumentLoader.load_txt(filename)` - Fixed path duplication bug
- Uses `DocumentIndexer.index_document()` - Creates vector embeddings
- Updates metadata with `chunk_count` and `indexed=True`

### Frontend Integration

**Recommended approach:**
1. Replace existing HTTP upload with WebSocket upload
2. Add real-time progress bar (0-100%)
3. Show stage-specific messages in Traditional Chinese
4. Display chunk count when indexing completes

---

## Performance

### Typical Upload Timeline

| Stage | Time (Small File <10KB) | Time (Large File >100KB) |
|-------|-------------------------|--------------------------|
| Upload | < 100ms | < 500ms |
| Save to disk | < 50ms | < 100ms |
| Metadata save | < 30ms | < 30ms |
| Indexing | 500ms - 2s | 2s - 10s |
| **Total** | **< 3 seconds** | **< 11 seconds** |

### Progress Update Frequency

- **Upload stage:** Single message at start (0%)
- **File save:** Single message (25%)
- **Metadata save:** Single message (40%)
- **Indexing:** 3 messages (50%, 60%, 80%)
- **Complete:** Single message (100%)

**Total:** 7 progress messages per upload

---

## Troubleshooting

### Issue: WebSocket connection refused (403)

**Cause:** CORS configuration doesn't allow WebSocket from origin

**Solution:** Update CORS settings in `src/finagent/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "ws://localhost:5173"],  # Add ws://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Progress stuck at "indexing"

**Cause:** DocumentIndexer error (e.g., path duplication bug)

**Solution:** Check backend logs for indexing errors. Verify file path handling.

### Issue: Base64 encoding/decoding errors

**Cause:** Incorrect UTF-8 handling

**Solution:** Use proper encoding:

```javascript
// JavaScript: Encode UTF-8 to base64
const contentB64 = btoa(unescape(encodeURIComponent(content)));

// Python: Encode UTF-8 to base64
content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
```

---

## Future Enhancements

1. **Batch upload progress** - Track multiple files simultaneously
2. **Metadata extraction progress** - Stream LLM extraction progress
3. **Cancel upload** - Allow mid-upload cancellation
4. **Resume on disconnect** - Persist upload state for reconnection
5. **Compression** - Compress large files before base64 encoding

---

## References

- **WebSocket Endpoint:** [src/finagent/api/routes/websocket.py:351-567](src/finagent/api/routes/websocket.py#L351-L567)
- **Test Script:** [tests/test_websocket_upload.py](tests/test_websocket_upload.py)
- **Auto-Index Fix:** [AUTO_INDEX_FIX.md](AUTO_INDEX_FIX.md)
- **FastAPI WebSocket Docs:** https://fastapi.tiangolo.com/advanced/websockets/

---

**Status:** ✅ Backend Implemented, Frontend Integration Pending
**Next Step:** Integrate WebSocket upload into React DocumentUpload component
