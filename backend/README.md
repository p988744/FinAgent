# FinAgent Backend

Legal Research Agent System (法律研究代理系統) - Backend API and CLI

## Quick Start

### 1. Installation

```bash
# Install dependencies with uv
cd backend
uv sync
```

### 2. Configure LLM (Required)

Create a `.env` file in the `backend` directory with your LLM configuration:

#### Option A: OpenAI (Recommended for Production)

```env
# LLM Configuration
USE_LOCAL_LLM=false
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Get OpenAI API Key:**
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy and paste into `.env` file

#### Option B: Local LLM (Free, Privacy-Focused)

```env
# LLM Configuration
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen2.5:7b
LOCAL_LLM_API_KEY=ollama

# Still need OpenAI for embeddings (for now)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Setup Local LLM (Ollama):**
```bash
# Install Ollama
brew install ollama  # macOS
# or download from https://ollama.com/download

# Start Ollama server
ollama serve

# Pull a model (recommended for Traditional Chinese)
ollama pull qwen2.5:7b
```

### 3. Index Documents

Place your legal documents (TXT files) in `data/documents/`:

```bash
mkdir -p data/documents
# Copy your .txt files here
```

Then run the indexer:

```bash
uv run finagent
# In the CLI:
finagent> /reindex
```

### 4. Start Using

```bash
# Start CLI
uv run finagent

# Example queries
finagent> 玉山銀行洗錢防制裁罰
finagent> 2020年金管會裁罰案件
finagent> /help
```

---

## Configuration

### Environment Variables (.env file)

Create a `.env` file in the `backend` directory with the following variables:

```env
# ============================================
# LLM Configuration (Required)
# ============================================

# Choose LLM Provider: false = OpenAI, true = Local LLM
USE_LOCAL_LLM=false

# OpenAI Configuration (if USE_LOCAL_LLM=false)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TEMPERATURE=0.0

# Local LLM Configuration (if USE_LOCAL_LLM=true)
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen2.5:7b
LOCAL_LLM_API_KEY=ollama

# ============================================
# Application Settings (Optional)
# ============================================

APP_ENV=development
APP_NAME=Legal Research Agent
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# ============================================
# Vector Database (Optional)
# ============================================

CHROMA_PERSIST_DIRECTORY=./data/vector_db
CHROMA_COLLECTION_NAME=legal_documents

# ============================================
# FSC Scraping (Optional)
# ============================================

FSC_BASE_URL=https://www.fsc.gov.tw
SCRAPING_DELAY_SECONDS=1
SCRAPING_MAX_RETRIES=3
SCRAPING_TIMEOUT_SECONDS=30

# ============================================
# Feature Flags (Optional)
# ============================================

ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
MAX_DOCUMENT_SIZE_MB=50
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT_SECONDS=60
```

### Configuration via CLI

You can also configure LLM settings interactively using the CLI:

```bash
uv run finagent

# Show current configuration
finagent> /config

# Configure LLM (interactive wizard)
finagent> /config llm
```

The `/config llm` command will:
1. Guide you through provider selection (OpenAI or Local LLM)
2. Help you choose model and credentials
3. Automatically save to `.env` file

---

## Supported LLM Models

### OpenAI Models

| Model | Speed | Cost | Quality | Recommended For |
|-------|-------|------|---------|-----------------|
| `gpt-4o-mini` | ⚡⚡⚡ Fast | 💰 $0.0015/query | ⭐⭐⭐⭐ High | **Production (Default)** |
| `gpt-4o` | ⚡⚡ Medium | 💰💰 $0.015/query | ⭐⭐⭐⭐⭐ Best | Critical queries |
| `gpt-4-turbo` | ⚡⚡ Medium | 💰💰 $0.01/query | ⭐⭐⭐⭐ High | Complex analysis |
| `gpt-3.5-turbo` | ⚡⚡⚡ Fast | 💰 $0.0005/query | ⭐⭐⭐ Medium | Development/testing |

**Embedding Models:**
- `text-embedding-3-small` - Fast, 1536 dimensions (recommended)
- `text-embedding-3-large` - Larger, 3072 dimensions (higher accuracy)
- `text-embedding-ada-002` - Legacy model

### Local LLM Models (OpenAI-Compatible)

