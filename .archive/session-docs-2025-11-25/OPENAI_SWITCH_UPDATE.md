# OpenAI API Switch - Updated Findings

**Date:** 2025-11-24
**Status:** ⚠️ Configuration Issue Identified

---

## Summary

Attempted to switch from llmgw to OpenAI API for E2E testing but discovered a configuration priority issue.

---

## Issues Discovered

### Issue 1: Docker Port Conflict (RESOLVED ✅)
- Docker container `deepnlp-ner` was occupying port 8000
- All API requests were hitting Docker instead of finagent backend
- **Solution:** Stopped Docker container with `docker stop e8a05dea9cab`
- **Verification:** Backend now shows 55 routes, `/api/v1/research/query/async` works

### Issue 2: Configuration Priority Problem (IDENTIFIED ⚠️)

**Root Cause:** The system has multiple configuration sources with the following priority:
1. Active model_config (database) - Highest priority
2. Settings table (database)
3. .env file - Lowest priority

**Problem:** Updating only `.env` file doesn't work because the database configuration (settings table) has higher priority and still contains llmgw configuration.

**Evidence:**
```bash
# Database still had old llmgw config:
sqlite3 data/finagent.db "SELECT key, value FROM settings WHERE key='llm_base_url';"
# Output: llm_base_url|https://llmgw.elandai.cloud

# Celery logs showed still using llmgw:
[2025-11-24 18:24:43] HTTP Request: POST https://llmgw.elandai.cloud/v1/chat/completions
```

---

## Actions Taken

1. ✅ Updated `.env` file with OpenAI configuration
2. ✅ Discovered and fixed Docker port conflict
3. ✅ Updated database `settings` table with OpenAI configuration:
   ```sql
   UPDATE settings SET value = '' WHERE key = 'llm_base_url';
   UPDATE settings SET value = 'sk-proj-...' WHERE key = 'llm_api_key';
   UPDATE settings SET value = '' WHERE key = 'embedding_base_url';
   UPDATE settings SET value = 'sk-proj-...' WHERE key = 'embedding_api_key';
   ```
4. ✅ Restarted Celery worker with `--concurrency=1`
5. ⚠️ Celery still using llmgw (configuration cached at worker startup)

---

## Current Status

### What's Working ✅
- Backend running on port 8000 with all 55 routes loaded
- `/api/v1/research/query/async` endpoint accessible
- Database configuration updated to OpenAI
- Celery worker running with concurrency=1

### What's Not Working ❌
- Celery worker still connecting to llmgw instead of OpenAI
- Worker cached configuration at startup time
- Need to restart worker OR use environment variables

---

## Solution Options

### Option 1: Restart Everything (RECOMMENDED)
Kill all processes and restart with fresh configuration:
```bash
# Kill everything
pkill -f "celery.*finagent"
pkill -f "uvicorn.*finagent"

# Start backend
cd /Users/weifanliao/PycharmProjects/finagent
uv run python -m uvicorn finagent.main:app --port 8000 &

# Wait for backend to start
sleep 5

# Start Celery (will pick up database config)
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=1 &

# Wait for Celery to start
sleep 5

# Run E2E tests
cd frontend && npm run test:e2e
```

### Option 2: Use litellm CLI Config
Create a `litellm_config.yaml` file to override configuration:
```yaml
model_list:
  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: sk-proj-...
      api_base: https://api.openai.com/v1
```

Then start Celery with:
```bash
export LITELLM_CONFIG_PATH=/path/to/litellm_config.yaml
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=1
```

### Option 3: Temporary .env Override
Since `.env` file is already correct, we can ensure it's loaded first by:
1. Removing database settings temporarily
2. Starting worker (will fall back to `.env`)
3. Restoring database settings

---

## Key Learnings

1. **Configuration Priority Matters:** The system's configuration priority (model_configs > settings > .env) means you must update the database, not just `.env`

2. **Worker Configuration Caching:** Celery workers cache configuration at startup, so changes require a restart

3. **Docker Can Block Ports:** Always check `lsof -i :PORT` and `docker ps` when experiencing connection issues

4. **Database Configuration Location:** Settings stored in `data/finagent.db` in the `settings` table

---

## Next Steps

**Immediate:**
1. Choose Option 1 (full restart) as it's the cleanest approach
2. Verify Celery connects to OpenAI by checking logs for `api.openai.com`
3. Run E2E tests with OpenAI configuration

**Documentation:**
1. Update [CLAUDE.md](CLAUDE.md) with configuration troubleshooting guide
2. Add note about configuration priority and worker restart requirements

---

## Testing Verification

After implementing solution, verify with:
```bash
# Check Celery is using OpenAI
tail -f /tmp/celery_*.log | grep "HTTP Request"
# Expected: POST https://api.openai.com/v1/chat/completions

# Submit test query
curl -X POST http://localhost:8000/api/v1/research/query/async \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test openai", "workflow_version": "v1.1"}'

# Check query processing
# Should complete quickly (no timeout) with OpenAI's faster response times
```

---

**Recommendation:** Proceed with Option 1 (full restart) to ensure clean configuration loading.
