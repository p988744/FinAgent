# FinAgent Web UI Specification

**Version:** 1.0.0
**Created:** 2025-11-17
**Status:** Planning Phase
**Target Release:** v0.1.0

---

## Overview

A modern web-based user interface for FinAgent that provides complete feature parity with the CLI, plus enhanced document management and visualization capabilities.

### Goals

1. **Full CLI Feature Parity** - All CLI commands accessible via web interface
2. **Config Management** - Visual configuration editor with validation
3. **Model Management** - LLM and embedding model configuration
4. **Document Wiki** - Auto-generated wiki from indexed documents
5. **Document Management** - Upload, version control, and pruning

### Target Users

- Legal researchers
- Financial analysts
- Compliance officers
- System administrators

---

## Technology Stack

### Frontend

```
Framework:     React 18+ with TypeScript
UI Library:    shadcn/ui (Tailwind CSS based)
State:         Zustand or React Query
Routing:       React Router v6
Build:         Vite
Charts:        Recharts or Chart.js
Markdown:      react-markdown with remark-gfm
Code Editor:   Monaco Editor (for config editing)
```

### Backend (Existing FastAPI + New Endpoints)

```
Framework:     FastAPI (existing)
Database:      SQLite (existing)
Vector DB:     Chroma (existing)
File Storage:  Local filesystem with metadata
WebSocket:     FastAPI WebSocket for real-time updates
```

### Project Structure

```
frontend/                    # New frontend directory
├── src/
│   ├── components/          # React components
│   │   ├── layout/          # Header, Sidebar, Footer
│   │   ├── query/           # Query interface
│   │   ├── config/          # Config management
│   │   ├── models/          # Model management
│   │   ├── documents/       # Document management
│   │   └── wiki/            # Document wiki
│   ├── pages/               # Page components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API client services
│   ├── stores/              # State management
│   ├── types/               # TypeScript types
│   └── utils/               # Utility functions
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js

src/finagent/api/routes/     # New API endpoints
├── config.py                # Config management API
├── models.py                # Model management API
├── documents.py             # Document management API
└── wiki.py                  # Document wiki API
```

---

## Feature Specifications

### 1. Query Interface (Full CLI Parity)

**Route:** `/query`

#### Features

- **Query Input**
  - Rich text input with Traditional Chinese support
  - Query history dropdown
  - Auto-save drafts
  - Query templates (common searches)

- **Results Display**
  - Formatted answer with markdown rendering
  - Collapsible sections (執行摘要, 關鍵發現, 詳細分析)
  - Citation highlighting with click-to-view
  - Confidence score visualization
  - **Real-time Process Monitoring Panel** (see section 1.1 below)

- **Export Options**
  - Export to Markdown
  - Export to JSON
  - Export to PDF (client-side generation)
  - Copy to clipboard

- **Query History**
  - List of past queries with timestamps
  - Filter by date range
  - Search within history
  - Re-run previous queries
  - Delete history entries

#### API Endpoints (New/Enhanced)

```python
# Existing
POST   /api/v1/research/query/sync     # Synchronous query
POST   /api/v1/research/query          # Async query
GET    /api/v1/research/query/{id}     # Get results

# New endpoints
GET    /api/v1/research/history        # Get query history
DELETE /api/v1/research/history/{id}   # Delete history entry
POST   /api/v1/research/templates      # Save query template
GET    /api/v1/research/templates      # List templates
WS     /api/v1/research/query/stream   # Real-time query progress
```

#### Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  FinAgent - Legal Research                           [User] │
├─────────────────────────────────────────────────────────────┤
│  [Query] [Documents] [Wiki] [Config] [Models]               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 請輸入查詢...                              [搜尋]│        │
│  │                                                  │        │
│  │ ________________________________________ [模板 ▼]│        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  [歷史查詢 ▼]  [匯出 ▼]  [清除]                              │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 執行摘要                                   [展開]│        │
│  │ ─────────────────────────────────────────────── │        │
│  │ 金管會於民國109年對玉山銀行開罰...              │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 關鍵發現                                        │        │
│  │ • 洗錢防制缺失 [引用1]                          │        │
│  │ • 內控機制不足 [引用2, 3]                       │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  信心評分: [████████░░] 高信心 (85%)                         │
│                                                              │
│  引用來源:                                                   │
│  [1] 金管會裁罰書 - 玉山銀行 (2020-09-15) [查看詳情]        │
│  [2] 內部控制規範 (2019-03-20) [查看詳情]                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 1.1 Real-Time Process Monitoring Panel

This is a critical feature that provides transparency into the multi-agent workflow. The panel shows three main components:

#### 1.1.1 Agent Workflow Steps (Pipeline Visualization)

**Component:** `<AgentWorkflowStepper />`

Displays the current position in the multi-agent pipeline:

```
Planning → Action → Validation → Answer
   ✓        ●          ○           ○
```

**States:**
- `○` Pending (gray)
- `●` In Progress (blue, animated pulse)
- `✓` Completed (green)
- `✗` Failed (red)

**Features:**
- Visual stepper/timeline component
- Elapsed time per step
- Current agent name and description
- Expandable details for each step
- Re-search iteration indicator (if applicable)

**Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│  Agent Pipeline                                    [收合 ▲] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [✓]──────[●]──────[○]──────[○]                             │
│  Planning   Action  Validation  Answer                       │
│  (2.3s)    (12.5s)                                          │
│                                                              │
│  Current: Action Agent - Retrieving relevant documents       │
│  Iteration: 1/3 | Strategy: strict (relevance ≥ 0.8)        │
│                                                              │
│  ▼ Step Details                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Planning Agent (Completed - 2.3s)                    │   │
│  │ • Analyzed query intent                              │   │
│  │ • Identified jurisdiction: 金管會                    │   │
│  │ • Generated 3 research tasks                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 1.1.2 Todo List Tracking

**Component:** `<TodoListPanel />`

Real-time task list showing what the agents are working on, synchronized with the backend's `AgentState.todos`.

**Todo Item States:**
- `pending` - Task not started
- `in_progress` - Currently executing (animated)
- `completed` - Task finished successfully
- `failed` - Task encountered error

**Features:**
- Live updates via WebSocket
- Checkmark animation on completion
- Progress percentage
- Task timing
- Collapsible completed tasks

**Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│  任務清單                                    進度: 2/5 (40%) │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [✓] 分析查詢意圖                                    (1.2s)  │
│  [✓] 識別管轄機構                                    (0.8s)  │
│  [●] 檢索相關文件                                    (8.3s)  │
│      └─ 正在搜尋: "玉山銀行 洗錢防制"                        │
│  [○] 驗證引用完整性                                          │
│  [○] 生成最終答案                                            │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│  Total Time: 10.3s | Estimated: ~30s remaining               │
└─────────────────────────────────────────────────────────────┘
```

#### 1.1.3 Tool/Agent Usage Log

**Component:** `<AgentActivityLog />`

Scrollable log showing detailed agent actions and tool invocations in real-time.

**Log Entry Types:**
- `agent_start` - Agent begins execution
- `agent_end` - Agent completes
- `tool_call` - Tool/function invoked
- `llm_call` - LLM API called
- `retrieval` - RAG document retrieval
- `validation` - Data validation step
- `error` - Error occurred

**Features:**
- Auto-scroll to latest entry
- Timestamp for each entry
- Color-coded by type
- Expandable details (JSON payload)
- Filter by type
- Search within log
- Export log as JSON

**Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│  活動日誌                     [Filter ▼] [Search] [Export]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  14:32:15.123  [Agent] Planning Agent started               │
│  14:32:16.456  [LLM]   GPT-4o-mini call (245 tokens)        │
│  14:32:17.789  [Agent] Planning Agent completed (2.3s)      │
│  14:32:17.890  [Agent] Action Agent started                 │
│  14:32:18.012  [Tool]  RAG Retriever invoked                │
│  14:32:18.234  [Query] "玉山銀行 洗錢防制 裁罰"              │
│  14:32:20.567  [Retrieval] Found 12 chunks (relevance ≥0.8) │
│  14:32:21.890  [LLM]   GPT-4o-mini call (1,234 tokens)      │
│  14:32:25.123  [Validation] Filtering chunks by relevance   │
│  14:32:26.456  [Result] 8 chunks passed threshold           │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│  [Auto-scroll ✓] | 12 entries | 156 tokens used | $0.0002   │
└─────────────────────────────────────────────────────────────┘
```

