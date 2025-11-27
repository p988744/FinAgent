# Celery + LangGraph Integration Guide

**Date:** 2025-11-21
**Version:** v1.1
**Purpose:** Implement async task queue with Celery and persist LangGraph execution state to database

---

## Overview

This guide shows how to:
1. **Run CLI scripts as Celery tasks** - Async background execution
2. **Store graph logs in PostgreSQL** - LangGraph checkpoints
3. **Store query history in database** - Track all queries and results
4. **Enable resume/replay** - Continue interrupted workflows

---

## Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│              │ Submit  │              │ Execute │              │
│   Frontend   ├────────>│  Celery Task ├────────>│  LangGraph   │
│   /CLI       │  Query  │    Queue     │  Graph  │   Workflow   │
│              │         │              │         │              │
└──────────────┘         └──────┬───────┘         └──────┬───────┘
                                │                        │
                                │                        │
                                v                        v
                         ┌──────────────┐         ┌──────────────┐
                         │              │         │              │
                         │  PostgreSQL  │<────────│ Checkpointer │
                         │   Database   │  Save   │   (State)    │
                         │              │         │              │
                         └──────────────┘         └──────────────┘
                                │
                                │
                                v
                         ┌──────────────┐
                         │              │
                         │   History    │
                         │    Table     │
                         │              │
                         └──────────────┘
```

---

## Part 1: Database Schema

### 1.1 LangGraph Checkpoint Tables

LangGraph automatically creates these tables when you call `checkpointer.setup()`:

```sql
-- Created automatically by PostgresSaver
-- DO NOT create manually

-- checkpoints: Stores graph execution state
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- checkpoint_blobs: Stores large binary data
CREATE TABLE checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- checkpoint_writes: Stores pending writes
CREATE TABLE checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    blob BYTEA NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

### 1.2 Query History Table

Add to your existing database schema:

```sql
-- Query history table
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query_id TEXT UNIQUE NOT NULL,          -- UUID for query
    thread_id TEXT NOT NULL,                 -- LangGraph thread ID
    query_text TEXT NOT NULL,                -- User query
    query_type TEXT,                         -- factual/analytical/comparative
    use_plan_execute BOOLEAN DEFAULT TRUE,   -- Workflow type

    -- Execution metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'pending',           -- pending/running/completed/failed
    error_message TEXT,

    -- Results
    query_insight JSONB,                     -- QueryInsight from analyzer
    plan JSONB,                              -- Plan from planner
    past_steps JSONB,                        -- Execution steps
    response TEXT,                           -- Final response

    -- Performance metrics
    total_tokens INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    llm_cost_usd DECIMAL(10, 6),
    execution_time_seconds DECIMAL(10, 3),

    -- User context
    user_id TEXT,
    session_id TEXT,

    -- Indexes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_query_history_thread_id ON query_history(thread_id);
CREATE INDEX idx_query_history_user_id ON query_history(user_id);
CREATE INDEX idx_query_history_status ON query_history(status);
CREATE INDEX idx_query_history_created_at ON query_history(created_at DESC);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_query_history_updated_at
    BEFORE UPDATE ON query_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Part 2: Dependencies

### 2.1 Install Required Packages

```bash
# Celery and message broker
uv add celery[redis]

# LangGraph PostgreSQL checkpointer
uv add langgraph-checkpoint-postgres

# PostgreSQL adapter
uv add psycopg[binary,pool]

# Optional: Flower for monitoring
uv add flower
```

### 2.2 Environment Variables

Add to `.env`:

```bash
# PostgreSQL for checkpoints and history
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=finagent
POSTGRES_USER=finagent_user
POSTGRES_PASSWORD=your_secure_password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# LangGraph
LANGGRAPH_CHECKPOINT_DB=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

---

## Part 3: Celery Configuration

### 3.1 Celery App Setup

**File:** `src/finagent/celery_app.py`

```python
"""Celery application for async task execution."""

import os
from celery import Celery
from finagent.config import settings

# Create Celery app
celery_app = Celery(
    'finagent',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    include=['finagent.tasks']  # Import task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,

    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store more task metadata

    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Retry on worker crash
    worker_prefetch_multiplier=1,  # Disable prefetching for long tasks

    # Performance settings
    worker_max_tasks_per_child=50,  # Restart worker after N tasks
    worker_disable_rate_limits=True,

    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'
)

if __name__ == '__main__':
    celery_app.start()
```

---

## Part 4: LangGraph with Checkpointer

### 4.1 Database Helper

**File:** `src/finagent/database/checkpoint_db.py`

