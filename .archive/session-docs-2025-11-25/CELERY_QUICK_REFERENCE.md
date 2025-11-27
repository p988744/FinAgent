# Celery Integration - Quick Reference Card

**Status:** 📝 Documentation Complete - Ready for Implementation
**Last Updated:** 2025-11-21

---

## 🎯 What Is This?

Celery + LangGraph integration for async task execution and state persistence.

**Problem Solved:**
- ❌ Long queries (40-50s) block the UI
- ❌ State lost on WebSocket reconnection
- ❌ No query history tracking
- ❌ Cannot handle concurrent users

**Solution:**
- ✅ Background task execution with Celery
- ✅ State persistence with PostgreSQL
- ✅ Full query audit trail
- ✅ Scale to 10+ concurrent users

---

## 📚 Documentation (Read in This Order)

### 1. Start Here: Status Report
**File:** [CELERY_INTEGRATION_STATUS.md](CELERY_INTEGRATION_STATUS.md)
**Purpose:** Executive summary, what's complete, what's needed
**Time:** 10 minutes

### 2. Implementation Plan
**File:** [CELERY_IMPLEMENTATION_ROADMAP.md](CELERY_IMPLEMENTATION_ROADMAP.md)
**Purpose:** Step-by-step implementation (6 phases, 2-3 days)
**Time:** 20 minutes (review), 12-20 hours (implement)

### 3. Technical Details
**File:** [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md)
**Purpose:** Complete code examples and configurations
**Time:** 30 minutes (reference as needed)

### 4. Session Context
**File:** [SESSION_SUMMARY_2025_11_21.md](SESSION_SUMMARY_2025_11_21.md)
**Purpose:** What was done, why, and what's next
**Time:** 5 minutes

---

## 🏗️ Architecture at a Glance

### Current (v1.1)
```
User → CLI/WebSocket → AgentOrchestrator → LangGraph → Response
                            ↓
                      (No persistence)
```

### After (With Celery)
```
User → CLI/WebSocket → Celery Queue → LangGraph
                            ↓             ↓
                       PostgreSQL    PostgreSQL
                       (Tasks)       (Checkpoints)
                            ↓
                         Redis
                         (Queue)
```

**Services:**
- **PostgreSQL** - Persistent storage (checkpoints + history)
- **Redis** - Message broker and result backend
- **Celery Worker** - Background task execution
- **Flower** - Monitoring dashboard (optional)

---

## 🚀 Quick Start (When Ready)

### Step 1: Prerequisites (1 hour)
```bash
# Install services
brew install postgresql@16 redis  # macOS
# or use docker-compose (see roadmap)

# Install Python packages
uv add celery[redis] langgraph-checkpoint-postgres psycopg[binary,pool]

# Configure .env (see roadmap for full list)
POSTGRES_DB=finagent
CELERY_BROKER_URL=redis://localhost:6379/0
LANGGRAPH_CHECKPOINT_DB=postgresql://user:pass@localhost:5432/finagent
```

### Step 2: Database Setup (2 hours)
```bash
# Create database
psql -U postgres -c "CREATE DATABASE finagent"

# Apply schema
psql -U finagent_user -d finagent -f src/finagent/database/query_history_schema.sql

# Initialize checkpoint tables
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db
db = get_checkpoint_db()
db.setup_tables()
"
```

### Step 3: Start Services (5 minutes)
```bash
# Option A: Docker (recommended)
docker-compose up -d

# Option B: Local services
redis-server &
celery -A finagent.celery_app worker --loglevel=info &
celery -A finagent.celery_app flower --port=5555 &
```

### Step 4: Test (5 minutes)
```bash
# Submit test query
uv run python scripts/cli_research_celery.py "Test query"

# Check Flower dashboard
open http://localhost:5555

# View query history
uv run python scripts/query_history.py
```

**Full details:** See [CELERY_IMPLEMENTATION_ROADMAP.md](CELERY_IMPLEMENTATION_ROADMAP.md)

---

## 📋 Implementation Phases (2-3 Days Total)

| Phase | Time | Status | Deliverable |
|-------|------|--------|-------------|
| 1. Database Setup | 2-3 hours | 📝 Ready | DB schema, connections |
| 2. Backend Code | 4-6 hours | 📝 Ready | celery_app.py, tasks.py |
| 3. CLI Scripts | 2-3 hours | 📝 Ready | Submit/check tasks |
| 4. Docker Setup | 1-2 hours | 📝 Ready | docker-compose.yml |
| 5. Testing | 2-3 hours | 📝 Ready | Integration tests |
| 6. Documentation | 1 hour | ✅ Done | CLAUDE.md updates |

