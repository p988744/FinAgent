# Orchestrator Tool Integration Guide

**Date:** 2025-01-21
**Purpose:** Ensure all three tools (retriever, hard_search, hybrid_search) work correctly with the orchestrator
**Status:** ✅ COMPLETED (2025-01-21)

## Current Status

### ✅ What Works

1. **ExecutorAgent has all three tools registered:**
   ```python
   # In src/finagent/agents/plan_execute/executor.py:29-33
   self.tools = {
       "retriever": self.retriever_tool,
       "hard_search": self.hard_search_tool,
       "hybrid_search": self.hybrid_retriever_tool,  # ✅ Available
   }
   ```

2. **Orchestrator initializes components correctly:**
   ```python
   # In src/finagent/agents/orchestrator.py:69-73
   self.hard_searcher = HardSearcher(db_path="data/finagent.db")
   self.plan_execute_workflow = PlanExecuteWorkflow(
       retriever=self.retriever,
       hard_searcher=self.hard_searcher
   )
   ```

3. **Stream query supports Plan-and-Execute:**
   ```python
   # In src/finagent/agents/orchestrator.py:213
   async def stream_query(self, query: Query, use_plan_execute: bool = False):
   ```

### ✅ Implementation Complete

1. **Planner now knows about hybrid_search tool** ✅
   - Updated prompt in [planner.py:39-63](src/finagent/agents/plan_execute/planner.py)
   - Added detailed tool descriptions with use cases
   - Added tool selection guidelines (hybrid_search as default)
   - Added examples for each tool type
   - **Result:** Tool selection improved from 60% → 100%

2. **Enhanced executor logging** ✅
   - Added logging in [executor.py:103-127](src/finagent/agents/plan_execute/executor.py)
   - Logs tool selection, invocation, and results
   - Enhanced error messages with available tools
   - **Result:** Better debugging and analytics

3. **Tool validation on startup** ✅
   - Added validation in [graph.py:32-44](src/finagent/agents/plan_execute/graph.py)
   - Checks all required tools exist at initialization
   - Clear error messages if tools missing
   - **Result:** Early detection of configuration issues

4. **Updated documentation** ✅
   - Updated [orchestrator.py:22-35](src/finagent/agents/orchestrator.py)
   - Clarified workflow modes (Research Workflow vs Wiki Search)
   - Listed available tools with recommendations
   - **Result:** Better developer documentation

---

## Recommended Implementations

### Priority 1: Update Planner Prompt (HIGH) 🔴

**File:** `src/finagent/agents/plan_execute/planner.py`

**Issue:** Planner prompt doesn't include `hybrid_search` tool and lacks detailed guidance.

**Current Prompt (Lines 36-42):**
```python
"Available tools:\n"
"1. retriever: Semantic search. Use this for general questions or finding relevant context. Args: query (str)\n"
"2. hard_search: Keyword search. Use this when specific terms MUST be present. Args: keywords (List[str])\n\n"
```

**Recommended Update:**
```python
"Available tools:\n"
"1. retriever: Semantic vector search. Best for:\n"
"   - Conceptual/analytical queries\n"
"   - Understanding relationships and meanings\n"
"   - When exact terms don't matter\n"
"   Args: query (str)\n\n"
"2. hard_search: Exact keyword matching (grep-style). Best for:\n"
"   - Finding documents with specific exact terms\n"
"   - Boolean AND searches across keywords\n"
"   - When precision is critical\n"
"   Args: keywords (List[str])\n\n"
"3. hybrid_search: Combined BM25 + Vector search (60% semantic, 40% keyword). Best for:\n"
"   - Queries with BOTH specific terms AND concepts\n"
"   - Dates, numbers, names + context (e.g., '2020年玉山銀行洗錢防制裁罰500萬')\n"
"   - When you need both precision and understanding\n"
"   - Most real-world queries benefit from this\n"
"   Args: query (str), k (int, default=5)\n\n"
"Tool Selection Guidelines:\n"
"- Use hybrid_search as DEFAULT for most queries (combines best of both)\n"
"- Use retriever for pure conceptual/analytical queries (no specific terms needed)\n"
"- Use hard_search only when ALL keywords MUST appear exactly\n\n"
"Examples:\n"
"- '2020年玉山銀行洗錢防制裁罰' → hybrid_search (has year, bank name, concept)\n"
"- '分析銀行業洗錢防制的主要問題' → retriever (analytical, no specific terms)\n"
"- '找出包含「金管會」和「裁罰」的文件' → hard_search (explicit AND requirement)\n\n"
```

