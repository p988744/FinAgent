# Enhanced Planning Agent Design

**Date:** 2025-11-14
**Purpose:** Enhance Planning Agent with query analysis, task tracking, and hard search capabilities
**Features:** Query analysis display, TODO tracking, plan validation, hard search, query memos

---

## Overview

Three major enhancements:

1. **Enhanced Planning Agent**: Shows query analysis and generates TODO list
2. **Hard Search Method**: Direct file reading for deep understanding (grep, readlines)
3. **Query Memo System**: Database tracking of query history and notes

---

## 1. Enhanced Planning Agent

### Current Behavior

```python
# Current Planning Agent
def plan(state):
    query = state["query"]
    plan = {"max_results": 5, "jurisdiction": "金管會"}
    return state
```

**Problem**: No visibility into planning process, no task tracking

### Enhanced Behavior

```python
# Enhanced Planning Agent
def plan(state):
    # 1. Query Analysis
    analysis = {
        "keywords": ["創投", "裁罰", "金管會"],
        "entity_type": "venture_capital",
        "jurisdiction": "證券期貨局",
        "time_period": None,
        "query_type": "enforcement_search",
    }

    # 2. Generate TODO List
    tasks = [
        {"id": 1, "task": "搜索創投公司相關文件", "status": "pending"},
        {"id": 2, "task": "過濾金管會裁罰案件", "status": "pending"},
        {"id": 3, "task": "驗證引用完整性", "status": "pending"},
        {"id": 4, "task": "生成答案", "status": "pending"},
    ]

    # 3. Display Analysis
    print("查詢分析：")
    print(f"  關鍵字: {analysis['keywords']}")
    print(f"  實體類型: {analysis['entity_type']}")
    print(f"  管轄機關: {analysis['jurisdiction']}")

    print("\n任務清單：")
    for task in tasks:
        print(f"  [ ] {task['id']}. {task['task']}")

    return state
```

### Implementation Plan