#### WebSocket Message Schema

```typescript
// WebSocket message types for real-time updates
interface WSMessage {
  type: 'step_update' | 'todo_update' | 'activity_log' | 'query_complete' | 'error';
  timestamp: string;
  payload: StepUpdate | TodoUpdate | ActivityLog | QueryResult | ErrorMessage;
}

interface StepUpdate {
  current_step: 'planning' | 'action' | 'validation' | 'answer';
  step_status: 'pending' | 'in_progress' | 'completed' | 'failed';
  elapsed_time_ms: number;
  iteration?: number;
  search_strategy?: string;
  details?: string;
}

interface TodoUpdate {
  todos: Array<{
    id: string;
    content: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    started_at?: string;
    completed_at?: string;
    elapsed_ms?: number;
  }>;
  progress_percent: number;
}

interface ActivityLog {
  level: 'info' | 'debug' | 'warning' | 'error';
  agent: string;
  action: string;
  message: string;
  details?: Record<string, any>;
  tokens_used?: number;
  cost_usd?: number;
}
```

#### Backend API Endpoints (New)

```python
# WebSocket endpoint for real-time updates
@router.websocket("/api/v1/research/query/stream/{query_id}")
async def query_stream(websocket: WebSocket, query_id: str):
    """
    Stream real-time updates for a query execution.

    Sends:
    - Step updates (agent pipeline progress)
    - Todo updates (task list status)
    - Activity logs (detailed agent actions)
    - Final result or error
    """
    await websocket.accept()

    # Create callback to send updates
    async def send_update(update_type: str, payload: dict):
        await websocket.send_json({
            "type": update_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        })

    # Process query with callbacks
    orchestrator = AgentOrchestrator(
        ui_callback=WebSocketUICallback(send_update)
    )

    try:
        result = await orchestrator.process_query(query)
        await send_update("query_complete", result.dict())
    except Exception as e:
        await send_update("error", {"message": str(e)})
    finally:
        await websocket.close()


# REST endpoint for querying logs after completion
GET /api/v1/research/query/{id}/logs          # Get all activity logs
GET /api/v1/research/query/{id}/steps         # Get step timing breakdown
GET /api/v1/research/query/{id}/todos         # Get final todo status
```

#### Complete Query Page Wireframe (with Monitoring Panel)

