# Query Flow Refactor - Implementation Status

**Date**: 2025-11-14
**Goal**: Implement UI-driven query flow with progressive updates

---

## ✅ Completed (Phase 1 - Core Infrastructure)

### 1. Design Document
- ✅ Created [QUERY_FLOW_REFACTOR_DESIGN.md](QUERY_FLOW_REFACTOR_DESIGN.md)
- Comprehensive 11-stage flow design
- UI callback architecture
- Parallel execution strategy
- Todo-based task tracking

### 2. Data Models Created

**[src/finagent/models/todo_item.py](src/finagent/models/todo_item.py)** (115 lines)
- `TodoItem` model with full lifecycle management
- Status tracking: pending → in_progress → completed/failed
- Progress percentage (0-100%)
- Dependency management
- Parallel execution support
- Methods: `mark_started()`, `update_progress()`, `mark_completed()`, `mark_failed()`
- Helper: `is_ready_to_execute()`, `duration_seconds`

**[src/finagent/models/resolution_plan.py](src/finagent/models/resolution_plan.py)** (155 lines)
- `ResolutionPlan` model for execution strategy
- Three plan types: simple, complex, deep_search
- Tool and agent selection
- Parallel execution capability
- Deep search decision logic
- Factory methods: `create_simple_plan()`, `create_complex_plan()`, `create_deep_search_plan()`
- Human-readable description with Chinese translations

### 3. UI Callback System

**[src/finagent/agents/ui_callback.py](src/finagent/agents/ui_callback.py)** (255 lines)
- `UICallback` abstract base class with 14 callback methods
- `NoOpCallback` for testing
- `LoggingCallback` for debugging with emojis
- Comprehensive progress tracking:
  - Query analysis lifecycle
  - Clarification requests
  - Plan creation
  - Todo list tracking
  - Retrieval progress
  - Answer generation
  - Citations formatting
  - Error handling

---

## 🚧 In Progress (Phase 2)

### Next Immediate Tasks

1. **TodoManager Implementation**
   - Create `src/finagent/agents/todo_manager.py`
   - Implement `execute_todos()` with parallel execution
   - Handle dependencies between tasks
   - Update UI callbacks during execution

2. **ResolutionPlanner Implementation**
   - Create `src/finagent/agents/resolution_planner.py`
   - Implement `create_resolution_plan()` with LLM decision
   - Map query complexity → plan strategy
   - Generate todo list from plan

3. **CLI UI Callback**
   - Create `src/finagent/cli/callbacks/progress_callback.py`
   - Rich terminal UI with progress bars
   - Live todo list display
   - Color-coded status indicators

4. **Parallel Retrieval**
   - Refactor `ActionAgent` for parallel concept + vector search
   - Merge and deduplicate results
   - Track retrieval metrics per strategy

---

## 📋 Remaining Work

### Phase 3: Integration (2-3 hours)

**Files to Create:**
```
src/finagent/agents/
├── todo_manager.py           # ⏳ In progress
├── resolution_planner.py     # ⏳ Pending
└── parallel_executor.py      # ⏳ Pending

src/finagent/cli/callbacks/
└── progress_callback.py      # ⏳ Pending

src/finagent/cli/formatters/
└── todo_display.py           # ⏳ Pending
```

**Files to Modify:**
```
src/finagent/agents/
├── orchestrator.py           # Add new flow method
└── action_agent.py           # Support parallel retrieval

src/finagent/cli/commands/
└── query.py                  # Use new UI callback
```

### Phase 4: Deep Search (Optional, 1 hour)
- Implement full document reading logic
- Add deep search decision criteria
- Integrate with todo execution

### Phase 5: Testing (1 hour)
- Unit tests for TodoItem, ResolutionPlan
- Integration test for parallel retrieval
- End-to-end CLI test with 10 documents
- Performance benchmarking

---

## 🎯 New Query Flow (Designed)

```
1. Query Input
   ↓
2. 🔍 Analysis & Display
   "分析查詢中... 意圖: 尋找裁罰案件, 複雜度: 中等"
   ↓
3. ❓ [Optional] Clarification
   "需要澄清: 請問您要查詢哪個時間範圍?"
   ↓
4. 📋 Resolution Plan
   "策略: 複雜查詢 | 並行檢索 | 預估: 25 秒"
   ↓
5. 📝 Todo List Display
   [ ] 1. 概念分析檢索
   [ ] 2. 向量相似度檢索
   [ ] 3. 結果驗證
   [ ] 4. 答案合成
   ↓
6. ⏳ Execute with Progress
   [✓] 1. 概念分析檢索 (找到 5 份文件)
   [✓] 2. 向量相似度檢索 (找到 8 份文件)
   [⏳] 3. 結果驗證... (60%)
   [ ] 4. 答案合成
   ↓
7. 🔬 [Optional] Deep Search
   "正在閱讀完整文件進行深度分析..."
   ↓
8. 🤖 Generate Answer
   "合成答案中..."
   ↓
9. 📚 Show Citations
   [1] 玉山銀行_洗錢防制裁罰_2020.txt
   [2] 華南商業銀行_洗錢防制_2019.txt
   ↓
10. ✨ Final Answer
```

