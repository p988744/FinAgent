# Tool Migration Plan - FinAgent

**Date:** 2025-11-24
**Objective:** Migrate custom tools to LangChain BaseTool for unified architecture
**Priority:** High - Blocking 7 implemented tools from being used

---

## Migration Strategy: LangChain BaseTool Adoption

After reviewing the architecture, we recommend **Option A: Full migration to LangChain BaseTool** as it provides the best long-term maintainability and integration.

---

## Phase 1: Tool Migration (Week 1)

### Tools to Migrate (Priority Order)

1. **MetadataSearchTool** ⭐ High Value
   - Fast search by document metadata
   - No embedding costs
   - Useful for filtered searches

2. **ListDocumentsTool** ⭐ High Value
   - Essential for document management
   - Simple implementation
   - Good first migration candidate

3. **ReadFileTool** ⭐ High Value
   - Direct document content access
   - Needed for detailed analysis
   - Complements search tools

4. **VectorSearchTool** 🔄 Medium Value
   - Alternative vector implementation
   - May have duplicate functionality
   - Consider merging with RetrieverTool

5. **HybridSearchTool** 🔄 Medium Value
   - Alternative hybrid implementation
   - Consider merging with HybridRetrieverTool

6. **MultiEntitySearchTool** 🎯 Specialized
   - Complex multi-entity extraction
   - Higher LLM costs
   - Keep for advanced queries

7. **ToolRegistry** 🏗️ Infrastructure
   - Convert to tool manager
   - Dynamic tool discovery
   - Configuration management

### Migration Template

```python
# Before (Custom BaseTool)
from finagent.tools.base import BaseTool

class MetadataSearchTool(BaseTool):
    name = "metadata_search"

    def execute(self, **kwargs) -> Any:
        filters = kwargs.get("filters", {})
        limit = kwargs.get("limit", 10)
        # Implementation
        return results

    def get_capability(self) -> str:
        return "Search documents by metadata filters"

# After (LangChain BaseTool)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional

class MetadataSearchArgs(BaseModel):
    """Input schema for metadata search."""
    filters: dict = Field(default={}, description="Metadata filters")
    limit: int = Field(default=10, ge=1, le=100, description="Result limit")

class MetadataSearchTool(BaseTool):
    """Tool for searching documents by metadata."""

    name: str = "metadata_search"
    description: str = "Search documents by metadata filters like date, type, authority"
    args_schema: type[BaseModel] = MetadataSearchArgs

    def _run(self, filters: dict = {}, limit: int = 10) -> str:
        """Synchronous execution."""
        # Migrate execute() logic here
        results = self._search_by_metadata(filters, limit)
        return self._format_results(results)

    async def _arun(self, filters: dict = {}, limit: int = 10) -> str:
        """Asynchronous execution."""
        # For now, can just call sync version
        return self._run(filters, limit)

    def _search_by_metadata(self, filters: dict, limit: int) -> list:
        """Internal search implementation."""
        # Original execute() logic
        pass

    def _format_results(self, results: list) -> str:
        """Format results for LLM consumption."""
        # Convert to string format
        pass
```

---

## Phase 2: Tool Integration (Week 2)

### 1. Update ExecutorAgent

```python
# In executor.py __init__()
from finagent.tools import (
    RetrieverTool, HardSearchTool, HybridRetrieverTool,
    MetadataSearchTool, ListDocumentsTool, ReadFileTool,
    MultiEntitySearchTool
)

class ExecutorAgent:
    def __init__(self, retriever: DocumentRetriever, hard_searcher: HardSearcher):
        # Existing tools
        self.retriever_tool = RetrieverTool(retriever=retriever)
        self.hard_search_tool = HardSearchTool(hard_searcher=hard_searcher)
        self.hybrid_retriever_tool = HybridRetrieverTool(
            retriever=retriever,
            semantic_weight=0.6,
            keyword_weight=0.4
        )

        # New migrated tools
        self.metadata_tool = MetadataSearchTool()
        self.list_docs_tool = ListDocumentsTool()
        self.read_file_tool = ReadFileTool()
        self.multi_entity_tool = MultiEntitySearchTool()

        # Register all tools
        self.tools = {
            # Search tools
            "retriever": self.retriever_tool,
            "hard_search": self.hard_search_tool,
            "hybrid_search": self.hybrid_retriever_tool,
            "metadata_search": self.metadata_tool,
            "multi_entity_search": self.multi_entity_tool,

            # Document tools
            "list_documents": self.list_docs_tool,
            "read_file": self.read_file_tool,
        }
```

### 2. Update Planner Prompts

```python
# In planner.py system prompt
AVAILABLE_TOOLS = """
Search Tools:
- retriever: Semantic vector search (best for concepts)
- hard_search: Exact keyword matching (best for specific terms)
- hybrid_search: Combined semantic + keyword (RECOMMENDED DEFAULT)
- metadata_search: Filter by date, type, authority (fast, no embeddings)
- multi_entity_search: Extract multiple entities (higher cost)

Document Tools:
- list_documents: List all available documents
- read_file: Read full document content
"""
```

### 3. Update Tool Validation

```python
# In graph.py
def _validate_tools(self):
    # Core required tools
    required_tools = {"retriever", "hard_search", "hybrid_search"}

    # Optional enhanced tools
    optional_tools = {
        "metadata_search", "multi_entity_search",
        "list_documents", "read_file"
    }

    available_tools = set(self.executor.tools.keys())
    missing_required = required_tools - available_tools

    if missing_required:
        raise RuntimeError(f"Missing required tools: {missing_required}")

    # Log available optional tools
    available_optional = optional_tools & available_tools
    if available_optional:
        logger.info(f"Optional tools available: {available_optional}")
```

