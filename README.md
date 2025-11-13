# FinAgent - Financial Legal Research Agent System

A specialized AI-powered financial legal research system for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan's financial sector.

## Features

- 🤖 **Multi-Agent Architecture**: LangGraph-based workflow with Planning, Action, Validation, and Answer agents
- 📚 **RAG Pipeline**: Semantic search with OpenAI embeddings and Chroma vector database
- 🔍 **Document Processing**: Support for TXT files with recursive subfolder indexing
- 💬 **Interactive CLI**: REPL interface with command auto-completion
- 🌐 **Flexible LLM Configuration**: OpenAI-compatible API support (OpenAI, Ollama, custom endpoints)
- 🇹🇼 **Traditional Chinese**: Full support with Jieba word segmentation

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/p988744/FinAgent.git
cd FinAgent/backend

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run the CLI
uv run finagent
```

### Configuration

The system uses a unified OpenAI-compatible API configuration:

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

See [AUTO_CONFIG_GUIDE.md](docs/implementation/AUTO_CONFIG_GUIDE.md) for detailed configuration options.

## Project Structure

```
backend/
├── src/finagent/           # Source code
│   ├── cli/               # CLI interface
│   ├── agents/            # Multi-agent system
│   ├── document_processing/  # RAG pipeline
│   ├── models/            # Pydantic models
│   └── config.py          # Configuration
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                  # Documentation
│   ├── guides/           # User guides
│   ├── implementation/   # Technical docs
│   └── api/              # API documentation
├── data/                  # Data directory
│   ├── documents/        # Indexed documents
│   └── vector_db/        # Chroma database
├── scripts/               # Utility scripts
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

## Usage

### CLI Commands

```bash
# Start the CLI
uv run finagent

# Query examples
finagent> 玉山銀行洗錢防制裁罰
finagent> 2020年金管會裁罰案件

# Useful commands
finagent> /help       # Show all commands
finagent> /config     # View/modify configuration
finagent> /reindex    # Rebuild document index
finagent> /history    # View query history
finagent> /exit       # Exit CLI
```

See [CLI_GUIDE.md](../CLI_GUIDE.md) for complete command reference.

### Importing Documents

```bash
# Place documents in data/documents/
mkdir -p data/documents
cp your_documents/*.txt data/documents/

# Run indexing
uv run finagent
finagent> /reindex
```

See [IMPORT_DOCUMENTS.md](../IMPORT_DOCUMENTS.md) for detailed instructions.

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_local_llm.py

# Run with coverage
uv run pytest --cov=src/finagent
```

### Test LLM Configuration

```bash
# Test LLM and embedding setup
uv run python tests/test_local_llm.py
```

## Architecture

### Multi-Agent Workflow

1. **Planning Agent** - Analyzes query and creates research plan
2. **Action Agent** - Retrieves relevant documents via RAG
3. **Validation Agent** - Verifies citation integrity
4. **Answer Agent** - Synthesizes LLM-powered response

### RAG Pipeline

- Document loading and chunking
- OpenAI embedding generation
- Chroma vector database indexing
- Semantic search with relevance filtering
- Citation tracking and formatting

## Documentation

- [CLI Guide](../CLI_GUIDE.md) - Complete CLI usage guide
- [Configuration Guide](docs/implementation/AUTO_CONFIG_GUIDE.md) - LLM configuration
- [Import Documents](../IMPORT_DOCUMENTS.md) - How to add documents
- [LangGraph Implementation](docs/implementation/LANGGRAPH_IMPLEMENTATION.md) - Multi-agent architecture
- [Documentation Index](docs/DOCUMENTATION_INDEX.md) - All documentation

## Requirements

- Python 3.11+
- OpenAI API key (or compatible endpoint)
- 2GB+ RAM for vector database
- Traditional Chinese language support

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

## Support

For issues and questions:
- GitHub Issues: https://github.com/p988744/FinAgent/issues
- Documentation: [docs/](docs/)

---

**Status**: Beta
**Version**: 0.1.0
**Last Updated**: 2025-01-12
