# Celery Implementation Roadmap - Revised (Hybrid Approach)

**Date:** 2025-11-21
**Version:** v1.1 Revised
**Approach:** Sync CLI + Async API/WebSocket
**Estimated Time:** 9-12 hours (vs. 12-20 hours in original plan)

---

## Architecture Summary

**User's Insight:** ✅
> "cli script can be sync, then http api should be async task, websocket be async task and streaming status of tasks"

This is the **correct and simpler approach**:

```
CLI Scripts (Sync)       →  Direct execution, no Celery
HTTP API (Async)         →  Celery tasks + polling
WebSocket (Async+Stream) →  Celery tasks + real-time events
```

---

## Phase 0: Prerequisites (1 hour)

**Status:** Same as before

### Install Dependencies

```bash
# Celery and async support
uv add celery[redis]
uv add langgraph-checkpoint-postgres
uv add psycopg[binary,pool]
uv add flower  # Optional: monitoring

# Redis and PostgreSQL
brew install redis postgresql@16  # macOS
# or use Docker
docker run -d -p 6379:6379 redis:7-alpine
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:16
```

### Configure Environment

Add to `.env`:

```bash
# PostgreSQL for checkpoints and history
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=finagent
POSTGRES_USER=finagent_user
POSTGRES_PASSWORD=your_secure_password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# LangGraph Checkpoint
LANGGRAPH_CHECKPOINT_DB=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

### Create Database

```bash
# Create database and user
psql -U postgres << EOF
CREATE DATABASE finagent;
CREATE USER finagent_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE finagent TO finagent_user;
\c finagent
GRANT ALL ON SCHEMA public TO finagent_user;
EOF
```

**Checkpoint 0:** ✅ Services running, environment configured

---

## Phase 1: Keep CLI Synchronous (0 hours) ✅

**Status:** Already complete - no changes needed!

### Current CLI Scripts (Keep As Is)

**scripts/cli_research.py** - Already works perfectly:
```python
async def research_query(query_text, verbose=False):
    """Direct synchronous execution - no Celery."""
    orchestrator = AgentOrchestrator()

    async for node_name, state_update in orchestrator.stream_query(
        query=Query(text=query_text),
        use_plan_execute=True
    ):
        if verbose:
            print(f"[{node_name}] {state_update}")

    return final_result
```

**Benefits:**
- ✅ Simple debugging
- ✅ No background services needed
- ✅ Direct terminal output
- ✅ Perfect for development

**Keep these scripts unchanged:**
- `scripts/cli_research.py`
- `scripts/cli_retrieval.py`
- `scripts/cli_import.py`

**Verification:**
```bash
# Test CLI (should work without Celery)
uv run python scripts/cli_research.py "玉山銀行洗錢防制裁罰"
```

**Checkpoint 1:** ✅ CLI scripts remain functional (no changes)

---

## Phase 2: HTTP API with Async Tasks (3-4 hours)

**Status:** New implementation needed

### Step 2.1: Create Database Helper (1 hour)

**File:** `src/finagent/database/checkpoint_db.py`

Copy implementation from [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md - Part 4.1](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md#41-database-helper)

**Key methods:**
- `get_checkpoint_db()` - Singleton instance
- `setup_tables()` - Initialize tables
- `create_query_record()` - Start tracking
- `update_query_status()` - Update status
- `update_query_result()` - Save results
- `get_query_history()` - Query history

**Create schema file:**

**File:** `src/finagent/database/query_history_schema.sql`

```sql
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query_id TEXT UNIQUE NOT NULL,
    thread_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    query_type TEXT,

    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'pending',
    error_message TEXT,

    query_insight JSONB,
    plan JSONB,
    past_steps JSONB,
    response TEXT,

    total_tokens INTEGER,
    llm_cost_usd DECIMAL(10, 6),
    execution_time_seconds DECIMAL(10, 3),

    user_id TEXT,
    session_id TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_query_history_thread_id ON query_history(thread_id);
CREATE INDEX idx_query_history_status ON query_history(status);
CREATE INDEX idx_query_history_created_at ON query_history(created_at DESC);
```

**Verification:**
```bash
# Apply schema
psql -U finagent_user -d finagent -f src/finagent/database/query_history_schema.sql

# Test connection
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db
db = get_checkpoint_db()
db.setup_tables()
print('✅ Database ready')
"
```

### Step 2.2: Create Celery App (30 minutes)

**File:** `src/finagent/celery_app.py`

```python
"""Celery application for async task execution."""

import os
from celery import Celery

