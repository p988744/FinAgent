# Frontend WebSocket Real-Time Monitoring Test Guide

This guide provides **step-by-step instructions** to verify that the frontend displays real-time workflow progress via WebSocket.

## Prerequisites

✅ Backend running on http://127.0.0.1:8000 (with `ENABLE_DEMO_DELAY=true` for easier visualization)
✅ Frontend running on http://localhost:5173

## Test Setup

### Check Services Are Running

```bash
# Check backend
curl http://127.0.0.1:8000/health

# Check frontend
open http://localhost:5173
```

## Step-by-Step Testing Procedure

### Test 1: WebSocket Connection

**Purpose**: Verify WebSocket establishes connection on page load

**Steps**:
1. Open browser to http://localhost:5173
2. Open Developer Tools (F12 or Cmd+Option+I)
3. Go to **Console** tab
4. Look for WebSocket connection message

**Expected Results**:
✅ Console shows: `WebSocket connected`
✅ Status indicator shows green dot with "WebSocket 已連線"
✅ No connection errors in console

**If Failed**:
- Check backend is running: `lsof -i:8000`
- Check for CORS errors in console
- Verify WebSocket endpoint: `ws://localhost:5173/ws/query` (proxied to backend)

---

### Test 2: Query Submission

**Purpose**: Verify query submission triggers WebSocket messages

**Steps**:
1. In Developer Tools, go to **Network** tab
2. Filter by **WS** (WebSocket)
3. In the app, enter query: `玉山銀行洗錢防制裁罰`
4. Click "送出查詢" button
5. Observe WebSocket messages in Network tab

**Expected Results**:
✅ Query input becomes disabled during processing
✅ "處理中..." button shows with spinner
✅ WebSocket sends `{ type: "query", text: "..." }` message
✅ Multiple WebSocket messages received (query_started, step_update, plan_created, etc.)

**Screenshot Location**: Network > WS > Messages tab

---

### Test 3: Research Plan Panel

**Purpose**: Verify plan panel shows real extracted data

**Steps**:
1. Submit query: `國泰世華銀行內線交易案件`
2. Watch for "研究計畫" panel to appear
3. Click panel header to expand (if collapsed)
4. Examine the displayed information

**Expected Results**:
✅ Panel appears immediately after query submission
✅ **Keywords** section shows: 國泰, 世華, 銀行, 內線, 交易 (or similar)
✅ **Entity type** shows: `commercial_bank` or similar (NOT "unknown")
✅ **Research tasks** show 3-4 specific tasks with descriptions
✅ **Estimated time** shows a number > 0 seconds

**Verification (NOT hardcoded)**:
- Try different query: `玉山銀行洗錢防制裁罰`
- Keywords should change to: 玉山, 銀行, 洗錢, 防制, 裁罰
- Entity type may differ
- Tasks should reference different keywords

---

### Test 4: Agent Stepper Real-Time Updates

**Purpose**: Verify steps update sequentially as nodes complete

**Steps**:
1. Submit query: `測試工作流程順序`
2. Watch the **Agent Stepper** panel (left side, 3-column layout)
3. Observe step progression in real-time

**Expected Results** (with `ENABLE_DEMO_DELAY=true`):

| Time | Step | Status | Elapsed |
|------|------|--------|---------|
| 0s | Planning | Active (blue spinner) | 0ms → increases |
| ~3s | Planning | Done (green checkmark) | ~3000ms |
| ~3s | Action | Active (blue spinner) | 0ms → increases |
| ~5s | Action | Done (green checkmark) | ~2000ms |
| ~5s | Validation | Active (blue spinner) | 0ms → increases |
| ~6s | Validation | Done (green checkmark) | ~1000ms |
| ~6s | Answer | Active (blue spinner) | 0ms → increases |
| ~11s | Answer | Done (green checkmark) | ~5000ms |

**Key Observations**:
✅ Steps appear **one at a time** (not all at once)
✅ Active step shows **blue spinner** icon
✅ Completed step shows **green checkmark** icon
✅ Elapsed time **increases in real-time** for active step
✅ Each step waits ~2-5 seconds before next (due to demo delay)

**Without Demo Delay**:
- Steps complete much faster (~30-60 seconds total)
- Still see sequential progression
- Timing values vary (not 0, 1000, 2000, etc.)

---

### Test 5: Activity Log Real-Time Updates

**Purpose**: Verify activity log shows messages as they arrive

**Steps**:
1. Submit query: `測試活動日誌`
2. Watch the **Activity Log** panel (right side, 3-column layout)
3. Scroll to see new messages appear

