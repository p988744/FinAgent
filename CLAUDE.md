# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinAgent is a **Financial Legal Research Agent System** (金融法律研究代理系統) specialized for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan's financial sector. The system uses a multi-agent architecture with LangGraph orchestration and RAG (Retrieval-Augmented Generation) for precise legal research with formal citations.

**Target Region:** Taiwan (繁體中文)
**Domain:** Financial law, banking penalties, regulatory enforcement, legal precedents
**Status:** v1.1.0 (release/v1.1) - Plan-and-Execute agent with LangGraph
**Architecture:** Python backend + React frontend, LangGraph multi-agent workflows, SQLite + Chroma vector DB

**Latest Release:** v1.1.0 "Strategic Planner"
- Plan-and-Execute workflow with Planner, Executor, Replanner agents
- Frontend toggle for workflow selection
- Retry logic with exponential backoff
- LangChain v1.0 compliant (StateGraph, LCEL, BaseTool)

## Development Commands

### Setup and Installation
```bash
# Backend setup
cd backend
uv sync

# Frontend setup
cd frontend
npm install

# Start backend (port 8000)
cd backend
uv run uvicorn finagent.main:app --reload --port 8000

# Start frontend (port 3000)
cd frontend
npm run dev

# CLI mode (legacy)
uv run finagent
uv run finagent query "玉山銀行洗錢防制裁罰"

# Reindex documents
uv run finagent reindex --skip-init    # Fast mode
uv run finagent reindex                 # Full mode with LLM
uv run finagent reindex --clear --yes   # Clear and rebuild
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_database.py

# Run with coverage
uv run pytest --cov=src/finagent --cov-report=html

# Run unit tests only
uv run pytest -m unit

# Run integration tests only
uv run pytest -m integration

# Database tests
uv run python tests/test_database.py
```

### Code Quality
```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

### Git Workflow
```bash
# Development branch
git checkout develop

# Create feature branch
git checkout -b feature/my-feature

# Commit with conventional commits
git commit -m "feat: add new feature"
```

## Core Architecture

### Documentation Structure

Before implementing features, consult these guides:

1. **[V1_1_RELEASE_PLAN.md](V1_1_RELEASE_PLAN.md)** - Current release status, gaps, implementation roadmap
2. **[PROJECT_SPEC.md](PROJECT_SPEC.md)** - Technical specifications
3. **[PROJECT_VISION.md](PROJECT_VISION.md)** - Product vision and roadmap

**Archived documentation** (in `.archive/session-docs-2025-11-25/`):
- Implementation guides, code reviews, test results from v1.1 development

### Multi-Agent LangGraph Workflows

**Two workflows available (user-selectable in frontend):**

#### 1. V1.0 Workflow (Legacy - 4 agents)
```
User Query → Planning Agent → Action Agent → Validation Agent → Answer Agent → Response
                    ↓              ↓              ↓                    ↓
                  Tasks       RAG Retrieval   Citations           Synthesis
```

**Agents:**
- **Planning Agent** ([planning_agent.py](src/finagent/agents/planning_agent.py)) - Query decomposition
- **Action Agent** ([action_agent.py](src/finagent/agents/action_agent.py)) - RAG retrieval (0.8 threshold)
- **Validation Agent** ([validation_agent.py](src/finagent/agents/validation_agent.py)) - Citation integrity
- **Answer Agent** ([answer_agent.py](src/finagent/agents/answer_agent.py)) - LLM synthesis (GPT-4o-mini)

#### 2. V1.1 Plan-and-Execute Workflow ⭐ **NEW** (3 agents)
```
User Query → Planner → Executor → Replanner → [loop or END]
                ↓         ↓          ↓
              Plan     Execute    Replan/Respond