```python
"""Database helpers for LangGraph checkpointing and query history."""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from psycopg import connect
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

logger = logging.getLogger(__name__)


class CheckpointDatabase:
    """Manage PostgreSQL connections for LangGraph checkpoints and query history."""

    def __init__(self, db_uri: Optional[str] = None):
        """Initialize database connection pool."""
        self.db_uri = db_uri or os.getenv('LANGGRAPH_CHECKPOINT_DB')

        if not self.db_uri:
            raise ValueError("LANGGRAPH_CHECKPOINT_DB environment variable not set")

        # Connection pool configuration
        self.connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        }

        # Create connection pool
        self.pool = ConnectionPool(
            conninfo=self.db_uri,
            max_size=20,
            kwargs=self.connection_kwargs
        )

        logger.info(f"Checkpoint database pool created: {self.db_uri}")

    def get_checkpointer(self) -> PostgresSaver:
        """Get PostgresSaver checkpointer instance."""
        checkpointer = PostgresSaver(self.pool)
        return checkpointer

    def setup_tables(self):
        """Setup checkpoint tables and query history table."""
        # Setup LangGraph checkpoint tables
        checkpointer = self.get_checkpointer()
        checkpointer.setup()
        logger.info("LangGraph checkpoint tables created")

        # Setup query history table
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                # Read schema from file
                schema_file = os.path.join(
                    os.path.dirname(__file__),
                    '../../database/query_history_schema.sql'
                )

                if os.path.exists(schema_file):
                    with open(schema_file, 'r') as f:
                        schema_sql = f.read()
                        cur.execute(schema_sql)
                    logger.info("Query history table created")
                else:
                    logger.warning(f"Schema file not found: {schema_file}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    def create_query_record(
        self,
        query_text: str,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Create a new query history record.

        Returns:
            query_id (str): UUID for the query
        """
        query_id = str(uuid.uuid4())
        thread_id = thread_id or str(uuid.uuid4())

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO query_history (
                        query_id, thread_id, query_text,
                        user_id, session_id, status
                    ) VALUES (%s, %s, %s, %s, %s, 'pending')
                    RETURNING query_id
                    """,
                    (query_id, thread_id, query_text, user_id, session_id)
                )
                result = cur.fetchone()
                conn.commit()

        logger.info(f"Created query record: {query_id}")
        return result['query_id']

    def update_query_status(
        self,
        query_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update query status."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE query_history
                    SET status = %s, error_message = %s, updated_at = NOW()
                    WHERE query_id = %s
                    """,
                    (status, error_message, query_id)
                )
                conn.commit()

    def update_query_result(
        self,
        query_id: str,
        query_insight: Optional[Dict] = None,
        plan: Optional[Dict] = None,
        past_steps: Optional[list] = None,
        response: Optional[str] = None,
        total_tokens: Optional[int] = None,
        llm_cost_usd: Optional[float] = None,
        execution_time: Optional[float] = None
    ):
        """Update query with execution results."""
        import json

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE query_history
                    SET
                        query_insight = %s,
                        plan = %s,
                        past_steps = %s,
                        response = %s,
                        total_tokens = %s,
                        llm_cost_usd = %s,
                        execution_time_seconds = %s,
                        status = 'completed',
                        completed_at = NOW(),
                        updated_at = NOW()
                    WHERE query_id = %s
                    """,
                    (
                        json.dumps(query_insight) if query_insight else None,
                        json.dumps(plan) if plan else None,
                        json.dumps(past_steps) if past_steps else None,
                        response,
                        total_tokens,
                        llm_cost_usd,
                        execution_time,
                        query_id
                    )
                )
                conn.commit()

        logger.info(f"Updated query result: {query_id}")

    def get_query_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """Get query history."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        """
                        SELECT * FROM query_history
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (user_id, limit)
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM query_history
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (limit,)
                    )

                return cur.fetchall()

    def close(self):
        """Close connection pool."""
        self.pool.close()
        logger.info("Checkpoint database pool closed")


# Global instance
_checkpoint_db: Optional[CheckpointDatabase] = None


def get_checkpoint_db() -> CheckpointDatabase:
    """Get global checkpoint database instance."""
    global _checkpoint_db
    if _checkpoint_db is None:
        _checkpoint_db = CheckpointDatabase()
    return _checkpoint_db
```

---

## Part 5: Celery Tasks

### 5.1 Research Query Task

**File:** `src/finagent/tasks.py`

