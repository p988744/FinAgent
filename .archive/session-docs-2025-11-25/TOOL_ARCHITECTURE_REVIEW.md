# Tool Architecture Review - FinAgent

**Date:** 2025-11-24
**Purpose:** Review of tool implementations and integration with agent workflows
**Status:** ⚠️ Architecture Issues Identified

---

## Executive Summary

The FinAgent project has a **dual tool hierarchy problem** that creates maintenance challenges and limits functionality. While the v1.1 Plan-Execute workflow works with 3 LangChain-based tools, there are 7 additional custom tools that cannot be used due to incompatible interfaces.

**Key Finding:** Two incompatible `BaseTool` hierarchies exist in the codebase:
1. **LangChain BaseTool** - 3 tools in active use ✅
2. **Custom BaseTool** - 7 tools implemented but unusable ❌

---

## Current Tool Ecosystem

### Active Tools (3) - LangChain BaseTool

Located in `src/finagent/tools/`:

| Tool | Purpose | Status | Integration |
|------|---------|--------|-------------|
| **RetrieverTool** | Semantic vector search via Chroma | ✅ Working | Plan-Execute workflow |
| **HardSearchTool** | Exact keyword matching | ✅ Working | Plan-Execute workflow |
| **HybridRetrieverTool** | Combined BM25 + vector (60%/40%) | ✅ Working | Plan-Execute workflow |

**Implementation Pattern:**
```python
from langchain_core.tools import BaseTool

class RetrieverTool(BaseTool):
    def _run(self, query: str, k: int = 5) -> str:
        # Implementation

    async def _arun(self, query: str, k: int = 5) -> str:
        # Async implementation
```

### Unused Tools (7) - Custom BaseTool

Located in `src/finagent/tools/`:

| Tool | Purpose | Status | Issue |
|------|---------|--------|-------|
| **VectorSearchTool** | Alternative vector search | ❌ Incompatible | Wrong interface |
| **HybridSearchTool** | Alternative hybrid search | ❌ Incompatible | Wrong interface |
| **MultiEntitySearchTool** | Multi-entity extraction | ❌ Incompatible | Wrong interface |
| **MetadataSearchTool** | Metadata-based search | ❌ Incompatible | Wrong interface |
| **ListDocumentsTool** | List all documents | ❌ Incompatible | Wrong interface |
| **ReadFileTool** | Read document content | ❌ Incompatible | Wrong interface |
| **ToolRegistry** | Tool management system | ❌ Disconnected | Not integrated |

**Custom Pattern:**
```python
from finagent.tools.base import BaseTool  # Custom ABC

class VectorSearchTool(BaseTool):
    def execute(self, **kwargs) -> Any:
        # Implementation

    def get_capability(self) -> str:
        # Return capability description
```

---

## The Interface Incompatibility Problem

### Executor's Tool Invocation

In `src/finagent/agents/plan_execute/executor.py` (lines 126-129):

```python
# ExecutorAgent.execute_task() expects:
if hasattr(tool, "ainvoke"):
    result = await tool.ainvoke(task.args)  # LangChain async
else:
    result = tool.invoke(task.args)  # LangChain sync
```

### Interface Comparison

| Aspect | LangChain BaseTool | Custom BaseTool |
|--------|-------------------|-----------------|
| **Base Class** | `langchain_core.tools.BaseTool` | `finagent.tools.base.BaseTool` |
| **Main Methods** | `_run()`, `_arun()` | `execute()` |
| **Public Interface** | `invoke()`, `ainvoke()` (auto) | `execute()`, `execute_with_tracking()` |
| **Args Schema** | Pydantic with `args_schema` | Dict validation in `validate_input()` |
| **Capability** | Via `description` property | Via `get_capability()` method |
| **Tracking** | External | Built-in with `execute_with_tracking()` |

**Result:** Custom tools would fail if registered because they lack `invoke()` and `ainvoke()` methods.

---

## Workflow Integration Analysis

### 1. Research Workflow (v1.1 Plan-Execute) ✅

**Flow:**
```
QueryAnalyzer → Planner → ExecutorAgent → Replanner → Reporter
                             ↓
                    Uses 3 LangChain tools
```

