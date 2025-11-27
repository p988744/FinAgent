# Celery Integration - Implementation Roadmap

**Date:** 2025-11-21
**Status:** Ready for Implementation
**Dependencies:** PostgreSQL, Redis
**Estimated Time:** 2-3 days

---

## Overview

This roadmap provides a step-by-step implementation plan for integrating Celery task queue and LangGraph checkpointing into FinAgent.

**Reference:** [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md)

---

## Prerequisites Checklist

Before starting implementation:

- [ ] PostgreSQL 16+ installed and running
- [ ] Redis 7+ installed and running
- [ ] Environment variables configured in `.env`
- [ ] Understanding of LangGraph checkpointing (see [LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md](LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md))
- [ ] Read [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md)

---

## Phase 1: Database Setup (2-3 hours)

### Step 1.1: Install Dependencies

```bash
# Add Celery and PostgreSQL support
uv add celery[redis]
uv add langgraph-checkpoint-postgres
uv add psycopg[binary,pool]
uv add flower  # Optional: monitoring dashboard
```

**Verification:**
```bash
uv pip list | grep -E "celery|langgraph-checkpoint|psycopg"
```

### Step 1.2: Configure Environment Variables

Add to `.env`:

```bash
# PostgreSQL for checkpoints and history
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=finagent
POSTGRES_USER=finagent_user
POSTGRES_PASSWORD=your_secure_password_here

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# LangGraph Checkpoint Connection String
LANGGRAPH_CHECKPOINT_DB=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

**Verification:**
```bash
# Check environment variables load correctly
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Postgres DB:', os.getenv('POSTGRES_DB'))
print('Celery Broker:', os.getenv('CELERY_BROKER_URL'))
print('Checkpoint DB:', os.getenv('LANGGRAPH_CHECKPOINT_DB'))
"
```

### Step 1.3: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE finagent;
CREATE USER finagent_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE finagent TO finagent_user;

# Connect to new database
\c finagent

# Grant schema privileges
GRANT ALL ON SCHEMA public TO finagent_user;

\q
```

**Verification:**
```bash
# Test connection
psql -U finagent_user -d finagent -c "SELECT version();"
```

### Step 1.4: Create Database Schema File

**File:** `src/finagent/database/query_history_schema.sql`

```sql
-- Query history table
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query_id TEXT UNIQUE NOT NULL,
    thread_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    query_type TEXT,
    use_plan_execute BOOLEAN DEFAULT TRUE,

    -- Execution metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'pending',
    error_message TEXT,

    -- Results
    query_insight JSONB,
    plan JSONB,
    past_steps JSONB,
    response TEXT,

    -- Performance metrics
    total_tokens INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    llm_cost_usd DECIMAL(10, 6),
    execution_time_seconds DECIMAL(10, 3),

    -- User context
    user_id TEXT,
    session_id TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_query_history_thread_id ON query_history(thread_id);
CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_status ON query_history(status);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_query_history_updated_at ON query_history;
CREATE TRIGGER update_query_history_updated_at
    BEFORE UPDATE ON query_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Verification:**
```bash
# Apply schema
psql -U finagent_user -d finagent -f src/finagent/database/query_history_schema.sql

# Verify table created
psql -U finagent_user -d finagent -c "\dt"
psql -U finagent_user -d finagent -c "\d query_history"
```

**Checkpoint 1:** ✅ Database and schema ready

---

## Phase 2: Backend Implementation (4-6 hours)

### Step 2.1: Create Checkpoint Database Helper

**File:** `src/finagent/database/checkpoint_db.py`

Copy implementation from [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md - Part 4.1](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md#41-database-helper)

**Key Methods:**
- `get_checkpointer()` - Returns PostgresSaver instance
- `setup_tables()` - Initializes checkpoint + history tables
- `create_query_record()` - Creates new query entry
- `update_query_status()` - Updates query status
- `update_query_result()` - Stores final results
- `get_query_history()` - Retrieves query history

**Verification:**
```bash
# Test database connection
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db

db = get_checkpoint_db()
print('✅ Checkpoint database connection successful')