```
┌─────────────────────────────────────────────────────────────┐
│  FinAgent - Legal Research                           [User] │
├─────────────────────────────────────────────────────────────┤
│  [Query] [Documents] [Wiki] [Config] [Models]               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 請輸入查詢...                              [搜尋]│        │
│  │ 玉山銀行洗錢防制裁罰________________________________│        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  ┌───────────────────────┬─────────────────────────┐        │
│  │                       │                         │        │
│  │  RESULT PANEL         │  MONITORING PANEL       │        │
│  │  (Left 60%)           │  (Right 40%)            │        │
│  │                       │                         │        │
│  │  執行摘要             │  Agent Pipeline         │        │
│  │  ─────────────        │  [✓]─[●]─[○]─[○]       │        │
│  │  金管會於民國109年... │  Planning→Action...     │        │
│  │                       │                         │        │
│  │  關鍵發現             │  任務清單 (40%)         │        │
│  │  • 洗錢防制 [引用1]   │  [✓] 分析查詢意圖       │        │
│  │  • 內控機制 [引用2]   │  [●] 檢索相關文件       │        │
│  │                       │  [○] 驗證引用...        │        │
│  │  詳細分析             │                         │        │
│  │  金管會於...          │  活動日誌               │        │
│  │                       │  14:32:15 [Agent]...   │        │
│  │  信心評分: 高信心     │  14:32:18 [Tool]...    │        │
│  │  [████████░░] 85%     │  14:32:20 [Retrieval]  │        │
│  │                       │                         │        │
│  │  引用來源             │  Tokens: 156 | $0.0002  │        │
│  │  [1] 金管會裁罰書...  │                         │        │
│  │                       │                         │        │
│  └───────────────────────┴─────────────────────────┘        │
│                                                              │
│  [歷史查詢 ▼]  [匯出 ▼]  [清除]  [Toggle Monitoring Panel]  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### React Component Structure

```typescript
// Query page components
<QueryPage>
  <QueryInput />
  <div className="flex">
    <ResultPanel className="w-3/5">
      <ExecutiveSummary />
      <KeyFindings />
      <DetailedAnalysis />
      <ConfidenceScore />
      <Citations />
    </ResultPanel>

    <MonitoringPanel className="w-2/5">
      <AgentWorkflowStepper />
      <TodoListPanel />
      <AgentActivityLog />
      <CostTracker />
    </MonitoringPanel>
  </div>
  <QueryActions />
</QueryPage>
```

#### User Preferences

```typescript
// User can customize monitoring panel
interface MonitoringPreferences {
  showMonitoringPanel: boolean;      // Toggle entire panel
  autoCollapseCompleted: boolean;    // Auto-collapse completed todos
  logLevel: 'info' | 'debug' | 'all'; // Filter log verbosity
  showTokenCost: boolean;            // Show token/cost tracking
  panelPosition: 'right' | 'bottom'; // Panel layout
  autoScroll: boolean;               // Auto-scroll logs
}
```

---

### 2. Configuration Management

**Route:** `/config`

#### Features

- **Settings Editor**
  - Category-based organization (LLM, Embedding, Vector DB, General)
  - Form-based editing with validation
  - JSON/YAML view toggle
  - Real-time validation feedback
  - Undo/Redo support

- **Preset Management**
  - Save current config as preset
  - Load preset with one click
  - Compare presets side-by-side
  - Import/Export presets (JSON)
  - Active preset indicator

- **Environment Variables**
  - View current .env values (masked secrets)
  - Override .env from UI
  - Reload configuration

#### API Endpoints

```python
# Settings
GET    /api/v1/config/settings              # Get all settings
PUT    /api/v1/config/settings/{key}        # Update setting
POST   /api/v1/config/settings/bulk         # Bulk update
GET    /api/v1/config/settings/categories   # Get by category
POST   /api/v1/config/reload                # Reload from .env

