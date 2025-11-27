# Shared Tools and Workflows Implementation Guide

**Purpose**: Guide for sharing retrieval tools and graph components between Plan-and-Execute workflow and new wiki search feature

**Based on**: LangChain v1.0 & LangGraph multi-agent patterns

---

## Overview

This guide shows how to refactor existing tools for reuse across multiple workflows without code duplication.

### Current Architecture
```
Plan-and-Execute Workflow
└── tools.py (RetrieverTool, HardSearchTool)
    └── retriever.py (DocumentRetriever)
```

### Target Architecture
```
Shared Tools Module
├── tools/
│   ├── __init__.py
│   ├── retrieval.py (RetrieverTool)
│   └── search.py (HardSearchTool)
└── workflows/
    ├── plan_execute/ (existing)
    └── wiki_search/ (new)
```

---

## Pattern 1: Shared Toolbox

### Step 1: Extract Tools to Shared Module

**Create**: `src/finagent/tools/` directory

**Move tools from**: `src/finagent/agents/plan_execute/tools.py`

**To**:
- `src/finagent/tools/retrieval.py`
- `src/finagent/tools/search.py`

**Example: `src/finagent/tools/retrieval.py`**
```python
"""Shared retrieval tool for multiple workflows."""

from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from finagent.document_processing.retriever import DocumentRetriever


class RetrieverInput(BaseModel):
    """Input schema for retriever tool."""
    query: str = Field(description="Search query for semantic retrieval")


class RetrieverTool(BaseTool):
    """Reusable semantic search tool."""

    name: str = "retriever"
    description: str = (
        "Semantic search tool for finding relevant documents. "
        "Use this for general questions or finding relevant context."
    )
    args_schema: Type[BaseModel] = RetrieverInput

    # Stateful components (excluded from tool schema)
    retriever: DocumentRetriever = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        """Synchronous execution."""
        results = self.retriever.retrieve(query, top_k=5)
        if not results:
            return "No relevant documents found."

        output = []
        for i, doc in enumerate(results, 1):
            output.append(f"[Document {i}]")
            output.append(f"Content: {doc.page_content[:300]}...")
            output.append(f"Source: {doc.metadata.get('source', 'unknown')}")
            output.append("---")

        return "\n".join(output)

    async def _arun(self, query: str) -> str:
        """Async execution (for async workflows)."""
        # If retriever has async methods, use them
        return self._run(query)
```

**Example: `src/finagent/tools/__init__.py`**
```python
"""Shared tools for all workflows."""

from finagent.tools.retrieval import RetrieverTool
from finagent.tools.search import HardSearchTool

__all__ = ["RetrieverTool", "HardSearchTool"]
```

### Step 2: Update Plan-and-Execute Workflow

**In**: `src/finagent/agents/plan_execute/executor.py`

**Change**:
```python
# OLD
from finagent.agents.plan_execute.tools import RetrieverTool, HardSearchTool

# NEW
from finagent.tools import RetrieverTool, HardSearchTool
```

---

## Pattern 2: Wiki Search Workflow

### Step 1: Define Wiki Search State

**Create**: `src/finagent/agents/wiki_search/models.py`

```python
"""Models for wiki search workflow."""

from typing import TypedDict, Optional, List
from pydantic import BaseModel, Field


class WikiSearchState(TypedDict):
    """State for wiki search workflow."""
    query: str  # User's wiki search query
    documents: Optional[List[dict]]  # Retrieved documents
    answer: Optional[str]  # Final synthesized answer
```

### Step 2: Create Wiki Search Agent

**Create**: `src/finagent/agents/wiki_search/searcher.py`

```python
"""Wiki searcher agent."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.tools import RetrieverTool  # SHARED TOOL
from finagent.agents.wiki_search.models import WikiSearchState
from finagent.config import settings


class WikiSearcher:
    """Agent for wiki-style document search."""

    def __init__(self, retriever_tool: RetrieverTool):
        """Initialize with shared retriever tool."""
        self.retriever_tool = retriever_tool

        base_url = settings.effective_llm_base_url
        if base_url:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                base_url=base_url,
                temperature=0,
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                temperature=0,
            )

    async def search(self, state: WikiSearchState) -> dict:
        """Execute wiki search using shared retriever."""
        query = state["query"]

        # Use shared retriever tool
        raw_results = self.retriever_tool._run(query)

        # Parse results (simplified)
        documents = self._parse_results(raw_results)

        return {"documents": documents}

    def _parse_results(self, raw_results: str) -> List[dict]:
        """Parse retriever output into structured documents."""
        # Implementation details...
        return []
```