```python
"""Celery tasks for async query execution."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from celery import Task
from finagent.celery_app import celery_app
from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query
from finagent.database.checkpoint_db import get_checkpoint_db

logger = logging.getLogger(__name__)


class ResearchTask(Task):
    """Base task for research queries with state tracking."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        query_id = kwargs.get('query_id')
        if query_id:
            checkpoint_db = get_checkpoint_db()
            checkpoint_db.update_query_status(
                query_id=query_id,
                status='failed',
                error_message=str(exc)
            )
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(
    bind=True,
    base=ResearchTask,
    name='finagent.tasks.research_query',
    max_retries=3,
    default_retry_delay=60  # Retry after 1 minute
)
def research_query_task(
    self,
    query_text: str,
    query_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    use_plan_execute: bool = True,
    verbose: bool = False
):
    """
    Execute research query as Celery task.

    Args:
        query_text: The research question
        query_id: UUID for tracking (creates new if None)
        thread_id: LangGraph thread ID for checkpointing
        user_id: User identifier
        session_id: Session identifier
        use_plan_execute: Use plan-and-execute workflow
        verbose: Enable verbose logging

    Returns:
        dict: Query results with metadata
    """
    start_time = datetime.now()
    checkpoint_db = get_checkpoint_db()

    # Create query record if not exists
    if not query_id:
        query_id = checkpoint_db.create_query_record(
            query_text=query_text,
            thread_id=thread_id,
            user_id=user_id,
            session_id=session_id
        )

    # Update status to running
    checkpoint_db.update_query_status(query_id, 'running')

    try:
        # Run async research query
        result = asyncio.run(_execute_research_query(
            query_text=query_text,
            query_id=query_id,
            thread_id=thread_id,
            use_plan_execute=use_plan_execute,
            verbose=verbose
        ))

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Update query results
        checkpoint_db.update_query_result(
            query_id=query_id,
            query_insight=result.get('query_insight'),
            plan=result.get('plan'),
            past_steps=result.get('past_steps'),
            response=result.get('response'),
            total_tokens=result.get('total_tokens'),
            llm_cost_usd=result.get('llm_cost_usd'),
            execution_time=execution_time
        )

        logger.info(f"Query {query_id} completed in {execution_time:.2f}s")

        return {
            'query_id': query_id,
            'status': 'completed',
            'execution_time': execution_time,
            **result
        }

    except Exception as e:
        logger.error(f"Query {query_id} failed: {e}", exc_info=True)
        checkpoint_db.update_query_status(
            query_id=query_id,
            status='failed',
            error_message=str(e)
        )
        raise


async def _execute_research_query(
    query_text: str,
    query_id: str,
    thread_id: Optional[str],
    use_plan_execute: bool,
    verbose: bool
) -> dict:
    """Execute research query with LangGraph checkpointing."""
    checkpoint_db = get_checkpoint_db()
    checkpointer = checkpoint_db.get_checkpointer()

    # Initialize orchestrator with checkpointer
    orchestrator = AgentOrchestrator(checkpointer=checkpointer)

    # Create query object
    query = Query(text=query_text)

    # Build configuration with thread ID
    config = {
        "configurable": {
            "thread_id": thread_id or query_id,
            "query_id": query_id
        }
    }

    # Stream query execution
    result = {
        'query_insight': None,
        'plan': None,
        'past_steps': [],
        'response': None
    }

    async for node_name, state_update in orchestrator.stream_query(
        query=query,
        use_plan_execute=use_plan_execute,
        config=config  # Pass config for checkpointing
    ):
        if verbose:
            logger.info(f"Node: {node_name}, Update: {state_update.keys()}")

        # Collect results
        if node_name == "query_analyzer" and "query_insight" in state_update:
            result['query_insight'] = state_update['query_insight'].dict()

        elif node_name == "planner" and "plan" in state_update:
            result['plan'] = state_update['plan'].dict()

        elif node_name == "execute_task" and "past_steps" in state_update:
            result['past_steps'] = state_update['past_steps']

        elif node_name == "reporter" and "response" in state_update:
            result['response'] = state_update['response']

    return result
```

---

## Part 6: CLI Integration

### 6.1 Update CLI Research Script

**File:** `scripts/cli_research_celery.py`

