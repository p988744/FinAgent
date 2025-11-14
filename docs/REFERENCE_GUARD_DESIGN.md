# Reference Guard and Re-Search Flow Design

**Date:** 2025-11-14
**Purpose:** Add automatic re-search capability when validation fails
**Feature:** Reference guard node with iterative broadening search

---

## Problem Statement

Currently, when validation fails (e.g., missing keywords or entity type mismatch), the system:
1. Flags the issue with a warning
2. Proceeds to generate an answer anyway
3. Does NOT attempt to find better documents

**Example:**
- Query: "金管會對創投公司的裁罰有哪些？"
- Retrieved: Documents about 證券投資信託 (wrong entity type)
- Validation: ⚠️ Entity type mismatch detected
- **Problem**: System doesn't try searching for actual 創投 documents

---

## Solution: Reference Guard + Re-Search Flow

### Architecture

```
START → Planning → Action → Validation → Reference Guard → [Decision] → Answer → END
                                ↑                             ↓
                                └─────── Re-Search ←──────────┘
                                         (max 2 iterations)
```

### Workflow Logic

1. **First Search** (Action Agent)
   - Normal retrieval with current criteria
   - Threshold: 0.8

2. **Validation** (Validation Agent)
   - Check keywords, entity types, citations
   - Generate validation issues

3. **Reference Guard** (NEW)
   - Evaluate validation severity
   - Decide: Continue to Answer OR Re-search

4. **Re-Search** (NEW - Modified Action Agent)
   - **Iteration 1**: Relax threshold to 0.9, increase results to 10
   - **Iteration 2**: Relax threshold to 1.0, increase results to 15, drop entity type requirement
   - **Iteration 3**: Give up, proceed to answer with best available

5. **Answer** (Answer Agent)
   - Synthesize answer
   - Include validation warnings if present

---

## Implementation Details

### 1. Update AgentState

Add re-search tracking fields:

```python
class AgentState(TypedDict):
    # ... existing fields ...

    # Re-search tracking (NEW)
    search_iteration: int  # Current iteration (0 = first search, 1-2 = re-search)
    max_search_iterations: int  # Maximum iterations allowed (default: 2)
    search_strategy: str  # Current search strategy: "strict", "relaxed", "broad"
```

### 2. Reference Guard Node

**Responsibilities:**
- Evaluate validation results
- Determine if re-search is needed
- Decide on re-search strategy

**Decision Logic:**

```python
def should_research(state: AgentState) -> bool:
    """Decide if re-search is needed."""

    # Don't re-search if already at max iterations
    if state["search_iteration"] >= state["max_search_iterations"]:
        return False

    # Don't re-search if no validation issues
    if state["validation_passed"]:
        return False

    # Check issue severity
    issues = state["validation_issues"]

    # Re-search for CRITICAL issues only
    critical_keywords = ["關鍵字檢查失敗", "實體類型不符"]
    has_critical_issue = any(
        any(keyword in issue for keyword in critical_keywords)
        for issue in issues
    )

    # Re-search if:
    # 1. Has critical validation issues
    # 2. Found some documents (if found 0, re-search won't help)
    # 3. Haven't reached max iterations

    has_documents = len(state.get("retrieved_chunks", [])) > 0

    return has_critical_issue and has_documents
```

### 3. Re-Search Strategies

**Strategy Progression:**

| Iteration | Strategy | Threshold | Max Results | Entity Check | Keyword Check |
|-----------|----------|-----------|-------------|--------------|---------------|
| 0 (First) | `strict` | 0.8 | 5 | Required | Required |
| 1 | `relaxed` | 0.9 | 10 | Preferred | Preferred |
| 2 | `broad` | 1.0 | 15 | Optional | Optional |

**Implementation:**