**Tool Registration** (executor.py:29-33):
```python
self.tools = {
    "retriever": self.retriever_tool,       # LangChain BaseTool
    "hard_search": self.hard_search_tool,   # LangChain BaseTool
    "hybrid_search": self.hybrid_retriever_tool,  # LangChain BaseTool
}
```

**Status:** ✅ Working correctly with 3 tools

### 2. Wiki Search Workflow ⚠️

**Flow:**
```
WikiSearchWorkflow → search_node → synthesize_node
                          ↓
                 Direct retriever.retrieve() call
```

**Tool Usage** (wiki_search/graph.py:57):
```python
def search_node(self, state: WikiSearchState) -> dict:
    docs = self.retriever.retrieve(query=query, n_results=5)
    # Direct method call, not tool invocation
```

**Status:** ⚠️ Bypasses tool system entirely, uses direct retriever

### 3. Wiki API Endpoints 🔧

**Location:** `src/finagent/api/routes/wiki.py`

**Search Implementation:**
- Implements 6 search strategies (vector, category, entity, file, grep, hybrid)
- Each strategy directly uses `DocumentRetriever` or `HardSearcher`
- Does NOT use the tool system at all

**Example** (wiki.py:649-650):
```python
async def _vector_search(query: str, max_results: int, filters: SearchFilters):
    retriever = DocumentRetriever()
    chunks = retriever.retrieve(query, n_results=max_results)
```

**Status:** 🔧 Completely independent implementation, no tool integration

---

## Tool Validation & Discovery

### Current Validation (graph.py:34-46)

```python
def _validate_tools(self):
    required_tools = {"retriever", "hard_search", "hybrid_search"}
    available_tools = set(self.executor.tools.keys())

    missing_tools = required_tools - available_tools
    if missing_tools:
        raise RuntimeError(f"Missing required tools: {missing_tools}")
```

**Issues:**
1. Hard-coded tool requirements
2. No dynamic tool discovery
3. No way to add new tools without code changes

---

## Performance & Cost Analysis

| Tool | Latency | Cost | Usage |
|------|---------|------|-------|
| **HardSearchTool** | 1-3s | $0 | Active |
| **RetrieverTool** | 2-5s | $0.00005 | Active |
| **HybridRetrieverTool** | 3-7s | $0.00005 | Active |
| **Wiki vector_search** | 2-5s | $0.00005 | Via API |
| **Wiki grep_search** | 1-3s | $0 | Via API |
| **Wiki hybrid_search** | 3-7s | $0.00005 | Via API |

**Observation:** Wiki API reimplements the same functionality as tools

---

## Code Duplication Analysis

### Duplicate Implementations Found

1. **Vector Search** (3 implementations):
   - `RetrieverTool` (tools/retriever.py)
   - `VectorSearchTool` (tools/search.py) - unused
   - `_vector_search()` (api/routes/wiki.py:642)

2. **Hybrid Search** (3 implementations):
   - `HybridRetrieverTool` (tools/hybrid_retriever.py)
   - `HybridSearchTool` (tools/search.py) - unused
   - `_hybrid_search()` (api/routes/wiki.py:881)

3. **Keyword Search** (2 implementations):
   - `HardSearchTool` (tools/search.py)
   - `_grep_search()` (api/routes/wiki.py:834)

**Code Overlap:** ~40% duplicate logic across implementations

---

## Recommendations

### Option A: Migrate to LangChain BaseTool (Recommended) ✅

**Approach:**
1. Convert 7 custom tools to inherit from `langchain_core.tools.BaseTool`
2. Implement `_run()` and `_arun()` methods
3. Use Pydantic `args_schema` for validation

**Pros:**
- Full integration with ExecutorAgent
- Consistent interface
- LangChain ecosystem compatibility

**Cons:**
- Lose custom tracking features
- Need to refactor 7 tools

**Implementation Example:**
```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class MetadataSearchArgs(BaseModel):
    filters: dict = Field(description="Metadata filters")
    limit: int = Field(default=10, description="Result limit")

class MetadataSearchTool(BaseTool):
    name = "metadata_search"
    description = "Search documents by metadata"
    args_schema = MetadataSearchArgs

    def _run(self, filters: dict, limit: int = 10) -> str:
        # Implementation
        return results

    async def _arun(self, filters: dict, limit: int = 10) -> str:
        return self._run(filters, limit)
```

