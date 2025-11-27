# Celery Concurrency Fix for Sequential E2E Testing

**Date:** 2025-11-24
**Issue:** E2E tests still timeout even with sequential Playwright execution
**Root Cause:** Celery has 10 workers by default, processing queries in parallel

---

## 🔍 The Problem

### What We Thought
```
Playwright (sequential) → Query 1 → Wait → Query 2 → Wait → Query 3...
```

### What Actually Happens
```
Playwright (sequential) → submits Query 1, 2, 3, 4, 5 (spaced by 3s)
                           ↓
                    Celery Worker Pool (10 workers)
                           ↓
            Worker-8: Query 1  (processing...)
            Worker-1: Query 2  (processing...)
            Worker-9: Query 3  (processing...)
            Worker-2: Query 4  (processing...)
            Worker-10: Query 5 (processing...)
                           ↓
                  All 5 queries run IN PARALLEL
                  → LLM gateway overloaded
                  → All timeout ❌
```

**The Issue:**
- Playwright submits queries sequentially (with 3s delays)
- But Celery **queues them up** and assigns to available workers
- With 10 workers, all 5 queries get processed **simultaneously**
- LLM gateway gets overwhelmed → all timeout

---

## ✅ The Solution

### Configure Celery with 1 Worker (Sequential Processing)

**Change:** Start Celery with `--concurrency=1` to process one task at a time

```bash
# Instead of:
uv run celery -A finagent.celery_app worker --loglevel=info

# Use:
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=1
```

**Result:**
```
Celery Worker (concurrency=1):
  Worker-1: Query 1 → completes → Query 2 → completes → Query 3...
```

---

## 📊 Expected Behavior After Fix

### Celery Logs (Should Show Sequential Processing)
```
[10:00:00] Worker-1: Query 1 → Analyzing query...
[10:00:03] Worker-1: Query analysis complete
[10:00:10] Worker-1: Planner complete
[10:00:11] Worker-1: Executor complete
[10:00:13] Worker-1: Replanner complete
[10:00:33] Worker-1: Reporter complete
[10:00:35] Worker-1: Query 1 COMPLETED ✅

[10:00:38] Worker-1: Query 2 → Analyzing query...
[10:00:41] Worker-1: Query analysis complete
...
[10:01:13] Worker-1: Query 2 COMPLETED ✅
```

**Key Observations:**
- Only **Worker-1** is active
- Queries process **one at a time**
- Each query completes before next starts
- No concurrent load on LLM gateway

---

## 🔧 Implementation

###Step 1: Stop Current Celery Worker

```bash
# Kill existing workers
pkill -f "celery.*finagent"
```

### Step 2: Start Celery with Concurrency=1

```bash
# In backend directory
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=1
```

### Step 3: Run E2E Tests

```bash
# In frontend directory
cd frontend
npm run test:e2e
```

---

## 📋 Complete Test Flow

**1. Backend Setup:**
```bash
# Terminal 1: Start backend API
uv run uvicorn finagent.main:app --reload --port 8000

# Terminal 2: Start Celery with concurrency=1
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=1
```

**2. Frontend Setup:**
```bash
# Terminal 3: Start frontend dev server
cd frontend
npm run dev
```

**3. Run Tests:**
```bash
# Terminal 4: Run E2E tests
cd frontend
npm run test:e2e
```

**Expected Duration:** ~3-4 minutes for 5 tests

---

## ✅ Why This Works

### Matching System Design

**Production:**
- 1-2 concurrent users maximum
- Users work sequentially (read reports before next query)
- LLM gateway handles light load

**Testing (After Fix):**
- 1 Celery worker (sequential processing)
- Queries processed one at a time
- LLM gateway handles light load
- **Matches production behavior** ✅

### Avoiding Unrealistic Scenarios

**Before Fix:**
- 10 Celery workers
- 5 queries processed simultaneously
- Heavy sustained load on LLM gateway
- **Unrealistic stress test** ❌

**After Fix:**
- 1 Celery worker
- 1 query processed at a time
- Light sequential load on LLM gateway
- **Realistic usage test** ✅

---

## 🎯 Alternative: Create Test-Specific Celery Configuration

**For cleaner separation, create a test configuration file:**

```python
# celery_test.py
from finagent.celery_app import app

# Override concurrency for testing
app.conf.worker_concurrency = 1
```

**Start with:**
```bash
uv run celery -A celery_test worker --loglevel=info
```

---

## 📊 Evidence from Logs

### Before Fix (10 Workers)
```
Worker-8: Query 1 → QueryAnalyzer (timeout after 60s)
Worker-1: Query 2 → QueryAnalyzer (timeout after 60s)
Worker-9: Query 3 → QueryAnalyzer (timeout after 60s)
Worker-2: Query 4 → QueryAnalyzer (timeout after 60s)
Worker-10: Query 5 → QueryAnalyzer (timeout after 60s)

All 5 queries timeout → LLM gateway overloaded ❌
```

### After Fix (1 Worker) - Expected
```
Worker-1: Query 1 → completes in 35s ✅
Worker-1: Query 2 → completes in 34s ✅
Worker-1: Query 3 → completes in 33s ✅
Worker-1: Query 4 → completes in 32s ✅
Worker-1: Query 5 → completes in 36s ✅

All 5 queries pass → Sequential processing works ✅
```

---

## 🔍 Why Wasn't This Obvious?

### Common Assumption (Incorrect)
> "Playwright sequential execution → Celery sequential processing"

### Reality
> "Playwright sequential execution → Celery **queues tasks** → Worker pool processes in parallel"

**The Learning:**
- Frontend test configuration (Playwright) doesn't control backend processing (Celery)
- Celery has its own concurrency settings independent of test framework
- Need to align **both** frontend test execution AND backend task processing

---

## ✅ Summary

### Root Cause
- Playwright submits queries sequentially ✅
- Celery processes them in parallel with 10 workers ❌
- LLM gateway gets overwhelmed ❌

### Solution
- Configure Celery with `--concurrency=1` ✅
- Queries process one at a time ✅
- LLM gateway handles light load ✅

### Command
```bash
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=1
```

---

**Status:** Ready to implement
**Next Step:** Restart Celery with concurrency=1 and rerun E2E tests
