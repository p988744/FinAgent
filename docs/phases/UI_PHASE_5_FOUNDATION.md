# Phase 5: Todo State Synchronization - Foundation

**Status:** Foundation Implemented
**Date:** 2025-01-14
**Objective:** Enable real-time todo status tracking across LangGraph workflow agents

## Overview

Phase 5 establishes the foundation for todo state synchronization, allowing agents in the LangGraph workflow to update todo item status in real-time as tasks are executed. This provides users with live progress updates during query processing.

## Architecture Design

### Todo Lifecycle Flow

```
Planning Agent (Creates todos)
    ↓
AgentState (Stores todos)
    ↓
Action/Validation/Answer Agents (Update status)
    ↓
UI Callbacks (Display updates)
    ↓
CLI Progress Display (Live rendering)
```

### State-Based Approach

**Key Decision:** Store todos in `AgentState` for cross-agent access.

**Rationale:**
- LangGraph passes `AgentState` to all workflow nodes
- Agents can read, modify, and emit callbacks for todo updates
- No need for separate todo storage or complex synchronization
- Enables sequential and parallel todo execution tracking

### Category-Based Task Mapping

Todos are categorized based on task content for better UI organization:

- **retrieval** - RAG search tasks (向量搜索, 深度搜索)
- **validation** - Citation and integrity checks (驗證引用)
- **synthesis** - Answer generation (生成答案)
- **analysis** - Other analysis tasks

## Implemented Foundation

### 1. AgentState Extension

**File:** [src/finagent/agents/state.py](../../src/finagent/agents/state.py)

**Changes:**
```python
from finagent.models.todo_item import TodoItem

class AgentState(TypedDict):
    # ... existing fields ...

    # Todo tracking (Phase 5)
    todos: list[TodoItem] | None  # Task tracking with real-time status updates
```

**Purpose:** Enable all agents to access and update the shared todo list.

### 2. PlanningAgent Todo Creation

**File:** [src/finagent/agents/planning_agent.py](../../src/finagent/agents/planning_agent.py:166-199)

**Implementation:**
```python
# Convert tasks to todo items and store in state (Phase 5)
from finagent.models.todo_item import TodoItem
todos = []
for t in tasks:
    # Determine category based on task content
    if "搜" in t.task or "檢索" in t.task or "深度搜索" in t.task:
        category = "retrieval"
    elif "驗證" in t.task:
        category = "validation"
    elif "生成" in t.task or "答案" in t.task:
        category = "synthesis"
    else:
        category = "analysis"

    todo = TodoItem(
        id=f"task_{t.id}",
        content=t.task,
        active_form=f"正在執行 {t.task}",
        status="pending",
        category=category,
    )
    todos.append(todo)

# Store todos in state for cross-agent access
state["todos"] = todos

# Emit todo list created callback
if self.ui_callback:
    try:
        asyncio.create_task(self.ui_callback.on_todo_list_created(todos))
    except RuntimeError:
        pass
```

**Features:**
- Automatic category detection from task content (Traditional Chinese)
- Proper active form for progress display (正在執行...)
- State storage for cross-agent access
- UI callback emission for initial display

## Remaining Implementation

### 1. ActionAgent Todo Updates

**File:** [src/finagent/agents/action_agent.py](../../src/finagent/agents/action_agent.py)

**Needed Changes:**
```python
def execute(self, state: AgentState) -> AgentState:
    # Find retrieval todo
    todos = state.get("todos", [])
    retrieval_todo = next((t for t in todos if t.category == "retrieval"), None)

    if retrieval_todo:
        # Mark as in_progress
        retrieval_todo.mark_started()
        if self.ui_callback:
            asyncio.create_task(self.ui_callback.on_todo_started(retrieval_todo))

    # Execute RAG retrieval
    all_chunks = self.retriever.retrieve(...)

    if retrieval_todo:
        # Mark as completed
        retrieval_todo.mark_completed(result={"count": len(all_chunks)})
        if self.ui_callback:
            asyncio.create_task(self.ui_callback.on_todo_completed(retrieval_todo))

    # Update state
    state["todos"] = todos
    return state
```

**Todo Items to Track:**
- Vector search task (向量搜索)
- Hard search task (深度搜索) if enabled

### 2. ValidationAgent Todo Updates

**File:** [src/finagent/agents/validation_agent.py](../../src/finagent/agents/validation_agent.py)

