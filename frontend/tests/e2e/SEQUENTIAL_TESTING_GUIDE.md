# Sequential E2E Testing Guide

**Purpose:** Document why we use sequential testing for research query E2E tests

---

## 🎯 Why Sequential Testing?

### Real User Behavior

**Typical Research Session:**
```
10:00:00 - User submits query: "玉山銀行洗錢防制裁罰"
10:00:35 - System returns comprehensive report with citations
10:01:00 - User reads report (2-5 minutes)
10:03:30 - User submits follow-up: "2020年相關案例"
10:04:05 - System returns analysis
```

**Key Observation:**
- Users submit **one query at a time**
- Users **read results** before submitting next query
- Queries are naturally **staggered**, not simultaneous

### Application Type

FinAgent is a **legal research assistant**, not a chatbot:
- Provides comprehensive reports with citations
- 30-40 second response time is **acceptable**
- Target users: Compliance officers, legal researchers
- Users value **accuracy** over speed

---

## ⚙️ Configuration

### Test File Configuration

```typescript
// research-query.spec.ts
test.describe('Research Query E2E Tests', () => {
  // Configure for SEQUENTIAL execution (one test at a time)
  // This mirrors real user behavior
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    // Health check
    // Navigate to page
    // Add delay between tests (simulates user reading results)
    await page.waitForTimeout(3000); // 3 seconds
  });
});
```

### Playwright Config

```typescript
// playwright.config.ts
export default defineConfig({
  workers: 1,           // Single worker
  fullyParallel: false, // Sequential execution
  // ...
});
```

---

## 📊 Expected Behavior

### Test Execution Flow

```
Test 1: Query "玉山銀行洗錢防制裁罰"
  - Submit query
  - Wait for processing (30-40s)
  - Verify results
  - Complete ✅

[3 second delay - simulates user reading]

Test 2: Query "國泰世華銀行財富管理違規"
  - Submit query
  - Wait for processing (30-40s)
  - Verify results
  - Complete ✅

[3 second delay]

Test 3: Processing time validation
  - Submit query
  - Measure time
  - Verify accuracy
  - Complete ✅

[3 second delay]

Test 4: State isolation test
  - Submit different query
  - Verify no pollution
  - Complete ✅

[3 second delay]

Test 5: Backend API direct test
  - Submit via API
  - Poll status
  - Verify result structure
  - Complete ✅
```

**Total Duration:** ~3-4 minutes
**Success Rate:** ~100% (when LLM gateway is responsive)

---

## ✅ Benefits

### 1. Matches Production Behavior
- Tests realistic usage patterns
- Validates actual user experience
- Catches real issues

### 2. Reliable Results
- No timeout failures from concurrent load
- Consistent test outcomes
- Builds deployment confidence

### 3. Appropriate for Application Type
- Research queries are naturally sequential
- 3-4 minute test duration is **reasonable**
- Quality validation over speed

---

## ❌ Why NOT Parallel Testing?

### Unrealistic Scenario
```
5 users submit complex research queries simultaneously
→ All 5 queries timeout
→ Bad user experience
```

**This will NEVER happen in production!**

### Production Reality
```
User A: Submits query at 10:00
User B: Submits query at 10:02 (reading A's results)
User C: Submits query at 10:05 (different timezone)
```

**Peak concurrency:** 1-2 queries at most

### Test Failures
- Parallel tests timeout due to LLM gateway overload
- Gateway is fine for production (1-2 concurrent users)
- Tests were failing due to **unrealistic test scenario**, not code bugs

---

## 🧪 Running the Tests

### Run All E2E Tests (Sequential)
```bash
cd frontend
npm run test:e2e
```

**Expected:**
```
Running 5 tests using 1 worker

✓ should successfully process query... (35s)
✓ should display processing time accurately (34s)
✓ should handle second query correctly (33s)
✓ should display citations with source information (32s)
✓ should verify backend is returning v1.1 workflow results (36s)

5 passed (3.2m)
```

### Run with UI (Debug Mode)
```bash
npm run test:e2e:ui
```

### Run in Headed Mode (Visible Browser)
```bash
npm run test:e2e:headed
```

---

## 📈 Performance Expectations

### Single Test Execution Time

| Step | Duration |
|------|----------|
| Navigate to page | 1-2s |
| Submit query | 1s |
| Wait for processing | 30-40s |
| Verify results | 2-3s |
| **Total per test** | **~35-45s** |

### Full Test Suite

| Component | Duration |
|-----------|----------|
| 5 tests × ~40s each | ~200s |
| 4 delays × 3s each | ~12s |
| Setup/teardown | ~15s |
| **Total** | **~3.5-4 minutes** |

**This is acceptable** for comprehensive E2E validation of a research application!

---

## 🔍 Debugging Tips

### If Tests Still Timeout

1. **Check Celery worker is running:**
```bash
ps aux | grep celery
```

2. **Check LLM gateway status:**
```bash
curl -X POST http://localhost:8000/api/v1/research/query/async \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test"}'
```

3. **Check Celery logs:**
```bash
# In Celery worker terminal
# Look for "Request timed out" or "Query analysis failed"
```

4. **Increase timeout if needed:**
```typescript
// In test file
maxExecutionTime: 90000, // 90 seconds instead of 60
```

### If Tests Pass Too Quickly

If tests complete in <15 seconds, it means RAG is not being used:

1. **Check vector database:**
```bash
ls -la data/vector_db/
```

2. **Check document count:**
```bash
sqlite3 data/finagent.db "SELECT COUNT(*) FROM documents;"
```

3. **Verify workflow is v1.1:**
- Check Celery logs for "v1.1 Plan-and-Execute workflow"

---

## 📚 Related Documentation

- [WHY_SEQUENTIAL_TESTING_MAKES_SENSE.md](../../WHY_SEQUENTIAL_TESTING_MAKES_SENSE.md) - Rationale
- [WORKFLOW_ANALYSIS.md](../../WORKFLOW_ANALYSIS.md) - Performance breakdown
- [LANGGRAPH_PRODUCTION_VS_TEST.md](../../LANGGRAPH_PRODUCTION_VS_TEST.md) - Why unit tests pass but E2E fails
- [PLAYWRIGHT_E2E_SUMMARY.md](../../PLAYWRIGHT_E2E_SUMMARY.md) - Complete test summary

---

## ✨ Summary

**Sequential testing is the correct approach** for FinAgent E2E tests because:

1. ✅ Mirrors real user behavior (one query at a time)
2. ✅ Appropriate for research application (30-40s response time is OK)
3. ✅ Reliable results (no concurrent load timeouts)
4. ✅ Validates production experience
5. ✅ 3-4 minute duration is reasonable for comprehensive validation

**Key Insight:** Test realistic scenarios, not stress scenarios that will never happen in production! 🎯