```python
# models/plan.py
class QueryAnalysis(BaseModel):
    """Query analysis results."""
    keywords: list[str]
    must_have_keywords: list[str]
    entity_type: str
    jurisdiction: str | None
    time_period: str | None
    query_type: str  # "enforcement_search", "legal_interpretation", etc.
    complexity: str  # "simple", "medium", "complex"

class PlanTask(BaseModel):
    """Individual task in research plan."""
    id: int
    task: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    search_method: Literal["vector_search", "hard_search", "hybrid"]
    estimated_time: int | None  # seconds

class ResearchPlan(BaseModel):
    """Complete research plan."""
    analysis: QueryAnalysis
    tasks: list[PlanTask]
    max_results: int
    use_hard_search: bool
    estimated_total_time: int

# agents/planning_agent.py
class PlanningAgent:
    def plan(self, state: AgentState) -> AgentState:
        query = state["query"]

        # Analyze query
        analysis = self._analyze_query(query.text)

        # Generate tasks
        tasks = self._generate_tasks(analysis)

        # Create research plan
        plan = ResearchPlan(
            analysis=analysis,
            tasks=tasks,
            max_results=self._determine_max_results(analysis),
            use_hard_search=self._should_use_hard_search(analysis),
            estimated_total_time=sum(t.estimated_time for t in tasks if t.estimated_time)
        )

        # Display plan
        self._display_plan(plan)

        # Update state
        state["plan"] = plan.dict()
        state["research_tasks"] = [t.task for t in tasks]
        state["plan_analysis"] = analysis.dict()

        return state

    def _analyze_query(self, query_text: str) -> QueryAnalysis:
        """Analyze query and extract key information."""
        from finagent.utils.keyword_extraction import (
            extract_critical_keywords,
            extract_must_have_keywords,
            identify_entity_type,
        )

        keywords = extract_critical_keywords(query_text)
        must_have = extract_must_have_keywords(query_text)
        entity_type = identify_entity_type(query_text)

        # Identify jurisdiction
        jurisdiction = None
        if "金管會" in query_text:
            jurisdiction = "金管會"
        elif "中央銀行" in query_text:
            jurisdiction = "中央銀行"

        # Identify query type
        query_type = "enforcement_search"
        if "判決" in query_text:
            query_type = "court_judgment"
        elif "解釋" in query_text or "規定" in query_text:
            query_type = "legal_interpretation"

        # Determine complexity
        complexity = "medium"
        if len(must_have) > 2 or entity_type != "unknown":
            complexity = "complex"
        elif len(keywords) <= 2:
            complexity = "simple"

        return QueryAnalysis(
            keywords=keywords,
            must_have_keywords=must_have,
            entity_type=entity_type,
            jurisdiction=jurisdiction,
            time_period=None,  # TODO: Extract time period
            query_type=query_type,
            complexity=complexity,
        )

    def _generate_tasks(self, analysis: QueryAnalysis) -> list[PlanTask]:
        """Generate research tasks based on analysis."""
        tasks = []
        task_id = 1

        # Task 1: Vector search
        tasks.append(PlanTask(
            id=task_id,
            task=f"向量搜索：{', '.join(analysis.keywords)}",
            status="pending",
            search_method="vector_search",
            estimated_time=10,
        ))
        task_id += 1

        # Task 2: Hard search (if complex query)
        if analysis.complexity == "complex" and analysis.must_have_keywords:
            tasks.append(PlanTask(
                id=task_id,
                task=f"深度搜索：grep 關鍵字 {analysis.must_have_keywords}",
                status="pending",
                search_method="hard_search",
                estimated_time=30,
            ))
            task_id += 1

        # Task 3: Validation
        tasks.append(PlanTask(
            id=task_id,
            task="驗證引用完整性和關鍵字匹配",
            status="pending",
            search_method="vector_search",  # N/A
            estimated_time=5,
        ))
        task_id += 1

        # Task 4: Answer synthesis
        tasks.append(PlanTask(
            id=task_id,
            task="生成答案並格式化引用",
            status="pending",
            search_method="vector_search",  # N/A
            estimated_time=15,
        ))

        return tasks

    def _display_plan(self, plan: ResearchPlan):
        """Display research plan to user."""
        logger.info("=" * 60)
        logger.info("查詢分析結果")
        logger.info("=" * 60)
        logger.info(f"關鍵字: {', '.join(plan.analysis.keywords)}")
        logger.info(f"必要關鍵字: {', '.join(plan.analysis.must_have_keywords)}")
        logger.info(f"實體類型: {plan.analysis.entity_type}")
        logger.info(f"管轄機關: {plan.analysis.jurisdiction or '未指定'}")
        logger.info(f"查詢類型: {plan.analysis.query_type}")
        logger.info(f"複雜度: {plan.analysis.complexity}")
        logger.info("")
        logger.info("研究任務清單")
        logger.info("-" * 60)
        for task in plan.tasks:
            symbol = "⏱" if task.search_method == "hard_search" else "🔍"
            logger.info(f"  [ ] {task.id}. {symbol} {task.task}")
        logger.info("")
        logger.info(f"預估總時間: {plan.estimated_total_time}秒")
        logger.info("=" * 60)
```

---

## 2. Hard Search Method

### Concept

Instead of relying only on vector similarity, use direct file operations to find exact matches:

```python
# Traditional approach (vector search only)
results = vector_db.similarity_search(query, k=5)

# Hard search approach
# 1. Use grep to find files containing keywords
# 2. Read matching files line by line
# 3. Extract relevant sections
# 4. Return high-confidence matches
```

### Implementation

