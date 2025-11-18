# Tool Execution Tracking - Testing Guide

This guide explains how to test the Tool Execution Tracking feature in the Web UI.

## Feature Overview

The Tool Execution Tracking feature displays real-time status updates as the system executes tools during query processing:

- **Dynamic Plan Analysis**: Shows query intent, entities, complexity, and selected tools
- **Real-time Execution Status**: Updates as tools transition through states (planned → executing → completed/failed)
- **Execution Results**: Displays result counts, execution times, and error messages

## Prerequisites

Both backend and frontend servers must be running:

```bash
# Terminal 1: Backend (with demo delay for better visualization)
ENABLE_DEMO_DELAY=true uv run python -m uvicorn finagent.main:app --reload --port 8000

# Terminal 2: Frontend
npm --prefix frontend run dev
```

The frontend should be accessible at: http://localhost:3000

## Test Scenarios

### Scenario 1: Basic Tool Execution Tracking

**Objective**: Verify that tool execution status updates appear in real-time

**Steps**:
1. Open http://localhost:3000 in your browser
2. Navigate to the Query page
3. Enter query: `玉山銀行與國泰世華銀行的裁罰紀錄比較`
4. Click "送出查詢"

**Expected Results**:
1. **Dynamic Plan Analysis Panel** appears showing:
   - Intent: `比較分析` (comparison)
   - Entities: `玉山銀行`, `國泰世華銀行`
   - Complexity: `medium`
   - Selected Tool: `多實體搜尋` with status badge

2. **Status Transitions** (watch the tool card):
   - Initially: Gray play icon, status badge "已規劃"
   - During execution: Blue spinning loader, status badge "執行中..."
   - After completion: Green checkmark, status badge "已完成"
   - Result display: `✓ 10 個結果 (850ms)`

### Scenario 2: Multiple Tool Execution

**Objective**: Verify that multiple tools can be tracked independently

**Test Query**: (Any query that triggers multiple tools)