**Total:** 12-20 hours (all steps documented with copy-paste code)

---

## 🔑 Key Files to Create

### Backend (src/finagent/)
1. **database/checkpoint_db.py** - Database helper
   - `get_checkpoint_db()` - Get singleton instance
   - `create_query_record()` - Start tracking
   - `update_query_result()` - Save results

2. **celery_app.py** - Celery configuration
   - Broker: Redis
   - Result backend: Redis
   - Worker settings

3. **tasks.py** - Task definitions
   - `research_query_task()` - Main task
   - Checkpointing integration
   - Error handling

### Scripts (scripts/)
1. **cli_research_celery.py** - Submit queries
2. **check_celery_task.py** - Check status
3. **query_history.py** - View history
4. **setup_celery.sh** - One-command setup
5. **e2e_test_celery.sh** - E2E testing

### Deployment
1. **Dockerfile** - Worker container
2. **docker-compose.yml** - Full stack

**All implementations provided in:** [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md)

---

## 🧪 Testing Strategy

### Unit Tests
```bash
# Test checkpoint database
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db
db = get_checkpoint_db()
query_id = db.create_query_record('Test')
print(f'✅ Created query: {query_id}')
"
```

### Integration Tests
```bash
# Test Celery task submission
python -c "
from finagent.tasks import research_query_task
result = research_query_task.delay('Test')
print(f'✅ Task submitted: {result.id}')
"
```

### E2E Tests
```bash
# Full workflow test
bash scripts/e2e_test_celery.sh
```