```python
# document_processing/hard_search.py
import logging
import subprocess
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class HardSearcher:
    """
    Hard searcher uses direct file operations for deep understanding.

    Methods:
    - grep_search: Use grep to find files with exact keyword matches
    - read_matching_files: Read entire files containing keywords
    - extract_context: Extract surrounding context for matches
    """

    def __init__(self, documents_dir: Path):
        """
        Initialize hard searcher.

        Args:
            documents_dir: Directory containing document files
        """
        self.documents_dir = documents_dir

    def hard_search(
        self,
        keywords: List[str],
        context_lines: int = 5,
        max_files: int = 10,
    ) -> List[dict]:
        """
        Perform hard search with grep and file reading.

        Args:
            keywords: List of keywords to search for
            context_lines: Number of lines of context to include
            max_files: Maximum number of files to process

        Returns:
            List of search results with file path, line number, and context
        """
        logger.info(f"Hard search for keywords: {keywords}")

        results = []

        # Step 1: Use grep to find matching files
        matching_files = self._grep_files(keywords)

        logger.info(f"Found {len(matching_files)} files via grep")

        # Step 2: Read each matching file
        for file_path in matching_files[:max_files]:
            file_results = self._process_file(file_path, keywords, context_lines)
            results.extend(file_results)

        logger.info(f"Hard search found {len(results)} matches")

        return results

    def _grep_files(self, keywords: List[str]) -> List[Path]:
        """
        Use grep to find files containing keywords.

        Args:
            keywords: Keywords to search for

        Returns:
            List of file paths
        """
        matching_files = set()

        for keyword in keywords:
            try:
                # Use grep to search for keyword
                result = subprocess.run(
                    ["grep", "-l", "-r", keyword, str(self.documents_dir)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                # Parse file paths from output
                for line in result.stdout.strip().split("\n"):
                    if line:
                        matching_files.add(Path(line))

            except subprocess.TimeoutExpired:
                logger.warning(f"Grep timeout for keyword: {keyword}")
            except Exception as e:
                logger.error(f"Grep failed for {keyword}: {e}")

        return sorted(matching_files)

    def _process_file(
        self,
        file_path: Path,
        keywords: List[str],
        context_lines: int,
    ) -> List[dict]:
        """
        Read file and extract matches with context.

        Args:
            file_path: Path to file
            keywords: Keywords to search for
            context_lines: Lines of context

        Returns:
            List of matches with context
        """
        results = []

        try:
            # Read entire file
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Find matching lines
            for line_num, line in enumerate(lines, 1):
                # Check if any keyword appears in this line
                if any(keyword in line for keyword in keywords):
                    # Extract context
                    start = max(0, line_num - context_lines - 1)
                    end = min(len(lines), line_num + context_lines)

                    context = "".join(lines[start:end])

                    results.append({
                        "file_path": str(file_path),
                        "filename": file_path.name,
                        "line_number": line_num,
                        "matching_line": line.strip(),
                        "context": context,
                        "keywords_found": [kw for kw in keywords if kw in line],
                    })

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")

        return results

    def read_full_file(self, file_path: Path) -> str:
        """
        Read entire file content.

        Args:
            file_path: Path to file

        Returns:
            Full file content
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return ""
```

### Integration with Action Agent

```python
# agents/action_agent.py
class ActionAgent:
    def __init__(self, retriever: DocumentRetriever, documents_dir: Path):
        self.retriever = retriever
        self.hard_searcher = HardSearcher(documents_dir)

    def execute(self, state: AgentState) -> AgentState:
        plan = state.get("plan", {})
        use_hard_search = plan.get("use_hard_search", False)

        if use_hard_search:
            # Perform hard search
            analysis = state.get("plan_analysis", {})
            keywords = analysis.get("must_have_keywords", [])

            logger.info("執行深度搜索（hard search）...")
            hard_results = self.hard_searcher.hard_search(keywords)

            # Convert hard search results to RetrievedChunks
            hard_chunks = self._convert_hard_results(hard_results)

            # Also do vector search
            logger.info("執行向量搜索...")
            vector_chunks = self.retriever.retrieve(...)

            # Combine results (prefer hard search matches)
            retrieved_chunks = self._merge_results(hard_chunks, vector_chunks)
        else:
            # Normal vector search only
            retrieved_chunks = self.retriever.retrieve(...)

        return state
```

---

## 3. Query Memo System

