# FinAgent LangGraph 升級計劃

> 基於 LangChain Academy 最新資源的具體升級方案，降低自行實作複雜度

## 目錄

1. [現況分析](#現況分析)
2. [升級路徑比較](#升級路徑比較)
3. [🌟 推薦方案: Deep Agents 重構](#推薦方案-deep-agents-重構)
4. [Phase 1: Memory & Checkpointer](#phase-1-memory--checkpointer)
5. [Phase 2: Subgraph 模組化](#phase-2-subgraph-模組化)
6. [Phase 3: RAG Agent 優化](#phase-3-rag-agent-優化)
7. [Phase 4: Hierarchical Multi-Agent](#phase-4-hierarchical-multi-agent)
8. [實作範例](#實作範例)
9. [遷移檢查清單](#遷移檢查清單)

---

## 現況分析

### 目前架構 (v1.1)

```
┌─────────────────────────────────────────────────────────┐
│                    Plan-and-Execute                      │
├─────────────────────────────────────────────────────────┤
│  Planner → Executor → Replanner → [loop] → Response     │
│     │         │          │                              │
│   Plan      Tools      Replan                           │
│            ├─ RetrieverTool                             │
│            └─ HardSearchTool                            │
├─────────────────────────────────────────────────────────┤
│  State: TypedDict (in-memory only)                      │
│  Memory: None (stateless per session)                   │
│  Tools: Custom BaseTool implementations                 │
└─────────────────────────────────────────────────────────┘
```

### 現有問題

| 問題 | 影響 | LangChain 解決方案 |
|------|------|-------------------|
| 無記憶功能 | 每次查詢重新開始，無法續談 | Checkpointer + Memory |
| 工具邏輯分散 | 維護困難，難以重用 | Subgraphs |
| RAG 單次檢索 | 複雜查詢準確度不足 | Agentic RAG |
| 無中斷恢復 | 長時間查詢失敗後需重來 | Checkpointer |
| 缺乏 Human-in-the-loop | 無法在關鍵節點確認 | interrupt_before |

---

## 升級路徑比較

有兩種主要升級路徑可選：

| 方案 | 優點 | 缺點 | 建議場景 |
|------|------|------|---------|
| **A: Deep Agents 重構** | 開箱即用、Claude Code 級功能、官方維護 | 需重構架構、有依賴 | **推薦** - 快速獲得完整功能 |
| **B: 漸進式升級** | 保留現有架構、低風險 | 需自行實作、耗時長 | 需高度客製化時 |

### 優先順序總表

| Priority | 升級項目 | 複雜度 | 價值 | 建議時程 |
|----------|---------|--------|------|---------|
| **P0** | 🌟 **Deep Agents 重構** | 中 | **極高** | v2.0 |
| **P1** | Checkpointer (SQLite) | 低 | 高 | v1.2 |
| **P2** | Memory Store | 中 | 高 | v1.2 |
| **P3** | Subgraph 重構 | 中 | 中 | v1.3 |
| **P4** | Agentic RAG | 高 | 高 | v1.4 |
| **P5** | Hierarchical Teams | 高 | 中 | v2.0 |

---

## 🌟 推薦方案: Deep Agents 重構

> **[Deep Agents](https://github.com/langchain-ai/deepagents)** 是 LangChain 官方發布的 Agent 框架，實現了 Claude Code 級別的功能，包括任務規劃、子代理委派、檔案系統存取等核心能力。

### 為什麼選擇 Deep Agents？

**Deep Agents 的四大支柱（來自 [LangChain Blog](https://blog.langchain.com/deep-agents/)）：**

1. **Detailed System Prompts** - 詳盡的系統提示詞指導 Agent 行為
2. **Planning Tools** - Todo List 機制組織複雜任務
3. **Sub-agents** - 子代理委派，實現上下文隔離
4. **File System Access** - 持久化存儲管理累積上下文

### FinAgent v1.1 vs Deep Agents 功能對比

| 功能 | FinAgent v1.1 | Deep Agents |
|------|--------------|-------------|
| 任務規劃 | 自訂 Planner | ✅ `TodoListMiddleware` (write_todos, read_todos) |
| 子代理 | ❌ 無 | ✅ `SubAgentMiddleware` (task tool) |
| 檔案操作 | ❌ 無 | ✅ `FilesystemMiddleware` (ls, read_file, write_file, edit_file, glob, grep) |
| 上下文管理 | 手動 | ✅ `SummarizationMiddleware` (170k token 自動摘要) |
| 狀態持久化 | ❌ 無 | ✅ 內建 Checkpointer |
| Human-in-the-loop | ❌ 無 | ✅ 內建支援 |
| Prompt Caching | ❌ 無 | ✅ `AnthropicPromptCachingMiddleware` |

### 安裝

```bash
uv add deepagents
```

**版本要求：**
- Python ≥ 3.11
- 當前版本：0.2.8 (2025-11-24)

### 實作範例：FinAgent Deep Agent

**檔案:** `src/finagent/agents/deep_agent/financial_agent.py`

```python
"""FinAgent Deep Agent - 金融法律研究代理"""
from deepagents import create_deep_agent
from deepagents.middleware import (
    TodoListMiddleware,
    SubAgentMiddleware,
    FilesystemMiddleware,
    SummarizationMiddleware,
)
from langchain_core.tools import tool
from finagent.tools.retriever import RetrieverTool
from finagent.tools.search import HardSearchTool

# 定義領域專用工具
@tool
def semantic_search(query: str, top_k: int = 5) -> str:
    """語意搜尋金融法律文件庫。

    Args:
        query: 搜尋查詢
        top_k: 返回結果數量
    """
    retriever = RetrieverTool()
    return retriever._run(query=query, top_k=top_k)

@tool
def keyword_search(keywords: str, top_k: int = 5) -> str:
    """關鍵字搜尋金融法律文件。

    Args:
        keywords: 搜尋關鍵字（逗號分隔）
        top_k: 返回結果數量
    """
    searcher = HardSearchTool()
    return searcher._run(keywords=keywords, top_k=top_k)

# 系統提示詞
FINANCIAL_AGENT_PROMPT = """你是 FinAgent，專精於台灣金融法律研究的 AI 助手。

## 專業領域
- 金管會裁罰案例分析
- 銀行監理法規解讀
- 洗錢防制法規研究
- 金融判決書分析

## 工作原則
1. **規劃先行**：使用 write_todos 工具規劃複雜任務
2. **引用為本**：所有事實陳述必須附帶來源引用
3. **多次檢索**：如初次檢索不足，應改寫查詢重試
4. **正式書寫**：使用繁體中文正式法律文體

## 引用格式
- 行內引用：[引用1]、[引用1、2]
- 引用清單：
  [1] 金管會裁罰書 - 玉山銀行洗錢防制 (2020-09-15)
      來源: data/documents/玉山銀行_洗錢防制裁罰_2020.txt

## 回答結構
1. 執行摘要（1-2 句）
2. 關鍵發現（要點列表，附引用）
3. 詳細分析
4. 信心評分與說明
5. 引用來源清單
"""

# 定義專業子代理
RAG_SUBAGENT = {
    "name": "rag_researcher",
    "description": "專門執行 RAG 檢索的子代理，可深度搜尋文件庫",
    "system_prompt": """你是 RAG 研究員，負責深度搜尋金融法律文件。

    工作流程：
    1. 分析查詢意圖
    2. 使用 semantic_search 進行語意搜尋
    3. 使用 keyword_search 補充關鍵字搜尋
    4. 彙整相關文件並評估相關性
    5. 返回最相關的文件摘要與引用
    """,
    "tools": [semantic_search, keyword_search],
    "model": "gpt-4o-mini",
}

LEGAL_ANALYZER_SUBAGENT = {
    "name": "legal_analyzer",
    "description": "專門分析法律文件的子代理，可解讀裁罰書與法規條文",
    "system_prompt": """你是法律分析專家，負責解讀金融法規與裁罰書。

    分析重點：
    1. 違規事實認定
    2. 適用法條與罰則
    3. 裁罰金額計算依據
    4. 前例比較分析
    5. 實務建議
    """,
    "tools": [semantic_search],
    "model": "gpt-4o-mini",
}

def create_finagent_deep_agent():
    """建立 FinAgent Deep Agent。"""

    agent = create_deep_agent(
        model="gpt-4o-mini",  # 或 "claude-sonnet-4-5-20250929"
        system_prompt=FINANCIAL_AGENT_PROMPT,
        tools=[semantic_search, keyword_search],
        middleware=[
            TodoListMiddleware(),
            SubAgentMiddleware(
                default_model="gpt-4o-mini",
                default_tools=[semantic_search, keyword_search],
                subagents=[RAG_SUBAGENT, LEGAL_ANALYZER_SUBAGENT],
            ),
            FilesystemMiddleware(),  # 可選：啟用檔案操作
            SummarizationMiddleware(),  # 自動摘要長對話
        ],
    )

    return agent

# 使用範例
async def run_research(query: str, session_id: str):
    """執行金融法律研究。"""
    agent = create_finagent_deep_agent()

    config = {"configurable": {"thread_id": session_id}}

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": query}]},
        config
    )

    return result
```

### 使用現有 LangGraph Graph 作為子代理

Deep Agents 支援將現有的 LangGraph Graph 作為子代理：

```python
from deepagents import CompiledSubAgent
from deepagents.middleware import SubAgentMiddleware
from finagent.agents.plan_execute.graph import create_plan_execute_graph

# 將現有 Plan-Execute Graph 包裝為子代理
plan_execute_graph = create_plan_execute_graph()

plan_execute_subagent = CompiledSubAgent(
    name="plan_execute_researcher",
    description="執行 Plan-and-Execute 研究流程，適合複雜多步驟查詢",
    runnable=plan_execute_graph
)

# 在 Deep Agent 中使用
agent = create_deep_agent(
    model="gpt-4o-mini",
    system_prompt=FINANCIAL_AGENT_PROMPT,
    middleware=[
        SubAgentMiddleware(
            default_model="gpt-4o-mini",
            subagents=[plan_execute_subagent],
        ),
    ],
)
```

### TodoListMiddleware 詳解

來自 [Deep Agents Middleware 文檔](https://docs.langchain.com/oss/python/deepagents/middleware)：

```python
from deepagents.middleware import TodoListMiddleware

# TodoListMiddleware 提供兩個工具：
# - write_todos: 寫入/更新任務清單
# - read_todos: 讀取當前任務清單

# Agent 會自動使用這些工具規劃任務
# 類似 Claude Code 的任務追蹤機制

# 自訂使用
middleware = TodoListMiddleware(
    system_prompt="在處理複雜查詢前，請先使用 write_todos 規劃研究步驟..."
)
```

### SubAgentMiddleware 詳解

```python
from deepagents.middleware import SubAgentMiddleware

# SubAgentMiddleware 提供 task 工具用於委派任務
# 每個子代理在隔離的上下文中執行

middleware = SubAgentMiddleware(
    default_model="gpt-4o-mini",
    default_tools=[],  # 所有子代理共享的工具
    default_middleware=[TodoListMiddleware()],  # 子代理也可有自己的 middleware
    subagents=[
        {
            "name": "specialist_name",
            "description": "子代理的專業描述",
            "system_prompt": "子代理的系統提示詞",
            "tools": [...],  # 子代理專用工具
            "model": "gpt-4o-mini",
            "middleware": [],  # 子代理專用 middleware
        }
    ],
)
```

### 遷移路徑

```
Phase 1: 基礎遷移
├── 安裝 deepagents
├── 建立 FinAgent Deep Agent
├── 整合現有 RAG 工具
└── 測試基本查詢

Phase 2: 子代理整合
├── 包裝現有 Plan-Execute Graph
├── 建立專業子代理 (RAG, Legal, Risk)
└── 測試子代理委派

Phase 3: 進階功能
├── 啟用 FilesystemMiddleware
├── 啟用 SummarizationMiddleware
├── 配置 Human-in-the-loop
└── 整合到 FastAPI 後端
```

### Deep Agents 遷移檢查清單

- [ ] 安裝 `deepagents` 套件
- [ ] 建立 `src/finagent/agents/deep_agent/` 目錄
- [ ] 實作 `financial_agent.py`
- [ ] 將 `RetrieverTool` 和 `HardSearchTool` 轉換為 `@tool` 函數
- [ ] 定義金融專業子代理
- [ ] 包裝現有 Plan-Execute Graph 為子代理
- [ ] 整合到 orchestrator.py
- [ ] 更新 API routes
- [ ] 測試端對端流程

---

## Phase 1: Memory & Checkpointer

### 目標
- 支援對話續談 (thread_id)
- 支援中斷恢復
- 支援 Human-in-the-loop

### 安裝依賴

```bash
uv add langgraph-checkpoint-sqlite
```

### 實作步驟

#### 1.1 建立 Checkpointer

**檔案:** `src/finagent/database/checkpoint_manager.py`

```python
"""LangGraph Checkpointer with SQLite persistence."""
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import aiosqlite

class CheckpointManager:
    """Manages LangGraph checkpointers for conversation persistence."""

    def __init__(self, db_path: str = "data/checkpoints.db"):
        self.db_path = db_path

    def get_sync_checkpointer(self) -> SqliteSaver:
        """Get synchronous checkpointer for CLI."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return SqliteSaver(conn)

    async def get_async_checkpointer(self) -> AsyncSqliteSaver:
        """Get async checkpointer for API."""
        conn = await aiosqlite.connect(self.db_path)
        return AsyncSqliteSaver(conn)
```

#### 1.2 修改 Graph 編譯

**檔案:** `src/finagent/agents/plan_execute/graph.py`

```python
# 現有代碼
workflow = StateGraph(PlanExecuteState)
# ... 添加節點和邊

# 新增: 使用 checkpointer 編譯
from finagent.database.checkpoint_manager import CheckpointManager

checkpoint_mgr = CheckpointManager()
checkpointer = checkpoint_mgr.get_sync_checkpointer()

graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"]  # 可選: 在特定節點前中斷
)
```

#### 1.3 使用 thread_id 調用

```python
# 配置 thread_id 以啟用記憶
config = {"configurable": {"thread_id": session_id}}

# 首次調用
result = await graph.ainvoke(initial_state, config)

# 後續調用 (同一 thread_id 會恢復狀態)
result = await graph.ainvoke({"messages": [follow_up_question]}, config)
```

#### 1.4 加入 Memory Store (可選進階功能)

```python
from langgraph.store.memory import InMemoryStore

# 建立記憶存儲
store = InMemoryStore()

# 編譯時加入
graph = workflow.compile(
    checkpointer=checkpointer,
    store=store
)

# 在節點中存取記憶
def my_node(state, config, store):
    # 讀取記憶
    namespace = ("user_memories", config["configurable"]["user_id"])
    memories = store.search(namespace)

    # 寫入記憶
    store.put(namespace, "preference", {"style": "formal"})
```

### 預期效果

- ✅ 支援對話續談 (`/chat` 模式)
- ✅ 查詢失敗可從上次狀態恢復
- ✅ 可查看歷史執行狀態 (time travel)
- ✅ 為 Human-in-the-loop 奠定基礎

---

## Phase 2: Subgraph 模組化

### 目標
- 將複雜邏輯拆分為獨立 subgraph
- 提高可測試性和重用性

### 現有架構問題

```
graph.py (monolithic)
├── plan_step (inline logic)
├── execute_step (inline tool calls)
├── replan_step (inline logic)
└── 所有邏輯混在一起
```

### 建議架構

```
plan_execute/
├── graph.py (主協調器)
├── subgraphs/
│   ├── planning_subgraph.py   # 規劃子圖
│   ├── execution_subgraph.py  # 執行子圖
│   └── rag_subgraph.py        # RAG 子圖
└── tools/
    ├── retriever.py
    └── search.py
```

### 實作範例: RAG Subgraph

**檔案:** `src/finagent/agents/plan_execute/subgraphs/rag_subgraph.py`

```python
"""RAG Subgraph for document retrieval and verification."""
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List

class RAGState(TypedDict):
    query: str
    documents: List[dict]
    relevance_scores: List[float]
    needs_more: bool

def retrieve(state: RAGState) -> dict:
    """Initial retrieval step."""
    # ... retrieval logic
    return {"documents": docs, "relevance_scores": scores}

def check_relevance(state: RAGState) -> dict:
    """Check if retrieved docs are relevant enough."""
    avg_score = sum(state["relevance_scores"]) / len(state["relevance_scores"])
    return {"needs_more": avg_score < 0.7}

def route_after_check(state: RAGState) -> str:
    """Route based on relevance check."""
    return "retrieve_more" if state["needs_more"] else "done"

# 建立 subgraph
rag_builder = StateGraph(RAGState)
rag_builder.add_node("retrieve", retrieve)
rag_builder.add_node("check_relevance", check_relevance)
rag_builder.add_node("retrieve_more", retrieve_more)

rag_builder.add_edge(START, "retrieve")
rag_builder.add_edge("retrieve", "check_relevance")
rag_builder.add_conditional_edges("check_relevance", route_after_check)
rag_builder.add_edge("retrieve_more", "check_relevance")

# 編譯為可重用的 subgraph
rag_subgraph = rag_builder.compile()
```

**在主 graph 中使用:**

```python
from .subgraphs.rag_subgraph import rag_subgraph

# 添加 subgraph 為節點
workflow.add_node("rag", rag_subgraph)
```

### 預期效果

- ✅ 各模組獨立測試
- ✅ 可在不同 workflow 重用
- ✅ 清晰的邏輯邊界
- ✅ 更容易維護和擴展

---

## Phase 3: RAG Agent 優化

### 目標
- 從單次 RAG 升級為 Agentic RAG
- 支援多步驟檢索和自我糾正

### RAG Chain vs RAG Agent

| 特性 | RAG Chain (現有) | RAG Agent (建議) |
|------|-----------------|------------------|
| 檢索次數 | 1 次 | 多次 (根據需要) |
| 判斷邏輯 | 無 | Agent 決定是否再查 |
| 適用場景 | 簡單查詢 | 複雜法律研究 |
| 延遲 | 低 | 中-高 |
| 準確度 | 中 | 高 |

### 實作: Self-RAG Pattern

```python
"""Self-correcting RAG Agent."""
from langgraph.graph import StateGraph, START, END

class SelfRAGState(TypedDict):
    question: str
    documents: List[Document]
    generation: str
    relevance_grade: str  # "relevant" | "not_relevant"
    hallucination_grade: str  # "grounded" | "not_grounded"
    answer_grade: str  # "useful" | "not_useful"

def grade_documents(state: SelfRAGState) -> dict:
    """Grade retrieved documents for relevance."""
    graded = []
    for doc in state["documents"]:
        score = grader.grade(state["question"], doc)
        if score >= 0.7:
            graded.append(doc)
    return {"documents": graded, "relevance_grade": "relevant" if graded else "not_relevant"}

def check_hallucination(state: SelfRAGState) -> dict:
    """Check if generation is grounded in documents."""
    is_grounded = hallucination_checker.check(state["generation"], state["documents"])
    return {"hallucination_grade": "grounded" if is_grounded else "not_grounded"}

def grade_answer(state: SelfRAGState) -> dict:
    """Grade if answer addresses the question."""
    is_useful = answer_grader.grade(state["question"], state["generation"])
    return {"answer_grade": "useful" if is_useful else "not_useful"}

# 條件路由
def route_after_grading(state: SelfRAGState) -> str:
    if state["relevance_grade"] == "not_relevant":
        return "rewrite_query"  # 改寫查詢重試
    return "generate"

def route_after_hallucination(state: SelfRAGState) -> str:
    if state["hallucination_grade"] == "not_grounded":
        return "generate"  # 重新生成
    return "grade_answer"

def route_final(state: SelfRAGState) -> str:
    if state["answer_grade"] == "not_useful":
        return "rewrite_query"  # 不夠好，重來
    return END

# 建立 Self-RAG 圖
self_rag = StateGraph(SelfRAGState)
self_rag.add_node("retrieve", retrieve)
self_rag.add_node("grade_documents", grade_documents)
self_rag.add_node("generate", generate)
self_rag.add_node("check_hallucination", check_hallucination)
self_rag.add_node("grade_answer", grade_answer)
self_rag.add_node("rewrite_query", rewrite_query)

self_rag.add_edge(START, "retrieve")
self_rag.add_edge("retrieve", "grade_documents")
self_rag.add_conditional_edges("grade_documents", route_after_grading)
self_rag.add_edge("generate", "check_hallucination")
self_rag.add_conditional_edges("check_hallucination", route_after_hallucination)
self_rag.add_conditional_edges("grade_answer", route_final)
self_rag.add_edge("rewrite_query", "retrieve")
```

### 預期效果

- ✅ 自動驗證文件相關性
- ✅ 自動檢測幻覺
- ✅ 答案品質把關
- ✅ 複雜查詢更準確

---

## Phase 4: Hierarchical Multi-Agent

### 目標
- 建立分層代理架構
- Supervisor 協調專業 Agent

### 架構設計

```
                    ┌─────────────────┐
                    │   Supervisor    │
                    │  (Top-level)    │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────┴─────┐     ┌──────┴──────┐    ┌──────┴──────┐
    │  Research │     │   Analysis  │    │   Report    │
    │  Supervisor│    │  Supervisor │    │  Generator  │
    └─────┬─────┘     └──────┬──────┘    └─────────────┘
          │                  │
    ┌─────┼─────┐      ┌─────┼─────┐
    │     │     │      │     │     │
   RAG  Search Web   Legal  Fine  Risk
   Agent Agent Agent  Agent Agent Agent
```

### 實作範例

```python
"""Hierarchical Agent Teams for Financial Legal Research."""
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# 各專業 Agent 定義
research_agents = {
    "rag_agent": create_rag_agent(),      # 文件檢索
    "search_agent": create_search_agent(), # 關鍵字搜尋
    "web_agent": create_web_agent(),       # 網路搜尋 (未來)
}

analysis_agents = {
    "legal_agent": create_legal_analyzer(),     # 法律分析
    "financial_agent": create_financial_agent(), # 財務分析
    "risk_agent": create_risk_assessor(),        # 風險評估
}

# Research Supervisor
def research_supervisor(state):
    """Coordinate research agents."""
    llm = ChatOpenAI(model="gpt-4o-mini")

    system_prompt = """你是研究團隊主管，負責協調：
    - rag_agent: 文件檢索專家
    - search_agent: 關鍵字搜尋專家

    根據查詢決定派遣哪個 agent，或回報 FINISH。"""

    # 使用 structured output 決定下一步
    response = llm.with_structured_output(RouterOutput).invoke([
        SystemMessage(content=system_prompt),
        *state["messages"]
    ])

    return {"next": response.next_agent}

# 建立 Research Team Subgraph
research_team = StateGraph(TeamState)
research_team.add_node("supervisor", research_supervisor)
research_team.add_node("rag_agent", research_agents["rag_agent"])
research_team.add_node("search_agent", research_agents["search_agent"])

research_team.add_edge(START, "supervisor")
research_team.add_conditional_edges("supervisor", lambda s: s["next"])
research_team.add_edge("rag_agent", "supervisor")
research_team.add_edge("search_agent", "supervisor")

# 頂層 Supervisor
def top_supervisor(state):
    """Top-level coordination."""
    # 決定派遣哪個團隊
    ...

# 主圖
main_graph = StateGraph(MainState)
main_graph.add_node("top_supervisor", top_supervisor)
main_graph.add_node("research_team", research_team.compile())
main_graph.add_node("analysis_team", analysis_team.compile())
main_graph.add_node("report_generator", report_generator)
```

### 預期效果

- ✅ 清晰的職責分工
- ✅ 可擴展新專業 Agent
- ✅ 複雜任務自動分解
- ✅ 團隊間協作

---

## 實作範例

### 完整 v1.2 Graph (含 Checkpointer)

```python
"""FinAgent v1.2 - Plan-and-Execute with Memory."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from typing import TypedDict, List, Annotated
from operator import add

class PlanExecuteState(TypedDict):
    messages: Annotated[List, add]
    plan: List[str]
    current_step: int
    results: List[dict]
    response: str

async def create_graph(db_path: str = "data/checkpoints.db"):
    """Create graph with async checkpointer."""

    # 建立 checkpointer
    import aiosqlite
    conn = await aiosqlite.connect(db_path)
    checkpointer = AsyncSqliteSaver(conn)

    # 建立 workflow
    workflow = StateGraph(PlanExecuteState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("replanner", replanner_node)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "replanner")
    workflow.add_conditional_edges(
        "replanner",
        should_continue,
        {"continue": "executor", "end": END}
    )

    # 編譯含 checkpointer
    return workflow.compile(checkpointer=checkpointer)

# 使用
async def run_query(query: str, session_id: str):
    graph = await create_graph()

    config = {"configurable": {"thread_id": session_id}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=query)]},
        config
    )

    return result
```

---

## 遷移檢查清單

### Phase 1: Checkpointer (v1.2)

- [ ] 安裝 `langgraph-checkpoint-sqlite`
- [ ] 建立 `checkpoint_manager.py`
- [ ] 修改 `graph.py` 加入 checkpointer
- [ ] 修改 API 傳入 `thread_id`
- [ ] 測試對話續談功能
- [ ] 測試中斷恢復功能

### Phase 2: Subgraph (v1.3)

- [ ] 建立 `subgraphs/` 目錄
- [ ] 抽取 RAG 邏輯為 `rag_subgraph.py`
- [ ] 抽取規劃邏輯為 `planning_subgraph.py`
- [ ] 修改主 graph 使用 subgraph
- [ ] 為各 subgraph 撰寫單元測試

### Phase 3: Agentic RAG (v1.4)

- [ ] 實作 Document Grader
- [ ] 實作 Hallucination Checker
- [ ] 實作 Answer Grader
- [ ] 實作 Query Rewriter
- [ ] 建立 Self-RAG 圖
- [ ] 整合到主 workflow

### Phase 4: Hierarchical (v2.0)

- [ ] 設計 Agent 分組
- [ ] 實作各專業 Agent
- [ ] 實作 Supervisor 邏輯
- [ ] 建立團隊 Subgraph
- [ ] 整合頂層協調

---

## 參考資源

### Deep Agents (推薦)
1. [Deep Agents GitHub](https://github.com/langchain-ai/deepagents) - 官方 Repository
2. [Deep Agents Blog](https://blog.langchain.com/deep-agents/) - 設計理念與架構
3. [Deep Agents Middleware Docs](https://docs.langchain.com/oss/python/deepagents/middleware) - Middleware 詳細文檔
4. [Deep Agents PyPI](https://pypi.org/project/deepagents/) - 套件資訊
5. [Deep Agents Quickstarts](https://github.com/langchain-ai/deepagents-quickstarts) - 範例專案

### LangGraph 核心
6. [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
7. [LangGraph Memory](https://langchain-ai.github.io/langgraph/concepts/memory/)
8. [LangGraph Subgraphs](https://langchain-ai.github.io/langgraph/concepts/low_level/#subgraphs)
9. [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
10. [LangGraph Multi-Agent](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)

---

## 總結

本升級計劃提供兩種路徑：

### 🌟 推薦方案：Deep Agents 重構

```
pip install deepagents
```

使用 [Deep Agents](https://github.com/langchain-ai/deepagents) 可一次獲得：
- ✅ 任務規劃 (TodoListMiddleware)
- ✅ 子代理委派 (SubAgentMiddleware)
- ✅ 檔案系統存取 (FilesystemMiddleware)
- ✅ 上下文管理 (SummarizationMiddleware)
- ✅ 狀態持久化 (內建 Checkpointer)
- ✅ Human-in-the-loop 支援

**這是最快達到 Claude Code 級功能的路徑。**

### 漸進式升級方案

如需保留現有架構並高度客製化：

| 自行實作 (現有) | LangGraph 內建 (建議) |
|----------------|---------------------|
| 自訂記憶邏輯 | Checkpointer + Store |
| 手動狀態恢復 | thread_id 自動恢復 |
| 單體式 graph | Subgraph 模組化 |
| 單次 RAG | Agentic RAG 多步驟 |
| 扁平化 Agent | Hierarchical Teams |

建議從 Phase 1 (Checkpointer) 開始，這是最低複雜度、最高價值的升級。

---

## 下一步行動

1. **評估 Deep Agents**：執行 `uv add deepagents` 並測試基本功能
2. **概念驗證**：建立簡單的 FinAgent Deep Agent 原型
3. **決定路徑**：根據 POC 結果選擇完整重構或漸進升級
4. **實作計劃**：按本文檔的檢查清單逐步執行