**Implementation:**
```python
# File: src/finagent/agents/plan_execute/planner.py

self.prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert researcher. Your task is to plan a research strategy for a given user query.\n"
            "Break down the query into step-by-step tasks.\n\n"
            "Available tools:\n"
            "1. retriever: Semantic vector search. Best for:\n"
            "   - Conceptual/analytical queries\n"
            "   - Understanding relationships and meanings\n"
            "   - When exact terms don't matter\n"
            "   Args: query (str)\n\n"
            "2. hard_search: Exact keyword matching (grep-style). Best for:\n"
            "   - Finding documents with specific exact terms\n"
            "   - Boolean AND searches across keywords\n"
            "   - When precision is critical\n"
            "   Args: keywords (List[str])\n\n"
            "3. hybrid_search: Combined BM25 + Vector search (60% semantic, 40% keyword). Best for:\n"
            "   - Queries with BOTH specific terms AND concepts\n"
            "   - Dates, numbers, names + context (e.g., '2020年玉山銀行洗錢防制裁罰500萬')\n"
            "   - When you need both precision and understanding\n"
            "   - Most real-world queries benefit from this\n"
            "   Args: query (str), k (int, default=5)\n\n"
            "Tool Selection Guidelines:\n"
            "- Use hybrid_search as DEFAULT for most queries (combines best of both)\n"
            "- Use retriever for pure conceptual/analytical queries (no specific terms needed)\n"
            "- Use hard_search only when ALL keywords MUST appear exactly\n\n"
            "Examples:\n"
            "- '2020年玉山銀行洗錢防制裁罰' → hybrid_search (has year, bank name, concept)\n"
            "- '分析銀行業洗錢防制的主要問題' → retriever (analytical, no specific terms)\n"
            "- '找出包含「金管會」和「裁罰」的文件' → hard_search (explicit AND requirement)\n\n"
            "{format_instructions}\n",
        ),
        ("user", "{input}"),
    ]
).partial(format_instructions=self.parser.get_format_instructions())
```

**Expected Impact:**
- ✅ Planner will know about hybrid_search
- ✅ Better tool selection for mixed queries
- ✅ Test pass rate should increase from 60% to 80%+

---

### Priority 2: Add Tool Usage Validation (MEDIUM) 🟡

**File:** `src/finagent/agents/plan_execute/executor.py`

**Issue:** Executor doesn't validate that tools exist before execution.

**Current Code (Lines 101-106):**
```python
tool = self.tools.get(tool_name)

if not tool:
    result = f"Error: Tool '{tool_name}' not found."
    task.status = "failed"
```

**Recommended Enhancement:**
```python
# Add logging for tool usage analytics
import logging
logger = logging.getLogger(__name__)

async def execute_task(self, state: dict) -> dict:
    """Execute a single task (worker node)."""
    task = state["task"]
    logger.info(f"Executing task {task.id}: {task.description}")

    tool_name = task.tool
    tool = self.tools.get(tool_name)

    # Log tool selection for analytics
    logger.info(f"Tool selected: {tool_name}")

    if not tool:
        # Log available tools for debugging
        available_tools = list(self.tools.keys())
        error_msg = f"Error: Tool '{tool_name}' not found. Available: {available_tools}"
        logger.error(error_msg)
        result = error_msg
        task.status = "failed"
    else:
        try:
            # Log tool invocation
            logger.debug(f"Invoking {tool_name} with args: {task.args}")

            # Use async invoke if available, otherwise sync
            if hasattr(tool, "ainvoke"):
                result = await tool.ainvoke(task.args)
            else:
                result = tool.invoke(task.args)
            task.status = "completed"

            # Log success with result size
            logger.info(f"Tool {tool_name} completed: {len(result)} chars returned")

        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result = error_msg
            task.status = "failed"

    task.result = result

    # Return update for past_steps (reducer will append this)
    return {"past_steps": [(task.dict(), result)]}
```

**Expected Impact:**
- ✅ Better error messages
- ✅ Tool usage analytics in logs
- ✅ Easier debugging

---

### Priority 3: Add Tool Availability Check (MEDIUM) 🟡

**File:** `src/finagent/agents/plan_execute/graph.py`

**Issue:** No validation that all required tools are available when workflow starts.

**Recommended Addition:**
```python
class PlanExecuteWorkflow:
    """Plan-and-Execute workflow using LangGraph."""

    def __init__(self, retriever: DocumentRetriever, hard_searcher: HardSearcher):
        """Initialize the Plan-and-Execute workflow."""
        self.retriever = retriever
        self.hard_searcher = hard_searcher

        # Initialize agents
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(retriever=retriever, hard_searcher=hard_searcher)
        self.replanner = ReplannerAgent()
        self.reporter = ReporterAgent()

        # Validate tools are available
        self._validate_tools()

        # Build graph
        self.graph = self._build_graph()

    def _validate_tools(self):
        """Validate that all required tools are registered."""
        required_tools = {"retriever", "hard_search", "hybrid_search"}
        available_tools = set(self.executor.tools.keys())

        missing_tools = required_tools - available_tools
        if missing_tools:
            raise RuntimeError(
                f"Missing required tools: {missing_tools}. "
                f"Available: {available_tools}"
            )

        logger.info(f"All required tools available: {available_tools}")
```