### Database Schema

```sql
-- Add to schema.sql
CREATE TABLE IF NOT EXISTS query_memos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id TEXT UNIQUE NOT NULL,  -- Hash of query text
    query_text TEXT NOT NULL,

    -- Query analysis
    keywords TEXT,  -- JSON array
    entity_type TEXT,
    jurisdiction TEXT,
    complexity TEXT,

    -- Research notes
    search_iterations INTEGER DEFAULT 0,
    hard_search_used BOOLEAN DEFAULT FALSE,
    validation_issues TEXT,  -- JSON array

    -- Results summary
    citations_count INTEGER,
    confidence_level TEXT,
    processing_time_ms INTEGER,

    -- Memo notes
    analyst_notes TEXT,  -- Free-text notes
    tags TEXT,  -- JSON array of tags

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_query_memos_query_id ON query_memos(query_id);
CREATE INDEX idx_query_memos_created_at ON query_memos(created_at);
```

### Python Models

```python
# database/models.py
class QueryMemo(BaseModel):
    """Query memo for tracking research history."""

    id: int | None = None
    query_id: str  # SHA256 hash of query text
    query_text: str

    # Analysis
    keywords: list[str] = Field(default_factory=list)
    entity_type: str | None = None
    jurisdiction: str | None = None
    complexity: str | None = None

    # Research tracking
    search_iterations: int = 0
    hard_search_used: bool = False
    validation_issues: list[str] = Field(default_factory=list)

    # Results
    citations_count: int = 0
    confidence_level: str | None = None
    processing_time_ms: int | None = None

    # Notes
    analyst_notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### CRUD Operations

```python
# database/db.py
class Database:
    def save_query_memo(self, memo: QueryMemo) -> int:
        """Save or update query memo."""
        import hashlib
        import json

        # Generate query_id if not provided
        if not memo.query_id:
            memo.query_id = hashlib.sha256(
                memo.query_text.encode()
            ).hexdigest()[:16]

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if exists
            cursor.execute(
                "SELECT id FROM query_memos WHERE query_id = ?",
                (memo.query_id,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update
                cursor.execute("""
                    UPDATE query_memos SET
                        keywords = ?,
                        entity_type = ?,
                        search_iterations = ?,
                        hard_search_used = ?,
                        validation_issues = ?,
                        citations_count = ?,
                        confidence_level = ?,
                        processing_time_ms = ?,
                        analyst_notes = ?,
                        tags = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE query_id = ?
                """, (
                    json.dumps(memo.keywords),
                    memo.entity_type,
                    memo.search_iterations,
                    memo.hard_search_used,
                    json.dumps(memo.validation_issues),
                    memo.citations_count,
                    memo.confidence_level,
                    memo.processing_time_ms,
                    memo.analyst_notes,
                    json.dumps(memo.tags),
                    memo.query_id,
                ))
                return existing[0]
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO query_memos (
                        query_id, query_text, keywords, entity_type,
                        jurisdiction, complexity, search_iterations,
                        hard_search_used, validation_issues,
                        citations_count, confidence_level,
                        processing_time_ms, analyst_notes, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memo.query_id,
                    memo.query_text,
                    json.dumps(memo.keywords),
                    memo.entity_type,
                    memo.jurisdiction,
                    memo.complexity,
                    memo.search_iterations,
                    memo.hard_search_used,
                    json.dumps(memo.validation_issues),
                    memo.citations_count,
                    memo.confidence_level,
                    memo.processing_time_ms,
                    memo.analyst_notes,
                    json.dumps(memo.tags),
                ))
                return cursor.lastrowid

    def get_query_memo(self, query_text: str) -> QueryMemo | None:
        """Get memo for a query."""
        import hashlib

        query_id = hashlib.sha256(query_text.encode()).hexdigest()[:16]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM query_memos WHERE query_id = ?",
                (query_id,)
            )
            row = cursor.fetchone()

            if row:
                return QueryMemo(**dict(row))
            return None