```python
"""CLI Research with Celery task queue."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.tasks import research_query_task
from celery.result import AsyncResult


def submit_research_query(query_text: str, wait: bool = True):
    """
    Submit research query as Celery task.

    Args:
        query_text: Research question
        wait: Wait for result or return immediately
    """
    print("=" * 80)
    print("  FinAgent Research (Celery)")
    print("=" * 80)
    print()
    print(f"Query: {query_text}")
    print()

    # Submit task
    result = research_query_task.delay(
        query_text=query_text,
        use_plan_execute=True,
        verbose=True
    )

    print(f"✅ Task submitted: {result.id}")
    print()

    if wait:
        print("⏳ Waiting for results...")
        print()

        # Wait for completion
        final_result = result.get(timeout=300)  # 5 minute timeout

        print("=" * 80)
        print("  Research Results")
        print("=" * 80)
        print()
        print(final_result.get('response', 'No response'))
        print()
        print(f"Execution time: {final_result['execution_time']:.2f}s")
        print(f"Query ID: {final_result['query_id']}")
        print()
    else:
        print(f"Task ID: {result.id}")
        print("Use this ID to check status later:")
        print(f"  python scripts/check_task.py {result.id}")
        print()


def check_task_status(task_id: str):
    """Check Celery task status."""
    result = AsyncResult(task_id)

    print(f"Task ID: {task_id}")
    print(f"Status: {result.status}")
    print()

    if result.ready():
        print("Result:")
        print(result.result)
    else:
        print("Task is still running...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/cli_research_celery.py \"your query\"")
        print("   or: python scripts/cli_research_celery.py --check TASK_ID")
        sys.exit(1)

    if sys.argv[1] == "--check":
        check_task_status(sys.argv[2])
    else:
        query = " ".join(sys.argv[1:])
        submit_research_query(query, wait=True)
```

---

## Part 7: Docker Compose Setup

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL for checkpoints and history
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: finagent
      POSTGRES_USER: finagent_user
      POSTGRES_PASSWORD: finagent_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U finagent_user -d finagent"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for Celery broker and results
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Celery worker
  celery-worker:
    build: .
    command: celery -A finagent.celery_app worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - LANGGRAPH_CHECKPOINT_DB=postgresql://finagent_user:finagent_password@postgres:5432/finagent
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./:/app

  # Flower for monitoring (optional)
  flower:
    build: .
    command: celery -A finagent.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
      - celery-worker

volumes:
  postgres_data:
```

---

## Part 8: Usage Examples

### 8.1 Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Initialize database tables
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db
db = get_checkpoint_db()
db.setup_tables()
"

# Start Celery worker
celery -A finagent.celery_app worker --loglevel=info

# Optional: Start Flower monitoring
celery -A finagent.celery_app flower --port=5555
```

### 8.2 Submit Query

```python
from finagent.tasks import research_query_task

# Submit async task
result = research_query_task.delay(
    query_text="2020年玉山銀行洗錢防制裁罰",
    user_id="user123",
    session_id="session456"
)

print(f"Task ID: {result.id}")

# Wait for result
final_result = result.get(timeout=300)
print(final_result['response'])
```

### 8.3 Check Task Status

```python
from celery.result import AsyncResult

# Check status
result = AsyncResult('task-id-here')
print(f"Status: {result.status}")

if result.ready():
    print(f"Result: {result.result}")
```

### 8.4 Resume from Checkpoint

```python
from finagent.database.checkpoint_db import get_checkpoint_db
from finagent.agents.orchestrator import AgentOrchestrator

# Get checkpoint database
checkpoint_db = get_checkpoint_db()
checkpointer = checkpoint_db.get_checkpointer()

# Initialize orchestrator
orchestrator = AgentOrchestrator(checkpointer=checkpointer)

# Resume from specific thread
config = {"configurable": {"thread_id": "previous-thread-id"}}

# Get current state
state = orchestrator.workflow.get_state(config)
print(f"Current state: {state.values}")

# Continue execution
result = orchestrator.workflow.invoke(None, config=config)
```

---

## Part 9: Monitoring and Debugging

### 9.1 Flower Dashboard

Access at `http://localhost:5555` to monitor:
- Active tasks
- Task history
- Worker status
- Task execution time

### 9.2 Query History

```python
from finagent.database.checkpoint_db import get_checkpoint_db

db = get_checkpoint_db()

# Get user's query history
history = db.get_query_history(user_id="user123", limit=10)

for query in history:
    print(f"Query: {query['query_text']}")
    print(f"Status: {query['status']}")
    print(f"Time: {query['execution_time_seconds']}s")
    print(f"Cost: ${query['llm_cost_usd']}")
    print()
```

### 9.3 Checkpoint Inspection

```python
# List all checkpoints for a thread
state_history = list(orchestrator.workflow.get_state_history(config))

for state in state_history:
    print(f"Checkpoint ID: {state.config['configurable']['checkpoint_id']}")
    print(f"Values: {state.values.keys()}")
    print()
```

---

## Summary

✅ **Celery Integration** - Async task execution with Redis
✅ **LangGraph Checkpointing** - PostgreSQL state persistence
✅ **Query History** - Track all queries and results
✅ **Resume/Replay** - Continue interrupted workflows
✅ **Monitoring** - Flower dashboard for task tracking
✅ **Production-Ready** - Docker Compose deployment

**Next Steps:**
1. Set up PostgreSQL and Redis
2. Create database tables
3. Start Celery workers
4. Test with sample queries
5. Monitor with Flower dashboard
