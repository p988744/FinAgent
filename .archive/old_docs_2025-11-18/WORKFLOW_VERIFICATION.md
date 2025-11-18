# Workflow Real-Time Verification

This document explains how to programmatically verify that the LangGraph workflow triggers **real WebSocket callbacks** with **actual data** (not hardcoded values) when each node completes.

## Problem Statement

When building real-time monitoring UIs, it's critical to verify:

1. **Each workflow node completion** triggers a WebSocket callback
2. **Plan data** contains real extracted information (not placeholder/hardcoded)
3. **Timing values** are real measurements with precision (not static like 0, 1000, 2000)
4. **Workflow sequence** follows correct LangGraph order
5. **Analysis varies** based on query content

## Verification Approach

### Test Strategy

We use a **mock WebSocket callback** to capture all messages sent during workflow execution, then verify:

✅ **Real-time callbacks**: Each LangGraph node triggers immediate callback
✅ **Real data extraction**: Keywords/entity type extracted from actual query
✅ **Real timing**: Values have 3+ digit precision, vary between runs
✅ **Correct sequence**: planning → action → validation → answer
✅ **Dynamic analysis**: Complexity/keywords change with different queries

### Test Files

1. **[tests/verify_workflow_realtime.py](tests/verify_workflow_realtime.py)** - Standalone verification script
2. **[tests/test_workflow_websocket_integration.py](tests/test_workflow_websocket_integration.py)** - Full pytest test suite

## Running Verification Tests

### Quick Verification (Standalone)

```bash
# Run standalone verification script
uv run python tests/verify_workflow_realtime.py
```

Expected output:
```
================================================================================
WORKFLOW → WEBSOCKET REAL-TIME VERIFICATION TESTS
================================================================================

TEST 1: Each LangGraph node triggers WebSocket callback
  ✓ Node completed: query_analysis
  ✓ Node completed: planning
  ✓ Node completed: action
  ✓ Node completed: validation
  ✓ Node completed: answer

✅ Total nodes completed: 5
✅ TEST 1 PASSED

TEST 2: Plan contains real extracted data (not hardcoded)
✅ Extracted keywords: ['國泰', '世華', '銀行', '內線', '交易']
✅ Found relevant terms: ['國泰', '世華', '銀行', '內線', '交易']
✅ Entity type: bank
✅ Generated 3 research tasks
✅ TEST 2 PASSED

TEST 3: Timing values are real measurements (3+ digit precision)
  Running workflow twice to verify timing variation...
✅ Run 1 timings (ms): [2341, 8762, 1456, 12893]
✅ Run 2 timings (ms): [2187, 9124, 1389, 11976]
✅ Run 1: 4/4 values have sub-100ms precision
✅ Run 2: 4/4 values have sub-100ms precision
✅ Max timing difference between runs: 917ms
   (Proves timing is measured, not hardcoded)
✅ TEST 3 PASSED

TEST 4: Workflow follows correct LangGraph sequence
  1. query_analysis
  2. planning
  3. action
  4. validation
  5. answer
✅ Planning → Action (correct order)
✅ Action → Validation (correct order)
✅ Validation → Answer (correct order)
✅ TEST 4 PASSED

TEST 5: Plan complexity varies based on query (not hardcoded)
  Simple query:
    Query: 玉山銀行
    Complexity: simple

  Complex query:
    Query: 2020至2023年所有銀行洗錢防制裁罰案件按時間趨勢分析
    Complexity: complex

✅ All complexities are valid (proves analysis is working)
✅ TEST 5 PASSED

================================================================================
✅ ALL TESTS PASSED
================================================================================

Conclusion:
  ✓ Workflow triggers real-time WebSocket callbacks
  ✓ Plan data is extracted from actual query (not hardcoded)
  ✓ Timing measurements have real precision
  ✓ Workflow executes in correct LangGraph sequence
  ✓ Analysis varies by query content

✅ Real-time monitoring is VERIFIED to work correctly
```

### Full Test Suite (pytest)

```bash
# Run full test suite with pytest
uv run pytest tests/test_workflow_websocket_integration.py -v -s
```

## What Each Test Verifies

### Test 1: Node Completion Callbacks

**Purpose**: Verify each LangGraph node triggers WebSocket callback when it completes.

**Method**:
- Run workflow with mock callback
- Track which nodes complete
- Verify expected nodes (planning, action, validation, answer) all execute

**Proves**:
✅ Workflow execution is real (not simulated)
✅ Each node triggers callback when it finishes
✅ Callbacks happen during execution (not batched at end)

### Test 2: Real Data Extraction

**Purpose**: Verify plan contains actual extracted data from query, not hardcoded placeholders.

**Method**:
- Submit query: "國泰世華銀行內線交易案件"
- Extract plan.analysis.keywords
- Verify keywords relate to query content (國泰, 世華, 銀行, 內線, 交易)
- Verify entity_type is inferred (not "unknown")

**Proves**:
✅ Keywords extracted from actual query text
✅ Entity type analyzed (not default value)
✅ Tasks generated based on query analysis

### Test 3: Real Timing Measurements

**Purpose**: Verify elapsed_ms values are real measurements with precision, not hardcoded round numbers.

**Method**:
- Run workflow twice
- Collect all elapsed_ms values from step_update messages
- Verify values have sub-100ms precision (e.g., 2341ms not 2000ms)
- Verify values vary between runs (proves real measurement)

