# FinAgent v1.2 Implementation Plan: Three Workflows

## Implementation Status: COMPLETE

All three workflows have been implemented:

| Workflow | Status | Files |
|----------|--------|-------|
| WikiBuilderWorkflow | DONE | `src/finagent/agents/wiki_builder/` |
| WikiSearchWorkflow | DONE | `src/finagent/agents/wiki_search/` |
| ResearchWorkflow (Human-in-the-Loop) | DONE | `src/finagent/agents/plan_execute/` |

**Implementation Date:** 2025-11-25

---

## Overview

Implementing 3 distinct LangGraph workflows for different user scenarios:

1. **WikiBuilderWorkflow** - Document upload → parse → extract concepts/labels → index
2. **WikiSearchWorkflow** - Enhanced query → plan → multi-tool retrieval → synthesize
3. **ResearchWorkflow** - Query → analyze → confirm with user → plan → execute → final answer

---

## Workflow 1: WikiBuilderWorkflow (NEW)

### Purpose
When user uploads documents, an agent will parse the doc, read context, build vector search, and extract concepts and labels for easy browsing.

### Current State
Components exist but are NOT orchestrated as a LangGraph workflow:
- `DocumentLoader` - loads TXT files
- `ChineseTextChunker` - paragraph-aware chunking
- `EmbeddingGenerator` - OpenAI embeddings
- `DocumentIndexer` - Chroma vector DB
- `MetadataExtractor` - LLM-based extraction
- `CategoryBuilder` - builds hierarchical categories

### Proposed LangGraph Design

```
                              WikiBuilderState
                                    │
                                    ▼
                     ┌──────────────────────────────┐
        START ───►   │         load_document        │
                     │   (DocumentLoader.load_txt)  │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │      extract_metadata        │
                     │  (MetadataExtractor.extract) │
                     │   - title, description       │
                     │   - issuing_authority        │
                     │   - violation_types          │
                     │   - keywords                 │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │      extract_concepts        │
                     │  (ConceptExtractor - NEW)    │
                     │   - entities (banks, orgs)   │
                     │   - topics (AML, fraud)      │
                     │   - regulations mentioned    │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │      chunk_document          │
                     │  (ChineseTextChunker.chunk)  │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │       index_chunks           │
                     │  (DocumentIndexer.index)     │
                     │   - generate embeddings      │
                     │   - store in Chroma          │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │     build_categories         │
                     │  (CategoryBuilder.build)     │
                     │   - authority categories     │
                     │   - institution categories   │
                     │   - violation type categories│
                     └──────────────────────────────┘
                                    │
                                    ▼
                                  END
```

### State Definition

```python
class WikiBuilderState(TypedDict):
    # Input
    file_path: str
    filename: str
    content: str

    # Processing outputs
    document: Optional[Document]
    metadata: Optional[DocumentMetadata]
    concepts: Optional[List[Concept]]
    chunks: Optional[List[TextChunk]]

    # Indexing outputs
    chunk_count: int
    doc_id: str

    # Categories built
    categories_updated: List[str]

    # Progress tracking
    current_stage: str  # loading, extracting, chunking, indexing, categorizing
    progress: int  # 0-100
    error: Optional[str]
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/finagent/agents/wiki_builder/graph.py` | CREATE | LangGraph workflow |
| `src/finagent/agents/wiki_builder/models.py` | CREATE | State definitions |
| `src/finagent/agents/wiki_builder/__init__.py` | CREATE | Module init |
| `src/finagent/document_processing/concept_extractor.py` | MODIFY | Add LangGraph-compatible interface |
| `src/finagent/agents/orchestrator.py` | MODIFY | Add wiki_builder_workflow |
| `src/finagent/api/routes/documents.py` | MODIFY | Integrate WikiBuilderWorkflow |

---

## Workflow 2: WikiSearchWorkflow (ENHANCED)

### Purpose
User sends a query, agent auto-plans and uses multiple retrieval tools to find useful information from wiki knowledge base.

### Current State
Basic 2-node workflow:
```
START → search (semantic only) → synthesize → END
```

### Proposed Enhancement

