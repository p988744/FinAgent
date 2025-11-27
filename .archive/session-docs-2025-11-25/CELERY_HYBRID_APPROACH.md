# Celery Hybrid Approach - Sync CLI + Async API/WebSocket

**Date:** 2025-11-21
**Version:** v1.1
**Approach:** Best of both worlds - Simple CLI + Scalable API

---

## 🎯 Architecture Design

### User's Insight
> "cli script can be sync, then http api should be async task, websocket be async task and streaming status of tasks"

**This is the correct approach!** ✅

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  CLI Scripts (Sync)          HTTP API (Async)      WebSocket (Async)│
│       ↓                           ↓                      ↓          │
│  Direct Call              Celery Task           Celery Task         │
│  AgentOrchestrator        + Progress           + Stream Events      │
│       ↓                           ↓                      ↓          │
│  Immediate Result         Task ID              Real-time Updates    │
│                          Long-polling                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Three Execution Modes

#### 1. **CLI Scripts: Synchronous** (Simple & Direct)
```bash
# Direct execution, wait for result
uv run python scripts/cli_research.py "Query"
└─> AgentOrchestrator.stream_query()
    └─> Immediate streaming output to terminal
    └─> Return final result
```

**Characteristics:**
- ✅ No Celery needed
- ✅ Simple debugging
- ✅ Direct feedback
- ✅ Perfect for development

#### 2. **HTTP API: Async Tasks** (REST + Polling)
```bash
# Submit task, get task_id
POST /api/v1/research/query
└─> Celery task submitted
    └─> Return: {"task_id": "abc-123", "status": "pending"}

# Poll for status
GET /api/v1/research/tasks/{task_id}
└─> Return: {"status": "running", "progress": 60%, ...}

# Get result when complete
GET /api/v1/research/tasks/{task_id}/result
└─> Return: {"status": "completed", "response": "...", ...}
```

**Characteristics:**
- ✅ Non-blocking
- ✅ Scalable (multiple workers)
- ✅ Works with any HTTP client
- ✅ Task ID for tracking

#### 3. **WebSocket: Async Tasks + Streaming** (Real-time)
```bash
# Connect WebSocket
WS /api/v1/research/stream
└─> Client sends: {"query": "...", "use_plan_execute": true}
    └─> Backend submits Celery task
        └─> Stream task events to client:
            ├─> {"event": "task_started", "task_id": "abc-123"}
            ├─> {"event": "query_analyzer", "data": {...}}
            ├─> {"event": "planner", "data": {...}}
            ├─> {"event": "executor", "data": {...}}
            ├─> {"event": "progress", "percent": 60}
            └─> {"event": "completed", "result": {...}}
```

**Characteristics:**
- ✅ Real-time streaming
- ✅ Progress updates
- ✅ Best UX for frontend
- ✅ Automatic reconnection handling

---

## Implementation Plan

### Phase 1: Keep CLI Synchronous ✅ (No Changes Needed)

**Current CLI scripts work perfectly:**

```python
# scripts/cli_research.py (KEEP AS IS)
async def research_query(query_text, verbose=False):
    """Direct synchronous execution - no Celery needed."""
    orchestrator = AgentOrchestrator()

    async for node_name, state_update in orchestrator.stream_query(
        query=Query(text=query_text),
        use_plan_execute=True
    ):
        # Print updates immediately
        print(f"[{node_name}] {state_update}")

    return final_result
```

**Benefits:**
- ✅ Simple debugging
- ✅ No background services needed for dev
- ✅ Direct output to terminal
- ✅ Immediate results

**Keep these CLI scripts synchronous:**
- `scripts/cli_research.py` ✅
- `scripts/cli_retrieval.py` ✅
- `scripts/cli_import.py` ✅

---

### Phase 2: HTTP API with Async Tasks (NEW)

**File:** `src/finagent/api/routes/research.py`

