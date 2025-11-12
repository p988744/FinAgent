# Legal Research Agent (法律研究代理系統)

A specialized AI-powered legal research system for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan.

## Overview

This system uses a multi-agent architecture to help legal professionals and researchers efficiently search, analyze, and cite Taiwan regulatory enforcement actions, particularly focusing on banking and financial regulations.

**Current Status:** MVP Development (v0.1.0)

**Supported Regulatory Bodies:**
- 金管會 (Financial Supervisory Commission) - MVP Focus
- 中央銀行 (Central Bank) - Coming Soon
- 公平會 (Fair Trade Commission) - Coming Soon

## Features (MVP)

- ✅ Traditional Chinese query processing
- ✅ Multi-agent research system (Planning, Action, Answer agents)
- ✅ RAG-based document analysis with vector search
- ✅ Taiwan legal citation formatting
- ✅ **Interactive CLI (REPL) Interface**
- ✅ LLM-powered document metadata extraction
- ✅ Automated document indexing with progress tracking

## Tech Stack

- Python 3.11+
- LangChain + LangGraph (Multi-agent orchestration)
- OpenAI GPT-4 / Local LLM support (via OpenAI-compatible API)
- Chroma Vector Database
- Rich CLI with prompt-toolkit
- uv Package Manager

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key (or local LLM like Ollama)

### Installation

```bash
cd backend

# Install uv (if not already installed)
pip install uv

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Usage

**Interactive REPL Mode (Recommended):**

```bash
uv run finagent

# You'll see:
# finagent>
# Now you can type queries directly in Traditional Chinese!

# Example queries:
finagent> 玉山銀行洗錢防制裁罰
finagent> 2020年金管會裁罰案件
finagent> /help  # Show all commands
```

**Single Query Mode:**

```bash
# Quick query without entering REPL
uv run finagent query "玉山銀行洗錢防制裁罰"
```

📖 **See [CLI_GUIDE.md](CLI_GUIDE.md) for complete CLI documentation**

## Development

### Git Flow Workflow

```bash
# Create a new feature
git checkout develop
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push origin feature/my-feature
```

### Development Commands

```bash
cd backend

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=finagent

# Format code
uv run black src/

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## Project Structure

```
finagent/
├── backend/          # Python backend
│   ├── src/
│   │   └── finagent/ # Main package (src layout)
│   │       ├── cli/  # CLI interface
│   │       ├── agents/ # Multi-agent system
│   │       ├── document_processing/ # RAG pipeline
│   │       └── tools/ # Research tools
│   ├── tests/        # Test suite
│   ├── data/         # Local data storage
│   └── model_config.yml # LLM model configuration
└── docs/             # Documentation
```


## Documentation

- **[CLI Usage Guide](CLI_GUIDE.md)** - Complete CLI documentation with examples
- [MVP Implementation Plan](MVP_PLAN.md)
- [Quickstart Guide](QUICKSTART.md)
- [Claude AI Context](CLAUDE.md)
- [Original Specification](法律研究代理系統規格書.md)

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions, please open an issue on GitHub.