```

**Location:** [src/finagent/agents/plan_execute/](src/finagent/agents/plan_execute/)

**Agents:**
- **PlannerAgent** ([planner.py](src/finagent/agents/plan_execute/planner.py)) - Creates research plan with tasks
- **ExecutorAgent** ([executor.py](src/finagent/agents/plan_execute/executor.py)) - Executes tasks using tools
- **ReplannerAgent** ([replanner.py](src/finagent/agents/plan_execute/replanner.py)) - Reviews progress, replans or responds

**Tools** (in [src/finagent/tools/](src/finagent/tools/)):
- **RetrieverTool** ([retriever.py](src/finagent/tools/retriever.py)) - Semantic vector search
- **HardSearchTool** ([search.py](src/finagent/tools/search.py)) - Exact keyword matching
- **HybridRetrieverTool** ([hybrid_retriever.py](src/finagent/tools/hybrid_retriever.py)) - BM25 + Vector (60%/40%)

**Features:**
- LangChain v1.0 compliant (StateGraph, LCEL, @retry decorator)
- Retry logic with exponential backoff (3 attempts, 4-10s wait)
- Dynamic replanning based on intermediate results
- Robust JSON parsing with fallback

**Orchestrator** ([orchestrator.py](src/finagent/agents/orchestrator.py))
- Routes to v1.0 or v1.1 workflow based on frontend selection
- Manages state transitions
- Handles fallback when RAG unavailable

### Database Layer (SQLite)

**Location:** `./data/finagent.db`

**Tables:**
1. **settings** - Application settings with categories (llm, embedding, vector_db)
2. **model_configs** - Saved LLM configuration presets with active state tracking
3. **history** - Query history with costs, tokens, and performance metrics (schema ready, logging pending)

**Key Files:**
- [database/db.py](src/finagent/database/db.py) - Full CRUD operations with context managers
- [database/models.py](src/finagent/database/models.py) - Pydantic models for type safety
- [database/schema.sql](src/finagent/database/schema.sql) - Schema with triggers for single active config enforcement
- [config_manager.py](src/finagent/config_manager.py) - High-level API with auto-init from .env

**Configuration Priority:**
1. Active model_config (database) - Highest priority
2. Settings table (database)
3. .env file - Fallback

### RAG Pipeline

**Document Processing Flow:**
```
TXT Documents → Load → Chunk → Embed → Index → Retrieve → Cite
                  ↓       ↓       ↓       ↓        ↓        ↓
              Metadata  Smart  OpenAI  Chroma  Semantic   Taiwan
                       512/128  API             Search    Citations
```

**Key Files:**
- [loader.py](src/finagent/document_processing/loader.py) - Document loading with metadata extraction
- [chunker.py](src/finagent/document_processing/chunker.py) - Paragraph-aware chunking (512 tokens, 128 overlap)
- [embeddings.py](src/finagent/document_processing/embeddings.py) - OpenAI text-embedding-3-small
- [indexer.py](src/finagent/document_processing/indexer.py) - Chroma vector DB indexing
- [retriever.py](src/finagent/document_processing/retriever.py) - Semantic search with relevance filtering

**Current Index:**
- 494 documents indexed
- 2,858 vector chunks
- text-embedding-3-small (1536 dimensions)
- Collection: "legal_documents"

### CLI Interface

**Entry Point:** [cli/main.py](src/finagent/cli/main.py) → [cli/repl.py](src/finagent/cli/repl.py)

**Commands:**
- `/query <query>` - Execute legal research query
- `/init [--reindex]` - Initialize/rebuild document index
- `/config [subcommand]` - Configuration management
  - `/config` - Show current configuration
  - `/config llm` - Interactive LLM configuration wizard
  - `/config save <name>` - Save configuration preset
  - `/config load <id>` - Load configuration preset
  - `/config list [llm|embedding]` - List saved presets
  - `/config delete <id>` - Delete preset
  - `/config reload` - Reload from .env and model_config.yml
- `/history` - View query history (pending)
- `/help` - Show all commands
- `/clear` - Clear screen
- `/exit` - Exit CLI

**Key Files:**
- [cli/commands/config.py](src/finagent/cli/commands/config.py) - Configuration management with database integration
- [cli/commands/query.py](src/finagent/cli/commands/query.py) - Query execution and orchestrator integration
- [cli/commands/init.py](src/finagent/cli/commands/init.py) - Document indexing
- [cli/formatters/answer.py](src/finagent/cli/formatters/answer.py) - Rich terminal output formatting

## Configuration System

### Unified OpenAI-Compatible API

Supports OpenAI, Ollama, and custom endpoints via unified configuration:

```bash
# OpenAI (default)
LLM_API_KEY=sk-proj-xxx
LLM_BASE_URL=                    # Empty = OpenAI
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Ollama (local)
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
```

### model_config.yml

**Purpose:** Provides model choices for UI selection (NOT stored in database)

**Sections:**
- `openai_chat_models` - Available OpenAI LLM models
- `openai_embedding_models` - Available embedding models
- `local_llm_presets` - Pre-configured local LLM settings
- `temperature_presets` - Temperature options (deterministic: 0.0, balanced: 0.3, creative: 0.7)

**Reload:** Use `/config reload` to apply changes

## Taiwan-Specific Implementation

### Regulatory Bodies
- **金管會 (FSC)** - Financial Supervisory Commission
  - Primary target for banking penalties
  - Document format: 金管銀法字第○○○○○○○○○○號
- **中央銀行 (CBC)** - Central Bank of Taiwan
- **公平會 (FTC)** - Fair Trade Commission

### Legal Citation Format

**In-Text Citations:**
- `[引用1]` - First citation
- `[引用1，第3頁]` - With page number
- `[引用1、2、3]` - Multiple sources

**Reference Format:**
```
[1] 金管會裁罰書 - 玉山銀行洗錢防制 (2020-09-15)
    來源: data/documents/玉山銀行_洗錢防制裁罰_2020.txt