### Step 3: Create Wiki Workflow Graph

**Create**: `src/finagent/agents/wiki_search/graph.py`

```python
"""Wiki search workflow using LangGraph."""

from langgraph.graph import StateGraph, END

from finagent.agents.wiki_search.models import WikiSearchState
from finagent.agents.wiki_search.searcher import WikiSearcher
from finagent.tools import RetrieverTool
from finagent.document_processing.retriever import DocumentRetriever


class WikiSearchWorkflow:
    """LangGraph workflow for wiki search."""

    def __init__(self):
        """Initialize workflow with shared tools."""
        # Create shared retriever tool instance
        doc_retriever = DocumentRetriever()
        retriever_tool = RetrieverTool(retriever=doc_retriever)

        # Initialize agents with shared tool
        self.searcher = WikiSearcher(retriever_tool=retriever_tool)

        # Build graph
        workflow = StateGraph(WikiSearchState)

        # Add nodes
        workflow.add_node("search", self.searcher.search)
        workflow.add_node("synthesize", self._synthesize)

        # Add edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "synthesize")
        workflow.add_edge("synthesize", END)

        self.graph = workflow.compile()

    async def _synthesize(self, state: WikiSearchState) -> dict:
        """Synthesize wiki answer from documents."""
        # Use LLM to create wiki-style summary
        # Implementation details...
        return {"answer": "Wiki summary..."}

    async def run(self, query: str) -> dict:
        """Execute wiki search workflow."""
        result = await self.graph.ainvoke({"query": query})
        return result
```

---

## Pattern 3: Parallel Search with Send API

For advanced use case: Run wiki search and plan-execute search in parallel.

**Create**: `src/finagent/agents/orchestrator_v2.py`

```python
"""Multi-workflow orchestrator using Send API."""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END, START
from langgraph.types import Send

from finagent.agents.plan_execute.graph import PlanExecuteWorkflow
from finagent.agents.wiki_search.graph import WikiSearchWorkflow


class OrchestratorState(TypedDict):
    """State for multi-workflow orchestrator."""
    query: str
    plan_execute_result: Annotated[dict, "Result from plan-execute workflow"]
    wiki_search_result: Annotated[dict, "Result from wiki search workflow"]
    combined_answer: str


class MultiWorkflowOrchestrator:
    """Orchestrator that runs multiple workflows in parallel."""

    def __init__(self):
        """Initialize with both workflows."""
        self.plan_execute_workflow = PlanExecuteWorkflow()
        self.wiki_search_workflow = WikiSearchWorkflow()

        # Build orchestrator graph
        workflow = StateGraph(OrchestratorState)

        workflow.add_node("dispatcher", self._dispatch)
        workflow.add_node("plan_execute_worker", self._run_plan_execute)
        workflow.add_node("wiki_worker", self._run_wiki)
        workflow.add_node("combiner", self._combine)

        workflow.set_entry_point("dispatcher")

        # Dispatcher sends work to both workers in parallel
        workflow.add_conditional_edges(
            "dispatcher",
            lambda state: [
                Send("plan_execute_worker", state),
                Send("wiki_worker", state)
            ]
        )

        workflow.add_edge("plan_execute_worker", "combiner")
        workflow.add_edge("wiki_worker", "combiner")
        workflow.add_edge("combiner", END)

        self.graph = workflow.compile()

    def _dispatch(self, state: OrchestratorState) -> OrchestratorState:
        """Dispatch query to workers."""
        return state

    async def _run_plan_execute(self, state: OrchestratorState) -> dict:
        """Run plan-execute workflow."""
        result = await self.plan_execute_workflow.graph.ainvoke({
            "input": state["query"]
        })
        return {"plan_execute_result": result}

    async def _run_wiki(self, state: OrchestratorState) -> dict:
        """Run wiki search workflow."""
        result = await self.wiki_search_workflow.run(state["query"])
        return {"wiki_search_result": result}

    async def _combine(self, state: OrchestratorState) -> dict:
        """Combine results from both workflows."""
        # Merge wiki overview with detailed plan-execute analysis
        plan_result = state.get("plan_execute_result", {})
        wiki_result = state.get("wiki_search_result", {})

        combined = f"""
        # Wiki Overview
        {wiki_result.get('answer', 'N/A')}

        # Detailed Analysis
        {plan_result.get('response', 'N/A')}
        """

        return {"combined_answer": combined}

    async def run(self, query: str) -> str:
        """Execute multi-workflow orchestration."""
        result = await self.graph.ainvoke({"query": query})
        return result["combined_answer"]
```

