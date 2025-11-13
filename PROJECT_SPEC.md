# FinAgent Project Specification

**Version:** 0.0.1-beta
**Last Updated:** 2025-01-13
**Status:** Beta - Database integration complete

## Project Overview

FinAgent is a Financial Legal Research Agent System (金融法律研究代理系統) specialized for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan's financial sector. The system uses a multi-agent architecture with RAG (Retrieval-Augmented Generation) for precise legal research with formal citations.

**Target Region:** Taiwan (繁體中文)
**Domain:** Financial law, banking penalties, regulatory enforcement, legal precedents
**Base Architecture:** Multi-agent system with LangGraph orchestration

## Architecture

### Multi-Agent Workflow

```
User Query → Planning Agent → Action Agent → Validation Agent → Answer Agent → Response
                    ↓              ↓              ↓
                  Tasks       RAG Retrieval   Citations
```

**Agents:**
1. **Planning Agent** - Query decomposition, jurisdiction identification, task sequencing
2. **Action Agent** - RAG retrieval with 0.8 relevance threshold, tool selection
3. **Validation Agent** - Citation integrity checking, source authority validation
4. **Answer Agent** - LLM-powered synthesis with formal Taiwan legal citation format

### Technology Stack

**Core Framework:**
- Python 3.11+
- LangChain/LangGraph - Agent orchestration
- OpenAI GPT-4o-mini - LLM (OpenAI-compatible API support)
- Pydantic - Data validation and settings management

**Document Processing:**
- PyMuPDF/pdfplumber - PDF extraction
- Jieba - Traditional Chinese word segmentation
- OpenAI text-embedding-3-small - Embedding generation
- Chroma - Vector database (2,858 chunks from 494 documents)

**CLI & UI:**
- Rich - Terminal UI with tables and colors
- Prompt Toolkit - Interactive REPL with auto-completion
- Click - Command-line argument parsing

**Database:**
- SQLite 3 - Settings, model configs, and history persistence
- Location: `./data/finagent.db`

**Build & Package:**
- Hatchling - Modern Python build backend
- uv - Fast Python package installer

## Project Structure

```
finagent/
├── src/finagent/              # Source code (src layout)
│   ├── agents/                # Multi-agent components
│   │   ├── planning_agent.py
│   │   ├── answer_agent.py
│   │   └── orchestrator.py    # LangGraph workflow
│   ├── database/              # SQLite database layer
│   │   ├── db.py              # CRUD operations
│   │   ├── models.py          # Pydantic models
│   │   └── schema.sql         # Database schema
│   ├── document_processing/   # RAG pipeline
│   │   ├── loader.py          # Document loading
│   │   ├── chunker.py         # Smart chunking
│   │   ├── embeddings.py      # Embedding generation
│   │   ├── indexer.py         # Vector DB indexing
│   │   └── retriever.py       # Semantic search
│   ├── cli/                   # CLI interface
│   │   ├── repl.py            # Interactive REPL
│   │   └── commands/          # CLI commands
│   │       ├── config.py      # Configuration management
│   │       ├── query.py       # Query execution
│   │       └── init.py        # Document initialization
│   ├── config.py              # Pydantic settings
│   ├── config_manager.py      # Database-backed config
│   └── model_config_loader.py # YAML model choices
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── test_database.py       # Database tests
├── data/                      # Data directory
│   ├── finagent.db           # SQLite database (auto-created)
│   ├── vector_db/            # Chroma persistence
│   ├── documents/            # Source documents (TXT)
│   └── document_metadata.json # Document metadata
├── docs/                      # Documentation
│   ├── guides/               # User guides
│   ├── implementation/       # Technical docs
│   └── api/                  # API documentation
├── spec_tmp/                  # Temporary specs
├── .env                       # Environment configuration
├── model_config.yml          # Model choices (not in DB)
├── pyproject.toml            # Project metadata
└── README.md                 # Project overview
```

## Database Schema

### Tables

**1. `settings` - Application settings**
```sql
id, key (UNIQUE), value, category, description, created_at, updated_at
```
- Categories: general, llm, embedding, vector_db
- Auto-updated timestamps via triggers

