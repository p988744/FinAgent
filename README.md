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
- ✅ Web-based user interface
- ✅ Docker deployment

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- LangChain
- OpenAI GPT-4
- Chroma Vector Database
- uv Package Manager

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- React 18
- Tailwind CSS

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- OpenAI API Key

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd finagent

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your OpenAI API key

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

**Backend:**

```bash
cd backend

# Install uv (if not already installed)
pip install uv

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run the server
uv run uvicorn finagent.main:app --reload

# API available at http://localhost:8000
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local

# Run development server
npm run dev

# App available at http://localhost:3000
```

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

### Backend Development

```bash
# Run tests
cd backend
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

### Frontend Development

```bash
cd frontend

# Run tests
npm test

# Lint
npm run lint

# Build
npm run build
```

## Project Structure

```
finagent/
├── backend/          # Python backend with FastAPI
│   ├── src/
│   │   └── finagent/ # Main package (src layout)
│   ├── tests/        # Test suite
│   └── data/         # Local data storage
├── frontend/         # Next.js frontend
│   └── src/
│       ├── app/      # App router pages
│       └── components/ # React components
├── docker/           # Docker configurations
└── docs/             # Documentation
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Documentation

- [MVP Implementation Plan](MVP_PLAN.md)
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