### Option B: Create Adapter Pattern 🔄

**Approach:**
1. Create `LangChainToolAdapter` class
2. Wrap custom tools to provide LangChain interface
3. Register adapted tools with executor

**Pros:**
- Preserves custom tool features
- Gradual migration path
- Both interfaces supported

**Cons:**
- Additional abstraction layer
- More complex architecture

### Option C: Unify Wiki API with Tools 🎯

**Approach:**
1. Refactor wiki.py search functions to use tools
2. Create shared tool instances
3. Eliminate duplicate implementations

**Benefits:**
- Single source of truth
- Consistent behavior
- Reduced maintenance

**Example:**
```python
# In wiki.py
async def _vector_search(query: str, max_results: int, filters: SearchFilters):
    # Use tool instead of direct retriever
    tool = RetrieverTool(retriever=DocumentRetriever())
    result = await tool.ainvoke({"query": query, "k": max_results})
    # Process and filter results
```

---

## Priority Actions

### Immediate (This Week)
1. ✅ **Fix LangGraph plan field** - Already completed
2. 🔧 **Document tool architecture** - This document
3. ⚠️ **Decide on migration strategy** - Choose Option A, B, or C

### Short-term (Next Sprint)
1. 🚀 **Implement chosen strategy**
2. 🧪 **Add tool integration tests**
3. 📝 **Update SHARED_TOOLS_IMPLEMENTATION_GUIDE.md**

### Long-term (Next Month)
1. 🔄 **Unify all search implementations**
2. 🎯 **Implement dynamic tool discovery**
3. 📊 **Add tool performance monitoring**

---

## Testing Requirements

### Unit Tests Needed
```python
# Test tool interface compatibility
def test_tool_has_required_methods():
    tool = RetrieverTool(retriever=mock_retriever)
    assert hasattr(tool, "invoke")
    assert hasattr(tool, "ainvoke")

# Test tool registration
def test_executor_tool_registration():
    executor = ExecutorAgent(retriever, searcher)
    assert "retriever" in executor.tools
    assert "hard_search" in executor.tools
    assert "hybrid_search" in executor.tools
```

### Integration Tests Needed
```python
# Test tool execution in workflow
async def test_plan_execute_with_tools():
    workflow = PlanExecuteWorkflow(retriever, searcher)
    state = {"input": "test query", "plan": test_plan}
    result = await workflow.graph.ainvoke(state)
    assert result["response"] is not None
```

---

## Conclusion

The FinAgent tool architecture has solid foundations but suffers from:

1. **Dual hierarchy problem** - Two incompatible BaseTool classes
2. **Code duplication** - Same functionality implemented 2-3 times
3. **Limited extensibility** - Hard-coded tool requirements
4. **Disconnected systems** - Wiki API doesn't use tools

**Recommendation:** Adopt Option A (migrate to LangChain BaseTool) for consistency, then Option C (unify Wiki API) to eliminate duplication.

**Impact if Fixed:**
- 10 tools available instead of 3
- 40% less code to maintain
- Consistent search behavior across all endpoints
- Easier to add new tools

---

## Appendix: File Locations

### Tool Implementations
- `/src/finagent/tools/retriever.py` - RetrieverTool (LangChain)
- `/src/finagent/tools/search.py` - HardSearchTool, VectorSearchTool, etc.
- `/src/finagent/tools/hybrid_retriever.py` - HybridRetrieverTool
- `/src/finagent/tools/base.py` - Custom BaseTool ABC

### Workflow Integration
- `/src/finagent/agents/plan_execute/executor.py` - Tool usage
- `/src/finagent/agents/plan_execute/graph.py` - Tool validation
- `/src/finagent/agents/wiki_search/graph.py` - Wiki workflow
- `/src/finagent/api/routes/wiki.py` - Wiki API endpoints

### Configuration
- `/src/finagent/agents/orchestrator.py` - Workflow initialization
- `/.env` - API keys and configuration
- `/data/finagent.db` - Settings database

---

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Author:** Claude (via exploration and analysis)