**2. `model_configs` - Saved configuration presets**
```sql
id, name, config_type (llm|embedding), api_key, base_url, model,
temperature, is_active (BOOLEAN), created_at, updated_at
```
- Only one active config per type (enforced by triggers)
- Instant switching between presets

**3. `history` - Query/interaction history**
```sql
id, session_id, query, response, model_used, tokens_used, cost_usd,
processing_time_seconds, success, error_message, metadata (JSON), created_at
```
- Track all queries with costs and performance
- Session-based grouping

## Configuration System

### Unified OpenAI-Compatible API

**Environment Variables (.env):**
```bash
# LLM Configuration
LLM_API_KEY=sk-xxx                       # API key
LLM_BASE_URL=                            # Empty = OpenAI, or custom endpoint
LLM_MODEL=gpt-4o-mini                    # Model name
LLM_TEMPERATURE=0.0                      # Temperature

# Embedding Configuration
EMBEDDING_API_KEY=                       # Empty = use LLM_API_KEY
EMBEDDING_BASE_URL=                      # Empty = use LLM_BASE_URL
EMBEDDING_MODEL=text-embedding-3-small   # Embedding model

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/vector_db
CHROMA_COLLECTION_NAME=legal_documents
```

### Configuration Priority

1. **Active Model Config** (from database) - Highest priority
2. **Database Settings** (settings table)
3. **.env File** (fallback)

### Supported Providers

**OpenAI** (default):
```bash
LLM_API_KEY=sk-proj-xxx
LLM_BASE_URL=                    # Empty
LLM_MODEL=gpt-4o-mini
```

**Ollama** (local):
```bash
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
```

**Custom Endpoint** (e.g., Azure, LM Studio):
```bash
LLM_API_KEY=your-key
LLM_BASE_URL=https://your-endpoint.com/v1
LLM_MODEL=your-model
```

## CLI Commands

### Core Commands

**`/config [subcommand]`** - Configuration management
```bash
/config                    # Show current configuration
/config llm                # Interactive LLM configuration wizard
/config save <name>        # Save current config as preset
/config load <id>          # Load saved preset (instant switch)
/config list [llm|embedding]  # List all saved presets
/config delete <id>        # Delete a saved preset
/config reload             # Reload .env and model_config.yml
```

**`/init [--reindex]`** - Initialize document database
```bash
/init                      # Index new documents only
/init --reindex           # Re-index all documents
```

**`/query <query>`** - Execute legal research query
```bash
/query 玉山銀行洗錢防制裁罰
```

**`/help`** - Show all available commands

**`/clear`** - Clear screen

**`/exit`** - Exit CLI

### Document Management

- Documents stored in `data/documents/` and `data/documents/裁罰歷史資料/`
- TXT format (UTF-8, Traditional Chinese)
- Auto-indexed with metadata extraction
- Recursive subfolder support

## RAG Pipeline

### Document Processing Flow

```
Documents → Load → Chunk → Embed → Index → Retrieve → Answer
   (TXT)     ↓       ↓       ↓       ↓        ↓         ↓
         Metadata  Smart  OpenAI  Chroma  Semantic  LLM+Citations
                  Chunking Embed           Search
```

**Chunking Strategy:**
- Paragraph-aware chunking
- Section preservation
- 512 token chunks with 128 overlap
- Metadata: filename, source_path, chunk_index, total_chunks

**Indexing:**
- 494 documents indexed
- 2,858 chunks in Chroma
- OpenAI text-embedding-3-small (1536 dimensions)
- Metadata includes document dates, entities, violation types

**Retrieval:**
- Semantic similarity search
- 0.8 relevance threshold
- Top-k retrieval (configurable)
- Citation tracking

## Model Configuration (model_config.yml)

### Purpose
Defines available model choices for UI selection (NOT stored in database).

### Structure

**OpenAI Chat Models:**
```yaml
openai_chat_models:
  - id: "gpt-4o-mini"
    name: "GPT-4o Mini (Fast & Cheap)"
    description: "Affordable and fast, suitable for most tasks"
    recommended: true
    default: true
```