---

## Pattern 4: Tool Factory (Advanced)

For dynamic tool instantiation with different configurations.

**Create**: `src/finagent/tools/factory.py`

```python
"""Tool factory for creating configured tool instances."""

from typing import Optional

from finagent.tools import RetrieverTool, HardSearchTool
from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher


class ToolFactory:
    """Factory for creating shared tool instances."""

    @staticmethod
    def create_retriever_tool(
        collection_name: str = "legal_documents",
        top_k: int = 5
    ) -> RetrieverTool:
        """Create retriever tool with specified configuration."""
        retriever = DocumentRetriever(
            collection_name=collection_name,
            top_k=top_k
        )
        return RetrieverTool(retriever=retriever)

    @staticmethod
    def create_hard_search_tool(
        collection_name: str = "legal_documents"
    ) -> HardSearchTool:
        """Create hard search tool with specified configuration."""
        searcher = HardSearcher(collection_name=collection_name)
        return HardSearchTool(searcher=searcher)

    @staticmethod
    def create_wiki_toolset() -> tuple[RetrieverTool, HardSearchTool]:
        """Create toolset optimized for wiki search."""
        return (
            ToolFactory.create_retriever_tool(
                collection_name="legal_documents",
                top_k=3  # Fewer results for wiki overview
            ),
            ToolFactory.create_hard_search_tool()
        )

    @staticmethod
    def create_research_toolset() -> tuple[RetrieverTool, HardSearchTool]:
        """Create toolset optimized for deep research."""
        return (
            ToolFactory.create_retriever_tool(
                collection_name="legal_documents",
                top_k=10  # More results for comprehensive research
            ),
            ToolFactory.create_hard_search_tool()
        )
```

**Usage**:
```python
from finagent.tools.factory import ToolFactory

# For wiki search
wiki_retriever, wiki_search = ToolFactory.create_wiki_toolset()

# For plan-execute
research_retriever, research_search = ToolFactory.create_research_toolset()
```

---

## Migration Checklist

### Phase 1: Extract Shared Tools
- [ ] Create `src/finagent/tools/` directory
- [ ] Move `RetrieverTool` to `tools/retrieval.py`
- [ ] Move `HardSearchTool` to `tools/search.py`
- [ ] Create `tools/__init__.py` with exports
- [ ] Add async `_arun()` methods to both tools
- [ ] Update imports in `plan_execute/executor.py`
- [ ] Run tests to verify Plan-and-Execute still works

### Phase 2: Create Wiki Search Workflow
- [ ] Create `src/finagent/agents/wiki_search/` directory
- [ ] Define `WikiSearchState` in `models.py`
- [ ] Implement `WikiSearcher` agent in `searcher.py`
- [ ] Build `WikiSearchWorkflow` graph in `graph.py`
- [ ] Write unit tests for wiki search
- [ ] Add integration test with shared retriever

### Phase 3: Tool Factory (Optional)
- [ ] Create `tools/factory.py`
- [ ] Implement configuration presets
- [ ] Update workflows to use factory
- [ ] Document factory patterns

### Phase 4: Parallel Orchestration (Optional)
- [ ] Create `orchestrator_v2.py` with Send API
- [ ] Implement dispatcher and combiner nodes
- [ ] Test parallel execution
- [ ] Add performance benchmarks

---

## Testing Strategy

### Unit Tests for Shared Tools

**File**: `tests/unit/tools/test_retrieval_tool.py`