```

### NLP Processing
- **Jieba** - Traditional Chinese word segmentation
- Full-width/half-width number conversion
- ROC (民國) calendar format support
- Traditional Chinese-optimized embeddings

### Answer Structure

```
執行摘要
[1-2 sentence summary]

關鍵發現
• Finding 1 [引用1]
• Finding 2 [引用2、3]

詳細分析
[Comprehensive analysis with citations]

信心評分: 高信心/中信心/低信心
[Explanation]

引用來源
[1] Source details...
```

## Key Data Models

Located in [src/finagent/models/](src/finagent/models/):

- **Query** ([queries.py](src/finagent/models/queries.py)) - User query with metadata
- **LegalAnswer** ([answers.py](src/finagent/models/answers.py)) - Structured answer with confidence level
- **LegalCitation** ([citations.py](src/finagent/models/citations.py)) - Formal citations with authority levels
- **DocumentMetadata** ([documents.py](src/finagent/models/documents.py)) - Document metadata
- **AgentState** ([agents/state.py](src/finagent/agents/state.py)) - LangGraph workflow state

## Important Implementation Notes

### LangChain v1.0 Standards (CRITICAL)
1. **Always use StateGraph** - NOT AgentExecutor (deprecated)
2. **Always use LCEL** - `prompt | llm | parser` NOT LLMChain
3. **Always use BaseTool** - With Pydantic args_schema
4. **Always use .ainvoke()** - NOT .arun() or .acall() (deprecated)
5. **Always use @retry decorator** - For LLM calls with exponential backoff
6. **Reference existing code** - See [src/finagent/agents/plan_execute/](src/finagent/agents/plan_execute/) for examples

### Domain-Specific Rules
7. **Citation Integrity**: Every factual statement MUST have a citation to a verifiable source
8. **Source Hierarchy**: Prefer primary sources (official documents) over secondary (news)
9. **Document Size**: Legal documents are 50-200 pages; RAG is REQUIRED, not optional
10. **Entity Resolution**: Use official legal names (e.g., "玉山商業銀行股份有限公司" not "玉山")
11. **Date Format**: Use ROC (民國) calendar for Taiwan documents
12. **Chunking Strategy**: Preserve document structure (sections/chapters) during chunking
13. **Traditional Chinese**: All system prompts and responses in 繁體中文
14. **Formal Tone**: Use formal legal writing style with passive voice

### System Rules
15. **Database Triggers**: SQLite triggers enforce single active config per type - don't bypass
16. **Configuration Presets**: Use ConfigManager API, not direct database access
17. **Test Scripts Location**: scripts/ or .archive/, NEVER project root (see .gitignore)
18. **Tool Sharing**: Extract to src/finagent/tools/ for reuse across workflows

## Key Terminology (繁體中文)

- **民國** - Republic of China calendar (民國109年 = 2020)
- **裁罰書** - Regulatory penalty/enforcement document
- **判決書** - Court judgment document
- **案號** - Case number
- **主文** - Main text/conclusion of judgment
- **事實** - Facts section
- **理由** - Reasoning/rationale
- **洗錢防制** - Anti-Money Laundering (AML)
- **內線交易** - Insider trading
- **資訊揭露** - Information disclosure
- **金管會** - Financial Supervisory Commission
- **裁罰** - Penalty/sanction

## Performance Metrics

**Query Processing:**
- Average time: ~40 seconds per query
- Cost: ~$0.0015 USD (~NT$0.05) per query
- Token usage: ~1,500 tokens average

**Accuracy:**
- True positive rate: 95%
- False positive rate: 0%
- Relevance threshold: 0.8

## Common Pitfalls to Avoid

### LangChain v1.0 Migration Errors
1. **Don't use AgentExecutor** - Deprecated, use StateGraph
2. **Don't use LLMChain** - Use LCEL pipes: `prompt | llm | parser`
3. **Don't use .arun()/.acall()** - Use .ainvoke()/.astream()
4. **Don't skip @retry decorator** - LLM calls need retry logic
5. **Don't forget Pydantic args_schema** - Required for BaseTool

### Project Organization
6. **Don't put test scripts in project root** - Use scripts/ or .archive/
7. **Don't duplicate tools** - Extract to src/finagent/tools/ for sharing
8. **Don't commit .env or finagent.db** - Excluded in .gitignore
9. **Don't bypass ConfigManager** - Use high-level API, not direct database access
10. **Don't modify triggers manually** - Schema enforcement is critical

### Domain-Specific
11. **Don't skip citation validation** - Every fact needs a source
12. **Don't mix ROC and AD dates** - Be consistent with calendar format
13. **Don't use simplified Chinese** - Always use Traditional Chinese (繁體中文)
14. **Don't use informal language** - Formal legal writing style required
15. **Don't store model_config.yml in database** - It's file-based for UI choices

## Testing Best Practices

- Use `tempfile.TemporaryDirectory()` for database tests
- Mock RAG retriever when testing agents in isolation
- Test Traditional Chinese input handling
- Validate citation format in answer tests
- Test configuration priority (database > env)
- Test trigger enforcement (single active config)

## Troubleshooting

**Vector DB Empty:**
- Run `/init` to index documents
- Check `data/documents/` for TXT files
- Verify Chroma connection

**Configuration Not Applied:**
- Use `/config reload` to reload from files
- Check active config with `/config`
- Verify .env file exists and is readable

**Query Failing:**
- Check if orchestrator initialized (`self.use_rag`)
- Verify LLM API key is valid
- Check RAG retriever collection exists

**Plan Panel Disappears (Known Issue v1.1):**
- UI bug: Plan appears then disappears after 5-20 seconds
- Workaround: Workflow still executes correctly, check activity log
- Root cause: WebSocket reconnection or state management issue
- See [V1_1_RELEASE_PLAN.md - Known Issues](V1_1_RELEASE_PLAN.md#known-issues)

**LLM JSON Parsing Errors:**
- Retry logic with exponential backoff already implemented
- Manual JSON parsing fallback in ReplannerAgent
- If persistent, check prompt format in planner.py/replanner.py

## Archive Structure

Historical files preserved in `.archive/`:
```
.archive/
├── session-docs-2025-11-25/  # v1.1 development docs (implementation guides, reviews, test results)
├── legacy-v1.0-agents/       # Deprecated v1.0 agent files (tool_selector, query_flow_graph, etc.)
├── legacy-tools/             # Deprecated tool implementations (replaced by src/finagent/tools/)
├── frontend_v1.1_backup/     # Frontend backup from v1.1 refactoring
├── test-scripts/             # E2E test scripts from v0.1-alpha releases
├── validation-scripts/       # Legacy alpha validation scripts
├── implementation-docs/      # v1.0 implementation documentation
├── V1_0_RELEASE_PLAN.md      # v1.0 release plan (superseded by V1_1_RELEASE_PLAN.md)
└── legacy_docs_*/            # Old documentation snapshots
```

**Note**: Never add new test scripts to project root. Use `scripts/` for active scripts or `.archive/` for historical reference.
