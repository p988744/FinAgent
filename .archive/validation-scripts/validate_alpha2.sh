#!/bin/bash
# FinAgent Web UI v0.1.0-alpha.2 Validation Script
# This script validates that all alpha.2 deliverables are complete

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

PASS=0
FAIL=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "FinAgent Web UI v0.1.0-alpha.2 Validation"
echo "=========================================="
echo ""

check() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $name"
        FAIL=$((FAIL + 1))
    fi
}

check_pattern() {
    local name="$1"
    local file="$2"
    local pattern="$3"

    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $name"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Backend WebSocket Checks ==="
echo ""

# WebSocket endpoint
check "WebSocket route file exists" "test -f src/finagent/api/routes/websocket.py"
check_pattern "WebSocket endpoint defined" "src/finagent/api/routes/websocket.py" "@router.websocket"
check_pattern "WebSocketUICallback class exists" "src/finagent/api/routes/websocket.py" "class WebSocketUICallback"
check_pattern "WebSocket router registered in main" "src/finagent/main.py" "app.include_router(websocket.router)"

# UICallback methods in WebSocket
check_pattern "on_analysis_start implemented" "src/finagent/api/routes/websocket.py" "async def on_analysis_start"
check_pattern "on_todo_list_created implemented" "src/finagent/api/routes/websocket.py" "async def on_todo_list_created"
check_pattern "on_answer_complete implemented" "src/finagent/api/routes/websocket.py" "async def on_answer_complete"
check_pattern "on_error implemented" "src/finagent/api/routes/websocket.py" "async def on_error"

# Message types
check_pattern "step_update message type" "src/finagent/api/routes/websocket.py" "step_update"
check_pattern "todo_update message type" "src/finagent/api/routes/websocket.py" "todo_update"
check_pattern "activity_log message type" "src/finagent/api/routes/websocket.py" "activity_log"
check_pattern "query_complete message type" "src/finagent/api/routes/websocket.py" "query_complete"

# Backend imports
check "Backend imports successfully" "uv run python -c 'from finagent.main import app'"

echo ""
echo "=== Frontend Query Components ==="
echo ""

# TypeScript types
check "Query types file exists" "test -f frontend/src/types/query.ts"
check_pattern "StepUpdate type defined" "frontend/src/types/query.ts" "interface StepUpdate"
check_pattern "TodoItem type defined" "frontend/src/types/query.ts" "interface TodoItem"
check_pattern "ActivityLogEntry type defined" "frontend/src/types/query.ts" "interface ActivityLogEntry"
check_pattern "QueryResult type defined" "frontend/src/types/query.ts" "interface QueryResult"
check_pattern "WSMessage type defined" "frontend/src/types/query.ts" "interface WSMessage"

# UI Components
check "AgentStepper component exists" "test -f frontend/src/components/query/AgentStepper.tsx"
check "TodoPanel component exists" "test -f frontend/src/components/query/TodoPanel.tsx"
check "ActivityLog component exists" "test -f frontend/src/components/query/ActivityLog.tsx"
check "ResultsPanel component exists" "test -f frontend/src/components/query/ResultsPanel.tsx"

# Component features
check_pattern "AgentStepper has 4 steps" "frontend/src/components/query/AgentStepper.tsx" "planning.*action.*validation.*answer"
check_pattern "AgentStepper shows status icons" "frontend/src/components/query/AgentStepper.tsx" "getStatusIcon"
check_pattern "AgentStepper shows elapsed time" "frontend/src/components/query/AgentStepper.tsx" "elapsed_ms"

check_pattern "TodoPanel shows progress bar" "frontend/src/components/query/TodoPanel.tsx" "progressPercentage"
check_pattern "TodoPanel shows todo list" "frontend/src/components/query/TodoPanel.tsx" "todos.map"
check_pattern "TodoPanel shows status badges" "frontend/src/components/query/TodoPanel.tsx" "getStatusBadge"

check_pattern "ActivityLog auto-scrolls" "frontend/src/components/query/ActivityLog.tsx" "scrollIntoView"
check_pattern "ActivityLog shows timestamps" "frontend/src/components/query/ActivityLog.tsx" "formatTimestamp"
check_pattern "ActivityLog shows level icons" "frontend/src/components/query/ActivityLog.tsx" "getLevelIcon"

check_pattern "ResultsPanel shows confidence score" "frontend/src/components/query/ResultsPanel.tsx" "信心評分"
check_pattern "ResultsPanel shows citations" "frontend/src/components/query/ResultsPanel.tsx" "引用來源"
check_pattern "ResultsPanel has export button" "frontend/src/components/query/ResultsPanel.tsx" "匯出 JSON"

# QueryPage integration
check_pattern "QueryPage uses WebSocket" "frontend/src/pages/QueryPage.tsx" "new WebSocket"
check_pattern "QueryPage handles messages" "frontend/src/pages/QueryPage.tsx" "handleWSMessage"
check_pattern "QueryPage has query input" "frontend/src/pages/QueryPage.tsx" "id=\"query\""
check_pattern "QueryPage shows connection status" "frontend/src/pages/QueryPage.tsx" "connectionStatus"
check_pattern "QueryPage exports JSON" "frontend/src/pages/QueryPage.tsx" "handleExport"
check_pattern "QueryPage integrates AgentStepper" "frontend/src/pages/QueryPage.tsx" "<AgentStepper"
check_pattern "QueryPage integrates TodoPanel" "frontend/src/pages/QueryPage.tsx" "<TodoPanel"
check_pattern "QueryPage integrates ActivityLog" "frontend/src/pages/QueryPage.tsx" "<ActivityLog"
check_pattern "QueryPage integrates ResultsPanel" "frontend/src/pages/QueryPage.tsx" "<ResultsPanel"

echo ""
echo "=== Build and Compile Checks ==="
echo ""

check "Frontend builds successfully" "npm --prefix frontend run build"
check "TypeScript compilation passes" "cd frontend && npx tsc --noEmit"

echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
echo ""
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
TOTAL=$((PASS + FAIL))
echo "Total:  $TOTAL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All alpha.2 validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test with actual backend (uv run uvicorn finagent.main:app)"
    echo "2. Manual E2E testing with real queries"
    echo "3. Commit changes to feature/web-ui-alpha.2 branch"
    echo "4. Create PR to develop branch"
    echo "5. Tag as v0.1.0-alpha.2"
    echo "6. Begin alpha.3 (Config Management) implementation"
    exit 0
else
    echo -e "${RED}✗ $FAIL validation(s) failed${NC}"
    echo ""
    echo "Please fix the failing checks before proceeding."
    exit 1
fi