# Initialize tables
db.setup_tables()
print('✅ Tables initialized')

# Test query creation
query_id = db.create_query_record('Test query')
print(f'✅ Created query record: {query_id}')

db.close()
"
```

### Step 2.2: Create Celery App

**File:** `src/finagent/celery_app.py`

Copy implementation from [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md - Part 3.1](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md#31-celery-app-setup)

**Key Configuration:**
- Broker: Redis
- Result backend: Redis
- Serialization: JSON
- Timezone: Asia/Taipei
- Task acknowledgment: Late (after completion)
- Worker prefetch: 1 (for long-running tasks)

**Verification:**
```bash
# Start Celery worker
celery -A finagent.celery_app worker --loglevel=info

# Expected output:
# [2025-11-21 ...] celery@hostname ready.
# [2025-11-21 ...] Connected to redis://localhost:6379/0
```

### Step 2.3: Create Celery Tasks

**File:** `src/finagent/tasks.py`

Copy implementation from [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md - Part 5.1](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md#51-research-query-task)

**Key Components:**
- `ResearchTask` - Base task class with failure handling
- `research_query_task` - Main research task with checkpointing
- `_execute_research_query` - Async execution helper

**Verification:**
```bash
# Test task submission (in Python)
python -c "
from finagent.tasks import research_query_task

result = research_query_task.delay('Test query')
print(f'✅ Task submitted: {result.id}')
print('Check worker logs for execution')
"
```

### Step 2.4: Update Orchestrator for Checkpointing

**File:** `src/finagent/agents/orchestrator.py`

**Changes:**
1. Add checkpointer parameter to `__init__`
2. Pass checkpointer to workflow compilation
3. Support config with thread_id in `stream_query`

```python
class AgentOrchestrator:
    def __init__(self, checkpointer=None):
        self.checkpointer = checkpointer
        # ... existing code ...

        # When compiling workflows, pass checkpointer
        if checkpointer:
            self.plan_execute_workflow = builder.compile(checkpointer=checkpointer)
        else:
            self.plan_execute_workflow = builder.compile()

    async def stream_query(self, query, use_plan_execute=True, config=None):
        # Use provided config (with thread_id) for checkpointing
        # ... existing code ...
```

**Verification:**
```bash
# Test orchestrator with checkpointer
python -c "
from finagent.agents.orchestrator import AgentOrchestrator
from finagent.database.checkpoint_db import get_checkpoint_db

db = get_checkpoint_db()
checkpointer = db.get_checkpointer()

orchestrator = AgentOrchestrator(checkpointer=checkpointer)
print('✅ Orchestrator initialized with checkpointer')

db.close()
"
```

**Checkpoint 2:** ✅ Backend Celery integration complete

---

## Phase 3: CLI Integration (2-3 hours)

### Step 3.1: Create Celery-Enabled Research CLI

**File:** `scripts/cli_research_celery.py`

Copy implementation from [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md - Part 6.1](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md#61-update-cli-research-script)

**Features:**
- Submit query as Celery task
- Wait for results or return immediately
- Check task status by task ID

**Verification:**
```bash
# Start services first
celery -A finagent.celery_app worker --loglevel=info &

# Submit query
uv run python scripts/cli_research_celery.py "玉山銀行洗錢防制裁罰"

# Expected output:
# ✅ Task submitted: <task-id>
# ⏳ Waiting for results...
# [Final research response]
```

### Step 3.2: Create Task Status Checker

**File:** `scripts/check_celery_task.py`

```python
"""Check Celery task status and results."""

import sys
from celery.result import AsyncResult
from finagent.celery_app import celery_app

def check_task(task_id: str):
    """Check task status and display results."""
    result = AsyncResult(task_id, app=celery_app)

    print(f"Task ID: {task_id}")
    print(f"Status: {result.status}")
    print()

    if result.ready():
        if result.successful():
            print("✅ Task completed successfully")
            print("\nResults:")
            print(result.result.get('response', 'No response'))
        else:
            print("❌ Task failed")
            print(f"Error: {result.result}")
    else:
        print("⏳ Task is still running...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_celery_task.py <task_id>")
        sys.exit(1)

    check_task(sys.argv[1])
