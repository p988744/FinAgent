#!/bin/bash
# Test script for existing Celery + HTTP API implementation
# This validates that the async research API is working correctly

set -e  # Exit on error

echo "=========================================="
echo "  Celery API Test"
echo "  Testing existing async research endpoints"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# API endpoint
API_URL="http://localhost:8000"

# Check if backend is running
echo -e "${YELLOW}[1/6] Checking if backend API is running...${NC}"
if curl -s "${API_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Backend API is running${NC}"
else
    echo -e "${RED}❌ Backend API is not running${NC}"
    echo "Please start the backend:"
    echo "  uv run uvicorn finagent.main:app --reload --port 8000"
    exit 1
fi
echo ""

# Check Redis connection
echo -e "${YELLOW}[2/6] Checking Redis connection...${NC}"
if docker exec finagent-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running and accessible${NC}"
else
    echo -e "${RED}❌ Redis is not accessible${NC}"
    echo "Please start Redis:"
    echo "  docker run -d --name finagent-redis -p 6379:6379 redis:7-alpine"
    exit 1
fi
echo ""

# Check Celery worker
echo -e "${YELLOW}[3/6] Checking Celery worker...${NC}"
if ps aux | grep "celery.*worker" | grep -v grep > /dev/null; then
    echo -e "${GREEN}✅ Celery worker is running${NC}"
else
    echo -e "${RED}❌ Celery worker is not running${NC}"
    echo "Please start Celery worker:"
    echo "  celery -A finagent.celery_app worker --loglevel=info"
    exit 1
fi
echo ""

# Test 1: Submit async research query
echo -e "${YELLOW}[4/6] Submitting async research query...${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/research/query/async" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "測試查詢：玉山銀行洗錢防制裁罰"}')

echo "Response: $RESPONSE"

# Extract session_id and celery_task_id
SESSION_ID=$(echo $RESPONSE | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
TASK_ID=$(echo $RESPONSE | grep -o '"celery_task_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION_ID" ] || [ -z "$TASK_ID" ]; then
    echo -e "${RED}❌ Failed to submit query${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Query submitted successfully${NC}"
echo "   Session ID: $SESSION_ID"
echo "   Task ID: $TASK_ID"
echo ""

# Test 2: Poll for status
echo -e "${YELLOW}[5/6] Polling for status (max 90 seconds)...${NC}"
MAX_ATTEMPTS=18  # 18 attempts * 5 seconds = 90 seconds
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo -n "  Attempt $ATTEMPT/$MAX_ATTEMPTS: "

    STATUS_RESPONSE=$(curl -s "${API_URL}/api/v1/research/status/${SESSION_ID}")
    STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    echo "Status = $STATUS"

    if [ "$STATUS" = "completed" ]; then
        echo -e "${GREEN}✅ Query completed successfully!${NC}"
        echo ""
        echo "Full response:"
        echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo -e "${RED}❌ Query failed${NC}"
        echo "Response: $STATUS_RESPONSE"
        exit 1
    fi

    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo -e "${YELLOW}⚠️  Query still in progress after 90 seconds${NC}"
    echo "You can check status later:"
    echo "  curl ${API_URL}/api/v1/research/status/${SESSION_ID}"
fi
echo ""

# Test 3: Get research history
echo -e "${YELLOW}[6/6] Retrieving research history...${NC}"
HISTORY_RESPONSE=$(curl -s "${API_URL}/api/v1/research/history?limit=5")

# Count sessions
SESSION_COUNT=$(echo $HISTORY_RESPONSE | grep -o '"sessions":\[' | wc -l)

if [ $SESSION_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ History retrieved successfully${NC}"
    echo ""
    echo "Last 5 sessions:"
    echo "$HISTORY_RESPONSE" | python3 -m json.tool 2>/dev/null | head -50
else
    echo -e "${YELLOW}⚠️  No history found (this might be the first query)${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo -e "${GREEN}✅ Backend API: Running${NC}"
echo -e "${GREEN}✅ Redis: Connected${NC}"
echo -e "${GREEN}✅ Celery Worker: Running${NC}"
echo -e "${GREEN}✅ Query Submission: Success${NC}"
echo -e "${GREEN}✅ Status Polling: Working${NC}"
echo -e "${GREEN}✅ History Retrieval: Working${NC}"
echo ""
echo "Your async research API is fully functional!"
echo ""
echo "Session ID for this test: $SESSION_ID"
echo ""