**Expected Results**:
✅ Log entries appear **incrementally** as workflow progresses
✅ First entry: "開始處理查詢: 測試活動日誌"
✅ Node completion messages: "執行節點: planning", "執行節點: action", etc.
✅ Plan creation message: "研究計畫建立完成，共 X 項任務"
✅ Final message: "查詢完成，共耗時 X 秒"

**Timestamps**:
- Each entry has a timestamp
- Timestamps should be sequential (increasing order)
- Time gaps between entries prove real-time updates

---

### Test 6: Todo Panel Updates

**Purpose**: Verify todo items update during workflow execution

**Steps**:
1. Submit query: `玉山銀行洗錢防制裁罰`
2. Watch the **Todo Panel** (middle column, 3-column layout)
3. Observe todo item state changes

**Expected Results** (if todos are used):
✅ Todo items appear when workflow starts
✅ Items change from `pending` → `in_progress` → `completed`
✅ Progress indicators update in real-time
✅ Completed items show checkmarks

**Note**: Current implementation may not use todos extensively. If panel stays empty, this is expected.

---

### Test 7: Results Panel

**Purpose**: Verify results appear only after workflow completes

**Steps**:
1. Submit query: `國泰世華銀行內線交易案件`
2. Watch workflow progress through all steps
3. Wait for Answer step to complete

**Expected Results**:
✅ Results panel is **hidden** during workflow execution
✅ Results panel **appears** only after Answer step completes (green checkmark)
✅ Results show:
  - Executive summary
  - Key findings (bullet points)
  - Detailed analysis
  - Confidence level
  - Citations with source details
✅ Export button is enabled

---

### Test 8: Timing Precision Verification

**Purpose**: Verify elapsed times have millisecond precision (not hardcoded)

**Steps**:
1. Submit same query **twice**: `玉山銀行洗錢防制裁罰`
2. Record elapsed times from Agent Stepper for each run
3. Compare values

**Expected Results**:

**Run 1**:
- Planning: 2,341ms
- Action: 8,762ms
- Validation: 1,456ms
- Answer: 12,893ms

**Run 2**:
- Planning: 2,187ms (different!)
- Action: 9,124ms (different!)
- Validation: 1,389ms (different!)
- Answer: 11,976ms (different!)

**Verification**:
✅ Values have **sub-second precision** (not round 0, 1000, 2000)
✅ Values **vary between runs** (proves not hardcoded)
✅ Some variation is expected due to LLM API latency

---

### Test 9: Error Handling

**Purpose**: Verify error messages display correctly

**Steps**:
1. Stop backend: `lsof -ti:8000 | xargs kill -9`
2. Submit query in frontend
3. Observe error handling

**Expected Results**:
✅ Error message appears: "WebSocket 連線失敗，請重試"
✅ Status indicator shows red dot with "未連線"
✅ Query button becomes enabled again
✅ No infinite loading state

**Recovery**:
1. Restart backend: `ENABLE_DEMO_DELAY=true uv run python -m uvicorn finagent.main:app --reload --port 8000`
2. Refresh page or wait for auto-reconnect
3. Status indicator should turn green

---

### Test 10: Demo Delay Verification

**Purpose**: Verify demo delay makes real-time updates visually obvious

**Steps**:
1. Ensure backend has `ENABLE_DEMO_DELAY=true`
2. Check backend logs for confirmation
3. Submit query
4. Use stopwatch to measure step durations

**Backend Log Verification**:
```bash
# Check backend output
tail -f <backend_log_or_check_BashOutput>

# Should see:
# "Starting LangGraph workflow with streaming (demo_delay=True)"
# "Demo delay: sleeping 3s after planning"
# "Demo delay: sleeping 2s after action"
```

**Expected Timing**:
- Planning → Action: ~3 second pause
- Action → Validation: ~2 second pause
- Validation → Answer: ~1 second pause
- Answer → Complete: ~5 second pause

**Without Demo Delay**:
- Steps complete faster
- No artificial pauses
- Still see real-time updates, just quicker

---

## Browser DevTools Tips

### Network Tab - WebSocket Messages

1. Open DevTools (F12)
2. Go to **Network** tab
3. Filter: **WS** (WebSocket)
4. Click on WebSocket connection
5. Click **Messages** sub-tab
6. Watch messages in real-time

**Message Types to Observe**:
- `query_started` - Query begins
- `plan_created` - Plan with keywords
- `step_update` - Step status changes
- `activity_log` - Log entries
- `query_complete` - Results ready
- `query_failed` - Error occurred

### Console Tab - Debugging

```javascript
// In console, watch WebSocket events
// (Already logged by QueryPage.tsx)

// Check connection status
// Look for: "WebSocket connected"
```

### React DevTools (Optional)