# Presets
GET    /api/v1/config/presets               # List all presets
POST   /api/v1/config/presets               # Create preset
PUT    /api/v1/config/presets/{id}          # Update preset
DELETE /api/v1/config/presets/{id}          # Delete preset
POST   /api/v1/config/presets/{id}/activate # Activate preset
GET    /api/v1/config/presets/active        # Get active preset
POST   /api/v1/config/presets/import        # Import preset
GET    /api/v1/config/presets/{id}/export   # Export preset
```

#### Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  Configuration Management                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Settings] [Presets] [Environment]                          │
│                                                              │
│  ┌─────────────────┬───────────────────────────────────┐    │
│  │ Categories      │  LLM Configuration                 │    │
│  │ ─────────────   │  ──────────────────────────────    │    │
│  │ > LLM          │                                     │    │
│  │   Embedding    │  API Key: [sk-proj-***...***]      │    │
│  │   Vector DB    │  Base URL: [________________]       │    │
│  │   General      │  Model: [gpt-4o-mini        ▼]     │    │
│  │                │  Temperature: [0.0____] [0.0-2.0]   │    │
│  │                │                                     │    │
│  │ Active Preset: │  ┌─────────────────────────────┐    │    │
│  │ [Production ✓] │  │ Validation: ✓ All valid     │    │    │
│  │                │  └─────────────────────────────┘    │    │
│  │ [Save Preset]  │                                     │    │
│  │ [Load Preset]  │  [Apply Changes] [Reset] [Reload]   │    │
│  └─────────────────┴───────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 3. Model Management

**Route:** `/models`

#### Features

- **LLM Configuration**
  - Provider selection (OpenAI, Ollama, Custom)
  - Model picker with descriptions
  - Connection testing
  - Performance metrics (tokens/sec, cost)
  - Temperature presets (deterministic, balanced, creative)

- **Embedding Configuration**
  - Model selection
  - Dimension display
  - API endpoint configuration
  - Test embedding generation

- **Model Comparison**
  - Side-by-side comparison
  - Cost calculator
  - Performance benchmarks
  - Recommendations based on use case

- **Usage Statistics**
  - Token usage over time
  - Cost breakdown by model
  - Query performance metrics
  - Model switching history

#### API Endpoints

```python
# LLM Models
GET    /api/v1/models/llm/available       # List available models
POST   /api/v1/models/llm/test            # Test LLM connection
GET    /api/v1/models/llm/active          # Get active LLM config
PUT    /api/v1/models/llm/active          # Update active LLM

# Embedding Models
GET    /api/v1/models/embedding/available # List embedding models
POST   /api/v1/models/embedding/test      # Test embedding
GET    /api/v1/models/embedding/active    # Get active embedding config

# Statistics
GET    /api/v1/models/stats               # Usage statistics
GET    /api/v1/models/stats/costs         # Cost breakdown
GET    /api/v1/models/stats/performance   # Performance metrics
```

#### Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  Model Management                                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [LLM] [Embedding] [Statistics] [Compare]                    │
│                                                              │
│  LLM Provider: [OpenAI ▼]                                   │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ Available Models                                 │        │
│  │ ─────────────────────────────────────────────── │        │
│  │ ○ gpt-4o          $15/$60 per 1M tokens         │        │
│  │   Most capable model                            │        │
│  │                                                  │        │
│  │ ● gpt-4o-mini     $0.15/$0.60 per 1M tokens ✓  │        │
│  │   Best price-performance ratio (Recommended)    │        │
│  │                                                  │        │
│  │ ○ gpt-3.5-turbo   $0.50/$1.50 per 1M tokens    │        │
│  │   Fast and economical                           │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  Temperature: [Deterministic ▼] (0.0)                        │
│                                                              │
│  [Test Connection]  Status: ✓ Connected                      │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ This Month's Usage                               │        │
│  │ Tokens: 45,230 | Cost: $0.0068 | Queries: 32    │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Document Wiki

**Route:** `/wiki`

#### Features

- **Auto-Generated Wiki**
  - Document categorization by type
  - Entity extraction (banks, dates, violation types)
  - Timeline view of penalties
  - Relationship graph visualization
  - Full-text search across documents

- **Document Viewer**
  - Markdown rendering of document content
  - Syntax highlighting for legal terms
  - Cross-reference links
  - Annotation support
  - Version history

- **Knowledge Graph**
  - Interactive graph of entities
  - Bank → Violations → Penalties relationships
  - Date-based filtering
  - Export graph data

- **Search & Filter**
  - Full-text search
  - Filter by bank name
  - Filter by violation type
  - Filter by date range
  - Filter by penalty amount

#### API Endpoints

```python
# Wiki Pages
GET    /api/v1/wiki/pages                  # List all wiki pages
GET    /api/v1/wiki/pages/{id}             # Get page content
GET    /api/v1/wiki/pages/{id}/history     # Page version history