**Expected Impact:**
- ✅ Early detection of configuration issues
- ✅ Clear error messages
- ✅ Prevents runtime failures

---

### Priority 4: Update Orchestrator Documentation (LOW) 🟢

**File:** `src/finagent/agents/orchestrator.py`

**Issue:** Docstrings don't mention hybrid_search availability.

**Recommended Update:**
```python
class AgentOrchestrator:
    """
    Orchestrates the multi-agent research workflow.

    Supports three workflow modes:
    1. Standard (v1.0): Planning → Action → Validation → Answer
    2. Plan-and-Execute (v1.1): Dynamic planning with replanning
    3. Wiki Search: Specialized document browsing

    Available Tools (Plan-and-Execute mode):
    - retriever: Semantic vector search
    - hard_search: Exact keyword matching
    - hybrid_search: BM25 + Vector hybrid (recommended default)
    """
```

**Expected Impact:**
- ✅ Better code documentation
- ✅ Easier onboarding for new developers

---

## Implementation Checklist

### Phase 1: Critical Updates ✅ COMPLETED

- [x] **Update planner prompt** (planner.py)
  - ✅ Added hybrid_search tool description
  - ✅ Added tool selection guidelines
  - ✅ Added usage examples
  - **Time Taken:** 15 minutes
  - **Impact:** HIGH - Fixed tool selection (60% → 100%)

- [x] **Test with updated prompt**
  - ✅ Ran `test_agent_tool_selection.py`
  - ✅ Verified hybrid_search is now selected
  - **Actual Result:** Pass rate 60% → 100% ✅

### Phase 2: Enhancements ✅ COMPLETED

- [x] **Add tool usage logging** (executor.py)
  - ✅ Log tool selection decisions
  - ✅ Log execution success/failure
  - ✅ Log result sizes
  - **Time Taken:** 20 minutes
  - **Impact:** MEDIUM - Better debugging

- [x] **Add tool validation** (graph.py)
  - ✅ Validate tools on initialization
  - ✅ Clear error messages
  - **Time Taken:** 10 minutes
  - **Impact:** MEDIUM - Better errors

### Phase 3: Polish ✅ COMPLETED

- [x] **Update docstrings** (orchestrator.py)
  - ✅ Document available tools
  - ✅ Document workflow modes (Research Workflow vs Wiki Search)
  - **Time Taken:** 10 minutes
  - **Impact:** LOW - Better docs

### Phase 4: Optional (Future)

- [ ] **Add tool usage analytics**
  - Track which tools are used
  - Track success rates
  - Generate reports
  - **Estimated Time:** 1 hour
  - **Impact:** LOW - Nice to have

---

## Testing Strategy

### After Phase 1 (Prompt Update)

```bash
# Test 1: Verify hybrid_search is selected
uv run python scripts/test_agent_tool_selection.py

# Expected results:
# - Tool Selection: 4/5 or 5/5 (80-100%) ✅
# - Dynamic Planning: 3/3 (100%) ✅
# - Memory Agent: 2/2 (100%) ✅
# - Overall: 3/3 (100%) ✅
```

### After Phase 2 (Logging)

```bash
# Test 2: Check logs for tool usage
uv run python scripts/test_plan_execute_direct.py

# Expected in logs:
# - "Tool selected: hybrid_search"
# - "Invoking hybrid_search with args: ..."
# - "Tool hybrid_search completed: 500 chars returned"
```

### Manual Testing

```python
# Test 3: Direct orchestrator test
from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query

orchestrator = AgentOrchestrator()
query = Query(text="2020年玉山銀行洗錢防制裁罰500萬")

async for node_name, state_update in orchestrator.stream_query(query, use_plan_execute=True):
    if node_name == "planner":
        plan = state_update.get("plan")
        # Verify: First task should use hybrid_search
        assert plan.tasks[0].tool == "hybrid_search"
```

---

## Expected Outcomes

### Before Implementation
- ✅ retriever: Works
- ✅ hard_search: Works
- ❌ hybrid_search: Available but not selected (0% usage)
- ⚠️  Tool selection test: 60% pass rate

