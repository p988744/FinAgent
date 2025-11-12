# Legal Research Agent MVP - Implementation Plan

## Executive Summary

This plan outlines the development of a Minimum Viable Product (MVP) for the Taiwan Legal Research Agent System, using modern development practices with git flow workflow, uv package management, and src source layout.

**Target Timeline:** 6 weeks
**Team Size:** 1-3 developers
**Tech Stack:** Python (Backend), React/Next.js (Frontend), uv package manager

---

## MVP Scope Definition

### Core Features (Must Have)

1. **Query Processing**
   - Accept Traditional Chinese legal queries
   - Basic query understanding and planning
   - Simple single-source search (金管會 only for MVP)

2. **Document Search & Retrieval**
   - Search enforcement actions from 金管會
   - Retrieve basic document metadata
   - Simple PDF text extraction (no OCR for MVP)

3. **Basic RAG System**
   - Vector database setup (Chroma - self-hosted)
   - Document chunking (simple paragraph-based)
   - Semantic search within documents

4. **Answer Generation**
   - Basic answer synthesis with citations
   - Taiwan legal citation format
   - Confidence scoring (simple heuristic-based)

5. **Simple Web Interface**
   - Query input form
   - Results display with citations
   - Basic document preview

### Deferred to Post-MVP

- Multi-regulator support (央行, 公平會)
- Advanced OCR for scanned PDFs
- Court judgment integration
- Precedent case comparison
- Multi-hop reasoning
- Advanced citation validation
- Export to PDF/DOCX
- User authentication
- Saved research sessions

---

## Project Structure (Src Layout)

```
finagent/
├── .git/
├── .github/
│   └── workflows/           # GitHub Actions CI/CD
├── backend/
│   ├── .python-version      # Python version for uv
│   ├── pyproject.toml       # uv project config
│   ├── uv.lock             # uv lockfile
│   ├── README.md
│   ├── src/
│   │   └── finagent/
│   │       ├── __init__.py
│   │       ├── main.py              # FastAPI app entry
│   │       ├── config.py            # Configuration management
│   │       ├── agents/              # Multi-agent system
│   │       │   ├── __init__.py
│   │       │   ├── base.py          # Base agent class
│   │       │   ├── planner.py       # Planning agent
│   │       │   ├── action.py        # Action agent
│   │       │   ├── answer.py        # Answer agent
│   │       │   └── orchestrator.py  # Agent orchestration
│   │       ├── tools/               # Research tools
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── fsc_search.py    # 金管會 search
│   │       │   ├── document_retrieval.py
│   │       │   └── rag_tools.py
│   │       ├── document_processing/ # Document pipeline
│   │       │   ├── __init__.py
│   │       │   ├── pdf_parser.py
│   │       │   ├── chunker.py
│   │       │   ├── embeddings.py
│   │       │   └── vector_store.py
│   │       ├── models/              # Pydantic models
│   │       │   ├── __init__.py
│   │       │   ├── citations.py
│   │       │   ├── documents.py
│   │       │   ├── queries.py
│   │       │   └── answers.py
│   │       ├── services/            # Business logic
│   │       │   ├── __init__.py
│   │       │   ├── scraper.py       # FSC web scraping
│   │       │   ├── entity_resolver.py
│   │       │   └── citation_formatter.py
│   │       ├── api/                 # FastAPI routes
│   │       │   ├── __init__.py
│   │       │   ├── routes/
│   │       │   │   ├── research.py
│   │       │   │   ├── documents.py
│   │       │   │   └── health.py
│   │       │   └── dependencies.py
│   │       └── utils/               # Utilities
│   │           ├── __init__.py
│   │           ├── chinese_nlp.py
│   │           ├── date_utils.py
│   │           └── validators.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_agents/
│   │   │   ├── test_tools/
│   │   │   └── test_services/
│   │   └── integration/
│   │       └── test_research_flow.py
│   ├── scripts/
│   │   ├── setup_db.py
│   │   └── seed_data.py
│   └── data/                        # Local data storage
│       ├── documents/
│       └── vector_db/
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── README.md
│   ├── src/
│   │   ├── app/                     # Next.js 14 App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── research/
│   │   │   │   └── page.tsx
│   │   │   └── api/                 # API proxy routes
│   │   ├── components/
│   │   │   ├── QueryInput.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   ├── CitationCard.tsx
│   │   │   └── DocumentPreview.tsx
│   │   ├── lib/
│   │   │   ├── api.ts               # Backend API client
│   │   │   └── types.ts             # TypeScript types
│   │   └── styles/
│   │       └── globals.css
│   ├── public/
│   └── tests/
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── api.md
│   ├── architecture.md
│   └── setup.md
├── .gitignore
├── .gitattributes
├── CLAUDE.md                        # AI assistant context
├── MVP_PLAN.md                      # This file
├── 法律研究代理系統規格書.md          # Original spec
└── README.md                        # Project overview
```