```
                            WikiSearchState
                                    │
                                    ▼
                     ┌──────────────────────────────┐
        START ───►   │      analyze_query           │
                     │  (QueryAnalyzerAgent)        │
                     │   - query_type               │
                     │   - search_strategy          │
                     │   - key_entities             │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │      plan_retrieval          │
                     │  (PlanRetrieval - NEW)       │
                     │   - select tools             │
                     │   - create search plan       │
                     └──────────────────────────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
          ┌─────────────────────┐   ┌─────────────────────┐
          │   semantic_search   │   │   keyword_search    │
          │  (RetrieverTool)    │   │  (HardSearchTool)   │
          └─────────────────────┘   └─────────────────────┘
                       │                         │
                       └────────────┬────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │      merge_results           │
                     │  (ResultMerger - NEW)        │
                     │   - deduplicate              │
                     │   - rank by relevance        │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │      synthesize              │
                     │  (WikiSynthesizer)           │
                     │   - generate wiki report     │
                     │   - add citations            │
                     └──────────────────────────────┘
                                    │
                                    ▼
                                  END
```

### State Definition

```python
class WikiSearchState(TypedDict):
    # Input
    input: str

    # Analysis outputs
    query_insight: Optional[QueryInsight]
    search_plan: Optional[SearchPlan]

    # Retrieval outputs
    semantic_results: List[Document]
    keyword_results: List[Document]
    merged_results: List[Document]

    # Output
    response: str
    citations: List[Citation]
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/finagent/agents/wiki_search/graph.py` | MODIFY | Add planning + multi-tool |
| `src/finagent/agents/wiki_search/models.py` | CREATE | State definitions |
| `src/finagent/agents/wiki_search/planner.py` | CREATE | Search planning agent |
| `src/finagent/agents/wiki_search/merger.py` | CREATE | Result merging agent |
| `src/finagent/agents/wiki_search/prompts.py` | MODIFY | Add planning prompts |

---

## Workflow 3: ResearchWorkflow (ENHANCED with User Confirmation)

### Purpose
User sends a topic/question, agent analyzes the query, confirms with user, creates a plan with todo tasks, executes wiki search retrievals, and generates a comprehensive research result.

### Current State
Automated Plan-and-Execute workflow without user confirmation:
```
START → QueryAnalyzer → Planner → Executor → Replanner → Reporter → END
```

### Proposed Enhancement: Add Human-in-the-Loop

```
                           PlanExecuteState
                                    │
                                    ▼
                     ┌──────────────────────────────┐
        START ───►   │      query_analyzer          │
                     │  (QueryAnalyzerAgent)        │
                     │   - intent classification    │
                     │   - entity extraction        │
                     │   - complexity assessment    │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │         planner              │
                     │  (PlannerAgent)              │
                     │   - create research plan     │
                     │   - define todo tasks        │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │    plan_confirmation  ◄──────┼─── INTERRUPT
                     │  (Human-in-the-Loop)         │    (WebSocket)
                     │   - show plan to user        │
                     │   - wait for approval        │
                     │   - allow modifications      │
                     └──────────────────────────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                    [approved]            [rejected/modified]
                         │                     │
                         ▼                     ▼
         ┌───────────────────────┐   ┌───────────────────────┐
         │    execute_tasks      │   │    re_planner         │
         │  (ExecutorAgent)      │   │  (back to planner)    │
         │   - parallel exec     │   └───────────────────────┘
         │   - wiki search tools │
         └───────────────────────┘
                         │
                         ▼
                     ┌──────────────────────────────┐
                     │       replanner              │
                     │  (ReplannerAgent)            │
                     │   - check completion         │
                     │   - add tasks if needed      │
                     └──────────────────────────────┘
                         │
                    [has more tasks]───────────┐
                         │                     │
                    [all done]                 ▼
                         │           (back to executor)
                         ▼
                     ┌──────────────────────────────┐
                     │        reporter              │
                     │  (ReporterAgent)             │
                     │   - synthesize results       │
                     │   - format citations         │
                     │   - generate final answer    │
                     └──────────────────────────────┘
                                    │
                                    ▼
                                  END
```

### Human-in-the-Loop Implementation

Use LangGraph's `interrupt` feature:

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

def build_graph():
    workflow = StateGraph(PlanExecuteState)

    # ... add nodes ...

    # Add interrupt before execution
    workflow.add_node("plan_confirmation", plan_confirmation_node)

    # Conditional edge based on user response
    workflow.add_conditional_edges(
        "plan_confirmation",
        route_after_confirmation,
        {
            "approved": "execute_task",
            "rejected": "planner",  # Re-plan
            "modified": "planner",  # Re-plan with modifications
        }
    )

    # Compile with checkpointer for interrupt support
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["plan_confirmation"])
```

### WebSocket Protocol for Confirmation

```typescript
// Frontend sends query
{ "type": "query", "text": "玉山銀行洗錢防制相關案例" }