**OpenAI Embedding Models:**
```yaml
openai_embedding_models:
  - id: "text-embedding-3-small"
    name: "Text Embedding 3 Small"
    description: "Best performance/cost ratio"
    recommended: true
    default: true
    dimensions: 1536
```

**Local LLM Presets:**
```yaml
local_llm_presets:
  - name: "Ollama (Qwen 2.5)"
    base_url: "http://localhost:11434/v1"
    model: "qwen2.5:7b"
    api_key: "ollama"
    description: "Qwen 2.5 7B via Ollama"
    recommended: true
```

**Settings:**
```yaml
settings:
  fetch_openai_models_dynamically: true
  use_static_model_list: false
  max_models_to_display: 10
  show_only_recommended: false
  temperature_presets:
    deterministic: 0.0
    balanced: 0.3
    creative: 0.7
    very_creative: 1.0
```

## Answer Format

### LLM-Powered Synthesis

Queries are processed through LangGraph workflow:

1. **Planning** - Decompose query, identify jurisdiction
2. **Action** - RAG retrieval with relevance filtering
3. **Validation** - Verify citation integrity
4. **Answer** - LLM synthesis with structured output

**Output Structure:**
```
執行摘要
[1-2 sentence summary]

關鍵發現
• Finding 1 [引用1]
• Finding 2 [引用2、3]

詳細分析
[Comprehensive analysis with embedded citations]

判例比較
[Precedent comparison table if applicable]

信心評分: 高信心
[Explanation of confidence]

引用來源
[1] 金管會裁罰書 - 玉山銀行洗錢防制 (2020-09-15)
    來源: data/documents/玉山銀行_洗錢防制裁罰_2020.txt
[2] ...
```

### Citation Format

**In-text:**
- `[引用1]` - First citation
- `[引用1，第3頁]` - With page number
- `[引用1、2、3]` - Multiple sources

**References:**
- Full source information
- Document path
- Relevance score
- Access date

## Performance Metrics

**Query Processing:**
- Average time: ~40 seconds per query
- Cost: ~$0.0015 USD (~NT$0.05) per query
- Token usage: ~1,500 tokens average

**Accuracy:**
- True positive rate: 95%
- False positive rate: 0%
- Relevance threshold: 0.8

**Database:**
- 494 documents indexed
- 2,858 vector chunks
- Database size: ~100KB (empty), grows with usage

## Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/p988744/FinAgent.git
cd FinAgent

# Install dependencies (uses uv for speed)
cd backend
uv sync

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # Add your API keys

# Run CLI
uv run finagent
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test suites
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run python tests/test_database.py

# Run with coverage
uv run pytest --cov=finagent --cov-report=html
```

### Building

```bash
# Build package
uv build