# Categories & Tags
GET    /api/v1/wiki/categories             # List categories
GET    /api/v1/wiki/tags                   # List all tags
GET    /api/v1/wiki/entities               # List extracted entities

# Search
POST   /api/v1/wiki/search                 # Full-text search
GET    /api/v1/wiki/timeline               # Timeline view

# Knowledge Graph
GET    /api/v1/wiki/graph                  # Get graph data
GET    /api/v1/wiki/graph/relationships    # Entity relationships
```

#### Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  Document Wiki                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Browse] [Timeline] [Graph] [Search]                        │
│                                                              │
│  Search: [______________________] [搜尋]                     │
│                                                              │
│  Filters:                                                    │
│  Bank: [All ▼]  Type: [All ▼]  Date: [2020-01-01] to [___] │
│                                                              │
│  ┌─────────────────┬───────────────────────────────────┐    │
│  │ Categories      │  玉山銀行洗錢防制裁罰案           │    │
│  │ ─────────────   │  ──────────────────────────────    │    │
│  │ > 裁罰案件      │                                     │    │
│  │   > 玉山銀行    │  裁罰日期: 民國109年9月15日        │    │
│  │   > 國泰銀行    │  裁罰金額: 新台幣500萬元           │    │
│  │   > 中信銀行    │  違規類型: 洗錢防制                │    │
│  │ > 判決書        │                                     │    │
│  │ > 法規          │  ## 裁罰內容                        │    │
│  │                 │                                     │    │
│  │ Tags:           │  金管會於民國109年9月15日對玉山    │    │
│  │ [洗錢防制]      │  商業銀行股份有限公司開罰500萬元   │    │
│  │ [內線交易]      │  ，主要違規事項如下：              │    │
│  │ [資訊揭露]      │                                     │    │
│  │                 │  1. 客戶身份辨識程序不完善         │    │
│  │                 │  2. 可疑交易通報機制缺失           │    │
│  │                 │                                     │    │
│  │                 │  相關文件: [引用1] [引用2]         │    │
│  └─────────────────┴───────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Document Management

**Route:** `/documents`

#### Features

- **Upload Documents**
  - Drag-and-drop file upload
  - Batch upload support
  - Format validation (TXT, PDF, HTML, DOCX)
  - Progress indicator
  - Metadata extraction preview

- **Version Control**
  - Upload new version of existing document
  - Version comparison (diff view)
  - Rollback to previous version
  - Version notes/changelog

- **Document Operations**
  - Rename documents
  - Move to different categories
  - Add/edit metadata
  - Tag management
  - Bulk operations

- **Indexing Management**
  - Index status per document
  - Reindex selected documents
  - Reindex all documents
  - Clear and rebuild index
  - Index statistics

- **Pruning & Removal**
  - Remove document from index only
  - Delete document completely
  - Archive old documents
  - Bulk deletion with confirmation
  - Impact analysis (show affected queries)

#### API Endpoints

```python
# Document CRUD
GET    /api/v1/documents                   # List all documents
POST   /api/v1/documents/upload            # Upload new document
GET    /api/v1/documents/{id}              # Get document details
PUT    /api/v1/documents/{id}              # Update document metadata
DELETE /api/v1/documents/{id}              # Delete document

# Versioning
POST   /api/v1/documents/{id}/versions     # Upload new version
GET    /api/v1/documents/{id}/versions     # List versions
GET    /api/v1/documents/{id}/versions/{v} # Get specific version
POST   /api/v1/documents/{id}/rollback     # Rollback to version

# Indexing
POST   /api/v1/documents/reindex           # Reindex all
POST   /api/v1/documents/{id}/reindex      # Reindex single
POST   /api/v1/documents/clear-index       # Clear all indexes
GET    /api/v1/documents/index-status      # Index statistics

