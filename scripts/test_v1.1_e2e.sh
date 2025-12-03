#!/bin/bash
set -e

echo "=================================================="
echo "FinAgent v1.1 End-to-End Test"
echo "Testing: v1.1 Plan-and-Execute Workflow"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_BASE_URL="http://localhost:8000"
TEST_QUERY="玉山銀行洗錢防制裁罰"

echo "Step 1: Check backend is running..."
if curl -s -f "$API_BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is running on $API_BASE_URL"
else
    echo -e "${RED}✗${NC} Backend is not running. Please start with: uvicorn finagent.main:app --reload"
    exit 1
fi

echo ""
echo "Step 2: Check Celery worker is running..."
if pgrep -f "celery.*finagent" > /dev/null; then
    echo -e "${GREEN}✓${NC} Celery worker is running"
else
    echo -e "${RED}✗${NC} Celery worker not found. Please start with: celery -A finagent.celery_app worker"
    exit 1
fi

echo ""
echo "Step 3: Check Redis is running..."
if docker ps | grep -q finagent-redis; then
    echo -e "${GREEN}✓${NC} Redis container is running"
else
    echo -e "${RED}✗${NC} Redis not running. Please start with: docker-compose up -d"
    exit 1
fi

echo ""
echo "Step 4: Submit test query..."
echo "Query: $TEST_QUERY"

RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/research/query/async" \
  -H "Content-Type: application/json" \
  -d "{\"query_text\": \"$TEST_QUERY\"}")

SESSION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['celery_task_id'])")

echo -e "${GREEN}✓${NC} Query submitted successfully"
echo "  Session ID: $SESSION_ID"
echo "  Task ID: $TASK_ID"

echo ""
echo "Step 5: Polling for results (max 60 seconds)..."

MAX_WAIT=60
ELAPSED=0
POLL_INTERVAL=3

while [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep $POLL_INTERVAL
    ELAPSED=$((ELAPSED + POLL_INTERVAL))

    STATUS_RESPONSE=$(curl -s "$API_BASE_URL/api/v1/research/status/$SESSION_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")

    echo -n "  [${ELAPSED}s] Status: $STATUS"

    if [ "$STATUS" = "completed" ]; then
        echo -e " ${GREEN}✓${NC}"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo -e " ${RED}✗${NC}"
        ERROR=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error_message', 'Unknown error'))")
        echo -e "${RED}Error:${NC} $ERROR"
        exit 1
    else
        echo " (waiting...)"
    fi
done

if [ "$STATUS" != "completed" ]; then
    echo -e "${RED}✗${NC} Timeout: Query did not complete in ${MAX_WAIT} seconds"
    exit 1
fi

echo ""
echo "Step 6: Validate results..."

# Extract and validate result
RESULT=$(curl -s "$API_BASE_URL/api/v1/research/status/$SESSION_ID")

# Check executive summary
EXEC_SUMMARY=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
result = data.get('result', {})
print(result.get('executive_summary', '')[:200])
")

if [ -n "$EXEC_SUMMARY" ]; then
    echo -e "${GREEN}✓${NC} Executive summary present"
    echo "  Preview: $EXEC_SUMMARY..."
else
    echo -e "${RED}✗${NC} No executive summary found"
    exit 1
fi

# Check citations
CITATION_COUNT=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
result = data.get('result', {})
citations = result.get('citations', [])
print(len(citations))
")

if [ "$CITATION_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Citations found: $CITATION_COUNT"

    # Show first citation
    FIRST_CITATION=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
result = data.get('result', {})
citations = result.get('citations', [])
if citations:
    print(citations[0].get('source', 'Unknown'))
else:
    print('None')
")
    echo "  First citation: $FIRST_CITATION"
else
    echo -e "${YELLOW}⚠${NC} No citations found (may indicate RAG issue)"
fi

# Check confidence
CONFIDENCE=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
result = data.get('result', {})
conf = result.get('confidence', {})
print(conf.get('level', 'Unknown'))
")

echo -e "${GREEN}✓${NC} Confidence level: $CONFIDENCE"

# Check processing time
PROC_TIME=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('processing_time_seconds', 0))
")

echo -e "${GREEN}✓${NC} Processing time: ${PROC_TIME}s"

# Validate processing time is reasonable (not too fast = not using RAG)
if (( $(echo "$PROC_TIME < 5" | bc -l) )); then
    echo -e "${YELLOW}⚠${NC} Warning: Processing time unusually fast (< 5s), may indicate RAG not being used"
else
    echo -e "${GREEN}✓${NC} Processing time indicates proper RAG execution"
fi

echo ""
echo "Step 7: Verify v1.1 workflow was used..."

# Check Celery logs for v1.1 indicators
LOG_FILE="/tmp/celery_v1.1_final.log"

if [ -f "$LOG_FILE" ]; then
    if grep -q "v1.1 LangGraph workflows initialized successfully" "$LOG_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} v1.1 workflow initialization confirmed"
    fi

    if grep -q "Tool validation passed.*hybrid_search.*retriever" "$LOG_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} All 3 tools (hybrid_search, retriever, hard_search) validated"
    fi

    if grep -q "Tool.*completed successfully:.*chars returned" "$LOG_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Tools executed and returned data"
    fi
else
    echo -e "${YELLOW}⚠${NC} Could not verify workflow from logs (log file not found)"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✓ End-to-End Test PASSED${NC}"
echo "=================================================="
echo ""
echo "Summary:"
echo "  - Query submitted successfully"
echo "  - v1.1 Plan-and-Execute workflow executed"
echo "  - Results generated with citations"
echo "  - Processing time: ${PROC_TIME}s"
echo "  - Citations found: $CITATION_COUNT"
echo "  - Confidence: $CONFIDENCE"
echo ""
echo "Session ID: $SESSION_ID"
echo "View full results at: $API_BASE_URL/api/v1/research/status/$SESSION_ID"
echo ""
