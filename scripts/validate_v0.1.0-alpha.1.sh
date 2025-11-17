#!/bin/bash
# v0.1.0-alpha.1 Validation Script
# Foundation: Backend API + Frontend Setup

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== v0.1.0-alpha.1 Validation ===${NC}"
echo "Testing: Foundation - Backend API + Frontend Setup"
echo ""

PASS=0
FAIL=0
RESULTS=""

# Helper function
check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        PASS=$((PASS + 1))
        RESULTS="${RESULTS}${GREEN}✓${NC} ${name}\n"
        echo -e "${GREEN}✓${NC} ${name}"
    else
        FAIL=$((FAIL + 1))
        RESULTS="${RESULTS}${RED}✗${NC} ${name}\n"
        echo -e "${RED}✗${NC} ${name}"
    fi
}

# === BACKEND CHECKS ===
echo -e "${YELLOW}Backend API Checks:${NC}"
echo "-------------------"

# 1. Check new API route files exist
check "Config API routes exist" "test -f src/finagent/api/routes/config.py"
check "Models API routes exist" "test -f src/finagent/api/routes/models.py"
check "Documents API routes exist" "test -f src/finagent/api/routes/documents.py"
check "Wiki API routes exist" "test -f src/finagent/api/routes/wiki.py"

# 2. Check database schema updates
check "Schema has document_versions table" "grep -q 'CREATE TABLE document_versions' src/finagent/database/schema.sql"
check "Schema has wiki_pages table" "grep -q 'CREATE TABLE wiki_pages' src/finagent/database/schema.sql"
check "Schema has entities table" "grep -q 'CREATE TABLE entities' src/finagent/database/schema.sql"
check "Schema has query_templates table" "grep -q 'CREATE TABLE query_templates' src/finagent/database/schema.sql"

# 3. Python syntax check
check "FastAPI app imports successfully" "uv run python -c 'from finagent.main import app'"

# 4. Check WebSocket support added
check "WebSocket import in routes" "grep -rq 'WebSocket\\|websocket' src/finagent/api/routes/ || grep -q 'WebSocket' src/finagent/main.py"

# === FRONTEND CHECKS ===
echo ""
echo -e "${YELLOW}Frontend Setup Checks:${NC}"
echo "----------------------"

# 5. Check frontend project structure
check "Frontend directory exists" "test -d frontend"
check "package.json exists" "test -f frontend/package.json"
check "tsconfig.json exists" "test -f frontend/tsconfig.json"
check "vite.config.ts exists" "test -f frontend/vite.config.ts || test -f frontend/vite.config.js"
check "tailwind.config.js exists" "test -f frontend/tailwind.config.js || test -f frontend/tailwind.config.ts"

# 6. Check key dependencies in package.json
check "React dependency" "grep -q '\"react\":' frontend/package.json"
check "TypeScript dependency" "grep -q '\"typescript\":' frontend/package.json"
check "Vite dependency" "grep -q '\"vite\":' frontend/package.json"
check "Tailwind dependency" "grep -q '\"tailwindcss\":' frontend/package.json"
check "React Router dependency" "grep -q '\"react-router-dom\":' frontend/package.json"
check "Axios dependency" "grep -q '\"axios\":' frontend/package.json"

# 7. Check frontend source structure
check "src directory exists" "test -d frontend/src"
check "components directory exists" "test -d frontend/src/components"
check "pages directory exists" "test -d frontend/src/pages"
check "services directory exists" "test -d frontend/src/services"
check "App.tsx exists" "test -f frontend/src/App.tsx"
check "main.tsx exists" "test -f frontend/src/main.tsx"

# 8. Check core services
check "API client service exists" "test -f frontend/src/services/api.ts"
check "WebSocket service exists" "test -f frontend/src/services/websocket.ts"

# 9. Check layout components
check "Layout directory exists" "test -d frontend/src/components/layout"
check "Header component exists" "ls frontend/src/components/layout/*[Hh]eader* 2>/dev/null | head -1"
check "Sidebar component exists" "ls frontend/src/components/layout/*[Ss]idebar* 2>/dev/null | head -1"

# 10. Build checks
echo ""
echo -e "${YELLOW}Build Checks:${NC}"
echo "-------------"

check "npm install succeeds" "cd frontend && npm install"
check "TypeScript compiles" "cd frontend && npx tsc --noEmit"
check "Build succeeds" "cd frontend && npm run build"

# === SUMMARY ===
echo ""
echo -e "${BLUE}=== VALIDATION SUMMARY ===${NC}"
echo ""
echo "Passed: ${GREEN}$PASS${NC}"
echo "Failed: ${RED}$FAIL${NC}"
echo "Total:  $((PASS + FAIL))"
echo ""

# Write results to file
REPORT_FILE="scripts/reports/v0.1.0-alpha.1_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p scripts/reports
{
    echo "v0.1.0-alpha.1 Validation Report"
    echo "Date: $(date)"
    echo ""
    echo "Passed: $PASS"
    echo "Failed: $FAIL"
    echo ""
    echo "Details:"
    echo -e "$RESULTS"
} > "$REPORT_FILE"

echo "Report saved to: $REPORT_FILE"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ v0.1.0-alpha.1 VALIDATED SUCCESSFULLY${NC}"
    exit 0
else
    echo -e "${RED}❌ v0.1.0-alpha.1 VALIDATION FAILED${NC}"
    echo ""
    echo "Please fix the failing checks before proceeding."
    exit 1
fi