```python
def get_search_params(iteration: int) -> dict:
    """Get search parameters based on iteration."""

    strategies = {
        0: {  # First search - strict
            "strategy": "strict",
            "threshold": 0.8,
            "max_results": 5,
            "require_keywords": True,
            "require_entity_match": True,
        },
        1: {  # First re-search - relaxed
            "strategy": "relaxed",
            "threshold": 0.9,
            "max_results": 10,
            "require_keywords": False,  # Prefer but don't require
            "require_entity_match": False,
        },
        2: {  # Second re-search - broad
            "strategy": "broad",
            "threshold": 1.0,
            "max_results": 15,
            "require_keywords": False,
            "require_entity_match": False,
        },
    }

    return strategies.get(iteration, strategies[2])
```

### 4. Conditional Edge Function

```python
def decide_next_step(state: AgentState) -> str:
    """Decide next node after reference guard."""

    reference_guard = ReferenceGuard()

    if reference_guard.should_research(state):
        return "research"  # Go back to action agent
    else:
        return "answer"  # Proceed to answer
```

### 5. Modified Action Agent

Add support for re-search with different strategies:

```python
class ActionAgent:
    def __init__(self, retriever: DocumentRetriever):
        self.retriever = retriever

    def execute(self, state: AgentState) -> AgentState:
        """Execute search with current iteration strategy."""

        # Get search parameters based on iteration
        iteration = state.get("search_iteration", 0)
        params = get_search_params(iteration)

        logger.info(f"Search iteration {iteration} using strategy: {params['strategy']}")

        # Execute retrieval with iteration-specific params
        all_chunks = self.retriever.retrieve(
            query=state["query"].text,
            n_results=params["max_results"]
        )

        # Filter by threshold
        retrieved_chunks = [
            chunk for chunk in all_chunks
            if chunk.score <= params["threshold"]
        ]

        # ... rest of processing ...

        return state
```

### 6. Workflow Graph Update

```python
def _build_graph(self) -> StateGraph:
    """Build LangGraph workflow with re-search capability."""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("planning", self._planning_node)
    workflow.add_node("action", self._action_node)
    workflow.add_node("validation", self._validation_node)
    workflow.add_node("reference_guard", self._reference_guard_node)  # NEW
    workflow.add_node("answer", self._answer_node)

    # Define edges
    workflow.add_edge(START, "planning")
    workflow.add_edge("planning", "action")
    workflow.add_edge("action", "validation")
    workflow.add_edge("validation", "reference_guard")  # NEW

    # Conditional edge from reference guard
    workflow.add_conditional_edges(
        "reference_guard",
        self._decide_next_step,
        {
            "research": "action",  # Loop back to action for re-search
            "answer": "answer",    # Proceed to answer
        }
    )  # NEW

    workflow.add_edge("answer", END)

    return workflow.compile()
```

---

## Expected Behavior

### Example: Query 4 (創投公司)

**First Search (Iteration 0):**
- Strategy: `strict`
- Retrieved: 3 documents about 證券投資信託
- Validation: ❌ Entity type mismatch + missing keywords
- Reference Guard: ⚠️ Critical issues detected → Re-search

**Second Search (Iteration 1):**
- Strategy: `relaxed`
- Threshold: 0.8 → 0.9
- Max results: 5 → 10
- Retrieved: Hopefully finds actual 創投 documents
- Validation: Check again
- Reference Guard: If still failing → Re-search again

**Third Search (Iteration 2):**
- Strategy: `broad`
- Threshold: 0.9 → 1.0
- Max results: 10 → 15
- Retrieved: Cast wider net
- Validation: Check again
- Reference Guard: Max iterations reached → Proceed to answer

**Answer:**
- Synthesize based on best available documents
- Include validation warnings if issues persist

---

## Configuration

### Environment Variables

```bash
# Max re-search iterations (default: 2)
MAX_SEARCH_ITERATIONS=2

# Enable/disable re-search feature
ENABLE_RESEARCH=true

# Re-search thresholds
RESEARCH_THRESHOLD_ITERATION_1=0.9
RESEARCH_THRESHOLD_ITERATION_2=1.0
```

### Code Constants

```python
# In workflow.py or config
DEFAULT_MAX_SEARCH_ITERATIONS = 2
ENABLE_RESEARCH = True  # Feature flag

# Search strategy thresholds
STRICT_THRESHOLD = 0.8
RELAXED_THRESHOLD = 0.9
BROAD_THRESHOLD = 1.0
```