**Proves**:
✅ Timing is measured in real-time (not static 0, 1000, 2000)
✅ Values have 3+ digit precision
✅ Values vary between runs (not hardcoded)

**Example**:
```python
# Real measurement (good)
elapsed_ms: [2341, 8762, 1456, 12893]

# Hardcoded values (bad)
elapsed_ms: [0, 1000, 2000, 5000]
```

### Test 4: Correct Workflow Sequence

**Purpose**: Verify nodes execute in correct LangGraph order.

**Method**:
- Track node completion order
- Verify: planning → action → validation → answer

**Proves**:
✅ Workflow follows LangGraph definition
✅ Dependencies respected (planning before action, etc.)

### Test 5: Dynamic Analysis

**Purpose**: Verify plan complexity varies based on query content (not hardcoded).

**Method**:
- Run simple query: "玉山銀行"
- Run complex query: "2020至2023年所有銀行洗錢防制裁罰案件按時間趨勢分析"
- Compare complexity values

**Proves**:
✅ Complexity is analyzed (not always "medium")
✅ Analysis adapts to query content

## Understanding the 3-Digit Precision Check

### Why It Matters

**Hardcoded timing** (bad):
```json
{
  "step": "planning",
  "elapsed_ms": 0
}
{
  "step": "action",
  "elapsed_ms": 1000
}
```

**Real timing** (good):
```json
{
  "step": "planning",
  "elapsed_ms": 2341
}
{
  "step": "action",
  "elapsed_ms": 8762
}
```

### Verification Logic

```python
# Check 1: Values are not round hundreds
non_round = sum(1 for val in timings if val % 100 != 0)
assert non_round > 0, "Real timing should have sub-100ms precision"

# Check 2: Values vary between runs
max_diff = max(abs(t1 - t2) for t1, t2 in zip(run1, run2))
assert max_diff > 100, "Timings should vary (proves not hardcoded)"

# Check 3: Statistical variation
stdev = statistics.stdev(timings)
assert stdev > 0, "Should have variation"
```

## Mock Callback Implementation

The tests use a **VerificationCallback** that captures all WebSocket messages:

```python
class VerificationCallback:
    """Callback that captures and verifies WebSocket messages."""

    def __init__(self):
        self.messages: list[dict] = []
        self.step_updates: dict[str, list[dict]] = {}
        self.plan_data: dict | None = None

    async def _send(self, msg_type: str, payload: Any):
        """Capture WebSocket message."""
        timestamp = datetime.now()
        message = {
            "type": msg_type,
            "timestamp": timestamp.isoformat(),
            "payload": payload,
        }
        self.messages.append(message)

        if msg_type == "step_update":
            # Track step updates by step name
            step = payload.get("step")
            if step not in self.step_updates:
                self.step_updates[step] = []
            self.step_updates[step].append(payload)

        if msg_type == "plan_created":
            # Capture plan data for verification
            self.plan_data = payload
```

## Integration with Real WebSocket

The same callback interface is used in production:

```python
# Production WebSocket (websocket.py)
class WebSocketUICallback(UICallback):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def _send(self, msg_type: str, payload: Any):
        await self.websocket.send_json({
            "type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
        })

# Tests use same interface
orchestrator = AgentOrchestrator(ui_callback=callback)
```

## Common Issues and Debugging

### Issue: Tests fail with "No nodes completed"

**Cause**: RAG retriever not initialized or workflow disabled

**Solution**:
```bash
# Initialize vector database first
uv run finagent reindex --skip-init
```

### Issue: Timing values are all 0

**Cause**: Callback not receiving step_update messages with elapsed_ms

**Debug**:
```python
# Add logging to see what messages are received
for msg in callback.messages:
    print(f"Type: {msg['type']}, Payload: {msg['payload']}")
```

### Issue: Plan data is None

**Cause**: plan_created message not sent or planning node failed

**Debug**:
```python
# Check which nodes completed
for node_name, state_update in orchestrator.stream_query(query):
    print(f"Node: {node_name}, Keys: {state_update.keys()}")
    if "plan" in state_update:
        print(f"Plan: {state_update['plan']}")
```

## Best Practices

### 1. Run Tests Before Deployment

```bash
# Quick verification
uv run python tests/verify_workflow_realtime.py

# Full test suite
uv run pytest tests/test_workflow_websocket_integration.py -v
```

### 2. Verify After Code Changes

Run tests after modifying:
- workflow.py (LangGraph workflow)
- orchestrator.py (Orchestrator)
- websocket.py (WebSocket handler)
- Any agent code (planning, action, validation, answer)

### 3. Add Custom Verifications

Extend tests for your specific use case:

```python
async def test_custom_verification():
    """Test custom requirement."""
    callback = VerificationCallback()
    orchestrator = AgentOrchestrator(ui_callback=callback)
    query = Query(text="your custom query")

    for node_name, state_update in orchestrator.stream_query(query):
        # Add custom assertions
        if node_name == "action":
            assert "retrieved_chunks" in state_update
            assert len(state_update["retrieved_chunks"]) > 0
```

## Summary

These tests provide **programmatic verification** that:

✅ **Real-time execution**: Each LangGraph node triggers WebSocket callback when it completes
✅ **Real data**: Plan contains extracted information from actual query, not placeholders
✅ **Real timing**: Values have 3+ digit precision and vary between runs
✅ **Correct flow**: Workflow follows expected sequence
✅ **Dynamic analysis**: Query analysis adapts to content

Run `uv run python tests/verify_workflow_realtime.py` to verify your implementation works correctly.