# Install locally
pip install dist/finagent-0.0.1-py3-none-any.whl
```

## Git Workflow

**Branches:**
- `main` - Stable releases (not yet created)
- `develop` - Active development (current)

**Recent Commits:**
1. `03e0386` - CLI interface and RAG pipeline
2. `87d4b6e` - Pydantic date/URL fixes
3. `0831124` - Database implementation
4. `b0e0d34` - CLI database integration

## Configuration Examples

### Scenario 1: OpenAI Only

```bash
# .env
LLM_API_KEY=sk-proj-xxx
LLM_BASE_URL=
LLM_MODEL=gpt-4o-mini
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=text-embedding-3-small
```

### Scenario 2: Local LLM + OpenAI Embeddings

```bash
# .env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
EMBEDDING_API_KEY=sk-proj-xxx  # OpenAI key
EMBEDDING_BASE_URL=             # Empty = use OpenAI
EMBEDDING_MODEL=text-embedding-3-small
```

### Scenario 3: All Local

```bash
# .env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
EMBEDDING_API_KEY=local
EMBEDDING_BASE_URL=http://localhost:11435/v1
EMBEDDING_MODEL=bge-m3
```

## Key Features

### Implemented ✅

- ✅ Multi-agent architecture with LangGraph
- ✅ RAG pipeline with Chroma vector DB
- ✅ Traditional Chinese support (Jieba)
- ✅ Interactive CLI with auto-completion
- ✅ Document management (/init command)
- ✅ LLM-powered answer synthesis
- ✅ Formal Taiwan legal citation format
- ✅ SQLite database for persistence
- ✅ Configuration management with presets
- ✅ OpenAI-compatible API support
- ✅ Instant config switching (no restart)
- ✅ Query history tracking (schema ready)

### Pending 🔄

- 🔄 History command (/history) - UI not implemented
- 🔄 Stats command (/stats) - UI not implemented
- 🔄 Query history logging in orchestrator
- 🔄 PDF/HTML/DOCX support (currently TXT only)
- 🔄 Cost tracking per query
- 🔄 Export to PDF/DOCX with citations
- 🔄 Frontend web interface

## Cost Estimates

**Per Query:**
- LLM (GPT-4o-mini): ~$0.0010 USD
- Embeddings (text-embedding-3-small): ~$0.0005 USD
- **Total: ~$0.0015 USD (~NT$0.05)**

**Monthly (100 queries):**
- LLM: ~$0.10 USD
- Embeddings: ~$0.05 USD
- Database: $0 (self-hosted SQLite)
- **Total: ~$0.15 USD (~NT$5)**

## Important Notes

### Database

- **Location**: `./data/finagent.db`
- **Auto-created**: On first run
- **Backup**: .env file provides fallback
- **Schema**: See `src/finagent/database/schema.sql`

### model_config.yml

- **NOT stored in database** - File-based for easy editing
- **Purpose**: Provide model choices for UI selection
- **Reload**: `/config reload` to apply changes
- **Version control**: Can be committed to git

### Data Files

- **Location**: `data/documents/` and subdirectories
- **Format**: TXT files (UTF-8, Traditional Chinese)
- **Gitignore**: Excluded from version control (large files)
- **Metadata**: Tracked in `data/document_metadata.json`

### Taiwan-Specific

- **Date format**: ROC calendar (民國)
- **Citation format**: Taiwan legal citation standards
- **Regulatory bodies**: FSC (金管會), CBC (中央銀行), FTC (公平會)
- **Language**: Traditional Chinese (繁體中文)

## Quick Start Commands

```bash
# First time setup
uv sync
cp .env.example .env
nano .env  # Add API key
uv run finagent
/init  # Index documents (first run)

# Daily usage
uv run finagent
/config  # Check configuration
/query 玉山銀行洗錢防制裁罰

# Configuration management
/config save Production
/config list llm
/config load 1

# Document management
/init --reindex  # Re-index all documents
```

## Documentation

**In-repo:**
- [README.md](README.md) - Project overview
- [docs/guides/](docs/guides/) - User guides
- [docs/implementation/](docs/implementation/) - Technical docs
- [spec_tmp/](spec_tmp/) - Implementation notes

**Key Documents:**
- `DATABASE_IMPLEMENTATION.md` - Database architecture
- `CLI_DATABASE_INTEGRATION.md` - CLI integration guide
- `LANGGRAPH_IMPLEMENTATION.md` - Multi-agent workflow
- `BOUNDARY_TESTS.md` - Edge case testing

## Contributing

**Code Style:**
- Python 3.11+ features
- Type hints required
- Pydantic for data validation
- Black formatting (line length 100)
- Docstrings in Google style

**Testing:**
- Unit tests required for new features
- Integration tests for workflows
- Database tests for schema changes
- Manual CLI testing for UI changes

**Commits:**
- Conventional commits format
- Clear, descriptive messages
- Include Co-Authored-By for AI assistance

## License

TBD - To be determined

## Contact & Resources

**Repository:** https://github.com/p988744/FinAgent
**Issues:** https://github.com/p988744/FinAgent/issues
**Version:** 0.0.1-beta
**Status:** Active development on `develop` branch

---

*Last Updated: 2025-01-13*
*Specification Version: 1.0*