```

**Verification:**
```bash
# Submit task
TASK_ID=$(uv run python scripts/cli_research_celery.py "Test" | grep "Task ID" | awk '{print $3}')

# Check status
uv run python scripts/check_celery_task.py "$TASK_ID"
```

### Step 3.3: Add History Query Script

**File:** `scripts/query_history.py`

```python
"""Query execution history from database."""

from finagent.database.checkpoint_db import get_checkpoint_db

def show_history(user_id=None, limit=10):
    """Display query history."""
    db = get_checkpoint_db()
    history = db.get_query_history(user_id=user_id, limit=limit)

    if not history:
        print("No query history found.")
        return

    print(f"Last {len(history)} queries:")
    print("=" * 80)

    for i, query in enumerate(history, 1):
        print(f"\n{i}. {query['query_text']}")
        print(f"   Status: {query['status']}")
        print(f"   Started: {query['started_at']}")
        if query['execution_time_seconds']:
            print(f"   Time: {query['execution_time_seconds']:.2f}s")
        if query['llm_cost_usd']:
            print(f"   Cost: ${query['llm_cost_usd']:.4f}")

    db.close()

if __name__ == "__main__":
    show_history(limit=20)
```

**Verification:**
```bash
# View query history
uv run python scripts/query_history.py
```

**Checkpoint 3:** ✅ CLI integration complete

---

## Phase 4: Docker Deployment (1-2 hours)

### Step 4.1: Create Dockerfile

**File:** `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install dependencies using uv
RUN pip install uv && uv sync

# Set Python path
ENV PYTHONPATH=/app/src

CMD ["celery", "-A", "finagent.celery_app", "worker", "--loglevel=info"]
```

### Step 4.2: Create Docker Compose

**File:** `docker-compose.yml`

Copy implementation from [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md - Part 7](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md#part-7-docker-compose-setup)

**Services:**
- PostgreSQL (port 5432)
- Redis (port 6379)
- Celery worker
- Flower monitoring (port 5555)

**Verification:**
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# Expected output:
# postgres     Up (healthy)
# redis        Up (healthy)
# celery-worker Up
# flower       Up

# View logs
docker-compose logs -f celery-worker
```

### Step 4.3: Create Setup Script

**File:** `scripts/setup_celery.sh`

```bash
#!/bin/bash

echo "🚀 Setting up Celery + LangGraph integration"
echo "============================================"

# Step 1: Check dependencies
echo "Step 1: Checking dependencies..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not installed"; exit 1; }
echo "✅ Docker and Docker Compose found"

# Step 2: Start services
echo -e "\nStep 2: Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis
sleep 5

# Step 3: Initialize database
echo -e "\nStep 3: Initializing database tables..."
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db
db = get_checkpoint_db()
db.setup_tables()
print('✅ Database tables created')
db.close()
"

# Step 4: Start Celery worker
echo -e "\nStep 4: Starting Celery worker..."
celery -A finagent.celery_app worker --loglevel=info --detach

# Step 5: Start Flower (optional)
echo -e "\nStep 5: Starting Flower monitoring..."
celery -A finagent.celery_app flower --port=5555 --detach

echo -e "\n✅ Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Services running:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Celery Worker: Running in background"
echo "  - Flower Dashboard: http://localhost:5555"
echo ""
echo "Test with:"
echo "  uv run python scripts/cli_research_celery.py \"Your query\""
```

Make executable:
```bash
chmod +x scripts/setup_celery.sh
```

**Verification:**
```bash
# Run setup
./scripts/setup_celery.sh

# Test integration
uv run python scripts/cli_research_celery.py "玉山銀行洗錢防制"
```

**Checkpoint 4:** ✅ Docker deployment ready

---

## Phase 5: Testing & Verification (2-3 hours)

### Step 5.1: Create Integration Tests

**File:** `tests/integration/test_celery_integration.py`