```python
"""Research API with Celery task queue."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from finagent.tasks import research_query_task
from celery.result import AsyncResult

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
    status: str  # pending, running, completed, failed
    progress: Optional[float] = None
    current_step: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/query", response_model=TaskResponse)
async def submit_research_query(request: QueryRequest):
    """
    Submit research query as async Celery task.

    Returns task_id for polling status.
    """
    # Submit to Celery
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
    """
    Poll task status.

    Client should call this endpoint periodically (every 2-5 seconds).
    """
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
        # Custom state for progress tracking
        response.status = "running"
        response.progress = result.info.get('progress', 0)
        response.current_step = result.info.get('current_step', '')

    return response


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """
    Get final task result (blocking until complete).

    Use this for simpler clients that don't want to poll.
    """
    result = AsyncResult(task_id)

    try:
        # Wait up to 5 minutes for result
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

**Client Usage Example:**

```typescript
// Submit query
const response = await fetch('/api/v1/research/query', {
  method: 'POST',
  body: JSON.stringify({ query: '玉山銀行洗錢防制裁罰' })
});
const { task_id } = await response.json();

// Poll for status
const interval = setInterval(async () => {
  const status = await fetch(`/api/v1/research/tasks/${task_id}`);
  const data = await status.json();

  console.log(`Progress: ${data.progress}% - ${data.current_step}`);

  if (data.status === 'completed') {
    clearInterval(interval);
    console.log('Result:', data.result);
  } else if (data.status === 'failed') {
    clearInterval(interval);
    console.error('Error:', data.error);
  }
}, 3000); // Poll every 3 seconds
```

---

### Phase 3: WebSocket with Async Tasks + Streaming (ENHANCED)

**File:** `src/finagent/api/routes/websocket.py` (UPDATE)

```python
"""WebSocket endpoint with Celery task streaming."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import AsyncGenerator
import asyncio
import json

from finagent.tasks import research_query_task
from finagent.celery_app import celery_app


async def stream_task_events(task_id: str) -> AsyncGenerator[dict, None]:
    """
    Stream Celery task events to WebSocket client.

    This monitors the task and yields events as they occur.
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)

    # Yield initial event
    yield {
        "event": "task_started",
        "task_id": task_id,
        "status": result.status
    }

    # Poll task state and stream updates
    while not result.ready():
        await asyncio.sleep(0.5)  # Check every 500ms

        # Check for progress updates
        if result.status == "PROGRESS":
            yield {
                "event": "progress",
                "task_id": task_id,
                "data": result.info
            }

        # Check for custom events (stored in backend)
        # This requires custom task implementation with state updates

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
    """
    WebSocket endpoint for real-time query streaming with Celery.

    Client sends:
    {
        "query": "玉山銀行洗錢防制裁罰",
        "use_plan_execute": true,
        "user_id": "user123",
        "session_id": "session456"
    }

    Server streams:
    {"event": "task_started", "task_id": "abc-123"}
    {"event": "query_analyzer", "data": {...}}
    {"event": "planner", "data": {...}}
    {"event": "progress", "percent": 60}
    {"event": "executor", "data": {...}}
    {"event": "completed", "result": {...}}
    """
    await websocket.accept()

    try:
        # Receive query from client
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

        # Stream task events
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

**Enhanced Task with Progress Updates:**

**File:** `src/finagent/tasks.py` (UPDATE)