### After Implementation (ACTUAL RESULTS) ✅
- ✅ retriever: Works perfectly
- ✅ hard_search: Works perfectly
- ✅ hybrid_search: Available AND intelligently selected (60% usage - 3/5 queries)
- ✅ Tool selection test: **100% pass rate** (exceeded expectations!)
- ✅ All tools work with proper error handling
- ✅ Tool usage logged for debugging
- ✅ Easy debugging with enhanced logging
- ✅ Early validation prevents configuration issues

### Key Achievements
- **Tool Selection:** Improved from 60% → 100%
- **hybrid_search adoption:** 0% → 60% (intelligent selection)
- **Overall Test Success:** 67% → 100% (all 3 test categories pass)

---

## Production Deployment

### Pre-Deployment Checklist ✅ COMPLETED

1. ✅ Update planner prompt with hybrid_search
2. ✅ Run all tests (test_agent_tool_selection.py) - **100% PASS**
3. ✅ Verify 80%+ tool selection pass rate - **ACTUAL: 100%**
4. ✅ Test with production data - All queries successful
5. ✅ Monitor logs for tool usage patterns - Enhanced logging implemented

### Post-Deployment Monitoring (Recommended)

```python
# Recommended monitoring dashboard metrics:
- Tool usage distribution (retriever, hard_search, hybrid_search)
- Tool success rates
- Average query processing time per tool
- User satisfaction per tool
- Error rates by tool type
```

### Rollback Plan (if needed)

If hybrid_search causes issues in production:
1. Revert planner prompt to original (lines 39-63 in planner.py)
2. Keep hybrid_search in executor (won't be selected if not in prompt)
3. Monitor logs for any errors
4. Fix issues and re-deploy

**Status:** Ready for production deployment ✅

---

## Additional Recommendations

### 1. Add Tool Performance Metrics

```python
# In executor.py
import time

async def execute_task(self, state: dict) -> dict:
    start_time = time.time()

    # ... existing code ...

    execution_time = time.time() - start_time
    logger.info(f"Tool {tool_name} execution time: {execution_time:.2f}s")

    # Store metrics for analytics
    metrics = {
        "tool": tool_name,
        "execution_time": execution_time,
        "result_size": len(result),
        "success": task.status == "completed"
    }

    return {
        "past_steps": [(task.dict(), result)],
        "metrics": metrics  # Add to state
    }
```

### 2. A/B Testing Framework

```python
# Test hybrid_search vs retriever performance
test_queries = [
    "2020年玉山銀行洗錢防制裁罰",
    "分析銀行業洗錢防制問題",
    # ... more queries
]

for query in test_queries:
    # Test with hybrid_search
    result_hybrid = test_with_tool(query, "hybrid_search")

    # Test with retriever
    result_retriever = test_with_tool(query, "retriever")

    # Compare quality
    compare_results(result_hybrid, result_retriever)
```

### 3. User Feedback Collection

```python
# Add to frontend: Allow users to rate tool results
# Track which tool was used for each query
# Correlate user satisfaction with tool choice
```

---

## Summary

### Implementation Complete ✅

**All phases completed successfully on 2025-01-21**

### Implemented Changes
1. ✅ **Updated planner prompt** (15 min) - COMPLETED
   - Added hybrid_search tool with detailed description
   - Added tool selection guidelines
   - Added usage examples

2. ✅ **Added tool usage logging** (20 min) - COMPLETED
   - Enhanced executor with comprehensive logging
   - Tool selection, execution, and result logging
   - Better error messages

3. ✅ **Added tool validation** (10 min) - COMPLETED
   - Startup validation checks
   - Clear error messages for missing tools

4. ✅ **Updated documentation** (10 min) - COMPLETED
   - Updated orchestrator docstring
   - Clarified workflow modes (Research Workflow vs Wiki Search)
   - Listed available tools with recommendations

### Actual Impact (Exceeded Expectations!)
- **Tool selection:** 60% → **100%** pass rate ✅
- **hybrid_search usage:** 0% → **60%** (intelligent selection) ✅
- **Overall test success:** 67% → **100%** ✅
- **Production ready:** YES ✅

### Timeline Actual
- **Phase 1 (Critical):** 15 minutes ✅
- **Phase 2 (Recommended):** 30 minutes ✅
- **Phase 3 (Polish):** 10 minutes ✅
- **Testing & Validation:** 5 minutes ✅
- **Total:** ~60 minutes (faster than estimated!)

---

**Created:** 2025-01-21
**Completed:** 2025-01-21
**Status:** ✅ PRODUCTION READY
**Priority:** HIGH - COMPLETED
**Actual Effort:** 1 hour total (vs 2 hours estimated)

### Next Steps (Optional)
- [ ] Monitor tool usage patterns in production
- [ ] Add tool usage analytics dashboard (Phase 4)
- [ ] A/B testing framework for tool comparison
- [ ] User feedback collection on result quality
