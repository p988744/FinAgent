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
