# Query Flow Refactor Design

**Date**: 2025-11-14
**Goal**: Refactor query flow to be UI-driven with progressive updates and task tracking

---

## 🎯 New Query Flow Architecture

### Flow Stages

```
1. Query Input
   ↓
2. Analysis & Display to UI
   ↓
3. [Optional] Human-in-the-Loop Clarification
   ↓
4. Create Resolution Plan (Tools + Agents)
   ↓
5. Create & Display Todo List to UI
   ↓
6. Execute Todo List (with parallel tasks where possible)
   ├─ Concept Analysis Retrieval
   ├─ Vector Retrieval
   └─ [Parallel execution]
   ↓
7. [Optional] Deep Search (Full Doc Reading)
   ↓
8. Update Todo List to UI (on each step completion)
   ↓
9. Generate Answer
   ↓
10. Show Citations
    ↓
11. Final Answer Display
```

---

## 📊 Current vs New Architecture

### Current Flow (LangGraph-based)
```
START → Query Analysis → [Clarification?] → Planning → Action → Validation → Reference Guard → Answer → END
                              ↓                                    ↑              ↓
                        Human-in-Loop                             └── Re-Search ←┘
```

**Issues**:
- No UI progress updates during execution
- No visible todo list for users
- Sequential execution (not parallelized where possible)
- Limited visibility into what the system is doing

### New Flow (UI-Driven with Progress Tracking)
```
START → Analysis (UI Update) → [Clarification?] → Plan (UI Update) → Todo List (UI Update)
           ↓                         ↓                                      ↓
    "Analyzing query..."     "Need clarification"           "📋 Plan: 1. Retrieve docs
                                                                      2. Analyze results
                                                                      3. Synthesize answer"
                                                                           ↓
                                                            Execute (with UI updates)
                                                            ✓ Task 1 completed
                                                            ⏳ Task 2 in progress
                                                                           ↓
                                                            Answer → Citations → Final
```

---

## 🏗️ Key Components

### 1. UI Callback System

**Purpose**: Allow workflow to send progress updates to UI

```python
class UICallback:
    """Callback interface for sending UI updates."""

    async def on_analysis_start(self, query: str):
        """Called when query analysis starts."""
        pass

    async def on_analysis_complete(self, analysis: QueryAnalysis):
        """Called when analysis completes."""
        pass

    async def on_clarification_request(self, request: ClarificationRequest) -> str:
        """Request clarification from user."""
        pass

    async def on_plan_created(self, plan: ResolutionPlan):
        """Called when resolution plan is created."""
        pass

    async def on_todo_created(self, todos: List[TodoItem]):
        """Called when todo list is created."""
        pass

    async def on_todo_updated(self, todo_id: str, status: str):
        """Called when a todo item is updated."""
        pass

    async def on_retrieval_start(self, strategy: str):
        """Called when retrieval starts."""
        pass

    async def on_retrieval_complete(self, chunks: List[Chunk], count: int):
        """Called when retrieval completes."""
        pass

    async def on_answer_start(self):
        """Called when answer synthesis starts."""
        pass

    async def on_citations_ready(self, citations: List[Citation]):
        """Called when citations are formatted."""
        pass

    async def on_answer_complete(self, answer: LegalAnswer):
        """Called when final answer is ready."""
        pass
```

### 2. Todo Item Model

```python
class TodoItem(BaseModel):
    """Represents a task in the execution plan."""

    id: str
    content: str  # Imperative form: "Retrieve documents"
    active_form: str  # Present continuous: "Retrieving documents"
    status: Literal["pending", "in_progress", "completed", "failed"]
    category: Literal["analysis", "retrieval", "validation", "synthesis"]
    can_parallel: bool = False  # Can run in parallel with other tasks
    dependencies: List[str] = []  # IDs of tasks that must complete first
    result: Any = None  # Result data from task execution
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

### 3. Resolution Plan

```python
class ResolutionPlan(BaseModel):
    """Plan for resolving the query."""

    strategy: Literal["simple", "complex", "deep_search"]
    tools: List[str]  # ["vector_search", "concept_search", "full_doc_reader"]
    agents: List[str]  # ["retrieval", "validation", "synthesis"]
    estimated_time_seconds: int
    parallel_capable: bool
    requires_deep_search: bool
    reasoning: str  # Why this plan was chosen
```

### 4. Query Analysis Result

```python
class QueryAnalysis(BaseModel):
    """Result of query analysis."""

    intent: str  # "Find penalties", "Compare cases", etc.
    entities: List[str]  # ["玉山銀行", "洗錢防制"]
    time_range: Optional[Dict[str, str]]
    complexity: Literal["simple", "moderate", "complex"]
    needs_clarification: bool
    clarification_questions: List[str]
    suggested_filters: Dict[str, Any]
    reasoning: str