**Test files documented in:** [CELERY_IMPLEMENTATION_ROADMAP.md - Phase 5](CELERY_IMPLEMENTATION_ROADMAP.md#phase-5-testing--verification-2-3-hours)

---

## 🔍 Monitoring & Debugging

### Flower Dashboard
```bash
# Start Flower
celery -A finagent.celery_app flower --port=5555

# Access dashboard
open http://localhost:5555
```

**Shows:** Active tasks, task history, worker status, execution time

### Query History
```bash
# View last 10 queries
uv run python scripts/query_history.py

# Query specific user
python -c "
from finagent.database.checkpoint_db import get_checkpoint_db
db = get_checkpoint_db()
history = db.get_query_history(user_id='user123', limit=10)
for q in history:
    print(f\"{q['query_text']}: {q['status']}\")
"
```

### Checkpoint Inspection
```python
from finagent.agents.orchestrator import AgentOrchestrator
from finagent.database.checkpoint_db import get_checkpoint_db

db = get_checkpoint_db()
orchestrator = AgentOrchestrator(checkpointer=db.get_checkpointer())

config = {"configurable": {"thread_id": "session-123"}}
state = orchestrator.plan_execute_workflow.get_state(config)
print(state.values)  # Current state
```

---

## 📊 Success Metrics (After Implementation)

### Functional ✅
- [ ] Celery worker starts without errors
- [ ] Tasks execute with checkpointing
- [ ] Query history saved to database
- [ ] State persists across restarts
- [ ] Flower dashboard accessible

### Performance 📈
- [ ] Query time: ~40-50s (same as before)
- [ ] Concurrent queries: 10+ supported
- [ ] Database latency: < 100ms
- [ ] Checkpoint overhead: < 2%

### Reliability 🛡️
- [ ] Task retry: 3 attempts with backoff
- [ ] Checkpoint recovery: 100%
- [ ] Worker uptime: 99.9%+
- [ ] Error tracking: Complete

---

## 🚨 Common Issues & Solutions

### Worker Won't Start
```bash
# Check Redis connection
redis-cli ping  # Should return PONG

# Check PostgreSQL connection
psql -U finagent_user -d finagent -c "SELECT 1"

# View logs
celery -A finagent.celery_app inspect active
```

### Tasks Stuck in Pending
```bash
# Restart worker
pkill -f "celery.*worker"
celery -A finagent.celery_app worker --loglevel=info
```

### Database Connection Error
```bash
# Verify environment variables
echo $LANGGRAPH_CHECKPOINT_DB

# Test connection string
psql "$LANGGRAPH_CHECKPOINT_DB" -c "SELECT version()"
```

**Full troubleshooting:** [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md - Part 9](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md#part-9-monitoring-and-debugging)

---

## 🎓 Key Concepts

### Celery Task Queue
- **Broker:** Redis stores task queue
- **Worker:** Python process executes tasks
- **Result Backend:** Redis stores results
- **Benefits:** Async execution, scalability

### LangGraph Checkpointing
- **PostgresSaver:** Persists graph state
- **Thread ID:** Isolates different sessions
- **Checkpoint:** State snapshot at each node
- **Benefits:** Resume workflows, debug state

### Query History
- **Custom Table:** Separate from checkpoints
- **Tracks:** Query text, status, results, metrics
- **Purpose:** Audit trail, analytics, debugging

---

## 📞 Getting Help

### Documentation Order
1. **Quick overview?** → [CELERY_INTEGRATION_STATUS.md](CELERY_INTEGRATION_STATUS.md)
2. **How to implement?** → [CELERY_IMPLEMENTATION_ROADMAP.md](CELERY_IMPLEMENTATION_ROADMAP.md)
3. **Code examples?** → [CELERY_LANGGRAPH_INTEGRATION_GUIDE.md](CELERY_LANGGRAPH_INTEGRATION_GUIDE.md)
4. **Session context?** → [SESSION_SUMMARY_2025_11_21.md](SESSION_SUMMARY_2025_11_21.md)

### External Resources
- [Celery Docs](https://docs.celeryq.dev/)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [PostgresSaver API](https://langchain-ai.github.io/langgraph/reference/checkpoints/#postgressaver)

---

## 🎯 Decision Matrix

### Should I implement this now?

**YES, if:**
- ✅ Need to handle concurrent users
- ✅ Queries blocking the UI is a problem
- ✅ Want query history and audit trail
- ✅ Need crash recovery for long queries
- ✅ Have 2-3 days available

**NO, if:**
- ❌ Single-user application only
- ❌ Queries are fast (< 10 seconds)
- ❌ No state persistence needed
- ❌ Timeline is tight (< 1 day available)

**DEFER to v1.2, if:**
- ⏸️ Current system meets needs
- ⏸️ Other priorities (frontend, features)
- ⏸️ Want to validate v1.1 in production first

---

## 🏁 Next Steps

### Option 1: Implement Now
1. Read [CELERY_INTEGRATION_STATUS.md](CELERY_INTEGRATION_STATUS.md) (10 min)
2. Review [CELERY_IMPLEMENTATION_ROADMAP.md](CELERY_IMPLEMENTATION_ROADMAP.md) (20 min)
3. Start Phase 1: Database Setup (2-3 hours)
4. Continue with phases 2-6 (10-17 hours)

### Option 2: Review Later
1. Bookmark this file
2. Add to v1.2 roadmap
3. Continue with other v1.1 tasks

### Option 3: Pilot First
1. Implement Phase 1-2 only (basic checkpointing)
2. Test with production queries
3. Decide on full Celery integration

---

## 📦 What's Included

### Documentation (100% Complete)
- ✅ Architecture design
- ✅ Implementation roadmap
- ✅ Code examples (15+)
- ✅ Testing strategy
- ✅ Deployment configuration
- ✅ Operations guide

### Code (Ready to Implement)
- ✅ Database schema (SQL)
- ✅ Python classes (7 files)
- ✅ CLI scripts (5 files)
- ✅ Docker setup (2 files)
- ✅ Test scripts (2 files)

### Verification
- ✅ All code reviewed against official docs
- ✅ Patterns validated with v1.1 implementations
- ✅ Step-by-step verification commands
- ✅ Rollback plan documented

**Total Investment:** ~1,500 lines of documentation, 15+ code examples, 6-phase plan

---

## 💡 Pro Tips

1. **Start Small:** Implement Phase 1-2 first, verify, then continue
2. **Use Docker:** Easier than managing local PostgreSQL + Redis
3. **Monitor Early:** Set up Flower from day 1 for debugging
4. **Test Checkpointing:** Manually kill worker mid-query to test recovery
5. **Track Metrics:** Use query_history to monitor costs and performance

---

## ✅ Checklist

Before starting:
- [ ] Read CELERY_INTEGRATION_STATUS.md
- [ ] Review CELERY_IMPLEMENTATION_ROADMAP.md
- [ ] PostgreSQL 16+ available
- [ ] Redis 7+ available
- [ ] 2-3 days allocated
- [ ] Team alignment on scope

During implementation:
- [ ] Follow roadmap phases in order
- [ ] Verify each checkpoint before proceeding
- [ ] Run tests after each phase
- [ ] Document any deviations

After completion:
- [ ] All success metrics met
- [ ] E2E tests passing
- [ ] Monitoring dashboard working
- [ ] Operations guide reviewed
- [ ] Team trained

---

**Status:** 📝 **Documentation Complete - Ready for Implementation**

**Last Updated:** 2025-11-21

**Questions?** Check the documentation links above or review session summary.
