# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinAgent is a **Financial Legal Research Agent System** (金融法律研究代理系統) specialized for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan's financial sector. The system uses a multi-agent architecture with LangGraph orchestration and RAG (Retrieval-Augmented Generation) for precise legal research with formal citations.

**Target Region:** Taiwan (繁體中文)
**Domain:** Financial law, banking penalties, regulatory enforcement, legal precedents
**Status:** v0.0.1-beta - Database integration complete
**Architecture:** LangGraph multi-agent system with SQLite persistence and Chroma vector DB

## Development Commands

### Setup and Installation
```bash
# Install dependencies
uv sync

# Run interactive CLI (REPL mode)
uv run finagent

# Run single query
uv run finagent query "玉山銀行洗錢防制裁罰"

# Reindex documents (fast mode without LLM)
uv run finagent reindex --skip-init

# Reindex documents (full mode with LLM metadata)
uv run finagent reindex

# Clear and rebuild index
uv run finagent reindex --clear --yes

# Build package
uv build
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

### Multi-Agent LangGraph Workflow

```
User Query → Planning Agent → Action Agent → Validation Agent → Answer Agent → Response
                    ↓              ↓              ↓                    ↓
                  Tasks       RAG Retrieval   Citations           Synthesis
```

**Key Components:**

1. **Planning Agent** ([planning_agent.py](src/finagent/agents/planning_agent.py))
   - Query decomposition with legal context
   - Jurisdiction identification (金管會/中央銀行/公平會)
   - Task sequencing and research plan generation

2. **Action Agent** ([action_agent.py](src/finagent/agents/action_agent.py))
   - RAG retrieval with 0.8 relevance threshold
   - Document semantic search via Chroma
   - Multi-source coordination

3. **Validation Agent** ([validation_agent.py](src/finagent/agents/validation_agent.py))
   - Citation integrity checking
   - Source authority validation
   - Fact statement coverage verification

4. **Answer Agent** ([answer_agent.py](src/finagent/agents/answer_agent.py))
   - LLM-powered synthesis (GPT-4o-mini)
   - Taiwan legal citation formatting
   - Confidence scoring (高信心/中信心/低信心)

5. **Orchestrator** ([orchestrator.py](src/finagent/agents/orchestrator.py))
   - Coordinates entire LangGraph workflow
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

1. **Citation Integrity**: Every factual statement MUST have a citation to a verifiable source
2. **Source Hierarchy**: Prefer primary sources (official documents) over secondary (news)
3. **Document Size**: Legal documents are 50-200 pages; RAG is REQUIRED, not optional
4. **Entity Resolution**: Use official legal names (e.g., "玉山商業銀行股份有限公司" not "玉山")
5. **Date Format**: Use ROC (民國) calendar for Taiwan documents
6. **Chunking Strategy**: Preserve document structure (sections/chapters) during chunking
7. **Database Triggers**: SQLite triggers enforce single active config per type - don't bypass
8. **Configuration Presets**: Use ConfigManager API, not direct database access
9. **Traditional Chinese**: All system prompts and responses in 繁體中文
10. **Formal Tone**: Use formal legal writing style with passive voice

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

1. **Don't bypass ConfigManager** - Use high-level API, not direct database access
2. **Don't skip citation validation** - Every fact needs a source
3. **Don't mix ROC and AD dates** - Be consistent with calendar format
4. **Don't use simplified Chinese** - Always use Traditional Chinese (繁體中文)
5. **Don't store model_config.yml in database** - It's file-based for UI choices
6. **Don't commit .env or finagent.db** - Excluded in .gitignore
7. **Don't modify triggers manually** - Schema enforcement is critical
8. **Don't use informal language** - Formal legal writing style required

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