```

---

## 🔄 Refactored Workflow Implementation

### Phase 1: Analysis & Planning

```python
async def execute_query_with_ui(
    query: Query,
    ui_callback: UICallback
) -> LegalAnswer:
    """Execute query with progressive UI updates."""

    # 1. Analysis
    await ui_callback.on_analysis_start(query.text)
    analysis = await analyze_query(query)
    await ui_callback.on_analysis_complete(analysis)

    # 2. [Optional] Clarification
    if analysis.needs_clarification:
        clarification = await ui_callback.on_clarification_request(
            ClarificationRequest(questions=analysis.clarification_questions)
        )
        # Enrich query with clarification
        query = enrich_query(query, clarification)

    # 3. Create Resolution Plan
    plan = await create_resolution_plan(query, analysis)
    await ui_callback.on_plan_created(plan)

    # 4. Create Todo List
    todos = create_todo_list(plan)
    await ui_callback.on_todo_created(todos)

    # 5. Execute Todos
    results = await execute_todos(todos, ui_callback)

    # 6. [Optional] Deep Search
    if plan.requires_deep_search:
        deep_results = await perform_deep_search(results, ui_callback)
        results.update(deep_results)

    # 7. Synthesize Answer
    await ui_callback.on_answer_start()
    answer = await synthesize_answer(results)

    # 8. Format Citations
    citations = format_citations(answer.citations)
    await ui_callback.on_citations_ready(citations)

    # 9. Final Answer
    await ui_callback.on_answer_complete(answer)

    return answer
```

### Phase 2: Todo Execution with Parallelization

```python
async def execute_todos(
    todos: List[TodoItem],
    ui_callback: UICallback
) -> Dict[str, Any]:
    """Execute todo list with parallel execution where possible."""

    results = {}
    completed = set()

    while len(completed) < len(todos):
        # Find tasks ready to execute (dependencies met)
        ready_tasks = [
            todo for todo in todos
            if todo.status == "pending"
            and all(dep in completed for dep in todo.dependencies)
        ]

        if not ready_tasks:
            break

        # Group by parallelization capability
        parallel_tasks = [t for t in ready_tasks if t.can_parallel]
        sequential_tasks = [t for t in ready_tasks if not t.can_parallel]

        # Execute parallel tasks concurrently
        if parallel_tasks:
            parallel_results = await asyncio.gather(*[
                execute_single_todo(todo, ui_callback)
                for todo in parallel_tasks
            ])

            for todo, result in zip(parallel_tasks, parallel_results):
                results[todo.id] = result
                completed.add(todo.id)

        # Execute sequential tasks one by one
        for todo in sequential_tasks:
            result = await execute_single_todo(todo, ui_callback)
            results[todo.id] = result
            completed.add(todo.id)

    return results


async def execute_single_todo(
    todo: TodoItem,
    ui_callback: UICallback
) -> Any:
    """Execute a single todo item."""

    # Mark as in progress
    todo.status = "in_progress"
    todo.started_at = datetime.now()
    await ui_callback.on_todo_updated(todo.id, "in_progress")

    try:
        # Execute based on category
        if todo.category == "retrieval":
            result = await execute_retrieval_task(todo)
        elif todo.category == "validation":
            result = await execute_validation_task(todo)
        elif todo.category == "synthesis":
            result = await execute_synthesis_task(todo)
        else:
            result = None

        # Mark as completed
        todo.status = "completed"
        todo.completed_at = datetime.now()
        todo.result = result
        await ui_callback.on_todo_updated(todo.id, "completed")

        return result

    except Exception as e:
        # Mark as failed
        todo.status = "failed"
        todo.error = str(e)
        await ui_callback.on_todo_updated(todo.id, "failed")
        raise
```

### Phase 3: Parallel Concept + Vector Retrieval

```python
async def execute_retrieval_task(todo: TodoItem) -> Dict[str, Any]:
    """Execute retrieval with parallel concept + vector search."""

    query = todo.result.get("query")

    # Run concept analysis and vector search in parallel
    concept_results, vector_results = await asyncio.gather(
        retrieve_via_concepts(query),
        retrieve_via_vectors(query)
    )

    # Merge and deduplicate results
    merged_chunks = merge_retrieval_results(
        concept_results,
        vector_results
    )

    return {
        "chunks": merged_chunks,
        "concept_count": len(concept_results),
        "vector_count": len(vector_results),
        "merged_count": len(merged_chunks)
    }


async def retrieve_via_concepts(query: Query) -> List[Chunk]:
    """Retrieve documents via semantic concept analysis."""
    from finagent.document_processing.concept_extractor import analyze_query_concepts

    # Extract concepts from query
    concepts = analyze_query_concepts(query.text)

    # Find documents matching concepts
    doc_ids = await find_documents_by_concepts(concepts)

    # Retrieve chunks from matching documents
    chunks = await get_chunks_by_doc_ids(doc_ids)

    return chunks