**Expected Results**:
- Each tool has its own status indicator
- Tools update independently as they execute
- Execution order numbers are displayed (#1, #2, #3)
- Previously completed tools remain in "completed" state

### Scenario 3: Failed Tool Execution

**Objective**: Verify that tool failures are properly displayed

**Simulated Scenario** (requires backend modification to simulate failure):

**Expected Results**:
- Tool card shows red X icon
- Status badge shows "失敗" in red
- Error message is displayed below the tool card: `✗ [error message]`

### Scenario 4: Visual Feedback

**Objective**: Verify all visual elements are working correctly

**Elements to Check**:

1. **Intent Badges** (color-coded):
   - Blue: Temporal queries
   - Purple: Comprehensive queries
   - Green: Specific file
   - Orange: Comparison
   - Indigo: Entity-specific
   - Gray: General search

2. **Complexity Badges** (traffic light colors):
   - Green: Simple
   - Yellow: Medium
   - Red: Complex

3. **Feature Tags** (when applicable):
   - ⏱️ Temporal constraint
   - 🏷️ Multi-entity
   - 🔍 Exhaustive search

4. **Execution Status Icons**:
   - Gray play icon: Planned
   - Blue spinning loader: Executing
   - Green checkmark: Completed
   - Red X: Failed

5. **Tool Icons** (emoji):
   - 🔍 Vector search
   - ⏱ Metadata search
   - 📋 List documents
   - 📄 Read file
   - 🔄 Hybrid search
   - 🔀 Multi-entity search

## WebSocket Message Flow

During a query, you should see these WebSocket messages in the browser DevTools (Network → WS):

```json
// 1. Query started
{"type": "query_started", "timestamp": "...", "payload": {}}

// 2. Dynamic plan analysis
{
  "type": "dynamic_plan_analysis",
  "timestamp": "...",
  "payload": {
    "query_analysis": {
      "intent": "comparison",
      "entities": ["玉山銀行", "國泰世華銀行"],
      "has_temporal_constraint": false,
      "temporal_type": null,
      "complexity": "medium",
      "requires_multi_entity": true,
      "requires_exhaustive_search": false
    },
    "selected_tools": [
      {
        "tool_name": "multi_entity_search",
        "reason": "比較查詢需要多實體搜尋",
        "parameters": {
          "entities": ["玉山銀行", "國泰世華銀行"],
          "top_k_per_entity": 5
        },
        "execution_order": 1
      }
    ]
  }
}

// 3. Tool execution started
{
  "type": "tool_execution_update",
  "timestamp": "...",
  "payload": {
    "tool_name": "multi_entity_search",
    "status": "executing",
    "parameters": {
      "entities": ["玉山銀行", "國泰世華銀行"],
      "top_k_per_entity": 5
    }
  }
}

// 4. Tool execution completed
{
  "type": "tool_execution_update",
  "timestamp": "...",
  "payload": {
    "tool_name": "multi_entity_search",
    "status": "completed",
    "result_count": 10,
    "execution_time_ms": 850
  }
}

// 5. Query complete
{
  "type": "query_complete",
  "timestamp": "...",
  "payload": {
    "summary": "...",
    "key_findings": [...],
    "detailed_analysis": "...",
    "confidence": "高信心",
    "processing_time_ms": 42000,
    "citations": [...]
  }
}
```

## Debugging WebSocket Messages

To inspect WebSocket messages in real-time:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter by WS (WebSocket)
4. Click on the WebSocket connection
5. Go to Messages tab
6. Submit a query
7. Watch messages appear in real-time

## Browser Console Logging

The QueryPage component logs WebSocket messages to the console:

```javascript
console.log('WebSocket connected')
console.log('Unknown message type:', type)  // For unhandled message types
console.error('Failed to parse WebSocket message:', err)
```

Open the Console tab in DevTools to see these logs.

## Common Issues

### Issue 1: WebSocket Not Connecting

**Symptoms**: Connection status shows "未連線" (disconnected)

**Solution**:
- Verify backend is running on port 8000
- Check browser console for WebSocket errors
- Ensure no CORS or proxy issues

### Issue 2: Dynamic Plan Panel Not Appearing

**Symptoms**: Panel doesn't show after submitting query

**Solution**:
- Check WebSocket messages - verify `dynamic_plan_analysis` message is received
- Check browser console for React errors
- Verify `dynamicPlan` state is being set in QueryPage

### Issue 3: Tool Status Not Updating

**Symptoms**: Tool stays in "planned" status even after execution

**Solution**:
- Check WebSocket messages - verify `tool_execution_update` messages are received
- Verify `tool_name` in update matches the tool in `selected_tools`
- Check that Map state is updating correctly

### Issue 4: Animations Not Working

**Symptoms**: Spinning loader doesn't spin

**Solution**:
- Verify Tailwind CSS is loaded correctly
- Check that `animate-spin` class is applied
- Inspect element in DevTools to verify classes

## Performance Testing

### Timing Checks

Use browser DevTools Performance tab to verify:

1. **WebSocket Message Latency**: Messages should appear within 10-50ms
2. **React Re-renders**: Component should re-render smoothly without lag
3. **Animation Performance**: Loader animation should be smooth (60fps)

### Memory Leak Check

After running 10+ queries:

1. Open DevTools → Memory tab
2. Take heap snapshot
3. Check for growing Map sizes
4. Verify WebSocket connections are properly closed

## Visual Regression Testing

Compare screenshots of the Dynamic Plan Panel with the reference images in the demo script output:

```bash
uv run python tests/test_dynamic_planning_with_execution.py
```

The ASCII art output shows the expected layout.

## Integration with Orchestrator

**IMPORTANT**: The tool execution tracking is currently integrated into the WebSocket callback system, but the orchestrator must call these methods:

```python
# In orchestrator/workflow during tool execution:

# Before executing a tool
await self.ui_callback.on_tool_execution_start(
    tool_name="multi_entity_search",
    parameters={"entities": [...], "top_k_per_entity": 5}
)

# After successful tool execution
await self.ui_callback.on_tool_execution_complete(
    tool_name="multi_entity_search",
    result_count=10,
    execution_time_ms=850
)

# If tool execution fails
await self.ui_callback.on_tool_execution_failed(
    tool_name="multi_entity_search",
    error="Tool execution timeout after 30s"
)
```

Without these callback invocations, the tool status will remain in "planned" state.

## Success Criteria

The feature is working correctly if:

1. ✅ Dynamic Plan Analysis panel appears after query submission
2. ✅ Query analysis shows correct intent, entities, and complexity
3. ✅ Selected tools are listed with reasons and parameters
4. ✅ Tool status icons update in real-time (play → spinner → checkmark/X)
5. ✅ Execution results display (result count and time for success, error message for failure)
6. ✅ Multiple tools can be tracked independently
7. ✅ Visual design matches the specifications (colors, icons, badges)
8. ✅ WebSocket messages are received and processed correctly
9. ✅ No console errors or warnings
10. ✅ Performance is acceptable (smooth animations, no lag)

## Next Steps

After verifying the UI works correctly:

1. Integrate tool execution callbacks into the actual orchestrator/workflow
2. Test with real queries that trigger different tools
3. Add error handling for edge cases
4. Consider adding user preferences (e.g., collapse/expand dynamic plan panel)
5. Add tooltips for technical terms (intent types, tool names)
