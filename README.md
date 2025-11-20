# FinAgent - Financial Legal Research Agent System

A specialized AI-powered financial legal research system for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan's financial sector.

## Features

- 🤖 **Multi-Agent Architecture**: LangGraph-based workflow with Planning, Action, Validation, and Answer agents
- 📚 **RAG Pipeline**: Semantic search with OpenAI embeddings and Chroma vector database
- 🔍 **Document Processing**: TXT files with recursive subfolder indexing and LLM-generated metadata
- 💬 **CLI Interface**: Interactive REPL with rich formatting
- 🌐 **FastAPI Backend**: RESTful API for programmatic access
- 🔧 **Flexible LLM Configuration**: OpenAI-compatible API support (OpenAI, Ollama, custom endpoints)
- 🇹🇼 **Traditional Chinese**: Full support with Jieba word segmentation
- 📊 **Todo Tracking**: Real-time task status monitoring in agent workflow

## Quick Start

```bash
# Clone the repository
git clone https://github.com/p988744/FinAgent.git
cd FinAgent

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the CLI
uv run finagent
```

### Configuration

```bash
# OpenAI (default)
LLM_API_KEY=sk-proj-xxx
LLM_BASE_URL=                    # Empty = use OpenAI
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Custom Endpoint (e.g., Ollama)
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
EMBEDDING_MODEL=bge-m3
```

## Project Structure

```
FinAgent/
├── src/finagent/              # Source code
│   ├── cli/                   # CLI interface
│   ├── api/                   # FastAPI routes
│   ├── agents/                # Multi-agent system
│   ├── document_processing/   # RAG pipeline
│   ├── database/              # SQLite persistence
│   ├── models/                # Pydantic models
│   └── config.py              # Configuration
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── data/                      # Data directory
│   ├── documents/             # Source documents
│   └── vector_db/             # Chroma database
├── pyproject.toml             # Project configuration
├── CLAUDE.md                  # Claude Code instructions
├── CHANGELOG.md               # Version history
└── README.md                  # This file
```

## Usage

### CLI Commands

```bash
# Start the CLI
uv run finagent

# Query examples
finagent> 玉山銀行洗錢防制裁罰
finagent> 2020年金管會裁罰案件
finagent> 內線交易相關判決

# Commands
finagent> /help       # Show all commands
finagent> /config     # View/modify configuration
finagent> /reindex    # Rebuild document index
finagent> /clear      # Clear screen
finagent> /exit       # Exit CLI
```

### FastAPI Server

```bash
# Start API server
uv run uvicorn finagent.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health

# Submit query
curl -X POST http://localhost:8000/api/v1/research/query/sync \
  -H "Content-Type: application/json" \
  -d '{"text": "玉山銀行洗錢防制裁罰"}'
```

### Importing Documents

```bash
# Place documents in data/documents/
mkdir -p data/documents
cp your_documents/*.txt data/documents/

# Reindex with LLM metadata
uv run finagent
finagent> /reindex

# Or via CLI directly
uv run finagent reindex --clear --yes
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/finagent --cov-report=html

# Run unit tests only
uv run pytest -m unit

# Run integration tests only
uv run pytest -m integration
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

## Architecture

### Multi-Agent Workflow

```
User Query → Planning Agent → Action Agent → Validation Agent → Answer Agent → Response
                    ↓              ↓              ↓                    ↓
                  Tasks       RAG Retrieval   Citations           Synthesis