```python
"""Tests for shared retrieval tool."""

import pytest
from unittest.mock import Mock, MagicMock

from finagent.tools import RetrieverTool
from finagent.document_processing.retriever import DocumentRetriever


def test_retriever_tool_schema():
    """Test that tool has correct schema."""
    mock_retriever = Mock(spec=DocumentRetriever)
    tool = RetrieverTool(retriever=mock_retriever)

    assert tool.name == "retriever"
    assert tool.args_schema is not None
    assert "query" in tool.args_schema.model_json_schema()["properties"]


def test_retriever_tool_execution():
    """Test tool execution with mock retriever."""
    mock_retriever = Mock(spec=DocumentRetriever)
    mock_retriever.retrieve.return_value = [
        MagicMock(
            page_content="Test content",
            metadata={"source": "test.txt"}
        )
    ]

    tool = RetrieverTool(retriever=mock_retriever)
    result = tool._run("test query")

    assert "Test content" in result
    assert "test.txt" in result
    mock_retriever.retrieve.assert_called_once_with("test query", top_k=5)
```

### Integration Tests

**File**: `tests/integration/test_wiki_search_workflow.py`

```python
"""Integration tests for wiki search workflow using shared tools."""

import pytest
from finagent.agents.wiki_search.graph import WikiSearchWorkflow


@pytest.mark.asyncio
async def test_wiki_search_with_real_retriever():
    """Test wiki search using real document retriever."""
    workflow = WikiSearchWorkflow()

    result = await workflow.run("玉山銀行洗錢防制裁罰")

    assert result["answer"] is not None
    assert result["documents"] is not None
    assert len(result["documents"]) > 0
```

---

## Performance Considerations

### Shared Tool Instantiation

**Problem**: Creating new tool instances for each workflow wastes resources.

**Solution**: Singleton pattern or dependency injection.

```python
# Singleton approach (simple)
_retriever_tool_instance = None

def get_retriever_tool() -> RetrieverTool:
    """Get or create shared retriever tool instance."""
    global _retriever_tool_instance
    if _retriever_tool_instance is None:
        retriever = DocumentRetriever()
        _retriever_tool_instance = RetrieverTool(retriever=retriever)
    return _retriever_tool_instance
```

### Parallel Execution Benefits

Running wiki search and plan-execute in parallel can reduce latency:

```
Sequential: Wiki (10s) + Plan-Execute (40s) = 50s total
Parallel:   max(Wiki (10s), Plan-Execute (40s)) = 40s total
Speedup:    25% reduction
```

---

## References

### Official Documentation
- **LangChain Tools**: https://python.langchain.com/docs/how_to/custom_tools/
- **LangGraph Multi-Agent**: https://langchain-ai.github.io/langgraph/how-tos/subgraph/
- **Send API**: https://langchain-ai.github.io/langgraph/concepts/low_level/#send

### Internal Documentation
- **[LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md](LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md)** - Core patterns
- **[V1_1_RELEASE_PLAN.md](V1_1_RELEASE_PLAN.md)** - Current implementation status
- **[TOOL_IMPLEMENTATION_REVIEW.md](TOOL_IMPLEMENTATION_REVIEW.md)** - Tool validation

---

## Next Steps

1. **Start with Phase 1**: Extract tools to shared module (low risk, high value)
2. **Validate with tests**: Ensure Plan-and-Execute still works after refactor
3. **Implement Phase 2**: Build wiki search workflow incrementally
4. **Measure impact**: Compare wiki search performance vs. full Plan-and-Execute

**Estimated Effort**:
- Phase 1 (Shared Tools): 2-3 hours
- Phase 2 (Wiki Workflow): 1 day
- Phase 3 (Tool Factory): 3-4 hours (optional)
- Phase 4 (Parallel Orchestration): 1 day (optional)

---

## Questions & Decisions

### Q1: Should wiki search use Plan-and-Execute or simpler workflow?

**Recommendation**: Start simple (search → synthesize → end), add planning if needed.

**Reasoning**: Wiki search is typically one-shot retrieval, not multi-step research.

### Q2: Should tools be stateless or stateful?

**Current approach**: Stateful (tools hold retriever instances)

**Pros**:
- Simpler initialization
- Connection pooling
- Caching benefits

**Cons**:
- Harder to serialize
- Testing requires mocks

**Recommendation**: Keep stateful, use Field(exclude=True) pattern (already implemented correctly).

### Q3: Should we cache retrieval results across workflows?

**Recommendation**: Yes, add caching layer in DocumentRetriever.

**Implementation hint**: Use functools.lru_cache or Redis for distributed scenarios.

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Status**: Ready for implementation