# Batch Operations
POST   /api/v1/documents/batch/delete      # Batch delete
POST   /api/v1/documents/batch/reindex     # Batch reindex
POST   /api/v1/documents/batch/tag         # Batch add tags
```

#### Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  Document Management                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Upload] [Reindex All] [Clear Index] [Refresh]             │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Drop files here to upload                       │        │
│  │  or [Browse Files]                               │        │
│  │  Supported: TXT, PDF, HTML, DOCX                 │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  Documents (494 total, 2,858 chunks indexed)                 │
│                                                              │
│  Search: [_______________] Category: [All ▼] Status: [All ▼]│
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │ [☐] Document Name          Category   Status     │        │
│  │ ─────────────────────────────────────────────── │        │
│  │ [☐] 玉山銀行_洗錢防制_2020  裁罰案件   ✓ Indexed │        │
│  │     Version: 1.0 | Chunks: 12 | Updated: 2h ago │        │
│  │     [View] [Edit] [Reindex] [Delete]            │        │
│  │                                                  │        │
│  │ [☐] 國泰銀行_內控缺失_2021  裁罰案件   ✓ Indexed │        │
│  │     Version: 2.1 | Chunks: 8 | Updated: 1d ago  │        │
│  │     [View] [Edit] [Reindex] [Delete] [History]  │        │
│  │                                                  │        │
│  │ [☐] 中信銀行_資訊安全_2022  裁罰案件   ⚠ Pending │        │
│  │     Version: 1.0 | Chunks: 0 | Not indexed yet  │        │
│  │     [View] [Edit] [Index Now] [Delete]          │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  Selected: 0 documents  [Batch Reindex] [Batch Delete]       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)

**Backend:**
- [ ] Set up new API routes structure
- [ ] Implement config management endpoints
- [ ] Implement document management endpoints
- [ ] Add WebSocket support for real-time updates
- [ ] Database schema updates for versioning

**Frontend:**
- [ ] Initialize React + TypeScript + Vite project
- [ ] Set up shadcn/ui components
- [ ] Create layout structure (Header, Sidebar)
- [ ] Implement API client service
- [ ] Set up routing

### Phase 2: Query Interface (Week 2-3)

- [ ] Query input component with validation
- [ ] Results display with markdown rendering
- [ ] Citation highlighting and navigation
- [ ] Query history management
- [ ] Export functionality (Markdown, JSON)
- [ ] WebSocket integration for real-time status

### Phase 3: Configuration & Models (Week 3-4)

- [ ] Settings editor with categories
- [ ] Preset management UI
- [ ] Model selection interface
- [ ] Connection testing
- [ ] Usage statistics dashboard
- [ ] Cost calculator

### Phase 4: Document Management (Week 4-5)

- [ ] File upload with drag-and-drop
- [ ] Document list with filtering
- [ ] Version control UI
- [ ] Batch operations
- [ ] Indexing controls
- [ ] Progress indicators

### Phase 5: Document Wiki (Week 5-6)

- [ ] Wiki page generator from metadata
- [ ] Category/tag browser
- [ ] Full-text search
- [ ] Timeline visualization
- [ ] Knowledge graph (basic)
- [ ] Entity relationship viewer

### Phase 6: Polish & Testing (Week 6-7)

- [ ] Error handling and user feedback
- [ ] Loading states and skeletons
- [ ] Responsive design
- [ ] Accessibility (a11y)
- [ ] Performance optimization
- [ ] End-to-end testing
- [ ] Documentation

---

## Database Schema Updates

### New Tables

```sql
-- Document versions
CREATE TABLE document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    checksum TEXT,
    changelog TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    UNIQUE(document_id, version)
);

-- Wiki pages (auto-generated)
CREATE TABLE wiki_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    metadata JSON,
    category TEXT,
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Entity extractions
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    entity_type TEXT NOT NULL, -- bank, date, violation, amount
    entity_value TEXT NOT NULL,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query templates