**Needed Changes:**
```python
def validate(self, state: AgentState) -> AgentState:
    # Find validation todo
    todos = state.get("todos", [])
    validation_todo = next((t for t in todos if t.category == "validation"), None)

    if validation_todo:
        validation_todo.mark_started()
        if self.ui_callback:
            asyncio.create_task(self.ui_callback.on_todo_started(validation_todo))

    # Run validation checks
    validation_result = self._run_validation(...)

    if validation_todo:
        if validation_result.passed:
            validation_todo.mark_completed()
        else:
            validation_todo.mark_failed(error=f"{len(validation_result.issues)} issues")

        if self.ui_callback:
            callback = (self.ui_callback.on_todo_completed if validation_result.passed
                       else self.ui_callback.on_todo_failed)
            asyncio.create_task(callback(validation_todo))

    state["todos"] = todos
    return state
```

**Todo Items to Track:**
- Citation validation task (驗證引用完整性)

### 3. AnswerAgent Todo Updates

**File:** [src/finagent/agents/answer_agent.py](../../src/finagent/agents/answer_agent.py)

**Needed Changes:**
```python
def synthesize(self, state: AgentState) -> AgentState:
    # Find synthesis todo
    todos = state.get("todos", [])
    synthesis_todo = next((t for t in todos if t.category == "synthesis"), None)

    if synthesis_todo:
        synthesis_todo.mark_started()
        if self.ui_callback:
            asyncio.create_task(self.ui_callback.on_todo_started(synthesis_todo))

    # Generate answer via LLM
    response = self.chain.invoke(...)
    answer = self._parse_response(...)

    if synthesis_todo:
        synthesis_todo.mark_completed(result={"citations": len(answer.citations)})
        if self.ui_callback:
            asyncio.create_task(self.ui_callback.on_todo_completed(synthesis_todo))

    state["todos"] = todos
    return state
```

**Todo Items to Track:**
- Answer synthesis task (生成答案並格式化引用)

### 4. CLI Progress Display Enhancement

**File:** [src/finagent/cli/callbacks/progress_callback.py](../../src/finagent/cli/callbacks/progress_callback.py)

**Current Implementation:**
- `on_todo_list_created()` - Initial display (lines 93-101)
- `on_todo_started()` - Show when task starts (lines 103-106)
- `on_todo_completed()` - Show completion with duration (lines 113-133)
- `on_todo_failed()` - Show failure (lines 135-140)

**Enhancement Needed:**
- **Live table updates**: Use Rich's `Live` display to update todo table in real-time
- **Progress bars**: Show progress percentage for long-running tasks
- **Color coding**: Green for completed, yellow for in_progress, red for failed
- **Timing display**: Show duration for each task

**Example Enhanced Display:**
```
📝 任務清單：
┏━━━━━━┳━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ 狀態 ┃ # ┃ 任務                    ┃ 進度      ┃
┡━━━━━━╇━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ ✓    │ 1 │ 向量搜索：玉山銀行      │ 完成 10.2s│
│ ⏳   │ 2 │ 深度搜索：洗錢防制      │ 75%       │
│ [ ]  │ 3 │ 驗證引用完整性          │ 待執行    │
│ [ ]  │ 4 │ 生成答案並格式化引用    │ 待執行    │
└──────┴───┴─────────────────────────┴───────────┘
```

## Testing Plan

### Unit Tests

**Test File:** `tests/test_todo_state_sync.py`

**Test Cases:**
1. `test_planning_agent_creates_todos_in_state()` - Verify PlanningAgent stores todos
2. `test_action_agent_updates_retrieval_todo()` - Verify ActionAgent updates status
3. `test_validation_agent_updates_validation_todo()` - Verify ValidationAgent updates
4. `test_answer_agent_updates_synthesis_todo()` - Verify AnswerAgent updates
5. `test_todo_state_persistence_across_agents()` - Verify state updates propagate

### Integration Tests

**Test File:** `tests/integration/test_full_workflow_todos.py`

**Test Cases:**
1. `test_full_query_workflow_with_todos()` - Execute complete query with todo tracking
2. `test_ui_callbacks_emitted_for_all_todos()` - Verify all callbacks fire correctly
3. `test_todo_timing_accuracy()` - Verify duration calculations
4. `test_parallel_todo_execution()` - Test parallel task tracking (if implemented)

### Manual Testing