// Backend sends plan for approval
{
  "type": "plan_confirmation_request",
  "payload": {
    "plan": {
      "tasks": [
        { "id": 1, "description": "搜尋玉山銀行洗錢防制裁罰", "tool": "hybrid_search" },
        { "id": 2, "description": "搜尋相關法規", "tool": "retriever" }
      ]
    },
    "estimated_time": 45,
    "tool_count": 2
  }
}

// User approves
{ "type": "plan_confirmation_response", "approved": true }

// Or user modifies
{
  "type": "plan_confirmation_response",
  "approved": false,
  "modifications": {
    "add_tasks": [{ "description": "也搜尋其他銀行案例" }],
    "remove_tasks": [2]
  }
}
```

### State Extension

```python
class PlanExecuteState(TypedDict):
    # Existing fields...
    input: str
    query_insight: Optional[QueryInsight]
    plan: Annotated[Plan, replace_plan]
    past_steps: Annotated[List[tuple], add]
    response: Optional[str]
    scratchpad: List[Any]

    # NEW: Confirmation tracking
    plan_approved: Optional[bool]
    user_modifications: Optional[dict]
    confirmation_requested_at: Optional[str]
    confirmation_received_at: Optional[str]
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/finagent/agents/plan_execute/graph.py` | MODIFY | Add interrupt + confirmation node |
| `src/finagent/agents/plan_execute/models.py` | MODIFY | Add confirmation fields |
| `src/finagent/agents/plan_execute/confirmation.py` | CREATE | Confirmation handler |
| `src/finagent/api/routes/websocket.py` | MODIFY | Add confirmation protocol |
| `frontend/src/hooks/useResearchWebSocket.ts` | MODIFY | Handle confirmation UI |
| `frontend/src/components/PlanConfirmation.tsx` | CREATE | Confirmation dialog |

---

## Implementation Order

### Phase 1: WikiBuilderWorkflow (Foundation)
1. Create `src/finagent/agents/wiki_builder/` directory
2. Implement state models
3. Create LangGraph workflow
4. Integrate with document upload API
5. Add WebSocket progress streaming

### Phase 2: WikiSearchWorkflow Enhancement
1. Add QueryAnalyzerAgent to wiki search
2. Implement search planning
3. Add multi-tool support (semantic + keyword)
4. Implement result merging
5. Update synthesizer for citations

### Phase 3: ResearchWorkflow User Confirmation
1. Add plan confirmation node
2. Implement LangGraph interrupt
3. Update WebSocket protocol
4. Create frontend confirmation UI
5. Handle plan modifications

---

## Dependencies

### Backend
- langgraph >= 0.2.0 (for interrupt support)
- langchain >= 0.3.0
- pydantic >= 2.0

### Frontend
- React 18+
- WebSocket hooks
- UI components for confirmation dialog

---

## Testing Strategy

### Unit Tests
- Test each agent node independently
- Mock LLM calls for deterministic testing

### Integration Tests
- Test full workflow execution
- Test interrupt/resume for confirmation flow

### E2E Tests
- Test WebSocket communication
- Test UI confirmation flow
- Test parallel tool execution

---

## Success Criteria

1. **WikiBuilderWorkflow** (IMPLEMENTED)
   - [x] Document upload triggers LangGraph workflow
   - [x] Metadata and concepts extracted automatically
   - [x] Categories updated in database
   - [x] Progress streamed via WebSocket

2. **WikiSearchWorkflow** (IMPLEMENTED)
   - [x] Query analyzed before search
   - [x] Multiple tools selected based on query type
   - [x] Results merged and deduplicated
   - [x] Wiki-style report with citations generated

3. **ResearchWorkflow** (IMPLEMENTED)
   - [x] Plan shown to user before execution (enable_confirmation=True)
   - [x] User can approve/reject/modify plan
   - [x] Workflow pauses and resumes correctly
   - [x] Modifications applied to plan

---

## Timeline Estimate

This plan does not include time estimates. Implementation should proceed in the order specified above, with each phase completed before moving to the next.
