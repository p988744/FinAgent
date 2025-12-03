#!/bin/bash
# Script to start backend and Celery with OpenAI configuration
# This script unsets any conflicting environment variables and uses .env file

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting FinAgent with OpenAI API configuration...${NC}"

# Step 1: Unset conflicting environment variables
echo -e "${YELLOW}Step 1: Unsetting conflicting environment variables...${NC}"
unset LLM_API_KEY
unset LLM_BASE_URL
unset LLM_MODEL
unset LLM_TEMPERATURE
unset EMBEDDING_API_KEY
unset EMBEDDING_BASE_URL
unset EMBEDDING_MODEL

echo -e "${GREEN}✓ Environment variables cleared${NC}"

# Step 2: Verify .env file has OpenAI configuration
echo -e "${YELLOW}Step 2: Verifying .env file configuration...${NC}"
if grep -q "^LLM_BASE_URL=$" .env; then
    echo -e "${GREEN}✓ .env file configured for OpenAI (LLM_BASE_URL is empty)${NC}"
else
    echo -e "${RED}✗ .env file not configured correctly!${NC}"
    echo -e "${RED}  Expected: LLM_BASE_URL= (empty)${NC}"
    echo -e "${RED}  Please update .env file first${NC}"
    exit 1
fi

# Step 3: Kill existing processes
echo -e "${YELLOW}Step 3: Stopping existing backend and Celery processes...${NC}"
pkill -f "celery.*finagent" 2>/dev/null || true
pkill -f "uvicorn.*finagent" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Existing processes stopped${NC}"

# Step 4: Start backend
echo -e "${YELLOW}Step 4: Starting backend on port 8000...${NC}"
uv run python -m uvicorn finagent.main:app --port 8000 > /tmp/backend_openai.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Step 5: Wait for backend to be ready
echo -e "${YELLOW}Step 5: Waiting for backend to be ready...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        echo -e "${RED}  Check logs: tail -f /tmp/backend_openai.log${NC}"
        exit 1
    fi
    sleep 1
done

# Step 6: Start Celery
echo -e "${YELLOW}Step 6: Starting Celery worker with concurrency=1...${NC}"
uv run celery -A finagent.celery_app worker --loglevel=info --concurrency=1 > /tmp/celery_openai.log 2>&1 &
CELERY_PID=$!
echo -e "${GREEN}✓ Celery started (PID: $CELERY_PID)${NC}"

# Step 7: Wait for Celery to be ready
echo -e "${YELLOW}Step 7: Waiting for Celery to be ready...${NC}"
sleep 5

# Step 8: Verify OpenAI API is being used
echo -e "${YELLOW}Step 8: Verifying OpenAI API configuration...${NC}"
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/research/query/async \
    -H "Content-Type: application/json" \
    -d '{"query_text": "test", "workflow_version": "v1.1"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null || echo "")

if [ -z "$SESSION_ID" ]; then
    echo -e "${RED}✗ Failed to submit test query${NC}"
    exit 1
fi

# Wait for Celery to process
sleep 10

# Check Celery logs for OpenAI API usage
if grep -q "api.openai.com" /tmp/celery_openai.log; then
    echo -e "${GREEN}✓ Confirmed: Using OpenAI API (api.openai.com)${NC}"
elif grep -q "llmgw.elandai.cloud" /tmp/celery_openai.log; then
    echo -e "${RED}✗ ERROR: Still using llmgw API!${NC}"
    echo -e "${RED}  This means environment variables are still set in parent shell${NC}"
    echo -e "${RED}  Solution: Open a NEW terminal and run this script again${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠ Could not determine API endpoint from logs${NC}"
    echo -e "${YELLOW}  Check logs manually: tail -f /tmp/celery_openai.log${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Backend PID:  ${GREEN}$BACKEND_PID${NC}"
echo -e "Celery PID:   ${GREEN}$CELERY_PID${NC}"
echo ""
echo -e "Backend logs: ${YELLOW}tail -f /tmp/backend_openai.log${NC}"
echo -e "Celery logs:  ${YELLOW}tail -f /tmp/celery_openai.log${NC}"
echo ""
echo -e "To run E2E tests:"
echo -e "  ${YELLOW}cd frontend && npm run test:e2e${NC}"
echo ""
echo -e "To stop services:"
echo -e "  ${YELLOW}pkill -f 'celery.*finagent' && pkill -f 'uvicorn.*finagent'${NC}"
echo ""