```

### Integration with Orchestrator

```python
# agents/orchestrator.py
class AgentOrchestrator:
    async def process_query(self, query: Query) -> LegalAnswer:
        start_time = time.time()

        # Process query through workflow
        answer = await self._process_with_langgraph(query)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Save query memo
        final_state = self.workflow.last_state  # Need to expose this
        analysis = final_state.get("plan_analysis", {})

        memo = QueryMemo(
            query_text=query.text,
            keywords=analysis.get("keywords", []),
            entity_type=analysis.get("entity_type"),
            jurisdiction=analysis.get("jurisdiction"),
            complexity=analysis.get("complexity"),
            search_iterations=final_state.get("search_iteration", 0),
            hard_search_used=final_state.get("plan", {}).get("use_hard_search", False),
            validation_issues=final_state.get("validation_issues", []),
            citations_count=len(answer.citations) if answer else 0,
            confidence_level=answer.confidence_score.value if answer else None,
            processing_time_ms=processing_time_ms,
        )

        self.db.save_query_memo(memo)

        return answer
```

---

## 4. Plan Validation

### Workflow Enhancement

```python
# workflow.py
class LegalResearchWorkflow:
    def _build_graph(self):
        # ... existing nodes ...

        # Add plan validator node
        workflow.add_node("plan_validator", self._plan_validator_node)

        # Update edges
        workflow.add_edge(START, "planning")
        workflow.add_edge("planning", "plan_validator")  # NEW
        workflow.add_edge("plan_validator", "action")     # NEW
        # ... rest of workflow ...

    def _plan_validator_node(self, state: AgentState) -> AgentState:
        """Validate that all planned tasks are feasible."""
        plan = state.get("plan", {})
        tasks = plan.get("tasks", [])

        logger.info("Validating research plan...")

        # Check if hard search is available
        if plan.get("use_hard_search") and not self.action_agent.hard_searcher:
            logger.warning("Hard search requested but not available")
            plan["use_hard_search"] = False

        # Validate task order
        # ... validation logic ...

        state["processing_steps"].append("計劃驗證：通過")
        return state
```

### Task Completion Tracking

```python
# workflow.py
def _action_node(self, state: AgentState) -> AgentState:
    """Execute action and mark tasks as completed."""

    # Execute action
    state = self.action_agent.execute(state)

    # Update task status
    plan = state.get("plan", {})
    tasks = plan.get("tasks", [])

    for task in tasks:
        if task["task"].startswith("向量搜索") or task["task"].startswith("深度搜索"):
            task["status"] = "completed"

    state["plan"]["tasks"] = tasks

    # Log progress
    completed = sum(1 for t in tasks if t["status"] == "completed")
    logger.info(f"任務進度: {completed}/{len(tasks)} 完成")

    return state
```

---

## Summary of Changes

### Files to Create
1. `models/plan.py` - QueryAnalysis, PlanTask, ResearchPlan models
2. `document_processing/hard_search.py` - HardSearcher class
3. `database/migrations/003_add_query_memos.sql` - Database migration

### Files to Modify
1. `agents/planning_agent.py` - Enhanced with analysis and task generation
2. `agents/action_agent.py` - Add hard search capability
3. `agents/workflow.py` - Add plan validator node
4. `agents/state.py` - Add plan_analysis field
5. `database/models.py` - Add QueryMemo model
6. `database/db.py` - Add query memo CRUD operations
7. `agents/orchestrator.py` - Save query memos

### Expected Benefits
1. **Transparency**: Users see query analysis and research plan
2. **Deep Understanding**: Hard search finds exact matches that vector search misses
3. **Historical Tracking**: Query memos provide research history
4. **Task Validation**: Ensures all planned tasks are executed
5. **Better Coverage**: Hybrid search (vector + hard) improves recall

### Implementation Priority
1. **P0**: Enhanced Planning Agent with query analysis display
2. **P1**: Hard Search implementation
3. **P2**: Query Memo database integration
4. **P3**: Plan validation and task tracking