```

1. **Planning Agent** - Analyzes query, creates research plan, generates todo items
2. **Action Agent** - Retrieves relevant documents via RAG, updates task status
3. **Validation Agent** - Verifies citation integrity, checks source coverage
4. **Answer Agent** - Synthesizes LLM-powered response with confidence scoring

### RAG Pipeline

- Document loading with LLM-generated metadata
- Paragraph-aware chunking (512 tokens, 128 overlap)
- OpenAI embedding generation (text-embedding-3-small)
- Chroma vector database indexing
- Semantic search with 0.8 relevance threshold
- Taiwan legal citation formatting ([引用1]、[引用2])

## Research Tools

FinAgent includes 6 specialized research tools that the Action Agent uses to retrieve relevant information. Each tool is optimized for specific query types and use cases.

### Tool Selection Strategy

The Planning Agent analyzes the user's query and selects appropriate tools based on:
- **Query intent** (semantic search, temporal analysis, comparison, etc.)
- **Required features** (entity names, date ranges, specific filenames)
- **Execution characteristics** (speed, cost, result completeness)

### Available Tools

#### 1. Vector Search Tool (`vector_search`)

**Best for**: General semantic search, keyword queries, concept-based search

**Capabilities**:
- Semantic similarity search using OpenAI embeddings
- Chroma vector database with 0.8 relevance threshold
- Returns top-k most relevant chunks (default: 10)

**Parameters**:
```python
{
  "query": "玉山銀行洗錢防制",
  "top_k": 10,                    # Number of results
  "relevance_threshold": 0.8,     # Max distance threshold
  "filter_document_ids": ["doc1"] # Optional: filter to specific documents
}
```

**Limitations**:
- Cannot filter by date or metadata
- Returns top-k only (not exhaustive)
- May miss exact filename matches
- Requires vector database index

**Use cases**:
- "玉山銀行洗錢防制裁罰" (semantic query)
- "內部控制缺失相關案例" (keyword search)
- "金融詐欺判決" (general search)

---

#### 2. Metadata Search Tool (`metadata_search`)

**Best for**: Date-based queries, entity-specific search, jurisdiction filtering

**Capabilities**:
- Filter documents by metadata attributes
- SQL-based database queries (fast, ~1-2 seconds)
- Returns all matching documents (not limited to top-k)

**Parameters**:
```python
{
  "entity": "玉山銀行",           # Entity name (partial match)
  "date_from": "2020-01-01",     # Start date (YYYY-MM-DD)
  "date_to": "2020-12-31",       # End date (YYYY-MM-DD)
  "penalty_type": "洗錢防制",    # Penalty type (partial match)
  "jurisdiction": "金管會",      # Jurisdiction (exact match)
  "year_ad": 2020                # Year in AD
}
```

**Limitations**:
- Requires metadata index
- Cannot perform semantic matching
- Returns metadata only (not full content)

**Use cases**:
- "2020年玉山銀行裁罰" (temporal + entity)
- "最近的金管會裁罰案件" (temporal)
- "內線交易相關裁罰" (penalty type)

---

#### 3. Hybrid Search Tool (`hybrid_search`)

**Best for**: Filtered semantic search with temporal or entity constraints

**Capabilities**:
- Two-stage process: metadata filtering → vector search
- Combines precision of metadata with semantic understanding
- Balances speed and accuracy

**Process**:
1. **Stage 1**: Filter documents by metadata (entity, date, jurisdiction)
2. **Stage 2**: Semantic vector search within filtered candidates

**Parameters**:
```python
{
  "query": "洗錢防制缺失",          # Semantic query
  "entity": "玉山銀行",            # Metadata filters (optional)
  "date_from": "2020-01-01",
  "date_to": "2020-12-31",
  "top_k": 10,
  "relevance_threshold": 0.8
}
```

**Limitations**:
- Slower than pure vector or metadata search (~3-7 seconds)
- Requires both vector index and metadata database
- Performance depends on candidate count

**Use cases**:
- "2020年玉山銀行洗錢防制缺失" (temporal + entity + semantic)
- "金管會最近的內部控制裁罰" (jurisdiction + temporal + semantic)

---

#### 4. Multi-Entity Search Tool (`multi_entity_search`)

**Best for**: Comparison queries, parallel entity analysis

**Capabilities**:
- Search multiple entities in parallel
- Optimized for "A vs B" queries
- Groups results by entity for easy comparison

**Parameters**:
```python
{
  "query": "洗錢防制裁罰",
  "entities": ["玉山銀行", "國泰世華銀行"], # Min 2 entities
  "top_k_per_entity": 5,                      # Results per entity
  "relevance_threshold": 0.8,
  "use_metadata": true                        # Use metadata filtering
}
```

**Limitations**:
- Higher cost (multiple embedding API calls)
- Requires comparison logic in Answer Agent
- Recommended max: 5 entities

**Use cases**:
- "玉山銀行 vs 國泰世華銀行洗錢防制" (comparison)
- "比較主要銀行的內線交易裁罰" (multi-entity analysis)

---

#### 5. List Documents Tool (`list_documents`)

**Best for**: Comprehensive inventories, catalog queries

**Capabilities**:
- Returns ALL matching documents (exhaustive, not top-k)
- Fast database queries
- Useful for "list all" queries

**Parameters**:
```python
{
  "entity": "玉山銀行",        # Entity name (required or penalty_type)
  "penalty_type": "洗錢防制"   # Penalty type (optional)
}
```

**Limitations**:
- Returns metadata only (not full content)
- Requires subsequent read for details
- Needs metadata index

**Use cases**:
- "列出所有玉山銀行的裁罰案件" (comprehensive list)
- "金管會所有洗錢防制裁罰目錄" (catalog)

---

#### 6. Read File Tool (`read_file`)

**Best for**: Direct file access by filename

**Capabilities**:
- Read specific file directly by name or path
- Fast file I/O
- Returns full file content and metadata

**Parameters**:
```python
{
  "filename": "玉山銀行_洗錢防制裁罰_2020.txt"  # Exact filename or path
}
```

**Limitations**:
- Requires exact filename or path
- Cannot perform semantic search
- File must exist in system

**Use cases**:
- "讀取玉山銀行_洗錢防制裁罰_2020.txt" (specific file)
- After list_documents returns a filename for deep read

---

### Tool Execution Tracking

All tool executions are tracked with:
- **Execution time**: Performance monitoring
- **Parameters**: Request details for verification
- **Results**: Sample results (top 3) with relevance scores
- **Metadata**: Tool-specific statistics

**Database Schema**: `tool_executions` table
```sql
CREATE TABLE tool_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    parameters TEXT NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    results_count INTEGER NOT NULL,
    sample_results TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Integration