```python
"""Celery tasks with progress tracking."""

from celery import Task
from finagent.celery_app import celery_app


class ProgressTrackingTask(Task):
    """Task that reports progress updates."""

    def update_progress(self, state, meta):
        """Update task progress for WebSocket streaming."""
        self.update_state(state=state, meta=meta)


@celery_app.task(
    bind=True,
    base=ProgressTrackingTask,
    name='finagent.tasks.research_query'
)
def research_query_task(self, query_text, use_plan_execute=True, **kwargs):
    """Research query with progress tracking."""

    # Report: Task started
    self.update_progress('PROGRESS', {
        'current_step': 'query_analyzer',
        'progress': 10
    })

    # Execute query with progress callbacks
    async def execute_with_progress():
        orchestrator = AgentOrchestrator(checkpointer=checkpointer)

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
                'progress': progress,
                'data': state_update
            })

            # Store results
            if node_name == "query_analyzer":
                result['query_insight'] = state_update.get('query_insight')
            elif node_name == "planner":
                result['plan'] = state_update.get('plan')
            elif node_name == "reporter":
                result['response'] = state_update.get('response')

        return result

    # Run async execution
    result = asyncio.run(execute_with_progress())

    # Save to database
    checkpoint_db.update_query_result(query_id, **result)

    return result
```

**Client Usage (Frontend):**

```typescript
// Connect WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/research/stream');

ws.onopen = () => {
  // Send query
  ws.send(JSON.stringify({
    query: '玉山銀行洗錢防制裁罰',
    use_plan_execute: true,
    user_id: 'user123',
    session_id: 'session456'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.event) {
    case 'task_started':
      console.log('Task ID:', data.task_id);
      setTaskId(data.task_id);
      break;

    case 'progress':
      console.log(`Progress: ${data.data.progress}%`);
      console.log(`Step: ${data.data.current_step}`);
      setProgress(data.data.progress);

      // Update UI based on current step
      if (data.data.current_step === 'planner' && data.data.data.plan) {
        setPlan(data.data.data.plan);
      }
      break;

    case 'completed':
      console.log('Query completed!');
      setResult(data.result);
      ws.close();
      break;

    case 'failed':
      console.error('Query failed:', data.error);
      setError(data.error);
      ws.close();
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket closed');
};
```

---

## Comparison Matrix

| Feature | CLI (Sync) | HTTP API (Async) | WebSocket (Async + Stream) |
|---------|-----------|------------------|---------------------------|
| **Execution** | Direct call | Celery task | Celery task |
| **Response** | Immediate | Task ID + Polling | Real-time events |
| **Progress** | Terminal output | Polling endpoint | Streaming events |
| **Use Case** | Development, debugging | REST clients, simple integration | Frontend UI, real-time UX |
| **Complexity** | Simple ⭐ | Medium ⭐⭐ | Complex ⭐⭐⭐ |
| **Scalability** | Single user | Multi-user ✅ | Multi-user ✅ |
| **Reconnection** | N/A | Resume with task_id | Auto-reconnect + resume |
| **Best For** | CLI tools, scripts | Mobile apps, external APIs | Web dashboard |

---

## Implementation Priority

### Phase 1: CLI Stays Synchronous ✅ (0 hours - Already done)
- No changes needed
- Current scripts work perfectly
- Keep for development and debugging

### Phase 2: HTTP API with Async Tasks 🔴 (3-4 hours)
**Priority: HIGH**
- Create `/api/v1/research/query` endpoint
- Create `/api/v1/research/tasks/{task_id}` status endpoint
- Implement task polling
- Test with Postman/curl

**Deliverables:**
- REST API endpoints
- Task submission
- Status polling
- Result retrieval

### Phase 3: WebSocket with Streaming 🟡 (4-5 hours)
**Priority: MEDIUM**
- Enhance WebSocket endpoint with Celery integration
- Implement progress tracking in tasks
- Stream events to client
- Test with frontend

**Deliverables:**
- Real-time WebSocket streaming
- Progress updates
- Plan/results streaming
- Reconnection handling

### Phase 4: Database Persistence 🟢 (2-3 hours)
**Priority: LOW (Nice to have)**
- Add query_history table
- Track all queries
- Enable history queries
- Analytics dashboard

---

## Files to Create/Modify

### New Files (HTTP API)
```
src/finagent/api/routes/research.py     - REST endpoints
tests/test_api_research.py              - API tests
```