1. Install React DevTools extension
2. Open DevTools > Components tab
3. Select `QueryPage` component
4. Watch state changes in real-time:
   - `isQuerying`: false → true → false
   - `steps`: Map updates as nodes complete
   - `plan`: null → ResearchPlan object
   - `result`: null → QueryResult object

---

## Common Issues & Solutions

### Issue 1: WebSocket not connecting

**Symptoms**: Red "未連線" indicator, no messages

**Solutions**:
```bash
# Check backend is running
lsof -i:8000

# Check frontend proxy config
cat frontend/vite.config.ts
# Should have WebSocket proxy to localhost:8000

# Restart both services
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
ENABLE_DEMO_DELAY=true uv run python -m uvicorn finagent.main:app --reload --port 8000 &
npm --prefix frontend run dev &
```

### Issue 2: Steps appear all at once (not real-time)

**Symptoms**: All steps show as "done" immediately

**Cause**: Frontend batching state updates or backend not streaming

**Solutions**:
```bash
# Check backend logs for streaming
# Should see: "Streaming node completed: planning", etc.

# Verify WebSocket messages arrive incrementally
# Check DevTools > Network > WS > Messages
# Messages should arrive one-by-one, not in batch
```

### Issue 3: Plan shows "unknown" or empty keywords

**Symptoms**: Entity type = "unknown", keywords = []

**Cause**: Planning Agent failed or returned default values

**Solutions**:
```bash
# Check backend logs for errors in planning_agent.py
# Verify LLM API key is valid
# Check OpenAI API quota/limits
```

### Issue 4: Demo delay not working

**Symptoms**: Steps complete very quickly (< 10 seconds total)

**Solutions**:
```bash
# Verify environment variable is set
env | grep DEMO_DELAY
# Should show: ENABLE_DEMO_DELAY=true

# Check backend startup logs
# Should see: "demo_delay=True" in logs

# Restart with explicit variable
ENABLE_DEMO_DELAY=true uv run python -m uvicorn finagent.main:app --reload --port 8000
```

---

## Expected vs Actual Comparison

### ✅ Real-Time (Correct Behavior)

| Observation | Expected | Actual |
|------------|----------|--------|
| Plan keywords | Vary by query | ✅ Different per query |
| Step timing | Varies between runs | ✅ 2341ms, 2187ms |
| Message arrival | Incremental | ✅ One-by-one |
| Step progression | Sequential | ✅ Planning → Action → ... |

### ❌ Hardcoded (Wrong Behavior)

| Observation | Expected | Actual |
|------------|----------|--------|
| Plan keywords | Same every time | ❌ Always ["bank", "penalty"] |
| Step timing | Round numbers | ❌ Always [0, 1000, 2000] |
| Message arrival | All at once | ❌ Batch at end |
| Step progression | Simultaneous | ❌ All steps complete together |

---

## Summary Checklist

Use this checklist for quick verification:

- [ ] WebSocket connects on page load (green indicator)
- [ ] Plan panel shows real keywords from query (not hardcoded)
- [ ] Agent steps update sequentially (Planning → Action → Validation → Answer)
- [ ] Elapsed times have millisecond precision (e.g., 2341ms, not 2000ms)
- [ ] Elapsed times vary between runs (proves real measurement)
- [ ] Activity log shows incremental messages
- [ ] Results appear only after Answer step completes
- [ ] Demo delay creates visible pauses between steps (if enabled)
- [ ] Error handling works (try disconnecting backend)
- [ ] Different queries produce different plans/keywords

If all items are checked, **real-time monitoring is working correctly!** ✅

---

## Quick Test Script

For rapid verification, run this sequence:

```bash
# 1. Ensure services running
lsof -i:8000 && lsof -i:5173

# 2. Open browser
open http://localhost:5173

# 3. Open DevTools > Network > WS

# 4. Submit query: "玉山銀行洗錢防制裁罰"

# 5. Watch for:
#    - Plan appears with keywords: 玉山, 銀行, 洗錢, 防制
#    - Steps update: Planning → Action → Validation → Answer
#    - Timing shows variation: e.g., 2341ms, 8762ms
#    - WebSocket messages arrive incrementally

# 6. Submit different query: "國泰世華銀行內線交易"

# 7. Verify:
#    - Different keywords: 國泰, 世華, 內線, 交易
#    - Different timing values
#    - Same workflow progression
```

---

## Video Recording (Optional)

For documentation, record a screen video:

1. Start screen recording
2. Submit query
3. Show:
   - WebSocket connection status
   - Plan panel expanding with real keywords
   - Agent steps updating one-by-one
   - Timing values increasing
   - Activity log entries appearing
   - Results appearing at end
4. Submit different query to show variation
5. Stop recording

This provides visual proof of real-time monitoring!
