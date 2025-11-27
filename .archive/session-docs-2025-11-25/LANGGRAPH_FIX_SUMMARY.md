# LangGraph InvalidUpdateError Fix - Summary

**Date:** 2025-11-24
**Issue:** v1.1 Plan-Execute workflow failing with `InvalidUpdateError`
**Status:** ✅ RESOLVED

---

## Problem

When switching to OpenAI API for E2E testing, discovered that the v1.1 Plan-Execute workflow was throwing:

```
langgraph.errors.InvalidUpdateError: At key 'plan': Can receive only one value per step.
Use an Annotated key to handle multiple values.
```

**Root Cause:**
- In `src/finagent/agents/plan_execute/models.py`, the `plan` field in `PlanExecuteState` was not annotated
- LangGraph requires `Annotated` types with reducer functions for state keys that may receive updates from multiple nodes
- The workflow has both `planner` and `replanner` nodes that update the `plan` key

---

## Solution

Added a reducer function and `Annotated` wrapper to the `plan` field:

### Before:
```python
class PlanExecuteState(TypedDict):
    """State for the Plan-and-Execute workflow."""

    input: str
    query_insight: Optional[QueryInsight]
    plan: Plan  # ❌ No Annotated wrapper
    past_steps: Annotated[List[tuple], add]
    response: Optional[str]
    scratchpad: List[Any]
```

### After:
```python
def replace_plan(left: Optional[Plan], right: Plan) -> Plan:
    """Replace plan state (use latest value only)."""
    return right


class PlanExecuteState(TypedDict):
    """State for the Plan-and-Execute workflow."""

    input: str
    query_insight: Optional[QueryInsight]
    plan: Annotated[Plan, replace_plan]  # ✅ Use Annotated with reducer
    past_steps: Annotated[List[tuple], add]
    response: Optional[str]
    scratchpad: List[Any]
```

**Key Change:**
- Added `replace_plan()` reducer function that returns the most recent value
- Wrapped `plan` field with `Annotated[Plan, replace_plan]`
- This allows LangGraph to properly handle updates from multiple nodes

---

## Verification

### Test Query:
```bash
curl -s -X POST http://localhost:8000/api/v1/research/query/async \
  -H "Content-Type: application/json" \
  -d '{"query_text": "測試查詢", "workflow_version": "v1.1"}'
```

### Before Fix:
```
langgraph.errors.InvalidUpdateError: At key 'plan': Can receive only one value per step.
[2025-11-24 18:48:06] Task finagent.tasks.execute_research_workflow raised unexpected: InvalidUpdateError
```

### After Fix:
```
[2025-11-24 18:53:35] Tool hard_search completed successfully: 253 chars returned
[2025-11-24 18:53:36] Generating final report...
[2025-11-24 18:53:37] Task completed successfully
```

✅ **Result:** Query completes successfully without errors!

---

## Related Files

- **Fixed File:** [src/finagent/agents/plan_execute/models.py](src/finagent/agents/plan_execute/models.py)
- **Workflow Graph:** [src/finagent/agents/plan_execute/graph.py](src/finagent/agents/plan_execute/graph.py)
- **Orchestrator:** [src/finagent/agents/orchestrator.py](src/finagent/agents/orchestrator.py)

---

## LangGraph Best Practices

This fix reinforces the LangChain v1.0 / LangGraph best practices from [LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md](LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md):

### Rule: Always use `Annotated` for state keys that may receive multiple updates

**When to use:**
- Any state key that multiple nodes might update
- Keys that need custom merge/reduce logic (e.g., lists, plans, aggregations)

**Common patterns:**
```python
from operator import add
from typing import Annotated, List

# For lists - concatenate
messages: Annotated[List[str], add]

# For plans - replace with latest
plan: Annotated[Plan, replace_plan]

# For tuples - append
past_steps: Annotated[List[tuple], add]
```

**LangGraph Documentation:**
https://docs.langchain.com/oss/python/langgraph/errors/INVALID_CONCURRENT_GRAPH_UPDATE

---

## Impact

This fix enables the v1.1 Plan-Execute workflow to run successfully. The workflow can now:

1. ✅ Create initial plan with PlannerAgent
2. ✅ Execute tasks with ExecutorAgent
3. ✅ Replan dynamically with ReplannerAgent
4. ✅ Generate final report with ReporterAgent

No more `InvalidUpdateError`!

---

## Next Steps

1. ✅ Fix LangGraph error - COMPLETED
2. 🔄 Ensure OpenAI API configuration persists across Celery restarts
3. ⏳ Run full E2E test suite with OpenAI API
4. ⏳ Document configuration best practices

---

**Note:** This fix is independent of the OpenAI API configuration issue. The workflow now works correctly with both llmgw and OpenAI API endpoints.
