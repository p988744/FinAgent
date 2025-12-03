<div align="center">

# 🏦 FinAgent

**AI-Powered Financial Legal Research System for Taiwan**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v2.0--beta1-orange.svg)](https://github.com/p988744/FinAgent)

*Specialized AI system for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan's financial sector*

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](#-documentation) • [API](#-api)

</div>

---

## 🆕 What's New in v2.0-beta1

- **Chat-based UI**: Modern React frontend with real-time research progress
- **Deep Research Agent**: Advanced multi-step reasoning with dynamic replanning
- **Async Processing**: Celery-based background task processing with Redis
- **Alembic Migrations**: Professional database schema management
- **Enhanced RAG**: Hybrid search combining vector similarity and BM25
- **Real-time Updates**: WebSocket-based progress streaming

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Web Interface](#web-interface)
  - [CLI Interface](#cli-interface)
  - [API Server](#api-server)
- [Architecture](#-architecture)
- [Research Tools](#-research-tools)
- [Database Schema](#-database-schema)
- [Development](#-development)
- [Performance](#-performance)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

🤖 **Multi-Agent Architecture**
- LangGraph-based Deep Research Agent with dynamic planning
- Real-time task tracking and progress monitoring
- Automatic query decomposition and synthesis

📚 **Advanced RAG Pipeline**
- Semantic search with OpenAI embeddings (text-embedding-3-small)
- Hybrid retrieval: Vector similarity + BM25 keyword matching
- Paragraph-aware chunking (512 tokens, 128 overlap)
- LLM-generated metadata extraction

🔍 **Document Processing**
- Automatic TXT file processing with recursive subfolder indexing
- 6 specialized research tools (vector search, metadata search, hybrid search, etc.)
- Taiwan legal citation formatting ([引用1]、[引用2])

🌐 **Modern Web Interface**
- React-based chat UI with real-time progress
- Document management with upload/indexing
- Research history and bookmarking
- Settings management for LLM configuration

🔧 **LLM Compatibility**
- OpenAI API support (GPT-4o, GPT-4o-mini)
- Ollama integration for local models
- Custom endpoint configuration

🇹🇼 **Traditional Chinese**
- Full Traditional Chinese support
- Jieba word segmentation
- Taiwan-specific legal terminology

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Redis (for async processing)

### Installation

```bash
# Clone repository
git clone https://github.com/p988744/FinAgent.git
cd FinAgent

# Backend setup
uv sync

# Frontend setup
cd frontend && npm install && cd ..

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Start Services

```bash
# Terminal 1: Backend API
uv run uvicorn finagent.main:app --reload --port 8000

# Terminal 2: Celery Worker (for async processing)
uv run celery -A finagent.celery_app worker --loglevel=info

# Terminal 3: Frontend
cd frontend && npm run dev
```

### Access

- **Web UI**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

---

## 📦 Installation

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Initialize database
uv run alembic upgrade head
```

### Using pip

```bash
pip install -e .
alembic upgrade head
```

### Environment Configuration

Create `.env` file:

```bash
# OpenAI (default)
LLM_API_KEY=sk-proj-xxx
LLM_BASE_URL=                    # Empty = use OpenAI
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Redis (for async processing)
REDIS_URL=redis://localhost:6379/0

# Ollama (alternative)
# LLM_API_KEY=ollama
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_MODEL=qwen2.5:7b
```

---

## 💻 Usage

### Web Interface

The React-based web interface provides:

- **Chat Interface**: Submit research queries and view real-time progress
- **Document Management**: Upload, index, and manage documents
- **Research History**: View past queries with bookmarking
- **Settings**: Configure LLM models and API keys

```bash
cd frontend
npm run dev
# Open http://localhost:5173
```

### CLI Interface

```bash
# Process documents from a directory
uv run finagent process -r data/documents

# Load documents only (no indexing)
uv run finagent load -r data/documents

# Extract metadata only
uv run finagent metadata -r data/documents

# Index documents only
uv run finagent index -r data/documents

# Show help
uv run finagent --help
```

### API Server

```bash
# Start FastAPI server
uv run uvicorn finagent.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health

# Submit async query
curl -X POST http://localhost:8000/api/v1/research/query \
  -H "Content-Type: application/json" \
  -d '{"text": "玉山銀行洗錢防制裁罰"}'

# API documentation
open http://localhost:8000/docs
```

---

## 🏗 Architecture

### System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │────▶│   Celery        │
│   (Port 5173)   │     │   (Port 8000)   │     │   Worker        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   SQLite DB     │     │   Redis Queue   │
                        │   (finagent.db) │     │   (Port 6379)   │
                        └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Chroma        │
                        │   Vector DB     │
                        └─────────────────┘
```

### Deep Research Agent Workflow

```
User Query
    │
    ▼
┌─────────────┐
│   Planner   │ ──▶ Creates research plan with tasks
└─────────────┘
    │
    ▼
┌─────────────┐
│  Executor   │ ──▶ Executes tasks using RAG tools
└─────────────┘
    │
    ▼
┌─────────────┐
│  Replanner  │ ──▶ Reviews progress, replans or responds
└─────────────┘
    │
    ▼
Final Response with Citations
```

### RAG Pipeline

- Document loading with LLM-generated metadata
- Paragraph-aware chunking (512 tokens, 128 overlap)
- OpenAI embedding generation (text-embedding-3-small)
- Chroma vector database indexing
- Hybrid search: Vector similarity (60%) + BM25 (40%)
- Taiwan legal citation formatting

---

## 🔧 Research Tools

FinAgent includes 6 specialized research tools:

| Tool | Best For | Speed | Key Features |
|------|----------|-------|--------------|
| **Vector Search** | General semantic search | Fast | Top-k semantic similarity |
| **Metadata Search** | Date/entity filtering | Very Fast | SQL-based filters |
| **Hybrid Search** | Filtered semantic search | Medium | Metadata + vector |
| **Multi-Entity** | Comparison queries | Slow | Parallel entity analysis |
| **List Documents** | Comprehensive inventories | Very Fast | Exhaustive results |
| **Read File** | Direct file access | Very Fast | Exact filename match |

---

## 🗄 Database Schema

SQLite with Alembic migrations for schema management:

**Core Tables:**
- `documents` - Document metadata and LLM-extracted fields
- `document_pipelines` - Processing status tracking
- `research_sessions` - Query sessions and results
- `tool_executions` - Research tool execution logs
- `concepts` - Extracted topics and concepts

**Database Commands:**
```bash
# Apply migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# View migration history
uv run alembic history
```

---

## 👨‍💻 Development

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/finagent --cov-report=html

# Unit tests only
uv run pytest -m unit

# Integration tests only
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

### Project Structure

```
FinAgent/
├── src/finagent/              # Backend source code
│   ├── api/                   # FastAPI routes
│   ├── agents/                # Multi-agent system
│   │   └── plan_execute/      # Deep Research Agent
│   ├── cli/                   # CLI commands
│   ├── database/              # SQLite + Alembic
│   ├── document_processing/   # RAG pipeline
│   ├── tools/                 # Research tools
│   └── wiki/                  # Wiki/knowledge base
├── frontend/                  # React UI
│   ├── src/components/        # React components
│   ├── src/hooks/             # Custom hooks
│   └── src/pages/             # Page components
├── tests/                     # Test suite
├── data/                      # Data directory
│   ├── documents/             # Source documents
│   └── vector_db/             # Chroma database
├── scripts/                   # Utility scripts
└── logs/                      # Application logs
```

---

## 📊 Performance

- **Query time**: 30-60 seconds (depending on complexity)
- **Cost per query**: ~$0.002-0.005 USD
- **Documents supported**: 500+ TXT files
- **Vector dimensions**: 1536 (text-embedding-3-small)
- **Confidence scoring**: 高信心/中信心/低信心

---

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Development instructions for AI assistants
- [CHANGELOG.md](CHANGELOG.md) - Version history

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- LangChain & LangGraph for the agent framework
- OpenAI for embeddings and LLM
- Chroma for vector database
- FastAPI for the API framework
- React & Vite for the frontend

---

<div align="center">

**[⬆ Back to Top](#-finagent)**

Made with ❤️ for Taiwan's financial sector

**Version**: v2.0-beta1 | **Last Updated**: 2025-12-02

</div>
