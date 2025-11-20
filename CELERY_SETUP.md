# Celery Background Task Setup

**Date**: 2025-11-19
**Purpose**: Replace FastAPI BackgroundTasks with persistent Celery task queue

---

## Architecture

```
Upload Request → FastAPI → Save File → Enqueue Celery Task → Return Response
                                              ↓
                                        Redis Broker
                                              ↓
                                      Celery Worker
                                              ↓
                              Load → Index → Extract Metadata → Update DB
```

**Key Benefits**:
- ✅ Persistent tasks (survive server restarts)
- ✅ Auto-retry with exponential backoff (3 attempts)
- ✅ Task monitoring and status tracking
- ✅ Horizontal scalability (multiple workers)
- ✅ Proper async/sync handling (no event loop blocking)

---

## Components

### 1. Redis (Broker + Result Backend)

**Installation**:
```bash
# macOS
brew install redis
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt install redis-server
sudo systemctl start redis

# Verify
redis-cli ping  # Should return "PONG"
```

**Configuration**: `redis://localhost:6379/0`

### 2. Celery App Configuration

**File**: [src/finagent/celery_app.py](src/finagent/celery_app.py)

**Key Settings**:
- Task time limits: 10min hard, 9min soft
- Retry settings: `task_acks_late=True`, max 3 retries
- Worker prefetch: 1 task at a time (prevents overload)
- Result expiry: 1 hour

### 3. Document Processing Task

**File**: [src/finagent/tasks/document_processing.py](src/finagent/tasks/document_processing.py)

**Task Name**: `finagent.tasks.process_document_upload`

**Workflow**:
1. Load document with validation
2. Index document (create vector embeddings)
3. Extract metadata using LLM
4. Update database with results
5. Mark pipeline as complete/failed

**Error Handling**:
- File not found → Mark as failed
- Empty content → Mark as failed
- Indexing produces 0 chunks → Mark as failed
- Auto-retry on transient errors (3 attempts)

### 4. Upload Endpoint (Modified)

**File**: [src/finagent/api/routes/documents.py](src/finagent/api/routes/documents.py)

**Changes**:
- Upload endpoint saves file and creates initial metadata
- Enqueues Celery task via `process_document_upload.delay()`
- Returns immediately with task ID
- Processing happens asynchronously in Celery worker

**New Field**: `celery_task_id` in `UploadProgress` model

### 5. Task Status Endpoint

**Endpoint**: `GET /api/v1/documents/tasks/{task_id}/status`

**Response**:
```json
{
  "task_id": "abc123...",
  "state": "PROGRESS",
  "status": "Indexing document...",
  "progress": 50,
  "result": null,
  "error": null
}
```

**Task States**:
- `PENDING`: Waiting in queue (0%)
- `STARTED`: Task has started (10%)
- `PROGRESS`: Running with custom progress (25-90%)
- `SUCCESS`: Completed successfully (100%)
- `FAILURE`: Failed with error (0%)
- `RETRY`: Being retried (0%)

---

## Running the System

### 1. Start Redis
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Manual
redis-server
```

### 2. Start Celery Worker
```bash
# Using provided script (recommended)
./scripts/start_celery_worker.sh

# Or manually
uv run celery -A finagent.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50
```

**Worker Configuration**:
- `--concurrency=2`: Run 2 worker processes
- `--max-tasks-per-child=50`: Restart after 50 tasks (prevents memory leaks)
- `--time-limit=600`: Hard limit 10 minutes per task
- `--soft-time-limit=540`: Soft limit 9 minutes (graceful cleanup)

**Logs**: `logs/celery_worker.log`

### 3. Start FastAPI Server
```bash
uv run uvicorn finagent.main:app --reload --port 8000
```

### 4. Start Frontend (if using web UI)
```bash
cd frontend
npm run dev
```

---

## Upload Flow

### User Perspective

1. User uploads file via web UI
2. File is immediately saved (progress: 40%)
3. UI shows "處理中..." with Celery task ID
4. Frontend polls `/api/v1/documents/tasks/{task_id}/status` every 2 seconds
5. Progress updates: 50% → 75% → 100%
6. UI shows "處理完成" when done

### Backend Perspective

1. **FastAPI receives upload** (0-40%)
   - Save file to disk
   - Create initial database entry
   - Enqueue Celery task

2. **Celery worker processes** (40-100%)
   - Load document (25%)
   - Index document (50%)
   - Extract metadata (75%)
   - Mark as complete (100%)

3. **Database updates**
   - Real-time pipeline status updates
   - Frontend polls for status
   - No stuck documents (tasks are persistent)

---

## Monitoring

### Check Worker Status
```bash
# List active workers
celery -A finagent.celery_app inspect active

# Check task stats
celery -A finagent.celery_app inspect stats

# Check registered tasks
celery -A finagent.celery_app inspect registered
```

### Check Task Status (API)
```bash
# Get task status
curl http://localhost:8000/api/v1/documents/tasks/{task_id}/status
```

### Check Logs
```bash
# Celery worker logs
tail -f logs/celery_worker.log