async def retrieve_via_vectors(query: Query) -> List[Chunk]:
    """Retrieve documents via vector similarity search."""
    from finagent.document_processing.retriever import DocumentRetriever

    retriever = DocumentRetriever()
    chunks = retriever.retrieve(query.text, top_k=10)

    return chunks
```

### Phase 4: Optional Deep Search

```python
async def perform_deep_search(
    initial_results: Dict[str, Any],
    ui_callback: UICallback
) -> Dict[str, Any]:
    """Perform deep search by reading full documents."""

    # Create deep search todo
    deep_todo = TodoItem(
        id="deep_search",
        content="Read full documents for detailed analysis",
        active_form="Reading full documents",
        status="in_progress",
        category="retrieval"
    )

    await ui_callback.on_todo_updated(deep_todo.id, "in_progress")

    # Get top document IDs from initial retrieval
    top_doc_ids = extract_top_doc_ids(initial_results["chunks"], top_n=3)

    # Read full documents
    full_docs = await read_full_documents(top_doc_ids)

    # Perform detailed analysis on full content
    deep_analysis = await analyze_full_documents(full_docs)

    deep_todo.status = "completed"
    await ui_callback.on_todo_updated(deep_todo.id, "completed")

    return {
        "full_documents": full_docs,
        "deep_analysis": deep_analysis
    }
```

---

## 🎨 CLI UI Updates

### New CLI Output Format

```
🔍 分析查詢中...
✓ 查詢分析完成
  意圖: 尋找玉山銀行洗錢防制裁罰案件
  實體: 玉山銀行、洗錢防制
  複雜度: 中等

📋 執行計劃
  策略: 標準檢索 + 語意分析
  預估時間: 20-30 秒

  任務清單:
  [ ] 1. 概念分析檢索
  [ ] 2. 向量相似度檢索
  [ ] 3. 結果驗證
  [ ] 4. 答案合成

⏳ 執行中...
  [✓] 1. 概念分析檢索 (找到 5 份文件)
  [✓] 2. 向量相似度檢索 (找到 8 份文件)
  [⏳] 3. 結果驗證...

✓ 檢索完成 (共 10 份文件，12 個區塊)

🤖 合成答案中...

📚 引用來源 (2 個)
  [1] 玉山銀行_洗錢防制裁罰_2020.txt
  [2] 華南商業銀行_洗錢防制_2019.txt

✨ 答案已生成
```

---

## 📁 File Structure

New files to create:

```
src/finagent/agents/
├── ui_callback.py          # UICallback interface and implementations
├── todo_manager.py         # TodoItem management and execution
├── resolution_planner.py   # Resolution plan creation
└── parallel_executor.py    # Parallel task execution

src/finagent/models/
├── todo_item.py           # TodoItem model
├── resolution_plan.py     # ResolutionPlan model
└── query_analysis.py      # QueryAnalysis model (refactor existing)

src/finagent/cli/formatters/
└── progress.py            # CLI progress display formatters
```

Modified files:

```
src/finagent/agents/
├── orchestrator.py        # Refactor to use new flow
└── workflow.py            # Simplify or deprecate

src/finagent/cli/commands/
└── query.py               # Use new UI callback system
```

---

## 🚀 Implementation Phases

### Phase 1: Core Infrastructure (1-2 hours)
1. Create `UICallback` interface
2. Create `TodoItem`, `ResolutionPlan`, `QueryAnalysis` models
3. Create `TodoManager` for todo execution
4. Create `ResolutionPlanner` for plan creation

### Phase 2: Parallel Retrieval (1 hour)
1. Refactor retrieval to support parallel concept + vector search
2. Implement result merging and deduplication
3. Add retrieval progress callbacks

### Phase 3: UI Integration (1 hour)
1. Create CLI implementation of `UICallback`
2. Add progress display formatters
3. Update query command to use new flow

### Phase 4: Deep Search (Optional, 1 hour)
1. Implement full document reading
2. Add deep search decision logic
3. Integrate with todo execution

### Phase 5: Testing & Refinement (1 hour)
1. Test with 10-document dataset
2. Verify parallel execution works
3. Ensure UI updates are smooth
4. Performance tuning

---

## ✅ Success Criteria

1. **Progressive UI Updates**: User sees each stage of execution in real-time
2. **Visible Todo List**: User can see task breakdown and progress
3. **Parallel Execution**: Concept and vector retrieval run concurrently
4. **Optional Deep Search**: System intelligently decides when to read full docs
5. **Backward Compatible**: Existing code still works during migration
6. **Maintainable**: Clear separation of concerns, easy to extend

---

## 📝 Next Steps

1. Review and approve this design
2. Start with Phase 1 implementation
3. Test incrementally after each phase
4. Gather user feedback on UI updates
5. Iterate based on performance metrics

---

**Questions for Discussion**:
1. Should we keep LangGraph or replace with simpler state machine?
2. How granular should todo items be?
3. Should deep search be automatic or user-controlled?
4. What additional progress metrics should we track?
