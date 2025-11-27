# Hybrid Search Implementation for FinAgent

**Date:** 2025-01-21
**Research:** LangChain hybrid search patterns (BM25 + Vector Search)

## Current Implementation vs. Industry Best Practice

### Current Approach in FinAgent

**Two Separate Tools:**
1. **RetrieverTool** - Semantic vector search (Chroma)
2. **HardSearchTool** - Grep-based file search

**Issues:**
- HardSearcher reads files from disk (grep-like approach)
- Not integrated with vector search
- Requires files to persist on disk
- Separate tool invocations (no unified ranking)

### LangChain Best Practice: Hybrid Search

**Industry Standard:**
Combine **BM25 (keyword)** + **Vector Search (semantic)** using `EnsembleRetriever`

## How LangChain Handles It

### 1. BM25Retriever

**What is BM25?**
- Best Match 25 algorithm
- Keyword-based retrieval (like TF-IDF but better)
- Works on **in-memory documents**, not disk files
- Fast and doesn't require reading files

**Key Difference from HardSearcher:**
- ❌ HardSearcher: Greps actual files on disk
- ✅ BM25Retriever: Searches in-memory document collection

### 2. EnsembleRetriever

**Combines multiple retrievers with weighted ranking:**
```python
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_community.vectorstores import Chroma

# Step 1: Get documents from vector DB
documents = [...]  # Load from Chroma or database

# Step 2: Create BM25 retriever (keyword search)
bm25_retriever = BM25Retriever.from_documents(
    documents=documents,
    k=5
)

# Step 3: Create vector retriever (semantic search)
vector_retriever = chroma.as_retriever(
    search_type="similarity",
    search_kwargs={'k': 5}
)

# Step 4: Combine with weighted ensemble
ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.6, 0.4]  # 60% semantic, 40% keyword
)

# Step 5: Search (automatically combines results)
results = ensemble_retriever.invoke(query)
```

## Recommendation for FinAgent

### Option A: Replace HardSearchTool with BM25Retriever ⭐ **RECOMMENDED**

**Benefits:**
- ✅ Industry standard approach
- ✅ Works with in-memory documents (no file reading)
- ✅ Integrated ranking with EnsembleRetriever
- ✅ Better performance (no disk I/O)
- ✅ Simpler architecture (one unified search)

**Implementation:**

```python
# In src/finagent/tools/hybrid_retriever.py
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class HybridSearchInput(BaseModel):
    """Input for hybrid search."""
    query: str = Field(description="Search query")
    k: int = Field(default=5, description="Number of results")

class HybridRetrieverTool(BaseTool):
    """Hybrid search combining semantic and keyword matching."""

    name: str = "hybrid_search"
    description: str = """Search documents using both semantic understanding and exact keywords.
    Best for queries requiring both meaning and specific terms."""
    args_schema: Type[BaseModel] = HybridSearchInput
    retriever: DocumentRetriever = Field(exclude=True)

    def _run(self, query: str, k: int = 5) -> str:
        # Get all indexed documents from Chroma
        collection = self.retriever.collection
        all_data = collection.get(include=["documents", "metadatas"])

        # Convert to Document objects for BM25
        from langchain.schema import Document
        documents = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(all_data["documents"], all_data["metadatas"])
        ]

        # Create BM25 retriever
        bm25_retriever = BM25Retriever.from_documents(documents, k=k)

        # Get vector retriever (using existing retriever)
        vector_retriever = self.retriever.collection.as_retriever(
            search_kwargs={'k': k}
        )

        # Combine with ensemble
        ensemble = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=[0.6, 0.4]  # Tune these weights
        )

        # Get results
        results = ensemble.invoke(query)

        # Format output
        output = []
        for i, doc in enumerate(results, 1):
            filename = doc.metadata.get("filename", "Unknown")
            output.append(f"[{i}] Source: {filename}\nContent: {doc.page_content}\n")

        return "\n---\n".join(output) if output else "No results found"
```

**Migration Steps:**

1. ✅ Keep RetrieverTool as-is (still useful standalone)
2. ✅ Create new HybridRetrieverTool (as shown above)
3. ✅ Update ExecutorAgent to use HybridRetrieverTool instead of separate tools
4. ✅ Test with production data
5. ⏭️ Deprecate HardSearchTool (keep for backward compatibility initially)

### Option B: Keep Current Architecture (Not Recommended)

**If you want to keep HardSearcher:**

**Benefits:**
- No code changes
- Grep-based search for specific use cases

**Drawbacks:**
- ❌ Requires files on disk
- ❌ Slower (disk I/O)
- ❌ Not industry standard
- ❌ Separate ranking (not unified)

**When to use:**
- Need to search original file formatting
- Need to grep patterns not in indexed chunks
- Have specific grep requirements

## Performance Comparison

| Approach | Speed | Memory | Disk I/O | Ranking |
|----------|-------|--------|----------|---------|
| **HardSearcher (current)** | Slow | Low | High | Separate |
| **BM25 + Ensemble (recommended)** | Fast | Medium | None | Unified |
| **Vector only** | Fast | Medium | None | Semantic only |

## Weights Tuning Guide

