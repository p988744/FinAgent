# Implementation Decision - Celery Hybrid Approach

**Date:** 2025-11-21
**Decision:** Sync CLI + Async API/WebSocket
**Status:** ✅ Approved by User

---

## User's Requirement

> "cli script can be sync, then http api should be async task, websocket be async task and streaming status of tasks"

**This is the correct approach!** ✅

---

## Decision Summary

### Three Execution Modes

| Mode | Execution | Use Case | Changes Needed |
|------|-----------|----------|----------------|
| **CLI Scripts** | Synchronous | Development, debugging, batch jobs | ✅ None (keep as is) |
| **HTTP API** | Async (Celery tasks + polling) | REST clients, mobile apps, external APIs | 🔴 Implement (3-4 hours) |
| **WebSocket** | Async (Celery tasks + streaming) | Web dashboard, real-time UI | 🟡 Enhance (4-5 hours) |

---

## Architecture

### CLI (Synchronous) - No Changes ✅
```
User → CLI Script → AgentOrchestrator → LangGraph → Terminal Output
```

**Characteristics:**
- Direct execution (no Celery)
- Immediate feedback
- Perfect for development
- No background services needed

**Files:**
- `scripts/cli_research.py` (keep as is)
- `scripts/cli_retrieval.py` (keep as is)
- `scripts/cli_import.py` (keep as is)

---

### HTTP API (Async) - Implement 🔴
```
Client → POST /api/v1/research/query → Celery Task
                                          ↓
                                    [Background execution]
                                          ↓
Client ← GET /api/v1/research/tasks/{id} ← Task status/result
```

**Characteristics:**
- Non-blocking submission
- Poll for status/result
- Scalable (multiple workers)
- REST-friendly

**New Files:**
- `src/finagent/api/routes/research.py` (create)
- `src/finagent/celery_app.py` (create)
- `src/finagent/tasks.py` (create)
- `src/finagent/database/checkpoint_db.py` (create)

**Endpoints:**
- `POST /api/v1/research/query` - Submit query
- `GET /api/v1/research/tasks/{task_id}` - Poll status
- `GET /api/v1/research/tasks/{task_id}/result` - Get result
- `DELETE /api/v1/research/tasks/{task_id}` - Cancel task

---

### WebSocket (Async + Streaming) - Enhance 🟡
```
Client → WS /api/v1/research/stream → Celery Task
                                         ↓
                              [Background execution]
                                         ↓
Client ← Real-time events ← Stream: progress, plan, results
```

**Characteristics:**
- Real-time event streaming
- Progress updates (0-100%)
- Plan/results as they're generated
- Best UX for interactive apps

**Modified Files:**
- `src/finagent/api/routes/websocket.py` (enhance)
- `src/finagent/tasks.py` (add progress tracking)

**Events Streamed:**
- `task_started` - Task ID assigned
- `progress` - Current step + percentage
- `plan_created` - Plan generated
- `executor_update` - Task execution results
- `completed` - Final response
- `failed` - Error details

---

## Implementation Phases

### Phase 0: Prerequisites (1 hour)
**Dependencies:**
```bash
uv add celery[redis] langgraph-checkpoint-postgres psycopg[binary,pool]
brew install redis postgresql@16
```

**Database setup:**
```bash
createdb finagent
psql finagent < src/finagent/database/query_history_schema.sql
```

---

### Phase 1: Keep CLI Synchronous (0 hours) ✅
**Status:** Already complete

**No changes needed!** Current CLI scripts work perfectly without Celery.

**Verification:**
```bash
uv run python scripts/cli_research.py "Test query"
```

---

### Phase 2: HTTP API with Async Tasks (3-4 hours) 🔴
**Priority:** HIGH

**Tasks:**
1. Create `checkpoint_db.py` (1 hour)
2. Create `celery_app.py` (30 min)
3. Create `tasks.py` (1 hour)
4. Create `research.py` API endpoints (1-2 hours)

**Deliverables:**
- REST API for query submission
- Task status polling
- Result retrieval
- Task cancellation

**Testing:**
```bash
# Start services
celery -A finagent.celery_app worker --loglevel=info &
uv run uvicorn finagent.main:app --reload --port 8000

# Submit query
curl -X POST http://localhost:8000/api/v1/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "玉山銀行洗錢防制裁罰"}'

# Poll status
curl http://localhost:8000/api/v1/research/tasks/<task_id>
```

---

### Phase 3: WebSocket with Streaming (4-5 hours) 🟡
**Priority:** MEDIUM

**Tasks:**
1. Enhance WebSocket endpoint (2-3 hours)
2. Add progress tracking to tasks (1 hour)
3. Update frontend hooks (1-2 hours)

**Deliverables:**
- Real-time WebSocket streaming
- Progress updates
- Plan/results streaming
- Reconnection handling

**Testing:**
```python
import asyncio
import websockets
import json

async def test():
    ws = await websockets.connect('ws://localhost:8000/api/v1/research/stream')
    await ws.send(json.dumps({"query": "Test query"}))

    async for msg in ws:
        event = json.loads(msg)
        print(f"{event['event']}: {event.get('data', {}).get('progress')}%")

asyncio.run(test())
```

---

### Phase 4: Testing & Documentation (2-3 hours) 🟢
**Priority:** LOW

