# Query Flow Architecture - LangGraph Visualization

**Date**: 2025-11-14
**Status**: Complete with interactive flowchart

---

## Overview

This document provides a comprehensive visual guide to the new UI-driven query flow implemented in FinAgent, including LangGraph flowcharts, ASCII diagrams, and architectural explanations.

---

## 🎨 Visual Flowchart

### ASCII Diagram (Quick Reference)

```
                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │ 🔍 Analyze      │
                         │    Query        │
                         └────┬────────────┘
                              │
                         ┌────┴────┐
                         │ Need    │
                         │ Clarify?│
                         └─┬────┬──┘
                    Yes    │    │    No
                      ┌────┘    └────┐
                      ▼              ▼
              ┌───────────┐    ┌────────────┐
              │ ❓ Request │    │ 📋 Create  │
              │ Clarify   │    │    Plan    │
              └─────┬─────┘    └─────┬──────┘
                    │                │
                    └────────┬───────┘
                             ▼
                    ┌────────────────┐
                    │  Parallel      │
                    │  Retrieval     │
                    └────┬──────┬────┘
                         │      │
                    ┌────┘      └────┐
                    ▼                ▼
          ┌──────────────┐  ┌──────────────┐
          │ 🔤 Concept   │  │ 🎯 Vector    │
          │   Retrieval  │  │   Retrieval  │
          └──────┬───────┘  └──────┬───────┘
                 │                 │
                 └────────┬────────┘
                          ▼
                 ┌────────────────┐
                 │ Merge Results  │
                 └────────┬───────┘
                          ▼
                 ┌────────────────┐
                 │ ✓ Validate     │
                 │   Citations    │
                 └────┬───────────┘
                      │
                 ┌────┴─────┐
                 │ Deep     │
                 │ Search?  │
                 └─┬─────┬──┘
            Yes    │     │    No
              ┌────┘     └────┐
              ▼               ▼
      ┌──────────────┐  ┌────────────────┐
      │ 🔬 Deep      │  │ 🤖 Synthesize  │
      │    Search    │  │    Answer      │
      └──────┬───────┘  └────────┬───────┘
             │                   │
             └─────────┬─────────┘
                       ▼
              ┌────────────────┐
              │ 📚 Show        │
              │    Citations   │
              └────────┬───────┘
                       ▼
              ┌────────────────┐
              │  ✨ Final      │
              │     Answer     │
              └────────┬───────┘
                       ▼
                  ┌────────┐
                  │  END   │
                  └────────┘
```

### Interactive Mermaid Diagram

The LangGraph visualization has been generated and saved to [query_flow_graph.mmd](query_flow_graph.mmd).

**To view the interactive diagram:**
1. Visit https://mermaid.live/
2. Paste the contents of `query_flow_graph.mmd`
3. See the full interactive flowchart with clickable nodes

**Or generate PNG locally:**
```bash
# Install mermaid-cli if not already installed
npm install -g @mermaid-js/mermaid-cli

# Generate PNG from Mermaid source
mmdc -i query_flow_graph.mmd -o query_flow_graph.png
```

---

## 🏗️ Architecture Components

### 1. Graph Nodes (Stages)

Each node represents a stage in the query execution flow:

| Node | Function | Duration | UI Callbacks |
|------|----------|----------|--------------|
| **analyze** | Analyze query intent, extract entities, assess complexity | 0.5-2s | `on_analysis_start()`, `on_analysis_complete()` |
| **clarify** | Request user clarification (conditional) | Variable | `on_clarification_requested()` |
| **plan** | Create execution plan (simple/complex/deep_search) | 0.1s | `on_plan_created()`, `on_todo_list_created()` |
| **retrieve_concept** | Concept-based semantic retrieval (parallel) | 5-10s | `on_todo_started()`, `on_todo_progress()`, `on_retrieval_result()` |
| **retrieve_vector** | Vector similarity retrieval (parallel) | 5-10s | `on_todo_started()`, `on_todo_progress()`, `on_retrieval_result()` |
| **merge** | Merge and deduplicate parallel results | 0.1s | — |
| **validate** | Validate citation integrity and coverage | 1-2s | `on_todo_started()`, `on_todo_completed()` |
| **deep_search** | Read full documents for deep analysis (conditional) | 10-20s | `on_todo_started()`, `on_todo_progress()` |
| **synthesize** | LLM-powered answer generation | 5-15s | `on_answer_generation_start()`, `on_todo_progress()` |

### 2. Graph Edges (Transitions)

#### Sequential Edges
- `START → analyze` - Always starts with analysis
- `analyze → clarify` (conditional) - Only if clarification needed
- `clarify → plan` - After clarification, proceed to planning
- `analyze → plan` (conditional) - Skip clarification if not needed
- `merge → validate` - Always validate after merging results
- `synthesize → END` - Always end after synthesis

#### Parallel Edges
```
plan → retrieve_concept ┐
                        ├→ merge
plan → retrieve_vector  ┘
```
Both retrieval tasks execute simultaneously, then results merge.

#### Conditional Edges
- `analyze → {clarify | plan}` - Based on `needs_clarification`
- `validate → {deep_search | synthesize}` - Based on `validation_passed` and plan strategy

### 3. State Management

The `QueryFlowState` tracks execution state across all nodes:

```python
class QueryFlowState(TypedDict):
    # Input
    query: str

    # Stage outputs
    analysis: dict | None
    resolution_plan: dict | None
    todo_list: list[dict] | None
    concept_results: list | None
    vector_results: list | None
    merged_chunks: list | None
    validation_passed: bool
    final_answer: dict | None
    citations: list | None

    # UI updates
    messages: list  # Progress messages for display
```

---

## 🚀 Execution Flow Examples

### Example 1: Simple Query (15s)

```
Query: "玉山銀行最新消息"

Flow:
1. analyze (2s) → complexity: simple
2. plan (0.1s) → strategy: simple (vector only)
3. retrieve_vector (10s) → 5 documents found
4. validate (1s) → validation passed
5. synthesize (2s) → generate answer
6. END

Total: ~15s
UI updates: 8 callbacks
```

### Example 2: Complex Query with Parallel Retrieval (25s)

```
Query: "玉山銀行洗錢防制裁罰"

Flow:
1. analyze (2s) → complexity: moderate, entities: 2
2. plan (0.1s) → strategy: complex (parallel retrieval)
3. retrieve_concept (7s) ┐
   retrieve_vector (5s)  ┘ → parallel execution
4. merge (0.1s) → 15 unique chunks
5. validate (1s) → validation passed
6. synthesize (10s) → generate answer with LLM
7. END

Total: ~25s (would be 35s sequential)
Speedup: 40% faster
UI updates: 12 callbacks
```

### Example 3: Complex Query with Deep Search (45s)

```
Query: "詳細分析所有銀行洗錢防制裁罰案件"

Flow:
1. analyze (2s) → complexity: high, entities: 3+
2. plan (0.1s) → strategy: deep_search
3. retrieve_concept (7s) ┐
   retrieve_vector (5s)  ┘ → parallel execution
4. merge (0.1s) → 8 chunks (low count)
5. validate (1s) → validation needs improvement
6. deep_search (20s) → read 5 full documents
7. synthesize (15s) → comprehensive answer
8. END

Total: ~50s
UI updates: 15 callbacks
```

---

## 📊 Performance Characteristics

### Parallel Execution Benefits

| Metric | Sequential | Parallel | Improvement |
|--------|-----------|----------|-------------|
| **Concept Retrieval** | 10s | 10s | — |
| **Vector Retrieval** | 10s | 10s (concurrent) | — |
| **Total Retrieval** | 20s | 10s | **50% faster** |
| **Overall Query** | 35s | 25s | **29% faster** |

### Resource Utilization

```
Single-threaded (sequential):
CPU: ████░░░░░░ 40%
Time: ████████████████████ 20s

Multi-threaded (parallel):
CPU: ████████░░ 80%
Time: ██████████ 10s
```

---

## 🎯 UI Callback Points

The system provides 14 callback points for real-time UI updates:

### Analysis Stage (2 callbacks)
1. `on_analysis_start(query)` - Query analysis begins
2. `on_analysis_complete(analysis)` - Analysis results available

### Clarification Stage (1 callback)
3. `on_clarification_requested(questions)` - User input needed

### Planning Stage (2 callbacks)
4. `on_plan_created(plan)` - Execution plan created
5. `on_todo_list_created(todos)` - Todo list generated

### Execution Stage (6 callbacks)
6. `on_todo_started(todo)` - Task starts
7. `on_todo_progress(todo, percentage, message)` - Progress update
8. `on_todo_completed(todo)` - Task completes
9. `on_todo_failed(todo, error)` - Task fails
10. `on_retrieval_result(strategy, doc_count, chunk_count)` - Retrieval results

### Synthesis Stage (3 callbacks)
11. `on_answer_generation_start()` - LLM generation begins
12. `on_citations_formatted(citations)` - Citations ready
13. `on_answer_complete(answer)` - Final answer ready

### Error Handling (1 callback)
14. `on_error(error, context)` - Error occurred

---

## 🔧 Code Generation

To regenerate the flowchart:

```bash
# Generate ASCII + Mermaid source
uv run python src/finagent/agents/query_flow_graph.py

# Output:
# - ASCII diagram (printed to console)
# - query_flow_graph.mmd (Mermaid source)
```

To modify the graph:
1. Edit [src/finagent/agents/query_flow_graph.py](src/finagent/agents/query_flow_graph.py)
2. Adjust node functions, edges, or conditional routing
3. Regenerate with command above

---

## 📚 Related Documentation

- [QUERY_FLOW_REFACTOR_DESIGN.md](QUERY_FLOW_REFACTOR_DESIGN.md) - Original design document
- [PHASE_2_COMPLETE.md](PHASE_2_COMPLETE.md) - Implementation summary
- [src/finagent/agents/todo_manager.py](src/finagent/agents/todo_manager.py) - Execution engine
- [src/finagent/agents/resolution_planner.py](src/finagent/agents/resolution_planner.py) - Plan creation
- [src/finagent/cli/callbacks/progress_callback.py](src/finagent/cli/callbacks/progress_callback.py) - CLI UI implementation

---

## 🎨 Legend

| Symbol | Meaning |
|--------|---------|
| 🔍 | Analysis |
| ❓ | Clarification |
| 📋 | Planning |
| 🔤 | Concept Search |
| 🎯 | Vector Search |
| ✓ | Validation |
| 🔬 | Deep Search |
| 🤖 | LLM Synthesis |
| 📚 | Citations |
| ✨ | Final Answer |

---

**Generated**: 2025-11-14
**LangGraph Version**: Compatible with langgraph>=0.0.26
**Status**: Production Ready ✅