**Tool Registry**:
```python
from finagent.tools import get_registry

# Get global registry
registry = get_registry()

# List all tools
tools = registry.list_tools()

# Get tool capabilities
capabilities = registry.get_all_capabilities()

# Find tools for specific intent
tools = registry.find_tools_for_intent("temporal")
```

**Execute Tool with Tracking**:
```python
from finagent.tools.base import ToolInput
from finagent.tools import get_registry

# Get tool
registry = get_registry()
tool = registry.get_tool("vector_search")

# Create input
tool_input = ToolInput(
    query="玉山銀行洗錢防制",
    parameters={"top_k": 10, "relevance_threshold": 0.8}
)

# Execute with tracking
output = await tool.execute_with_tracking(
    tool_input=tool_input,
    query_id="query_123"
)

# Check results
if output.success:
    print(f"Found {len(output.results)} results")
    print(f"Execution time: {output.metadata['execution_time_ms']}ms")
```

## Performance

- **Query time**: ~40 seconds
- **Cost per query**: ~$0.0015 USD (~NT$0.05)
- **True positive rate**: 95%
- **False positive rate**: 0%
- **Confidence scoring**: 高信心/中信心/低信心

## Requirements

- Python 3.11+
- OpenAI API key (or compatible endpoint)
- 2GB+ RAM for vector database
- macOS, Linux, or Windows

## Documentation

- [CLAUDE.md](CLAUDE.md) - Claude Code development instructions
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [PROJECT_SPEC.md](PROJECT_SPEC.md) - Project specifications
- [UNIMPLEMENTED_FEATURES.md](UNIMPLEMENTED_FEATURES.md) - Feature backlog

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: https://github.com/p988744/FinAgent/issues

---

**Status**: Beta (v0.0.1-beta)
**Last Updated**: 2025-11-17