---

## Phase 3: Wiki API Unification (Week 3)

### Refactor Wiki Search to Use Tools

```python
# In api/routes/wiki.py

from finagent.tools import (
    RetrieverTool, HardSearchTool, HybridRetrieverTool,
    MetadataSearchTool
)

class WikiSearchHandler:
    """Unified search handler using tools."""

    def __init__(self):
        retriever = DocumentRetriever()
        hard_searcher = HardSearcher()

        self.tools = {
            "vector": RetrieverTool(retriever=retriever),
            "grep": HardSearchTool(hard_searcher=hard_searcher),
            "hybrid": HybridRetrieverTool(
                retriever=retriever,
                semantic_weight=0.6,
                keyword_weight=0.4
            ),
            "metadata": MetadataSearchTool()
        }

    async def search(
        self,
        query: str,
        search_type: str,
        filters: SearchFilters
    ) -> list[SearchResult]:
        """Unified search using tools."""

        tool = self.tools.get(search_type)
        if not tool:
            raise ValueError(f"Unknown search type: {search_type}")

        # Prepare tool arguments
        args = {"query": query}
        if search_type == "metadata":
            args["filters"] = filters.dict()

        # Execute tool
        result = await tool.ainvoke(args)

        # Parse and return results
        return self._parse_tool_output(result, search_type)
```

---

## Phase 4: Testing & Validation (Week 4)

### Test Suite Requirements

```python
# tests/test_tool_migration.py

import pytest
from finagent.tools import MetadataSearchTool

class TestToolMigration:
    """Test migrated tools maintain functionality."""

    @pytest.mark.asyncio
    async def test_metadata_search_tool_interface(self):
        """Test tool has LangChain interface."""
        tool = MetadataSearchTool()

        # Check required attributes
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "args_schema")

        # Check required methods
        assert hasattr(tool, "invoke")
        assert hasattr(tool, "ainvoke")
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")

    @pytest.mark.asyncio
    async def test_metadata_search_execution(self):
        """Test tool executes correctly."""
        tool = MetadataSearchTool()

        result = await tool.ainvoke({
            "filters": {"document_type": "penalty"},
            "limit": 5
        })

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_executor_with_new_tools(self):
        """Test executor can use migrated tools."""
        executor = ExecutorAgent(mock_retriever, mock_searcher)

        # Check all tools registered
        assert len(executor.tools) >= 7
        assert "metadata_search" in executor.tools

        # Test execution
        state = {
            "task": PlanTask(
                id=1,
                description="Search by date",
                tool="metadata_search",
                args={"filters": {"date_from": "2020-01-01"}}
            )
        }

        result = await executor.execute_task(state)
        assert result["past_steps"][0][1] is not None
```

---

## Migration Checklist

### Week 1: Tool Migration
- [ ] Create feature branch: `feature/tool-migration-langchain`
- [ ] Migrate MetadataSearchTool
- [ ] Migrate ListDocumentsTool
- [ ] Migrate ReadFileTool
- [ ] Review and possibly merge VectorSearchTool
- [ ] Review and possibly merge HybridSearchTool
- [ ] Migrate MultiEntitySearchTool
- [ ] Update tool imports in `__init__.py`

### Week 2: Integration
- [ ] Update ExecutorAgent with new tools
- [ ] Update Planner system prompt
- [ ] Update tool validation logic
- [ ] Test workflow with new tools
- [ ] Update tool documentation

### Week 3: Wiki Unification
- [ ] Create WikiSearchHandler class
- [ ] Refactor _vector_search to use tool
- [ ] Refactor _grep_search to use tool
- [ ] Refactor _hybrid_search to use tool
- [ ] Add _metadata_search using tool
- [ ] Remove duplicate implementations

### Week 4: Testing & Deployment
- [ ] Write unit tests for each migrated tool
- [ ] Write integration tests for executor
- [ ] Test Wiki API endpoints
- [ ] Performance testing
- [ ] Update documentation
- [ ] Code review
- [ ] Merge to develop

---

## Success Metrics

### Functionality
- ✅ All 10 tools accessible via ExecutorAgent
- ✅ Wiki API uses shared tools
- ✅ No duplicate search implementations

### Performance
- ⚡ Search latency < 5 seconds
- 💰 Cost per query < $0.001
- 🎯 Search accuracy maintained or improved

### Code Quality
- 📉 40% reduction in duplicate code
- 📊 100% test coverage for tools
- 📝 Complete documentation

---

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation:**
- Keep old tools during migration
- Use feature flags for gradual rollout
- Extensive testing before removal

### Risk 2: Performance Regression
**Mitigation:**
- Benchmark before and after
- Profile tool execution
- Optimize if needed

### Risk 3: LLM Compatibility
**Mitigation:**
- Test with multiple LLM models
- Validate prompt formats
- Add retry logic

---

## Long-term Benefits

1. **Unified Architecture** - Single tool interface for all components
2. **Extensibility** - Easy to add new tools
3. **Maintainability** - Less code duplication
4. **Testing** - Consistent test patterns
5. **Documentation** - Single source of truth
6. **Performance** - Optimized shared implementations
7. **Cost** - Reduced redundant API calls

---

## Next Steps

1. **Immediate:** Review and approve migration plan
2. **Day 1:** Create feature branch and start MetadataSearchTool migration
3. **Day 2-3:** Complete remaining tool migrations
4. **Day 4-5:** Integration and testing
5. **Week 2:** Full integration and Wiki unification

---

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Approved By:** [Pending]
**Target Completion:** [4 weeks from approval]