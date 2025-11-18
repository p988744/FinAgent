# Testing Real-Time Workflow Monitoring

This document explains how to verify that the web UI's workflow monitoring displays **real-time progress** rather than simulated/static updates.

## Background

The FinAgent web UI displays real-time progress as the LangGraph multi-agent workflow executes:
- **Planning Agent**: Query analysis and research plan generation
- **Action Agent**: RAG retrieval from vector database
- **Validation Agent**: Citation integrity checking
- **Answer Agent**: LLM-powered answer synthesis

Each agent step should appear in the UI **as it completes**, not all at once at the end.

## Demo Delay Feature

To visually verify real-time updates are working, you can enable **demo delays** that add artificial pauses after each workflow node completes. This makes the real-time nature of updates obvious during testing/demos.

### Enable Demo Delay

Set the environment variable before starting the backend:

```bash
# Enable demo delay
export ENABLE_DEMO_DELAY=true

# Start backend
uv run uvicorn finagent.main:app --reload --port 8000
```

### Demo Delay Timings

When enabled, the following delays are added after each node:

| Workflow Node | Delay | UI Step |
|--------------|-------|---------|
| query_analysis | 2s | Planning |
| planning | 3s | Planning |
| action | 2s | Action |
| validation | 1s | Validation |
| reference_guard | 1s | Validation |
| answer | 5s | Answer |

### Expected Behavior

With demo delay enabled:

1. **Submit query** in web UI (http://localhost:5173)
2. **Planning step** starts immediately
3. After ~5 seconds, Planning completes and **Action step** starts
4. After ~2 seconds, Action completes and **Validation step** starts
5. After ~2 seconds, Validation completes and **Answer step** starts
6. After ~5 seconds, Answer completes and **results display**

### What This Proves

If you see steps updating one-by-one with these delays, it confirms:

✅ **Real-time streaming**: Updates are sent as each node completes
✅ **Thread/queue pattern**: Background workflow execution + async WebSocket updates
✅ **Not simulated**: Progress reflects actual LangGraph node completion

## Production Use

**IMPORTANT**: Demo delay is for **testing/demo purposes only**.

In production:
- Keep `ENABLE_DEMO_DELAY` unset or `false`
- Workflow will execute at full speed (~30-60 seconds typical)
- Real-time updates still work, just faster

## Implementation Details

### Code Flow

1. **Frontend** ([QueryPage.tsx](frontend/src/pages/QueryPage.tsx)): WebSocket client listening for step updates
2. **Backend** ([websocket.py](src/finagent/api/routes/websocket.py)): Thread + queue pattern for real-time streaming
3. **Orchestrator** ([orchestrator.py](src/finagent/agents/orchestrator.py)): Wraps workflow streaming with delay parameter
4. **Workflow** ([workflow.py](src/finagent/agents/workflow.py)): Yields events for each LangGraph node + optional delay

### Key Files

- [src/finagent/agents/workflow.py](src/finagent/agents/workflow.py#L311): `stream(enable_demo_delay=False)`
- [src/finagent/agents/orchestrator.py](src/finagent/agents/orchestrator.py#L196): `stream_query(enable_demo_delay=False)`
- [src/finagent/api/routes/websocket.py](src/finagent/api/routes/websocket.py#L28): `ENABLE_DEMO_DELAY` environment variable

## Alternative Testing Methods

Without demo delay, you can verify real-time updates by:

1. **Watch network tab**: WebSocket messages arrive incrementally
2. **Add logging**: Check backend logs for node completion timestamps
3. **Monitor CPU**: Workflow execution is continuous, not batched
4. **Add breakpoints**: Pause execution mid-workflow to see partial progress

## Best Practices

### For Development/Testing
```bash
ENABLE_DEMO_DELAY=true uv run uvicorn finagent.main:app --reload --port 8000
```

### For Production/Benchmarking
```bash
# No demo delay - full speed
uv run uvicorn finagent.main:app --reload --port 8000
```

### For Demos/Screenshots
```bash
# Enable for visually obvious progress
ENABLE_DEMO_DELAY=true uv run uvicorn finagent.main:app --reload --port 8000
```

## Troubleshooting

**Q: Steps still appear all at once even with demo delay enabled**
A: Check backend logs for "demo_delay=true" message. If false, environment variable not set correctly.

**Q: Delays seem longer than specified**
A: Delays are added ON TOP of actual execution time. Total time = execution + demo delay.

**Q: How to verify streaming without demo delay?**
A: Open browser DevTools → Network → WS → Messages. You'll see step_update messages arrive incrementally.

## Summary

The demo delay feature provides a simple way to visually verify that workflow monitoring displays **actual real-time execution progress** rather than simulated updates. It's a testing/demo tool, not for production use.

For production, the real-time streaming works the same way, just faster without artificial delays.