**Requirements:**
- Ollama/LM Studio/vLLM installed
- ~8GB VRAM for 7B models, ~16GB for 14B models
- Mac: M1/M2/M3 with Metal, Linux/Windows: NVIDIA GPU with CUDA

**Recommended Models:**

| Model | Size | Quality | Speed | Chinese Support |
|-------|------|---------|-------|-----------------|
| `qwen2.5:7b` | 4.7GB | ⭐⭐⭐⭐ | ⚡⚡ Medium | ⭐⭐⭐⭐⭐ Excellent |
| `qwen2.5:14b` | 8.8GB | ⭐⭐⭐⭐⭐ | ⚡ Slow | ⭐⭐⭐⭐⭐ Excellent |
| `llama3.1:8b` | 4.9GB | ⭐⭐⭐⭐ | ⚡⚡ Medium | ⭐⭐⭐ Good |
| `mistral:7b` | 4.1GB | ⭐⭐⭐ | ⚡⚡⚡ Fast | ⭐⭐ Fair |

**Setup Ollama:**
```bash
# Install
brew install ollama  # macOS
curl -fsSL https://ollama.com/install.sh | sh  # Linux

# Start server
ollama serve

# Pull recommended model
ollama pull qwen2.5:7b

# List available models
ollama list
```

---

## CLI Commands

### Query Commands

```bash
# Direct query (most common)
finagent> 玉山銀行洗錢防制裁罰

# Or use explicit command
finagent> /query 國泰世華銀行法規違規
```

### Configuration Commands

```bash
# Show current LLM configuration
finagent> /config

# Configure LLM interactively
finagent> /config llm
```

### Document Management

```bash
# Reindex documents (incremental)
finagent> /reindex

# Clear and rebuild index
finagent> /reindex --clear
```

### History & Results

```bash
# Show query history
finagent> /history

# Show citations from last query
finagent> /citations

# Export results (TODO)
finagent> /export markdown
```

### Other Commands

```bash
# Show help
finagent> /help

# Clear screen
finagent> /clear

# Exit
finagent> /exit
```

---

## Project Structure

```
backend/
├── src/finagent/
│   ├── agents/              # Multi-agent LangGraph workflow
│   │   ├── planning_agent.py    # Query decomposition
│   │   ├── action_agent.py      # RAG retrieval
│   │   ├── validation_agent.py  # Citation validation
│   │   ├── answer_agent.py      # LLM synthesis
│   │   ├── workflow.py          # LangGraph orchestration
│   │   └── orchestrator.py      # Main orchestrator
│   ├── cli/                 # CLI interface
│   │   ├── repl.py             # Interactive REPL
│   │   └── commands/           # Command handlers
│   │       ├── query.py
│   │       ├── config.py       # LLM configuration
│   │       ├── reindex.py
│   │       └── help.py
│   ├── document_processing/ # Document processing
│   │   ├── loader.py           # Document loader
│   │   ├── chunker.py          # Text chunking
│   │   ├── embedder.py         # Embedding generation
│   │   └── retriever.py        # Vector search
│   ├── models/              # Pydantic models
│   │   ├── queries.py
│   │   ├── answers.py
│   │   └── citations.py
│   └── config.py            # Configuration management
├── data/
│   ├── documents/           # Source documents (TXT)
│   └── vector_db/           # Chroma vector database
├── tests/                   # Unit tests
├── .env                     # Configuration (create this!)
├── pyproject.toml          # Dependencies
└── README.md               # This file
```

---

## Performance & Cost

### OpenAI (gpt-4o-mini)

**Performance:**
- Query time: ~40 seconds
- Planning: 4.2s
- Retrieval: 0.5s
- Answer synthesis: 34.7s

**Cost:**
- Per query: ~$0.0015 USD (~NT$0.05)
- 1,000 queries/month: ~$1.50 USD (~NT$45)
- Input: 4,500 tokens @ $0.15/1M
- Output: 1,300 tokens @ $0.60/1M

### Local LLM (qwen2.5:7b)

**Performance:**
- Query time: ~60-120 seconds (hardware dependent)
- Planning: 8-15s
- Retrieval: 0.5s
- Answer synthesis: 50-100s

**Cost:**
- Per query: $0 (free)
- Hardware: One-time cost
- 8GB VRAM GPU recommended