---

## 💡 Key Design Decisions

### 1. UICallback Interface
**Decision**: Use async callbacks with abstract base class
**Rationale**:
- Supports both CLI and web UI
- Easy to test with NoOpCallback
- Clear separation of concerns
- Future-proof for streaming responses

### 2. TodoItem with Dependencies
**Decision**: Each todo can specify dependency IDs
**Rationale**:
- Enables DAG-based execution order
- Supports parallel execution where safe
- Clear task relationships
- Easy to visualize

### 3. Three Plan Types
**Decision**: Simple, Complex, Deep Search
**Rationale**:
- Simple: Single vector search (5-10s)
- Complex: Parallel concept + vector (20-30s)
- Deep Search: Full document reading (40-60s)
- User can see trade-off between speed and depth

### 4. Parallel by Default
**Decision**: Complex plan uses parallel retrieval
**Rationale**:
- 2x faster retrieval (concept + vector in parallel)
- Better result coverage
- Transparent to user (just faster)

---

## 📊 Expected Performance Improvements

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Retrieval Time** | 15-20s | 8-12s | 40-50% faster |
| **User Visibility** | None (black box) | Real-time | 100% transparent |
| **Parallel Tasks** | 0 | 2-3 | 2-3x throughput |
| **Progress Updates** | 0 | 8-12 updates | Full visibility |

---

## 🧪 Testing Strategy

### Unit Tests
```python
# Test TodoItem lifecycle
def test_todo_item_lifecycle():
    todo = TodoItem(id="test", content="Test task", ...)
    todo.mark_started()
    assert todo.status == "in_progress"
    todo.update_progress(50, "Halfway done")
    assert todo.progress_percentage == 50
    todo.mark_completed(result={"count": 10})
    assert todo.status == "completed"

# Test ResolutionPlan factory methods
def test_create_complex_plan():
    plan = ResolutionPlan.create_complex_plan()
    assert plan.strategy == "complex"
    assert plan.parallel_capable == True
    assert "vector_search" in plan.tools
    assert "concept_search" in plan.tools
```

### Integration Tests
```python
# Test parallel retrieval
async def test_parallel_retrieval():
    callback = LoggingCallback()
    query = Query(text="玉山銀行洗錢防制裁罰")

    results = await execute_parallel_retrieval(query, callback)

    assert "concept_results" in results
    assert "vector_results" in results
    assert results["merged_count"] > 0
```

### End-to-End Test
```bash
# Run with 10-document dataset
uv run finagent query "玉山銀行洗錢防制裁罰" --verbose

# Expected output:
# 🔍 分析查詢中...
# ✓ 查詢分析完成
# 📋 執行計劃: 複雜查詢 (預估 25 秒)
# 📝 任務清單:
#   [ ] 1. 概念分析檢索
#   [ ] 2. 向量相似度檢索
#   ...
# ⏳ 執行中...
#   [✓] 1. 概念分析檢索 (5 docs, 3.2s)
#   [✓] 2. 向量相似度檢索 (8 docs, 3.5s)
#   ...
# ✨ 答案已生成 (總時間: 22.3 秒)
```

---

## 🔗 Related Files

### Design & Planning
- [QUERY_FLOW_REFACTOR_DESIGN.md](QUERY_FLOW_REFACTOR_DESIGN.md) - Full design spec
- [CLI_TEST_RESULTS.md](CLI_TEST_RESULTS.md) - Current system test results
- [TEST_ISSUES_SUMMARY.md](TEST_ISSUES_SUMMARY.md) - Known issues

### Current Implementation
- [src/finagent/agents/orchestrator.py](src/finagent/agents/orchestrator.py) - Current orchestrator
- [src/finagent/agents/workflow.py](src/finagent/agents/workflow.py) - Current LangGraph workflow
- [src/finagent/agents/action_agent.py](src/finagent/agents/action_agent.py) - Current retrieval agent

### New Models
- [src/finagent/models/todo_item.py](src/finagent/models/todo_item.py) - ✅ Created
- [src/finagent/models/resolution_plan.py](src/finagent/models/resolution_plan.py) - ✅ Created
- [src/finagent/agents/ui_callback.py](src/finagent/agents/ui_callback.py) - ✅ Created

---

## 📌 Next Session Action Items

1. **Implement TodoManager** (60 min)
   - Parallel execution with asyncio.gather()
   - Dependency resolution
   - UI callback integration

2. **Implement ResolutionPlanner** (45 min)
   - LLM-based plan selection
   - Todo list generation
   - Complexity heuristics

3. **Create CLI Progress Callback** (45 min)
   - Rich terminal UI
   - Live progress display
   - Todo list visualization

4. **Test with 10-Document Dataset** (30 min)
   - Run end-to-end test
   - Measure performance
   - Verify UI updates

**Total Estimated Time**: 3 hours

---

**Status**: Phase 1 complete, ready for Phase 2 implementation
**Last Updated**: 2025-11-14
