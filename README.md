<div align="center">

# 🏦 FinAgent

**AI-Powered Financial Legal Research System for Taiwan**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Beta-yellow.svg)](https://github.com/p988744/FinAgent)

*Specialized AI system for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan's financial sector*

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](#-documentation) • [API](#-api)

</div>

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [CLI Interface](#cli-interface)
  - [API Server](#api-server)
  - [Celery Worker](#celery-worker)
  - [Document Processing](#document-processing)
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
- LangGraph-based workflow with Planning, Action, Validation, and Answer agents
- Real-time todo tracking and task status monitoring

📚 **Advanced RAG Pipeline**
- Semantic search with OpenAI embeddings and Chroma vector database
- Paragraph-aware chunking (512 tokens, 128 overlap)
- LLM-generated metadata extraction

🔍 **Document Processing**
- Automatic TXT file processing with recursive subfolder indexing
- 6 specialized research tools (vector search, metadata search, hybrid search, etc.)
- Taiwan legal citation formatting ([引用1]、[引用2])

🌐 **Flexible Deployment**
- Interactive CLI with rich formatting
- FastAPI backend with async support
- Celery worker for background document processing

🔧 **LLM Compatibility**
- OpenAI API support
- Ollama integration
- Custom endpoint configuration

🇹🇼 **Traditional Chinese**
- Full Traditional Chinese support
- Jieba word segmentation
- Taiwan-specific legal terminology

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/p988744/FinAgent.git
cd FinAgent
uv sync

# Configure
cp .env.example .env
# Edit .env with your OpenAI API key

# Process documents
uv run python src/finagent/cli/main.py process -r data/documents
```

**Example Usage:**
```bash
# Process documents from a directory
uv run python src/finagent/cli/main.py process -r data/documents/範例資料
```

---

## 📦 Installation

### Prerequisites

- Python 3.11+
- Redis (for async processing)
- 2GB+ RAM (for vector database)

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### Using pip

```bash
pip install -e .
```

### Environment Configuration

Create `.env` file:

```bash
# OpenAI (default)
LLM_API_KEY=sk-proj-xxx
LLM_BASE_URL=                    # Empty = use OpenAI
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Ollama (alternative)
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
EMBEDDING_MODEL=bge-m3
```

---

## 💻 Usage

### CLI Interface

```bash
# Process documents from a directory
uv run python src/finagent/cli/main.py process -r data/documents/範例資料

# Load documents only
uv run python src/finagent/cli/main.py load -r data/documents

# Extract metadata only
uv run python src/finagent/cli/main.py metadata -r data/documents

# Index documents only
uv run python src/finagent/cli/main.py index -r data/documents

# Show help
uv run python src/finagent/cli/main.py --help
```

### API Server

```bash
# Start FastAPI server
uv run uvicorn finagent.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health

# Submit query
curl -X POST http://localhost:8000/api/v1/research/query/sync \
  -H "Content-Type: application/json" \
  -d '{"text": "玉山銀行洗錢防制裁罰"}'

# API documentation
open http://localhost:8000/docs
```

### Celery Worker

Required for async document processing:

```bash
# Start Redis
brew services start redis  # macOS
sudo systemctl start redis # Linux

# Start Celery worker
./scripts/start_celery_worker.sh

# Or manually
uv run celery -A finagent.celery_app worker --loglevel=info

# Check worker status
celery -A finagent.celery_app inspect active
```

**Worker Configuration:**
- Concurrency: 2 processes
- Max tasks per child: 50
- Task time limit: 10 minutes
- Logs: `logs/celery_worker.log`

### Document Processing

```bash
# Add documents
mkdir -p data/documents
cp your_documents/*.txt data/documents/

# Process documents from a directory
uv run python src/finagent/cli/main.py process -r data/documents

# Process specific subdirectory
uv run python src/finagent/cli/main.py process -r data/documents/範例資料
```

### Frontend (React UI)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

**Prerequisites:**
- Node.js 18+ and npm
- Backend API server running on port 8000
- Celery worker running for async queries

**Production Build:**
```bash
cd frontend
npm run build
npm run preview  # Preview production build
```

---

## 🏗 Architecture

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
- Taiwan legal citation formatting

---

## 🔧 Research Tools

FinAgent includes 6 specialized research tools optimized for different query types:

| Tool | Best For | Speed | Key Features |
|------|----------|-------|--------------|
| **Vector Search** | General semantic search | Fast | Top-k semantic similarity |
| **Metadata Search** | Date/entity filtering | Very Fast | SQL-based filters |
| **Hybrid Search** | Filtered semantic search | Medium | Metadata + vector |
| **Multi-Entity** | Comparison queries | Slow | Parallel entity analysis |
| **List Documents** | Comprehensive inventories | Very Fast | Exhaustive results |
| **Read File** | Direct file access | Very Fast | Exact filename match |

### Example Usage

**Vector Search:**
```python
{"query": "玉山銀行洗錢防制", "top_k": 10}
```

**Metadata Search:**
```python
{"entity": "玉山銀行", "date_from": "2020-01-01", "date_to": "2020-12-31"}
```

**Hybrid Search:**
```python
{"query": "洗錢防制缺失", "entity": "玉山銀行", "date_from": "2020-01-01"}
```

See [full tool documentation](README.md#research-tools) for detailed parameters and use cases.

---

## 🗄 Database Schema

SQLite with normalized schema optimized for document management:

**Core Tables:**
- `documents` - Document metadata (filename, description, LLM-extracted fields)
- `document_pipelines` - Processing status tracking (1:1 with documents)
- `document_concepts` - Document-concept relationships (many-to-many)
- `concepts` - Extracted topics/concepts

**Key Features:**
- Integer foreign keys for performance
- Normalized design with separated pipeline data
- Automatic triggers for counts and timestamps
- JSON fields for flexible metadata

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
├── src/finagent/              # Source code
│   ├── cli/                   # CLI interface
│   ├── api/                   # FastAPI routes
│   ├── agents/                # Multi-agent system
│   ├── document_processing/   # RAG pipeline
│   ├── database/              # SQLite persistence
│   └── tools/                 # Research tools
├── tests/                     # Test suite
├── data/                      # Data directory
│   ├── documents/             # Source documents
│   └── vector_db/             # Chroma database
├── scripts/                   # Utility scripts
└── logs/                      # Application logs
```

---

## 📊 Performance

- **Query time**: ~40 seconds
- **Cost per query**: ~$0.0015 USD (~NT$0.05)
- **True positive rate**: 95%
- **False positive rate**: 0%
- **Confidence scoring**: 高信心/中信心/低信心

---

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Development instructions
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [PROJECT_SPEC.md](PROJECT_SPEC.md) - Project specifications
- [UNIMPLEMENTED_FEATURES.md](UNIMPLEMENTED_FEATURES.md) - Feature backlog

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

- LangChain for the agent framework
- OpenAI for embeddings and LLM
- Chroma for vector database
- FastAPI for the API framework

---

<div align="center">

**[⬆ Back to Top](#-finagent)**

Made with ❤️ for Taiwan's financial sector

**Status**: Beta (v0.0.1-beta) | **Last Updated**: 2025-12-02

</div>