---

## Technology Stack

### Backend
- **Language:** Python 3.11+
- **Package Manager:** uv (https://github.com/astral-sh/uv)
- **Web Framework:** FastAPI
- **LLM Framework:** LangChain
- **LLM Provider:** OpenAI GPT-4 (or Claude 3.5 Sonnet)
- **Vector DB:** Chroma (self-hosted)
- **Embeddings:** OpenAI text-embedding-3-small
- **PDF Processing:** PyMuPDF (fitz)
- **Chinese NLP:** jieba (OCR/advanced NLP deferred)
- **HTTP Client:** httpx
- **Testing:** pytest, pytest-asyncio
- **Validation:** Pydantic v2

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **UI Library:** React 18
- **Styling:** Tailwind CSS
- **Component Library:** shadcn/ui
- **State Management:** React Context / Zustand (if needed)
- **API Client:** axios / fetch
- **Testing:** Jest, React Testing Library

### Infrastructure
- **Containerization:** Docker, Docker Compose
- **Version Control:** Git with git flow
- **CI/CD:** GitHub Actions
- **Local Development:** Docker Compose

---

## Git Flow Workflow

### Branch Structure

```
main (production-ready code)
├── develop (integration branch)
    ├── feature/backend-setup
    ├── feature/agent-system
    ├── feature/rag-pipeline
    ├── feature/fsc-scraper
    ├── feature/frontend-ui
    └── release/v0.1.0
```

### Branch Naming Conventions

- `feature/*` - New features (e.g., `feature/planning-agent`)
- `bugfix/*` - Bug fixes (e.g., `bugfix/citation-format`)
- `hotfix/*` - Critical production fixes
- `release/*` - Release preparation (e.g., `release/v0.1.0`)
- `docs/*` - Documentation updates

### Workflow Steps

1. **Start Feature**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/feature-name
   ```

2. **Develop & Commit**
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

3. **Keep Updated**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/feature-name
   git merge develop
   ```

4. **Create Pull Request**
   - Push to origin
   - Create PR from `feature/*` → `develop`
   - Code review
   - Merge to develop

5. **Release Process**
   ```bash
   git checkout develop
   git checkout -b release/v0.1.0
   # Update version, test, fix bugs
   git checkout main
   git merge release/v0.1.0
   git tag -a v0.1.0 -m "MVP Release"
   git checkout develop
   git merge release/v0.1.0
   ```

### Commit Message Convention (Conventional Commits)

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting, missing semicolons, etc.
refactor: code refactoring
test: add tests
chore: update dependencies, build tasks
```

---

## Development Phases (6 Weeks)

### Week 1: Project Setup & Foundation

#### Sprint 1.1: Infrastructure Setup (Days 1-2)
- [ ] Initialize git repository with git flow
- [ ] Create branch structure (main, develop)
- [ ] Set up backend with uv package manager
  ```bash
  cd backend
  uv init
  uv add fastapi uvicorn pydantic langchain openai chromadb pymupdf jieba httpx
  uv add --dev pytest pytest-asyncio black ruff mypy
  ```
- [ ] Set up frontend with Next.js 14
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind --app
  cd frontend
  npm install axios zustand
  ```
- [ ] Configure Docker and docker-compose
- [ ] Set up GitHub Actions for CI/CD
- [ ] Create src layout structure

#### Sprint 1.2: Core Models & Configuration (Days 3-5)
- [ ] Define Pydantic models (citations, documents, queries, answers)
- [ ] Implement configuration management (environment variables)
- [ ] Set up logging infrastructure
- [ ] Create base classes for agents and tools
- [ ] Database schema design (if using PostgreSQL for metadata)
- [ ] Write initial tests for models

**Deliverable:** Runnable backend server with health check endpoint, basic frontend with routing

---

### Week 2: Document Processing Pipeline

#### Sprint 2.1: PDF Processing & Chunking (Days 1-3)
- [ ] Implement PDF text extraction (PyMuPDF)
- [ ] Create Chinese-aware chunker (paragraph-based)
- [ ] Implement metadata extraction from PDFs
- [ ] Add Chinese text normalization utilities
- [ ] Unit tests for document processing

#### Sprint 2.2: Vector Database & Embeddings (Days 4-5)
- [ ] Set up Chroma vector database
- [ ] Implement embedding generation (OpenAI)
- [ ] Create document indexing pipeline
- [ ] Implement semantic search functionality
- [ ] Integration tests for RAG pipeline

**Deliverable:** Working RAG system that can index and search PDF documents

---

### Week 3: Agent System Core

#### Sprint 3.1: Planning Agent (Days 1-2)
- [ ] Implement planning agent with LangChain
- [ ] Create Traditional Chinese prompts
- [ ] Task decomposition logic
- [ ] Task model with dependencies
- [ ] Unit tests for planning agent

#### Sprint 3.2: Action Agent & Tools (Days 3-5)
- [ ] Implement action agent (tool selection)
- [ ] Create base tool interface
- [ ] Implement FSC search tool (web scraping or mock data)
- [ ] Implement document retrieval tool
- [ ] Implement RAG query tool
- [ ] Tool execution and error handling
- [ ] Integration tests for agent flow

**Deliverable:** Working multi-agent system that can plan and execute simple queries

---

### Week 4: FSC Integration & Answer Generation

#### Sprint 4.1: FSC Data Source (Days 1-3)
- [ ] Implement FSC website scraper (or create mock data API)
- [ ] Parse enforcement action listings
- [ ] Extract document metadata (case numbers, dates, entities)
- [ ] Entity name normalization
- [ ] Cache mechanism for scraped data
- [ ] Tests for scraper

#### Sprint 4.2: Answer Agent & Citations (Days 4-5)
- [ ] Implement answer synthesis agent
- [ ] Create Taiwan legal citation formatter
- [ ] Implement confidence scoring logic
- [ ] Generate structured answers with citations
- [ ] Citation validation logic
- [ ] Tests for answer generation

**Deliverable:** End-to-end query processing with cited answers

---

### Week 5: Frontend Development

#### Sprint 5.1: Core UI Components (Days 1-3)
- [ ] Design and implement QueryInput component
- [ ] Create ResultsDisplay component
- [ ] Build CitationCard component
- [ ] Implement DocumentPreview component
- [ ] Loading states and error handling
- [ ] Component tests

#### Sprint 5.2: API Integration & UX (Days 4-5)
- [ ] Create API client service
- [ ] Connect frontend to backend API
- [ ] Implement query submission flow
- [ ] Display results with citations
- [ ] Add document preview functionality
- [ ] Responsive design
- [ ] End-to-end tests

**Deliverable:** Fully functional web interface

---

### Week 6: Testing, Documentation & Deployment

#### Sprint 6.1: Integration Testing (Days 1-2)
- [ ] End-to-end integration tests
- [ ] Test with real FSC data (if available)
- [ ] Test with sample legal queries
- [ ] Performance testing (response time)
- [ ] Fix critical bugs

#### Sprint 6.2: Documentation & Deployment (Days 3-5)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Setup and installation guide
- [ ] Architecture documentation
- [ ] User guide with examples
- [ ] Docker deployment configuration
- [ ] Create release/v0.1.0 branch
- [ ] Final testing and bug fixes
- [ ] Merge to main and tag v0.1.0
- [ ] Deploy MVP

**Deliverable:** Production-ready MVP with complete documentation

---

## uv Package Management Setup

### Backend Setup

```bash
# Initialize uv project
cd backend
uv init --name finagent --lib

# Add core dependencies
uv add fastapi uvicorn[standard] pydantic pydantic-settings
uv add langchain langchain-openai langchain-community
uv add openai chromadb
uv add pymupdf jieba
uv add httpx beautifulsoup4 lxml
uv add python-multipart
uv add aiofiles

# Add development dependencies
uv add --dev pytest pytest-asyncio pytest-cov
uv add --dev black ruff mypy
uv add --dev pre-commit

# Lock dependencies
uv lock

# Create virtual environment and sync
uv sync
```

### pyproject.toml Example

```toml
[project]
name = "finagent"
version = "0.1.0"
description = "Taiwan Legal Research Agent System"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.5",
    "langchain-community>=0.0.20",
    "openai>=1.10.0",
    "chromadb>=0.4.22",
    "pymupdf>=1.23.0",
    "jieba>=0.42.1",
    "httpx>=0.26.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.1.0",
    "python-multipart>=0.0.6",
    "aiofiles>=23.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Running Commands with uv

```bash
# Run backend server
uv run uvicorn finagent.main:app --reload

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=finagent

# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Type check
uv run mypy src/
```

---

## Environment Configuration

### Backend .env

```env
# LLM Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/vector_db
CHROMA_COLLECTION_NAME=legal_documents

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
API_PORT=8000

# FSC Scraping
FSC_BASE_URL=https://www.fsc.gov.tw
SCRAPING_DELAY_SECONDS=1
SCRAPING_MAX_RETRIES=3

# Feature Flags
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
```

### Frontend .env.local

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Legal Research Agent
```

---

## Docker Setup

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/backend.Dockerfile
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=development
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend/src:/app/src
      - ./backend/data:/app/data
    command: uv run uvicorn finagent.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/frontend.Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    volumes:
      - ./frontend/src:/app/src
    depends_on:
      - backend
    command: npm run dev

  # Optional: PostgreSQL for metadata storage
  # postgres:
  #   image: postgres:16-alpine
  #   environment:
  #     POSTGRES_DB: finagent
  #     POSTGRES_USER: finagent
  #     POSTGRES_PASSWORD: finagent
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### backend.Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "finagent.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Testing Strategy

### Unit Tests
- Models validation
- Utility functions
- Individual agent logic
- Tool implementations

### Integration Tests
- Agent orchestration flow
- RAG pipeline
- API endpoints
- Database operations

### Test Coverage Goals
- Minimum 70% code coverage
- 100% coverage for critical paths (citation formatting, query processing)

### Sample Test Structure

```python
# tests/unit/test_agents/test_planner.py
import pytest
from finagent.agents.planner import PlanningAgent
from finagent.models.queries import Query

@pytest.mark.asyncio
async def test_planning_agent_basic_query():
    agent = PlanningAgent()
    query = Query(text="玉山銀行在2020年的裁罰記錄")

    tasks = await agent.plan(query)

    assert len(tasks) > 0
    assert tasks[0].task_type == "搜尋"
    assert "玉山" in tasks[0].description
```

---

## API Design (MVP)

### Core Endpoints

```
POST   /api/v1/research/query          # Submit research query
GET    /api/v1/research/{query_id}     # Get query results
POST   /api/v1/documents/index         # Index a document
GET    /api/v1/documents/{doc_id}      # Get document metadata
GET    /api/v1/health                  # Health check
```

### Example Request/Response

```json
// POST /api/v1/research/query
{
  "query": "玉山銀行在2020年因洗錢防制違規受到什麼處分？",
  "options": {
    "max_results": 5,
    "include_full_documents": false
  }
}

// Response
{
  "query_id": "uuid-here",
  "status": "completed",
  "answer": {
    "executive_summary": "玉山商業銀行於2020年...",
    "key_findings": [
      "罰款金額：新台幣2.5億元 [引用1]",
      "違規類型：洗錢防制法相關規定 [引用1，第三章]"
    ],
    "detailed_analysis": "...",
    "citations": [
      {
        "id": 1,
        "type": "enforcement_document",
        "formatted": "金融監督管理委員會，金管銀法字第...",
        "url": "https://www.fsc.gov.tw/...",
        "authority": "primary"
      }
    ],
    "confidence_score": "高",
    "confidence_explanation": "基於官方裁罰書..."
  },
  "processing_time_ms": 3500
}
```

---

## Success Metrics (MVP)

### Functional Metrics
- [ ] Successfully process 90%+ of test queries
- [ ] Generate answers with at least 1 primary source citation
- [ ] Average response time < 10 seconds for simple queries
- [ ] Citation format accuracy: 100%

### Technical Metrics
- [ ] API uptime: 95%+
- [ ] Test coverage: 70%+
- [ ] Zero critical security vulnerabilities
- [ ] Docker build success rate: 100%

### User Experience
- [ ] Query submission works without errors
- [ ] Results display clearly with citations
- [ ] Mobile-responsive interface
- [ ] Error messages in Traditional Chinese

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| FSC website structure changes | High | Mock data API, error handling, version snapshots |
| LLM API rate limits | Medium | Implement caching, retry logic, exponential backoff |
| Chinese text processing issues | Medium | Use proven libraries (jieba), extensive testing |
| PDF parsing failures | Medium | Graceful degradation, multiple parser fallbacks |
| Vector DB performance | Low | Index optimization, limit document size in MVP |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Underestimated complexity | High | Time buffers, prioritize core features, defer non-critical |
| Dependency issues | Medium | Lock versions with uv, test early |
| Integration challenges | Medium | Early integration testing, weekly integration |

---

## Next Steps After MVP

### Post-MVP Roadmap

1. **Phase 2: Multi-Source Integration** (Weeks 7-10)
   - Add 央行 (Central Bank) data source
   - Add 公平會 (FTC) data source
   - Court judgment integration

2. **Phase 3: Advanced Features** (Weeks 11-14)
   - OCR for scanned documents
   - Precedent case comparison
   - Advanced citation validation
   - Export to PDF/DOCX

3. **Phase 4: Production Readiness** (Weeks 15-18)
   - User authentication
   - Saved research sessions
   - Usage analytics
   - Performance optimization
   - Production deployment

---

## Quick Start Commands

### Initial Setup

```bash
# Clone and setup git flow
git clone <repo-url>
cd finagent
git checkout -b develop

# Backend setup
cd backend
uv sync
cp .env.example .env
# Edit .env with your API keys
uv run uvicorn finagent.main:app --reload

# Frontend setup (in another terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev

# Docker setup (alternative)
docker-compose up --build
```

### Development Workflow

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Make changes, commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push origin feature/my-feature
# Create PR on GitHub: feature/my-feature -> develop

# After PR approved and merged
git checkout develop
git pull origin develop
git branch -d feature/my-feature
```

---

## Conclusion

This MVP plan provides a realistic 6-week timeline to deliver a functional Legal Research Agent focused on Taiwan's 金管會 enforcement actions. The system will demonstrate core capabilities including:

- Traditional Chinese query processing
- Document search and retrieval
- RAG-based document analysis
- Taiwan legal citation formatting
- Web-based user interface

By using modern tools (uv, Next.js 14) and best practices (git flow, src layout, comprehensive testing), the codebase will be maintainable and ready for future expansion to full production system.

**Key Success Factor:** Start with a focused MVP scope, deliver working software early, and iterate based on real usage feedback.