---

## Metrics and Logging

### Track Re-Search Performance

```python
# In processing_steps
state["processing_steps"].append(
    f"參考守衛：檢測到關鍵問題，啟動第 {iteration + 1} 次搜索（策略：{strategy}）"
)

# After each iteration
logger.info(
    f"Re-search iteration {iteration}: "
    f"Retrieved {len(chunks)} chunks with threshold {threshold}"
)

# Final stats
logger.info(
    f"Search completed after {final_iteration + 1} iterations. "
    f"Final validation: {'PASSED' if passed else 'FAILED'}"
)
```

### Add to LegalAnswer

```python
class LegalAnswer(BaseModel):
    # ... existing fields ...

    # Re-search metadata (optional)
    search_iterations_used: int | None = Field(
        None,
        description="Number of search iterations performed (0 = first search only)"
    )
    final_search_strategy: str | None = Field(
        None,
        description="Final search strategy used: strict/relaxed/broad"
    )
```

---

## Testing Plan

### Test Cases

1. **Test: No Re-Search Needed** (Query 1, 3, 5, 6)
   - Validation passes on first try
   - Reference guard: No re-search needed
   - Expected iterations: 0

2. **Test: Re-Search Finds Better Results** (Query 2, 4)
   - First search: Entity mismatch
   - Re-search 1: Broader search finds correct documents
   - Expected iterations: 1

3. **Test: Max Iterations Reached**
   - First search: No good matches
   - Re-search 1: Still no good matches
   - Re-search 2: Still no good matches
   - Expected: Proceed to answer with best available
   - Expected iterations: 2

4. **Test: Zero Results on First Search**
   - First search: 0 documents
   - Reference guard: Don't re-search (won't help)
   - Expected iterations: 0

### Success Criteria

- ✅ Re-search improves citation quality for Queries 2 & 4
- ✅ No re-search for queries that pass validation
- ✅ Max iterations respected (no infinite loops)
- ✅ Processing time acceptable (< 2 minutes for 2 iterations)
- ✅ Logging clearly shows re-search decisions

---

## Implementation Checklist

- [ ] Update `AgentState` with re-search fields
- [ ] Create `ReferenceGuard` class
- [ ] Update `ActionAgent` to support search strategies
- [ ] Add `_reference_guard_node` to workflow
- [ ] Add `_decide_next_step` conditional edge function
- [ ] Update `_build_graph` with conditional edges
- [ ] Add re-search logging and metrics
- [ ] Update `LegalAnswer` model (optional)
- [ ] Write unit tests for `ReferenceGuard`
- [ ] Write integration tests for re-search flow
- [ ] Test with all 6 queries
- [ ] Document configuration options

---

## Future Enhancements

### Phase 2: Intelligent Query Reformulation

Instead of just relaxing thresholds, reformulate the query:

```python
# Example for Query 4
Original: "金管會對創投公司的裁罰有哪些？"
Iteration 1: "創業投資 裁罰"  # Drop 金管會, use synonym
Iteration 2: "創投 OR 創業投資 OR 德信創投"  # Add specific names
```

### Phase 3: Multi-Strategy Re-Search

Try different strategies in parallel:
- Strategy A: Relax threshold
- Strategy B: Reformulate query
- Strategy C: Search different time period
- Pick best results from all strategies

### Phase 4: User Feedback Integration

```python
# Allow users to trigger re-search manually
if user_feedback == "找不到相關結果":
    trigger_research(broader_search=True)
```

---

## Summary

This design adds a **Reference Guard node** that:
1. Evaluates validation results after each search
2. Decides if re-search is needed based on issue severity
3. Progressively relaxes search criteria over 2 iterations max
4. Prevents infinite loops with max iteration limit
5. Logs all decisions for transparency

**Expected Impact:**
- Reduce false negatives from overly strict search
- Automatically recover from initial search failures
- Maintain system reliability (max 2 re-searches)
- Improve user experience (fewer "no results" responses)