CREATE TABLE query_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template TEXT NOT NULL,
    description TEXT,
    category TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Security Considerations

1. **Authentication** (Future)
   - JWT-based authentication
   - Role-based access control
   - Session management

2. **File Upload Security**
   - File type validation
   - Size limits (configurable)
   - Virus scanning (optional)
   - Secure file storage

3. **API Security**
   - Rate limiting
   - Input validation
   - CORS configuration
   - SQL injection prevention

4. **Data Protection**
   - API key masking in UI
   - Secure storage of credentials
   - Audit logging

---

## Performance Considerations

1. **Frontend**
   - Code splitting and lazy loading
   - Virtual scrolling for large lists
   - Debounced search inputs
   - Optimistic UI updates

2. **Backend**
   - Pagination for all list endpoints
   - Caching frequently accessed data
   - Background task processing
   - Database query optimization

3. **File Operations**
   - Chunked file uploads
   - Async document processing
   - Progress streaming via WebSocket
   - Index optimization

---

## Success Metrics

1. **Usability**
   - Time to complete query: < 45 seconds
   - Document upload success rate: > 99%
   - Config change application: < 5 seconds

2. **Performance**
   - Page load time: < 2 seconds
   - API response time: < 500ms (excluding LLM calls)
   - File upload speed: > 10MB/s

3. **Reliability**
   - System uptime: > 99.9%
   - Zero data loss for documents
   - Successful index rebuilds: 100%

---

## Future Enhancements

1. **Collaboration Features**
   - Multi-user support
   - Shared query templates
   - Document annotations
   - Comment system

2. **Advanced Analytics**
   - Custom dashboards
   - Report generation
   - Trend analysis
   - Predictive insights

3. **Integration**
   - Export to legal databases
   - API for third-party tools
   - Webhook notifications
   - Email reports

4. **AI Enhancements**
   - Query suggestions
   - Auto-categorization
   - Anomaly detection
   - Citation verification

---

## Development Guidelines

### Code Standards

- **TypeScript**: Strict mode enabled
- **React**: Functional components with hooks
- **Styling**: Tailwind CSS with shadcn/ui
- **Testing**: Jest + React Testing Library
- **Linting**: ESLint + Prettier
- **Git**: Conventional commits

### API Design

- RESTful conventions
- Consistent error responses
- Pagination with cursor-based navigation
- JSON:API-like structure
- OpenAPI documentation

### Documentation

- Component storybook
- API endpoint documentation
- User guides (Traditional Chinese)
- Developer setup guide
- Deployment instructions

---

## Appendix

### Dependencies (Frontend)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.x",
    "@tanstack/react-query": "^5.x",
    "zustand": "^4.x",
    "axios": "^1.x",
    "react-markdown": "^9.x",
    "remark-gfm": "^4.x",
    "recharts": "^2.x",
    "@monaco-editor/react": "^4.x",
    "date-fns": "^3.x",
    "lucide-react": "^0.x"
  },
  "devDependencies": {
    "typescript": "^5.x",
    "vite": "^5.x",
    "@vitejs/plugin-react": "^4.x",
    "tailwindcss": "^3.x",
    "postcss": "^8.x",
    "autoprefixer": "^10.x",
    "eslint": "^8.x",
    "prettier": "^3.x"
  }
}
```

### Dependencies (Backend - Additional)

```python
# pyproject.toml additions
dependencies = [
    # Existing...
    "python-multipart",  # File uploads
    "aiofiles",          # Async file operations
    "websockets",        # WebSocket support
]
```

---

**Next Steps:**
1. Review and approve this specification
2. Create GitHub issues for each phase
3. Set up frontend project structure
4. Begin Phase 1 implementation

---

*Created: 2025-11-17*
*Author: Claude Code*
*Status: Ready for Review*
