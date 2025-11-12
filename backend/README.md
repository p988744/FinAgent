# FinAgent Backend

FastAPI backend for the Taiwan Legal Research Agent System.

## Setup

```bash
# Install uv if not already installed
pip install uv

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Run development server
uv run uvicorn finagent.main:app --reload
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=finagent --cov-report=html

# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Type check
uv run mypy src/
```

## Project Structure

```
src/finagent/
├── __init__.py
├── main.py              # FastAPI application
├── config.py            # Configuration
├── agents/              # Multi-agent system
├── tools/               # Research tools
├── document_processing/ # Document pipeline
├── models/              # Pydantic models
├── services/            # Business logic
├── api/                 # API routes
└── utils/               # Utilities
```