**Tasks:**
1. Write API tests (1 hour)
2. Update CLAUDE.md (30 min)
3. Update V1_1_RELEASE_PLAN.md (30 min)
4. Create operations guide (1 hour)

---

## Time Estimate

| Phase | Time | Priority |
|-------|------|----------|
| 0. Prerequisites | 1 hour | Required |
| 1. CLI (sync) | 0 hours | ✅ Done |
| 2. HTTP API | 3-4 hours | 🔴 HIGH |
| 3. WebSocket | 4-5 hours | 🟡 MEDIUM |
| 4. Testing/Docs | 2-3 hours | 🟢 LOW |
| **Total** | **9-12 hours** | |

**Comparison:** Original plan was 12-20 hours (25% faster!) ⚡

---

## Benefits of This Approach

### ✅ Simplicity
- CLI remains simple (no Celery dependency)
- Clear separation of concerns
- Easier to debug

### ✅ Flexibility
- Use CLI for development
- Use HTTP API for external integrations
- Use WebSocket for real-time UI

### ✅ Scalability
- HTTP API scales with Celery workers
- WebSocket scales with connection pooling
- CLI doesn't need scaling

### ✅ Developer Experience
- Quick CLI testing without background services
- Production-ready API with async execution
- Real-time feedback for end users

---

## What's Different from Original Plan?

| Original Plan | Revised Plan | Benefit |
|---------------|--------------|---------|
| Convert CLI to use Celery | Keep CLI synchronous | ✅ Simpler development |
| Full database persistence for all modes | Only for API/WebSocket | ✅ Less complexity |
| Single execution path | Three execution paths | ✅ More flexibility |
| 12-20 hours | 9-12 hours | ⚡ 25% faster |

---

## Documentation Structure

### For Users
- [CELERY_QUICK_REFERENCE.md](CELERY_QUICK_REFERENCE.md) - Quick overview
- [CELERY_HYBRID_APPROACH.md](CELERY_HYBRID_APPROACH.md) - Architecture details

### For Developers
- [CELERY_ROADMAP_REVISED.md](CELERY_ROADMAP_REVISED.md) - Implementation plan
- [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md) - Code examples

### For Context
- [CELERY_INTEGRATION_STATUS.md](CELERY_INTEGRATION_STATUS.md) - Overall status
- [SESSION_SUMMARY_2025_11_21.md](SESSION_SUMMARY_2025_11_21.md) - Session notes

---

## Next Steps

### Immediate (Phase 2)
1. Read [CELERY_ROADMAP_REVISED.md](CELERY_ROADMAP_REVISED.md)
2. Install dependencies (PostgreSQL, Redis)
3. Create database helper (checkpoint_db.py)
4. Create Celery app (celery_app.py)
5. Create research task (tasks.py)
6. Create HTTP API endpoints (research.py)

### Follow-up (Phase 3)
7. Enhance WebSocket endpoint
8. Add progress tracking
9. Update frontend

### Final (Phase 4)
10. Write tests
11. Update documentation
12. Deploy to production

---

## Decision Matrix

### Should I implement this now?

**YES, if:**
- ✅ Need to support concurrent users
- ✅ Queries blocking UI is a problem
- ✅ Want query history and audit trail
- ✅ Need production-ready async API
- ✅ Have 9-12 hours available

**NO, if:**
- ❌ Single-user CLI is sufficient
- ❌ No concurrent users needed
- ❌ Timeline is very tight (< 1 day)

**DEFER to v1.2, if:**
- ⏸️ Current system meets immediate needs
- ⏸️ Want to validate v1.1 in production first
- ⏸️ Other priorities (frontend polish, features)

---

## Approval Status

**User Feedback:** ✅ Approved
> "cli script can be sync, then http api should be async task, websocket be async task and streaming status of tasks"

**Recommendation:** ✅ Proceed with implementation

**Start with:** Phase 2 (HTTP API) - 3-4 hours

---

## Success Criteria

After implementation:

### Functional ✅
- [ ] CLI scripts work without Celery
- [ ] HTTP API accepts queries and returns task IDs
- [ ] Status polling works correctly
- [ ] WebSocket streams events in real-time
- [ ] Progress tracking accurate (0-100%)

### Performance ✅
- [ ] Query execution time: ~40-50s (same as before)
- [ ] Concurrent queries: 10+ supported
- [ ] API response time: < 100ms (for submission)
- [ ] WebSocket latency: < 500ms

### Quality ✅
- [ ] Tests pass (API, WebSocket)
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Production-ready

---

## Rollback Plan

If issues arise:

```bash
# 1. Keep using CLI (always works)
uv run python scripts/cli_research.py "Query"

# 2. Disable API endpoints (if needed)
# Comment out router registration in main.py

# 3. Stop Celery worker
pkill -f "celery.*worker"

# 4. Revert code changes
git revert <commit-hash>
```

---

## Summary

**Decision:** Implement hybrid approach (Sync CLI + Async API/WebSocket)

**Rationale:**
1. ✅ Simpler - CLI remains synchronous
2. ✅ Faster - 25% less time than original plan
3. ✅ Flexible - Three execution modes for different use cases
4. ✅ Production-ready - Scalable async API with real-time streaming

**Timeline:** 9-12 hours (2 days)

**Status:** Ready to implement

**Next:** Proceed with Phase 2 (HTTP API endpoints)

---

**Last Updated:** 2025-11-21
**Approved By:** User
**Ready for Implementation:** ✅ Yes
