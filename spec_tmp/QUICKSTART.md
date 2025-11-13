# Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (recommended)
- OpenAI API Key

## Option 1: Docker (Recommended for Quick Start)

### 1. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 2. Start the application

```bash
# Development mode with hot reload
docker-compose -f docker-compose.dev.yml up

# OR Production mode
docker-compose up --build
```

### 3. Access the application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 4. Test the application

Open http://localhost:3000 and try a query:
```
玉山銀行在2020年因洗錢防制違規受到什麼處分？
```

## Option 2: Local Development

### Backend Setup

```bash
cd backend

# Install uv
pip install uv

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the server
uv run uvicorn finagent.main:app --reload
```

Backend will be available at http://localhost:8000

### Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=finagent

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/integration/ -m integration
```

### Frontend Tests

```bash
cd frontend

# Lint check
npm run lint

# Build test
npm run build
```

## Development Workflow

### Creating a new feature

```bash
# Make sure you're on develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/my-new-feature

# Make changes, commit
git add .
git commit -m "feat: add my new feature"

# Push and create PR
git push origin feature/my-new-feature
```

## Troubleshooting

### Backend won't start

1. Check Python version: `python --version` (should be 3.11+)
2. Check if .env file exists and has OPENAI_API_KEY
3. Try: `cd backend && uv sync --reinstall`

### Frontend won't start

1. Check Node version: `node --version` (should be 18+)
2. Delete node_modules and reinstall: `rm -rf node_modules && npm install`
3. Check if .env.local exists

### Docker issues

1. Rebuild containers: `docker-compose down && docker-compose up --build`
2. Check Docker daemon is running
3. Check .env file has OPENAI_API_KEY

### Tests failing

1. Make sure backend server is not running on port 8000
2. Install dev dependencies: `uv sync --all-extras`
3. Check Python version compatibility

## Next Steps

1. Review [MVP_PLAN.md](MVP_PLAN.md) for development roadmap
2. Read [CLAUDE.md](CLAUDE.md) for system architecture
3. Check [backend/README.md](backend/README.md) for backend details
4. Explore API docs at http://localhost:8000/docs

## Getting Help

- Check logs: `docker-compose logs -f` (for Docker)
- Review error messages in terminal
- Consult documentation files