**Test Query:** "玉山銀行洗錢防制裁罰"

**Expected Todo Flow:**
```
1. [ ] 向量搜索：玉山銀行, 洗錢防制
   → ⏳ 正在執行向量搜索...
   → ✓ 完成 (找到 7 個區塊) 9.8s

2. [ ] 深度搜索：grep 關鍵字「玉山銀行、洗錢防制」
   → ⏳ 正在執行深度搜索...
   → ✓ 完成 (找到 3 個區塊) 28.3s

3. [ ] 驗證引用完整性和關鍵字匹配
   → ⏳ 正在驗證引用...
   → ✓ 完成 4.2s

4. [ ] 生成答案並格式化引用
   → ⏳ 正在生成答案...
   → ✓ 完成 (提取 5 個引用) 14.7s
```

## Benefits

### For Users
- **Real-time visibility** into query processing steps
- **Progress indicators** showing current task and completion percentage
- **Timing information** for performance awareness
- **Error transparency** if tasks fail

### For Developers
- **Debugging clarity** - see which agent is stuck or failing
- **Performance profiling** - identify slow tasks
- **State inspection** - verify todo updates propagate correctly
- **UI testing** - validate callback emissions

## Integration with Existing Phases

### Phase 1: Config-Driven Agent Init ✅
- Agents initialized with `ui_callback` parameter
- Todo updates use existing callback infrastructure

### Phase 2: Callback Interface ✅
- Todo callbacks defined in `UICallback` base class
- `on_todo_started/completed/failed` methods implemented

### Phase 3: Agent Callback Wiring ✅
- All agents have `self.ui_callback` reference
- Callback emission pattern established

### Phase 4: Callback Emissions ✅
- `on_todo_list_created` already emitted from PlanningAgent
- `on_todo_started/completed` ready for use in other agents

### Phase 5: Todo State Sync (This Phase) 🔄
- Foundation complete
- Full implementation pending

## Future Enhancements

### Parallel Todo Execution
- Track multiple todos executing simultaneously
- Display concurrent progress in UI
- Example: Vector search + hard search running in parallel

### Todo Dependencies
- Implement `depends_on` field in TodoItem
- Block todos until dependencies complete
- Show dependency graph in UI

### Todo Cancellation
- Add cancel capability to TodoManager
- Allow user to interrupt long-running tasks
- Update UI with cancelled status

### Todo Persistence
- Save todo execution history to database
- Analyze task duration trends
- Optimize task ordering based on historical data

## Next Steps

1. **Implement ActionAgent todo updates** (priority: high)
2. **Implement ValidationAgent todo updates** (priority: high)
3. **Implement AnswerAgent todo updates** (priority: high)
4. **Enhance CLI progress display with live updates** (priority: medium)
5. **Add unit tests for todo state synchronization** (priority: medium)
6. **Add integration tests for full workflow** (priority: low)
7. **Document Phase 5 completion** (priority: low)

## Technical Notes

### Async Callback Pattern in Sync Nodes

LangGraph nodes are synchronous, but UI callbacks are async. Use this pattern:

```python
if self.ui_callback:
    import asyncio
    try:
        asyncio.create_task(self.ui_callback.on_todo_started(todo))
    except RuntimeError:
        # No event loop available (testing or non-async context)
        pass
```

### State Mutation Safety

LangGraph passes state by reference. Ensure todos are properly updated:

```python
# Get todos from state
todos = state.get("todos", [])

# Find and update todo
for todo in todos:
    if todo.category == "retrieval":
        todo.mark_started()

# Store updated todos back in state
state["todos"] = todos
```

### TodoItem Methods

Use these methods for status updates:

- `mark_started()` - Sets status to "in_progress", records start time
- `mark_completed(result=None)` - Sets status to "completed", records end time
- `mark_failed(error="")` - Sets status to "failed", stores error message
- `update_progress(percentage, substep="")` - Updates progress during execution

## Conclusion

Phase 5 foundation provides the infrastructure for real-time todo state tracking across the LangGraph workflow. The core state management is in place, with todos created by PlanningAgent and stored in AgentState for cross-agent access.

Full implementation requires adding todo status updates to ActionAgent, ValidationAgent, and AnswerAgent, along with enhanced CLI display using Rich's Live updates. This will complete the UI-driven query flow, giving users complete visibility into the legal research process.

**Status:** Foundation complete, full implementation pending.