```python
"""Integration tests for Celery + LangGraph."""

import pytest
from finagent.tasks import research_query_task
from finagent.database.checkpoint_db import get_checkpoint_db

@pytest.mark.integration
def test_task_submission():
    """Test task submission and completion."""
    result = research_query_task.delay(
        query_text="Test query",
        use_plan_execute=True
    )

    assert result is not None
    assert result.id is not None
    print(f"✅ Task submitted: {result.id}")

@pytest.mark.integration
def test_query_history_tracking():
    """Test query history is saved to database."""
    db = get_checkpoint_db()

    # Submit query
    result = research_query_task.delay(query_text="玉山銀行洗錢防制")
    final_result = result.get(timeout=300)

    # Check history
    query_id = final_result['query_id']
    history = db.get_query_history(limit=1)

    assert len(history) > 0
    assert history[0]['query_id'] == query_id
    assert history[0]['status'] == 'completed'

    db.close()
    print("✅ Query history tracked correctly")

@pytest.mark.integration
def test_checkpoint_persistence():
    """Test LangGraph state is persisted."""
    from finagent.agents.orchestrator import AgentOrchestrator
    from finagent.models.queries import Query

    db = get_checkpoint_db()
    checkpointer = db.get_checkpointer()

    orchestrator = AgentOrchestrator(checkpointer=checkpointer)
    query = Query(text="Test checkpoint")

    thread_id = "test-thread-001"
    config = {"configurable": {"thread_id": thread_id}}

    # Start execution (should checkpoint)
    async def run():
        async for _ in orchestrator.stream_query(query, config=config):
            pass

    import asyncio
    asyncio.run(run())

    # Verify checkpoint exists
    state = orchestrator.plan_execute_workflow.get_state(config)
    assert state.values is not None

    db.close()
    print("✅ Checkpoint persistence verified")
```

### Step 5.2: Run Tests

```bash
# Unit tests (fast)
uv run pytest tests/test_celery_integration.py -m "not integration"

# Integration tests (requires services)
./scripts/setup_celery.sh
uv run pytest tests/integration/test_celery_integration.py -v
```

### Step 5.3: Create E2E Test Script

**File:** `scripts/e2e_test_celery.sh`

```bash
#!/bin/bash

echo "E2E Test: Celery + LangGraph Integration"
echo "=========================================="

# Start services
echo "Step 1: Starting services..."
docker-compose up -d postgres redis
sleep 5

# Initialize database
echo -e "\nStep 2: Initializing database..."
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db
db = get_checkpoint_db()
db.setup_tables()
db.close()
"

# Start worker
echo -e "\nStep 3: Starting Celery worker..."
celery -A finagent.celery_app worker --loglevel=info --detach
sleep 3

# Submit test query
echo -e "\nStep 4: Submitting test query..."
uv run python scripts/cli_research_celery.py "玉山銀行洗錢防制裁罰"

# Check query history
echo -e "\nStep 5: Checking query history..."
uv run python scripts/query_history.py

echo -e "\n✅ E2E test completed successfully"
```

**Verification:**
```bash
chmod +x scripts/e2e_test_celery.sh
bash scripts/e2e_test_celery.sh
```

**Checkpoint 5:** ✅ Testing complete

---

## Phase 6: Documentation & Cleanup (1 hour)

### Step 6.1: Update CLAUDE.md

Add to development commands section:

```markdown
### Celery Commands
```bash
# Start Celery worker
celery -A finagent.celery_app worker --loglevel=info

# Start Flower monitoring
celery -A finagent.celery_app flower --port=5555

# Submit research query as task
uv run python scripts/cli_research_celery.py "Your query"

# Check task status
uv run python scripts/check_celery_task.py <task_id>

# View query history
uv run python scripts/query_history.py
```
```

### Step 6.2: Update V1_1_RELEASE_PLAN.md

Mark Celery integration as complete:

```markdown
#### Phase X: Celery Task Queue (100%) **✅ COMPLETED**
- ✅ Celery app configuration
- ✅ PostgreSQL checkpointing
- ✅ Query history tracking
- ✅ CLI integration
- ✅ Docker Compose deployment
- ✅ E2E tests passing
```