celery_app = Celery(
    'finagent',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    include=['finagent.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,
    result_expires=3600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

if __name__ == '__main__':
    celery_app.start()
```

**Verification:**
```bash
# Start Celery worker
celery -A finagent.celery_app worker --loglevel=info

# Expected: Worker starts without errors
```

### Step 2.3: Create Research Task (1 hour)

**File:** `src/finagent/tasks.py`

```python
"""Celery tasks for research queries."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from celery import Task
from finagent.celery_app import celery_app
from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query
from finagent.database.checkpoint_db import get_checkpoint_db

logger = logging.getLogger(__name__)


class ProgressTrackingTask(Task):
    """Base task with progress tracking."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        query_id = kwargs.get('query_id')
        if query_id:
            db = get_checkpoint_db()
            db.update_query_status(query_id, 'failed', str(exc))
            db.close()
        logger.error(f"Task {task_id} failed: {exc}")

    def update_progress(self, state, meta):
        """Update task state for progress tracking."""
        self.update_state(state=state, meta=meta)


@celery_app.task(
    bind=True,
    base=ProgressTrackingTask,
    name='finagent.tasks.research_query',
    max_retries=3
)
def research_query_task(
    self,
    query_text: str,
    query_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    use_plan_execute: bool = True
):
    """
    Execute research query as Celery task with progress tracking.

    Args:
        query_text: The research question
        query_id: UUID for tracking (creates new if None)
        thread_id: LangGraph thread ID
        user_id: User identifier
        session_id: Session identifier
        use_plan_execute: Use plan-and-execute workflow

    Returns:
        dict: Query results with metadata
    """
    start_time = datetime.now()
    db = get_checkpoint_db()

    # Create query record if not exists
    if not query_id:
        query_id = db.create_query_record(
            query_text=query_text,
            thread_id=thread_id,
            user_id=user_id,
            session_id=session_id
        )

    # Update status to running
    db.update_query_status(query_id, 'running')

    # Report initial progress
    self.update_progress('PROGRESS', {
        'current_step': 'initializing',
        'progress': 5
    })

    try:
        # Execute query with progress tracking
        async def execute_with_progress():
            checkpointer = db.get_checkpointer()
            orchestrator = AgentOrchestrator(checkpointer=checkpointer)

            config = {
                "configurable": {
                    "thread_id": thread_id or query_id,
                    "query_id": query_id
                }
            }

            progress_map = {
                'query_analyzer': 20,
                'planner': 40,
                'executor': 70,
                'replanner': 85,
                'reporter': 95
            }

            result = {}
            async for node_name, state_update in orchestrator.stream_query(
                query=Query(text=query_text),
                use_plan_execute=use_plan_execute,
                config=config
            ):
                # Update progress
                progress = progress_map.get(node_name, 50)
                self.update_progress('PROGRESS', {
                    'current_step': node_name,
                    'progress': progress
                })

                # Store intermediate results
                if node_name == "query_analyzer" and "query_insight" in state_update:
                    result['query_insight'] = state_update['query_insight'].dict()

                elif node_name == "planner" and "plan" in state_update:
                    result['plan'] = state_update['plan'].dict()

                elif node_name == "reporter" and "response" in state_update:
                    result['response'] = state_update['response']

            return result

        # Run async execution
        result = asyncio.run(execute_with_progress())

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Update query results
        db.update_query_result(
            query_id=query_id,
            query_insight=result.get('query_insight'),
            plan=result.get('plan'),
            response=result.get('response'),
            execution_time=execution_time
        )

        logger.info(f"Query {query_id} completed in {execution_time:.2f}s")

        return {
            'query_id': query_id,
            'status': 'completed',
            'execution_time': execution_time,
            **result
        }

    except Exception as e:
        logger.error(f"Query {query_id} failed: {e}", exc_info=True)
        db.update_query_status(query_id, 'failed', str(e))
        raise

    finally:
        db.close()
```

**Verification:**
```bash
# Test task submission
python -c "
from finagent.tasks import research_query_task

result = research_query_task.delay('Test query')
print(f'✅ Task submitted: {result.id}')
print(f'Status: {result.status}')
"
```

### Step 2.4: Create HTTP API Endpoints (1-2 hours)

**File:** `src/finagent/api/routes/research.py`

```python
"""Research API with Celery task queue."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from celery.result import AsyncResult

from finagent.tasks import research_query_task

router = APIRouter(prefix="/api/v1/research", tags=["research"])


class QueryRequest(BaseModel):
    query: str
    use_plan_execute: bool = True
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    current_step: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/query", response_model=TaskResponse)
async def submit_research_query(request: QueryRequest):
    """Submit research query as async Celery task."""
    result = research_query_task.delay(
        query_text=request.query,
        use_plan_execute=request.use_plan_execute,
        user_id=request.user_id,
        session_id=request.session_id
    )

    return TaskResponse(
        task_id=result.id,
        status="pending",
        message="Query submitted for processing"
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get task status (poll endpoint)."""
    result = AsyncResult(task_id)

    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status.lower()
    )

    if result.ready():
        if result.successful():
            response.status = "completed"
            response.result = result.result
        else:
            response.status = "failed"
            response.error = str(result.result)
    elif result.status == "PROGRESS":
        response.status = "running"
        response.progress = result.info.get('progress', 0)
        response.current_step = result.info.get('current_step', '')

    return response


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """Get final task result (blocking)."""
    result = AsyncResult(task_id)

    try:
        final_result = result.get(timeout=300)
        return final_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel running task."""
    result = AsyncResult(task_id)
    result.revoke(terminate=True)
    return {"message": "Task cancelled", "task_id": task_id}
```

**Register router in main app:**

**File:** `src/finagent/main.py` (UPDATE)

```python
from finagent.api.routes import research

app = FastAPI(title="FinAgent API")

# Add research router
app.include_router(research.router)
```

**Verification:**
```bash
# Start backend
uv run uvicorn finagent.main:app --reload --port 8000

# Test task submission
curl -X POST http://localhost:8000/api/v1/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "玉山銀行洗錢防制裁罰"}'

# Response: {"task_id": "abc-123", ...}

# Poll status
TASK_ID="<task_id from above>"
curl http://localhost:8000/api/v1/research/tasks/$TASK_ID
```

**Checkpoint 2:** ✅ HTTP API with async tasks working

---

## Phase 3: WebSocket with Streaming (4-5 hours)

**Status:** Enhancement to existing WebSocket

### Step 3.1: Enhance WebSocket Endpoint (2-3 hours)

**File:** `src/finagent/api/routes/websocket.py` (UPDATE)

Add new WebSocket endpoint with Celery streaming:

```python
"""WebSocket endpoint with Celery task streaming."""

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from celery.result import AsyncResult

from finagent.tasks import research_query_task
from finagent.celery_app import celery_app


async def stream_task_events(task_id: str):
    """Stream Celery task events to WebSocket client."""
    result = AsyncResult(task_id, app=celery_app)

    # Initial event
    yield {
        "event": "task_started",
        "task_id": task_id,
        "status": result.status
    }

    # Poll for updates
    while not result.ready():
        await asyncio.sleep(0.5)

        if result.status == "PROGRESS":
            yield {
                "event": "progress",
                "task_id": task_id,
                "data": result.info
            }

    # Final result
    if result.successful():
        yield {
            "event": "completed",
            "task_id": task_id,
            "result": result.result
        }
    else:
        yield {
            "event": "failed",
            "task_id": task_id,
            "error": str(result.result)
        }


@router.websocket("/stream")
async def websocket_research_stream(websocket: WebSocket):
    """WebSocket endpoint with real-time Celery task streaming."""
    await websocket.accept()

    try:
        # Receive query
        data = await websocket.receive_json()
        query_text = data.get("query")
        use_plan_execute = data.get("use_plan_execute", True)
        user_id = data.get("user_id")
        session_id = data.get("session_id")

        # Submit to Celery
        result = research_query_task.delay(
            query_text=query_text,
            use_plan_execute=use_plan_execute,
            user_id=user_id,
            session_id=session_id
        )

        # Stream events
        async for event in stream_task_events(result.id):
            await websocket.send_json(event)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({
            "event": "error",
            "error": str(e)
        })
    finally:
        await websocket.close()
```

**Verification:**
```bash
# Test with Python WebSocket client
python << 'EOF'
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/api/v1/research/stream"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"query": "Test query"}))

        async for message in ws:
            event = json.loads(message)
            print(f"Event: {event['event']}")

            if event['event'] in ['completed', 'failed']:
                break

asyncio.run(test())
EOF
```

### Step 3.2: Update Frontend to Use WebSocket (1-2 hours)

**File:** `frontend/src/hooks/useResearchWebSocket.ts` (UPDATE)

```typescript
const ws = new WebSocket('ws://localhost:8000/api/v1/research/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    query: queryText,
    use_plan_execute: usePlanExecute,
    user_id: userId,
    session_id: sessionId
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.event) {
    case 'task_started':
      setTaskId(data.task_id);
      break;

    case 'progress':
      setProgress(data.data.progress);
      setCurrentStep(data.data.current_step);
      break;

    case 'completed':
      setResult(data.result);
      ws.close();
      break;

    case 'failed':
      setError(data.error);
      ws.close();
      break;
  }
};
```

**Checkpoint 3:** ✅ WebSocket with real-time streaming working

---

## Phase 4: Testing & Documentation (2-3 hours)

### Step 4.1: Create API Tests (1 hour)

**File:** `tests/test_api_research.py`

```python
"""Tests for research API endpoints."""

import pytest
from fastapi.testclient import TestClient

from finagent.main import app

client = TestClient(app)


def test_submit_query():
    """Test query submission."""
    response = client.post(
        "/api/v1/research/query",
        json={"query": "Test query"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_get_task_status():
    """Test task status retrieval."""
    # Submit query first
    submit_response = client.post(
        "/api/v1/research/query",
        json={"query": "Test query"}
    )
    task_id = submit_response.json()["task_id"]

    # Get status
    status_response = client.get(f"/api/v1/research/tasks/{task_id}")

    assert status_response.status_code == 200
    data = status_response.json()
    assert data["task_id"] == task_id
    assert data["status"] in ["pending", "running", "completed", "failed"]
```

Run tests:
```bash
uv run pytest tests/test_api_research.py -v
```

### Step 4.2: Update Documentation (1-2 hours)

**Update CLAUDE.md:**

Add to development commands:
```markdown
### Celery Commands
```bash
# Start Celery worker
celery -A finagent.celery_app worker --loglevel=info

# Start Flower monitoring
celery -A finagent.celery_app flower --port=5555

# Submit query via API
curl -X POST http://localhost:8000/api/v1/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your query"}'

# Check task status
curl http://localhost:8000/api/v1/research/tasks/<task_id>
```
```

**Update V1_1_RELEASE_PLAN.md:**

Mark complete:
```markdown
#### Phase X: Celery Async API (100%) **✅ COMPLETED**
- ✅ Database setup (checkpoint_db.py)
- ✅ Celery app configuration
- ✅ HTTP API endpoints (POST /query, GET /tasks/{id})
- ✅ WebSocket streaming
- ✅ Progress tracking
- ✅ Integration tests
```

**Checkpoint 4:** ✅ Testing and documentation complete

---

## Final Verification

### Checklist

- [ ] CLI scripts still work (synchronous)
- [ ] Celery worker starts without errors
- [ ] HTTP API accepts queries
- [ ] Task status polling works
- [ ] WebSocket streaming works
- [ ] Progress updates stream correctly
- [ ] Database saves query history
- [ ] Tests pass

### Commands

```bash
# 1. Start services
redis-server &
celery -A finagent.celery_app worker --loglevel=info &
uv run uvicorn finagent.main:app --reload --port 8000 &

# 2. Test CLI (synchronous)
uv run python scripts/cli_research.py "Test query"

# 3. Test HTTP API (async)
TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query"}' | jq -r .task_id)

echo "Task ID: $TASK_ID"

# Poll status
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/research/tasks/$TASK_ID | jq -r .status)
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 3
done

# 4. Test WebSocket (async + streaming)
# Use frontend or Python WebSocket client

# 5. Check Flower dashboard
open http://localhost:5555
```

---

## Comparison: Original vs. Revised Plan

| Aspect | Original Plan | Revised Plan |
|--------|---------------|--------------|
| **CLI** | Convert to Celery | ✅ Keep synchronous (0 hours) |
| **HTTP API** | Full implementation | ✅ Async tasks + polling (3-4 hours) |
| **WebSocket** | Full rewrite | ✅ Enhance existing (4-5 hours) |
| **Database** | Complete setup | ✅ Same (1 hour) |
| **Testing** | Extensive | ✅ Focused (2-3 hours) |
| **Total Time** | 12-20 hours | **9-12 hours** ⚡ |
| **Complexity** | High | **Medium** ⭐⭐ |
| **CLI Usability** | Requires Celery | ✅ **Works standalone** |
| **Production Ready** | Yes | ✅ **Yes** |

---

## Summary

**Revised approach is simpler and faster:** ✅

1. **CLI: Keep synchronous** (0 hours)
   - No changes needed
   - Works without Celery
   - Perfect for development

2. **HTTP API: Async tasks** (3-4 hours)
   - Submit queries to Celery
   - Poll for status
   - REST-friendly

3. **WebSocket: Async + streaming** (4-5 hours)
   - Real-time events
   - Progress updates
   - Best UX

4. **Testing & Docs** (2-3 hours)
   - API tests
   - Documentation updates
   - Final verification

**Total: 9-12 hours** (25% faster than original plan)

**Next step:** Proceed with Phase 2 (HTTP API implementation)?