### Modified Files (WebSocket)
```
src/finagent/api/routes/websocket.py    - Enhanced with Celery streaming
src/finagent/tasks.py                   - Progress tracking
```

### Keep Unchanged (CLI)
```
scripts/cli_research.py                 - ✅ No changes (sync)
scripts/cli_retrieval.py                - ✅ No changes (sync)
scripts/cli_import.py                   - ✅ No changes (sync)
```

---

## Testing Strategy

### 1. CLI (Synchronous) - Already tested ✅
```bash
uv run python scripts/cli_research.py "玉山銀行洗錢防制裁罰"
# Immediate output, direct execution
```

### 2. HTTP API (Async Tasks)
```bash
# Test task submission
curl -X POST http://localhost:8000/api/v1/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "玉山銀行洗錢防制裁罰"}'

# Response: {"task_id": "abc-123", "status": "pending"}

# Test status polling
curl http://localhost:8000/api/v1/research/tasks/abc-123

# Response: {"status": "running", "progress": 60, "current_step": "executor"}

# Wait for completion
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/research/tasks/abc-123 | jq -r .status)
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 3
done

# Get result
curl http://localhost:8000/api/v1/research/tasks/abc-123/result
```

### 3. WebSocket (Async + Streaming)
```python
# Test WebSocket streaming
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/research/stream"

    async with websockets.connect(uri) as websocket:
        # Send query
        await websocket.send(json.dumps({
            "query": "玉山銀行洗錢防制裁罰",
            "use_plan_execute": True
        }))

        # Receive streaming events
        async for message in websocket:
            event = json.loads(message)
            print(f"Event: {event['event']}")

            if event['event'] == 'progress':
                print(f"  Progress: {event['data']['progress']}%")
                print(f"  Step: {event['data']['current_step']}")

            elif event['event'] == 'completed':
                print("Query completed!")
                print(f"Result: {event['result']['response']}")
                break

asyncio.run(test_websocket())
```

---

## Decision: Which Mode for Production?

### Recommendation: **All Three** 🎯

| Mode | Use Case | When to Use |
|------|----------|-------------|
| **CLI (Sync)** | Development, debugging, batch processing | Always keep for developers |
| **HTTP API (Async)** | REST clients, mobile apps, external integrations | Production for external APIs |
| **WebSocket (Async + Stream)** | Web dashboard, real-time UI | Production for frontend |

**Why all three?**
1. **CLI** - Essential for development and scripting
2. **HTTP API** - Standard REST integration for external clients
3. **WebSocket** - Best UX for interactive web application

---

## Minimal Implementation (MVP)

If you need to start quickly, implement in this order:

### Week 1: Phase 2 (HTTP API) - 1 day
- REST endpoints for query submission
- Task status polling
- Simple but functional

### Week 2: Phase 3 (WebSocket) - 1 day
- Real-time streaming
- Better UX
- Frontend integration

### Week 3: Phase 4 (Database) - 1 day
- Query history
- Analytics
- Production-ready

**Total: 3 days for full async implementation**

---

## Summary

**User's Approach is Correct:** ✅

- **CLI scripts: Synchronous** → Keep as is, no Celery needed
- **HTTP API: Async tasks** → Submit to Celery, poll for status
- **WebSocket: Async tasks + streaming** → Real-time event streaming

**Implementation Focus:**
1. ✅ Keep CLI simple and synchronous (0 hours)
2. 🔴 Add HTTP API with Celery tasks (3-4 hours)
3. 🟡 Enhance WebSocket with streaming (4-5 hours)
4. 🟢 Add database persistence (2-3 hours)

**Total: 9-12 hours** (vs. 12-20 hours in original plan)

**Next Step:** Implement Phase 2 (HTTP API with async tasks) first, then Phase 3 (WebSocket streaming).

Would you like me to start implementing Phase 2 (HTTP API endpoints)?
