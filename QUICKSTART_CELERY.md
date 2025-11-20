# Quick Start - Celery Background Tasks

## TL;DR

**Problem**: Documents stuck at upload stage when server restarts
**Solution**: Celery + Redis for persistent background task processing

---

## Start the System (3 Steps)

### 1. Start Redis
```bash
docker-compose up -d redis
```

### 2. Start Celery Worker
```bash
./scripts/start_celery_worker.sh
```
Or manually:
```bash
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=2
```

### 3. Start FastAPI Server
```bash
uv run uvicorn finagent.main:app --reload --port 8000
```

**Done!** System is now ready to process uploads.

---

## Verify Everything is Running

```bash
# Check Redis
docker exec finagent-redis redis-cli ping
# Expected: PONG

# Check Celery Worker
tail -10 logs/celery_worker.log
# Expected: "celery@hostname ready."

# Check registered tasks
celery -A finagent.celery_app inspect registered
# Expected: finagent.tasks.process_document_upload
```

---

## Test Upload

```bash
# Upload a test file
curl -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@data/documents/test.txt" \
  -F "auto_index=true" \
  -F "extract_metadata=true"

# Response includes:
# - job_id: for upload progress tracking
# - celery_task_id: for background task tracking

# Check upload progress
curl http://localhost:8000/api/v1/documents/upload-progress/{job_id}

# Check Celery task status
curl http://localhost:8000/api/v1/documents/tasks/{celery_task_id}/status

# Watch Celery logs in real-time
tail -f logs/celery_worker.log
```

---

## Architecture Overview

```
Upload → FastAPI → Save File → Enqueue Celery Task → Return (2s)
                        ↓
                   Redis Queue
                        ↓
                  Celery Worker (async, 30-50s)
                        ↓
         Load → Index → Extract Metadata → Complete
```

**Key Benefits**:
- ✅ Upload returns immediately (~2 seconds)
- ✅ Processing happens in background (30-50 seconds)
- ✅ Tasks survive server restarts
- ✅ Auto-retry on errors (3 attempts)
- ✅ Real-time monitoring

---

## Monitoring

### Check Worker Status
```bash
# Active tasks
celery -A finagent.celery_app inspect active

# Worker stats
celery -A finagent.celery_app inspect stats
```

### Check Logs
```bash
# Celery worker logs
tail -f logs/celery_worker.log

# Redis logs
docker logs finagent-redis
```

### Find Stuck Documents
```sql
-- Should return 0 rows (no stuck documents)
SELECT doc_id, filename, pipeline_stage,
       ROUND((JULIANDAY('now') - JULIANDAY(pipeline_started_at)) * 24 * 60) as minutes_stuck
FROM documents
WHERE pipeline_status = 'in_progress'
  AND pipeline_started_at < datetime('now', '-15 minutes');
```

---

## Troubleshooting

### Worker not starting?
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis if stopped
docker-compose up -d redis

# Check worker logs
tail -50 logs/celery_worker.log
```

### Tasks not processing?
```bash
# Check if worker is connected
celery -A finagent.celery_app inspect active

# Check task queue
docker exec finagent-redis redis-cli llen celery
```

### Import errors?
```bash
# Use uv run
uv run celery -A finagent.celery_app worker

# Check module import
uv run python -c "import finagent.tasks; print('OK')"
```

---

## Stop the System

```bash
# Stop Celery worker
pkill -f "celery.*finagent"

# Stop Redis
docker-compose down redis

# Stop FastAPI
# Ctrl+C in the uvicorn terminal
```

---

## Files Reference

- [docker-compose.yml](docker-compose.yml) - Redis setup
- [src/finagent/celery_app.py](src/finagent/celery_app.py) - Celery config
- [src/finagent/tasks/document_processing.py](src/finagent/tasks/document_processing.py) - Processing task
- [scripts/start_celery_worker.sh](scripts/start_celery_worker.sh) - Worker startup
- [CELERY_SETUP.md](CELERY_SETUP.md) - Detailed guide
- [CELERY_IMPLEMENTATION_COMPLETE.md](CELERY_IMPLEMENTATION_COMPLETE.md) - Complete summary

---

## Common Commands

```bash
# Start everything
docker-compose up -d redis && \
./scripts/start_celery_worker.sh && \
uv run uvicorn finagent.main:app --reload --port 8000

# Check status
docker ps | grep redis && \
tail -5 logs/celery_worker.log && \
celery -A finagent.celery_app inspect active

# Stop everything
pkill -f "celery.*finagent" && \
docker-compose down redis
```

---

**Status**: ✅ Production Ready
**Date**: 2025-11-19