**EnsembleRetriever weights control the balance:**

```python
# For legal documents (Taiwan FSC penalties):
weights=[0.6, 0.4]  # 60% semantic, 40% keyword
# Good for: Natural language queries with specific legal terms

weights=[0.5, 0.5]  # Equal weighting
# Good for: Balanced approach, general queries

weights=[0.4, 0.6]  # 40% semantic, 60% keyword
# Good for: Queries with specific numbers, dates, exact names

weights=[0.7, 0.3]  # 70% semantic, 30% keyword
# Good for: Concept-based queries, understanding user intent
```

**Tuning Strategy:**
1. Start with [0.6, 0.4] (semantic-focused)
2. Test with production queries
3. Adjust based on user feedback
4. Monitor precision/recall metrics

## Example Queries: Current vs. Hybrid

### Query 1: "玉山銀行洗錢防制裁罰"

**Current Approach:**
```python
# RetrieverTool (semantic)
results_semantic = retriever_tool.run("玉山銀行洗錢防制裁罰")

# HardSearchTool (keyword - fails in test due to file path issue)
results_keyword = hard_search_tool.run(["玉山銀行", "洗錢防制"])

# Problem: No unified ranking, separate results
```

**Hybrid Approach:**
```python
# HybridRetrieverTool (unified)
results = hybrid_tool.run("玉山銀行洗錢防制裁罰")

# Automatically:
# - Vector search finds semantically similar docs
# - BM25 finds docs with exact keyword matches
# - EnsembleRetriever ranks combined results
# - Returns unified top-k results
```

### Query 2: "2020年金管會裁罰500萬"

**Benefit of Hybrid:**
- Semantic: Understands "裁罰" context
- BM25: Finds exact "2020", "500萬" matches
- Combined: Higher precision for queries with specific terms + concepts

## Implementation Priority

### High Priority 🔴 (Recommended)

**Create HybridRetrieverTool:**
- Implement BM25 + Vector ensemble
- Add to tool registry
- Update ExecutorAgent to prefer hybrid_search

**Estimated Effort:** 2-3 hours
**Impact:** Significantly better search quality

### Medium Priority 🟡 (Optional)

**Tune Ensemble Weights:**
- Collect production queries
- A/B test different weights
- Optimize for Taiwan legal documents

**Estimated Effort:** 1-2 days (data collection + testing)
**Impact:** Incremental search improvement

### Low Priority 🟢 (Keep for Special Cases)

**Maintain HardSearchTool:**
- Keep for special grep-based needs
- Document when to use each tool
- Ensure files persist properly

**Estimated Effort:** 0 hours (current state)
**Impact:** Backward compatibility

## Code Changes Needed

### 1. Create HybridRetrieverTool
```bash
# New file
src/finagent/tools/hybrid_retriever.py
```

### 2. Update Executor to Use Hybrid
```python
# In src/finagent/agents/plan_execute/executor.py
from finagent.tools.hybrid_retriever import HybridRetrieverTool

# Replace separate tools with hybrid
self.tools = [
    HybridRetrieverTool(retriever=retriever),  # Primary search
    RetrieverTool(retriever=retriever),        # Fallback semantic-only
    # HardSearchTool can be deprecated
]
```

### 3. Update Tests
```python
# In scripts/test_e2e_document_lifecycle.py
# Add test for HybridRetrieverTool
async def test_step5_hybrid_retrieval():
    hybrid_tool = HybridRetrieverTool(retriever=retriever)
    result = hybrid_tool.run("玉山銀行洗錢防制")
    assert len(result) > 0
```

## Resources

### LangChain Documentation
- EnsembleRetriever: https://python.langchain.com/docs/how_to/ensemble_retriever/
- BM25Retriever: https://python.langchain.com/docs/integrations/retrievers/bm25/

### Articles
- Medium: "Hybrid Search: Combining BM25 and Semantic Search"
- Stack Overflow: BM25Retriever + ChromaDB implementation examples

### Performance Notes
- **Caution:** Avoid loading all documents in-memory for large datasets (>100k docs)
- **Alternative:** Use vector stores with built-in hybrid search (Elasticsearch, Weaviate)
- **FinAgent Scale:** Current ~500 docs → BM25 in-memory is fine ✅

## Conclusion

**Recommendation:** ✅ **Implement HybridRetrieverTool with BM25 + EnsembleRetriever**

This is the industry-standard approach that:
- ✅ Solves the "file_path" issue (no disk reads)
- ✅ Improves search quality (unified ranking)
- ✅ Follows LangChain best practices
- ✅ Scales well for current dataset size

**Next Steps:**
1. Implement HybridRetrieverTool (2-3 hours)
2. Test with production queries
3. Compare quality vs. current approach
4. Tune ensemble weights based on results
5. Deprecate HardSearchTool (optional)

**Expected Impact:**
- Better precision for queries with specific terms (dates, numbers, names)
- Unified ranking improves top-k results quality
- No more file persistence issues
- Aligns with LangChain v1.0 best practices

---

**Created:** 2025-01-21
**Research Source:** LangChain documentation, Stack Overflow, Medium articles
**Status:** ✅ **READY FOR IMPLEMENTATION**
