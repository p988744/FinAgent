# OpenAI API Switch Test Results

**Date:** 2025-11-24
**Status:** ⚠️ Tests Failed - Different Issue

---

## 🔧 What We Did

1. ✅ **Switched to OpenAI API**
   - Updated `.env`: `LLM_BASE_URL=` (empty = OpenAI)
   - Updated `.env`: `EMBEDDING_BASE_URL=` (empty = OpenAI)
   - Restarted Celery with `--concurrency=1`

2. ✅ **Ran E2E Tests**
   - Tests failed immediately (9.6 seconds)
   - No timeout this time!

---

## ❌ Test Results

```
✘  Test 1 - FAILED (9.6s)
Error: text=/處理中|執行中|in.?progress|processing/i not visible
Timeout: 5000ms

✘  Test 2 - FAILED (20ms)
Error: expect(response.ok()).toBeTruthy()
Received: false
```

---

## 🔍 Root Cause

**The query wasn't submitted to Celery at all!**

### Evidence:
1. ✅ Backend health check: OK (`/health` returns `{"status":"ok"}`)
2. ✅ Celery running: Concurrency=1, ready for tasks
3. ❌ Celery logs: **No tasks received**
4. ❌ API endpoint: Returns `{"detail":"Not Found"}`

### Investigation:
- Research router defined: `/api/v1/research` (line 17 in research.py)
- Endpoint exists: `@router.post("/query/async", ...)` (line 63)
- Router included in main app (line 77 in main.py)
- **But:** curl test shows endpoint returns "Not Found"

---

## 🤔 Possible Issues

### Issue 1: Frontend Using Wrong Endpoint
The frontend might be calling a different endpoint than `/api/v1/research/query/async`.

**Check:** Frontend API service configuration

### Issue 2: Backend Not Fully Initialized
Backend might have failed to initialize the research routes.

**Check:** Backend startup logs for errors

### Issue 3: Port Mismatch
Frontend might be calling wrong backend port.

**Check:** Frontend `.env` for `BACKEND_URL`

### Issue 4: CORS or Network Issue
Request might be blocked before reaching the endpoint.

**Check:** Browser dev tools network tab

---

## ✅ What We Confirmed

1. **OpenAI API works** - No LLM timeout issue (tests failed fast, not slow)
2. **Celery concurrency=1 works** - Only one worker ready
3. **Sequential test configuration works** - Tests run one at a time
4. **Backend runs** - Health check passes

---

## 🎯 Next Steps

### Option 1: Debug Frontend API Service
```typescript
// Check src/services/api.ts
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Verify it's calling the correct endpoint:
const response = await fetch(`${BACKEND_URL}/api/v1/research/query/async`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query_text, workflow_version })
});
```

### Option 2: Test Backend Endpoint Directly
```bash
# Test if endpoint works with curl
curl -X POST 'http://localhost:8000/api/v1/research/query/async' \
  -H 'Content-Type: application/json' \
  -d '{"query_text": "玉山銀行洗錢防制裁罰", "workflow_version": "v1.1"}'

# Expected: {"session_id": "...", "task_id": "..."}
# Actual: {"detail":"Not Found"} ❌
```

### Option 3: Check Backend Startup
```bash
# Restart backend and check logs
pkill -f "uvicorn.*finagent"
uv run uvicorn finagent.main:app --reload --port 8000 2>&1 | tee /tmp/backend_startup.log

# Look for:
# - "Application startup complete"
# - Research router registration
# - Any errors during startup
```

---

## 📊 Comparison: llmgw vs OpenAI

| Aspect | llmgw | OpenAI |
|--------|-------|--------|
| **Test Duration** | 30-60s (timeout) | 9.6s (fast fail) |
| **Celery Received Tasks** | ✅ Yes | ❌ No |
| **Query Processing** | Started then timeout | Never started |
| **Error Type** | LLM timeout | Endpoint not found |

**Conclusion:** Switching to OpenAI revealed a different issue - the API endpoint isn't being called correctly!

---

## 💡 Key Insight

**The LLM timeout issue masked an API routing problem!**

When using llmgw:
- Frontend successfully called the API ✅
- Query was submitted to Celery ✅
- Celery started processing ✅
- **But:** LLM calls timed out ❌

When using OpenAI:
- Frontend tried to call the API ❌
- Query NOT submitted to Celery ❌
- **Different problem entirely!**

This suggests:
1. The E2E tests might have been working with an older API structure
2. The tests need to be updated for the current v1.1 API
3. OR there's a recent breaking change in the API routes

---

## 🔍 Investigation Needed

1. **Check when the research API was last changed**
   ```bash
   git log --oneline -- src/finagent/api/routes/research.py
   ```

2. **Check what the tests expect**
   ```bash
   grep -n "api/v1/research" frontend/tests/e2e/research-query.spec.ts
   ```

3. **Check if there are multiple backend versions running**
   ```bash
   ps aux | grep uvicorn
   lsof -i :8000
   ```

---

## 📝 Summary

| Item | Status |
|------|--------|
| Switched to OpenAI | ✅ DONE |
| Celery concurrency=1 | ✅ DONE |
| Sequential tests | ✅ DONE |
| Tests pass | ❌ NO - Different issue |
| Root cause | API endpoint not found |
| LLM timeout fixed | ✅ YES (but reveals API issue) |

**Recommendation:** Fix the API routing issue first, then retest with OpenAI.

---

**Status:** Investigation needed - API endpoint routing problem
**Next Action:** Check frontend API service and backend route registration