**Trade-offs:**
- ✅ No per-query cost
- ✅ Complete data privacy
- ✅ No internet required
- ❌ Slower than cloud
- ❌ Requires GPU/powerful CPU
- ❌ Setup required

---

## Troubleshooting

### Error: "OpenAI API key not found"

**Cause:** Missing or invalid OPENAI_API_KEY in `.env`

**Fix:**
1. Create `.env` file in `backend/` directory
2. Add: `OPENAI_API_KEY=sk-your-key-here`
3. Get key from https://platform.openai.com/api-keys

### Error: "Connection refused" (Local LLM)

**Cause:** Local LLM server not running

**Fix:**
```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/v1/models
```

### Error: "Model not found" (Local LLM)

**Cause:** Model not downloaded

**Fix:**
```bash
# Pull the model
ollama pull qwen2.5:7b

# List available models
ollama list
```

### Slow performance with local LLM

**Options:**
1. Use smaller model: `qwen2.5:7b` (4.7GB)
2. Enable GPU acceleration
3. Use quantized models (Q4, Q5)
4. Switch to OpenAI for faster results

### Poor quality results

**For OpenAI:**
- Try larger model: `gpt-4o` or `gpt-4-turbo`
- Check relevance threshold in action_agent.py

**For Local LLM:**
- Use larger model: `qwen2.5:14b` or `qwen2.5:32b`
- Ensure GPU acceleration is working
- Consider switching to OpenAI for critical queries

---

## Development

### Running Tests

```bash
cd backend
uv run pytest
```

### Manual Testing

```bash
# Test LangGraph workflow
uv run python test_langgraph.py

# Test specific query
uv run finagent query "玉山銀行洗錢防制裁罰" --max-results 5
```

### Architecture Diagram

```
┌─────────────┐
│   User CLI  │
└──────┬──────┘
       │
       v
┌──────────────────┐
│  Orchestrator    │
└──────┬───────────┘
       │
       v
┌──────────────────────────────────────────┐
│         LangGraph Workflow               │
│                                          │
│  ┌──────────┐   ┌──────────┐           │
│  │ Planning │──>│  Action  │           │
│  │  Agent   │   │  Agent   │           │
│  └──────────┘   └────┬─────┘           │
│                      │                  │
│                      v                  │
│  ┌──────────┐   ┌──────────┐           │
│  │Validation│──>│  Answer  │           │
│  │  Agent   │   │  Agent   │           │
│  └──────────┘   └──────────┘           │
└──────────────────────────────────────────┘
       │
       v
┌──────────────────┐
│  Vector DB       │
│  (Chroma)        │
└──────────────────┘
```

---

## Documentation

- [LLM Configuration Guide](LLM_CONFIG.md) - Detailed LLM setup
- [LangGraph Implementation](LANGGRAPH_IMPLEMENTATION.md) - Multi-agent architecture
- [Boundary Tests](BOUNDARY_TESTS.md) - Edge case testing
- [CLI Guide](CLI_GUIDE.md) - Complete CLI documentation (if exists)
- [RAG Quickstart](RAG_QUICKSTART.md) - RAG pipeline details (if exists)

---

## Feature Status

### ✅ Implemented

- [x] CLI interface with REPL
- [x] LangGraph multi-agent workflow
- [x] LLM-powered answer synthesis
- [x] OpenAI integration (GPT-4o-mini)
- [x] Local LLM support (Ollama/LM Studio/vLLM)
- [x] Interactive LLM configuration (`/config llm`)
- [x] RAG document processing
- [x] Semantic search with relevance filtering
- [x] Citation tracking and formatting
- [x] Traditional Chinese support
- [x] Final answer summary section

### 🚧 Planned

- [ ] PDF/DOCX/HTML document support
- [ ] Local embedding models
- [ ] Web search integration
- [ ] Database query tools
- [ ] Export to PDF/Markdown
- [ ] Multi-user collaboration
- [ ] API server mode
- [ ] Web UI

---

## Version History

- **v0.0.1-beta** (2025-01-12) - LangGraph multi-agent, LLM configuration, final answer
- **v0.0.1-alpha** (2025-01-12) - Initial CLI and RAG implementation

---

## License

MIT License - See LICENSE file for details