# FastAPI logs
# (printed to console with uvicorn --reload)
```

### Find Stuck Documents
```sql
-- Documents in progress for > 15 minutes
SELECT doc_id, filename, pipeline_stage, pipeline_status,
       ROUND((JULIANDAY('now') - JULIANDAY(pipeline_started_at)) * 24 * 60) as minutes_stuck
FROM documents
WHERE pipeline_status = 'in_progress'
  AND pipeline_started_at < datetime('now', '-15 minutes')
ORDER BY pipeline_started_at;
```

**Expected Result**: Should be empty (Celery tasks complete or fail within 10 minutes)

---

## Error Handling

### Task Failure
When a Celery task fails:
1. Error is logged to `logs/celery_worker.log`
2. Task is automatically retried (max 3 attempts, exponential backoff)
3. Database is updated with `pipeline_status='failed'`
4. Frontend shows error message with details

### Worker Crash
If Celery worker crashes:
1. Tasks in progress are requeued (due to `task_acks_late=True`)
2. Start worker again: `./scripts/start_celery_worker.sh`
3. Tasks will be retried automatically

### Redis Crash
If Redis crashes:
1. No tasks can be enqueued (upload will fail with 500 error)
2. Restart Redis: `brew services start redis` (macOS) or `sudo systemctl start redis` (Linux)
3. Restart Celery worker

---

## Migration from FastAPI BackgroundTasks

### Before (Alpha 1-4)
```python
# Inline processing in FastAPI endpoint
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    # ... save file ...
    background_tasks.add_task(_process_upload, file)
    # Tasks lost on server restart ❌
```

### After (Alpha 5+)
```python
# Enqueue Celery task
async def upload_file(file: UploadFile):
    # ... save file ...
    task = process_document_upload.delay(doc_id, filename, path)
    # Tasks persist in Redis ✅
    return {"task_id": task.id}
```

---

## Configuration

### Environment Variables

**Redis URL** (default: `redis://localhost:6379/0`):
```bash
export REDIS_URL="redis://localhost:6379/0"
```

**Task Time Limits** (in celery_app.py):
```python
task_time_limit=600,         # 10 minutes hard limit
task_soft_time_limit=540,    # 9 minutes soft limit
```

**Retry Settings** (in document_processing.py):
```python
autoretry_for = (Exception,)
retry_kwargs = {'max_retries': 3, 'countdown': 5}
retry_backoff = True         # Exponential backoff: 5s, 10s, 20s
```

---

## Frontend Integration

### Polling Celery Task Status

**When to use**:
- After upload completes (when `celery_task_id` is returned)
- Poll every 2 seconds until task completes

**Example**:
```typescript
useEffect(() => {
  if (!celeryTaskId) return;

  const pollTaskStatus = async () => {
    const response = await fetch(
      `${API_BASE}/api/v1/documents/tasks/${celeryTaskId}/status`
    );
    const data = await response.json();

    setProgress(data.progress);
    setStatus(data.status);

    // Stop polling when complete
    if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
      clearInterval(interval);
    }
  };

  const interval = setInterval(pollTaskStatus, 2000);
  return () => clearInterval(interval);
}, [celeryTaskId]);
```

---

## Troubleshooting

### Issue: Tasks not running

**Check**:
1. Is Redis running? `redis-cli ping`
2. Is Celery worker running? `ps aux | grep celery`
3. Are there errors in logs? `tail -f logs/celery_worker.log`

### Issue: Tasks timing out

**Increase time limits** in [src/finagent/celery_app.py](src/finagent/celery_app.py):
```python
task_time_limit=1200,        # 20 minutes
task_soft_time_limit=1080,   # 18 minutes
```

### Issue: Too many retries

**Reduce retry attempts** in [src/finagent/tasks/document_processing.py](src/finagent/tasks/document_processing.py):
```python
retry_kwargs = {'max_retries': 1, 'countdown': 5}
```

### Issue: Memory leaks

**Restart worker more frequently**:
```bash
celery -A finagent.celery_app worker --max-tasks-per-child=10
```

---

## Summary

**Problem**: FastAPI BackgroundTasks are not persistent, causing stuck uploads on server restart

**Solution**: Celery + Redis for persistent, reliable background task processing

**Key Features**:
- ✅ Persistent tasks (survive restarts)
- ✅ Auto-retry (3 attempts with exponential backoff)
- ✅ Task monitoring (real-time status tracking)
- ✅ Scalable (multiple workers)
- ✅ Robust error handling (no stuck documents)

**Files Changed**:
- [src/finagent/celery_app.py](src/finagent/celery_app.py) - Celery configuration
- [src/finagent/tasks/document_processing.py](src/finagent/tasks/document_processing.py) - Processing task
- [src/finagent/api/routes/documents.py](src/finagent/api/routes/documents.py) - Upload endpoint + task status endpoint
- [scripts/start_celery_worker.sh](scripts/start_celery_worker.sh) - Worker startup script

**Next Steps**:
1. Start Redis
2. Start Celery worker: `./scripts/start_celery_worker.sh`
3. Test upload with auto-index enabled
4. Verify task completes successfully
5. Update frontend to poll Celery task status (optional)