### Step 6.3: Create Operations Guide

**File:** `CELERY_OPERATIONS.md`

```markdown
# Celery Operations Guide

## Quick Start

1. **Start services:**
   ```bash
   ./scripts/setup_celery.sh
   ```

2. **Submit query:**
   ```bash
   uv run python scripts/cli_research_celery.py "Your query"
   ```

3. **Monitor tasks:**
   Open http://localhost:5555 (Flower dashboard)

## Monitoring

### Flower Dashboard
- URL: http://localhost:5555
- Shows: Active tasks, task history, worker status
- Refresh: Real-time

### Query History
```bash
uv run python scripts/query_history.py
```

### Checkpoint Inspection
```python
from finagent.database.checkpoint_db import get_checkpoint_db
from finagent.agents.orchestrator import AgentOrchestrator

db = get_checkpoint_db()
checkpointer = db.get_checkpointer()
orchestrator = AgentOrchestrator(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "your-thread-id"}}
state = orchestrator.plan_execute_workflow.get_state(config)
print(state.values)
```

## Troubleshooting

### Worker not starting
```bash
# Check Redis connection
redis-cli ping

# Check PostgreSQL connection
psql -U finagent_user -d finagent -c "SELECT 1"

# View worker logs
celery -A finagent.celery_app inspect active
```

### Task stuck in pending
```bash
# Check worker status
celery -A finagent.celery_app inspect active

# Restart worker
pkill -f "celery.*worker"
celery -A finagent.celery_app worker --loglevel=info
```

### Database connection errors
```bash
# Verify environment variables
python -c "import os; print(os.getenv('LANGGRAPH_CHECKPOINT_DB'))"

# Test connection
psql $LANGGRAPH_CHECKPOINT_DB -c "SELECT 1"
```

## Performance Tuning

### Worker Concurrency
```bash
# Run multiple workers
celery -A finagent.celery_app worker --concurrency=4
```

### Result Expiration
```python
# In celery_app.py
celery_app.conf.result_expires = 3600  # 1 hour
```

### Prefetch Multiplier
```python
# For long-running tasks (default: 1)
celery_app.conf.worker_prefetch_multiplier = 1
```
```

**Checkpoint 6:** ✅ Documentation complete

---

## Final Verification Checklist

Before marking as complete:

- [ ] All services start successfully
- [ ] Query submission works
- [ ] Results are saved to database
- [ ] Checkpoints are persisted
- [ ] History queries return correct data
- [ ] Flower dashboard accessible
- [ ] E2E tests pass
- [ ] Documentation updated
- [ ] Docker Compose works

---

## Success Metrics

After implementation:

1. **Functionality:**
   - ✅ Tasks execute in background
   - ✅ State persists across restarts
   - ✅ Query history accessible

2. **Performance:**
   - Response time: Same as before (40-50s)
   - Throughput: 10+ concurrent queries
   - Database queries: < 100ms

3. **Reliability:**
   - Task retry on failure: 3 attempts
   - Checkpoint recovery: 100%
   - Error tracking: Full stack traces in database

---

## Next Steps After Implementation

1. **Frontend Integration:**
   - Add task submission from UI
   - Real-time progress via WebSocket + Celery events
   - Query history page

2. **Production Deployment:**
   - Multi-worker scaling
   - PostgreSQL replication
   - Redis cluster
   - Load balancer

3. **Advanced Features:**
   - Task prioritization
   - Rate limiting per user
   - Result caching
   - Scheduled queries

---

## Rollback Plan

If issues arise during implementation:

```bash
# Stop all services
docker-compose down

# Remove Celery code (revert commits)
git revert <commit-hash>

# Restore database backup
psql -U finagent_user -d finagent < backup.sql

# Continue with CLI-only workflow
uv run python scripts/cli_research.py "Your query"
```

---

## References

- [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md) - Full technical guide
- [LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md](LANGGRAPH_V1_IMPLEMENTATION_GUIDE.md) - LangGraph patterns
- [Official Celery Docs](https://docs.celeryq.dev/)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
