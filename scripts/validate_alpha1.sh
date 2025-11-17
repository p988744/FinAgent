#!/bin/bash
# FinAgent Web UI v0.1.0-alpha.1 Validation Script
# This script validates that all alpha.1 deliverables are complete

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
echo "FinAgent Web UI v0.1.0-alpha.1 Validation"
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

echo "=== Backend Checks ==="
echo ""

# API Route Files
check "Config API route exists" "test -f src/finagent/api/routes/config.py"
check "Models API route exists" "test -f src/finagent/api/routes/models.py"
check "Documents API route exists" "test -f src/finagent/api/routes/documents.py"

# API Route Content
check_pattern "Config route has endpoints" "src/finagent/api/routes/config.py" "@router.get"
check_pattern "Models route has endpoints" "src/finagent/api/routes/models.py" "@router.get"
check_pattern "Documents route has endpoints" "src/finagent/api/routes/documents.py" "@router.post"

# Main app integration
check_pattern "Config router imported in main" "src/finagent/main.py" "from finagent.api.routes import.*config"
check_pattern "Models router imported in main" "src/finagent/main.py" "from finagent.api.routes import.*models"
check_pattern "Documents router imported in main" "src/finagent/main.py" "from finagent.api.routes import.*documents"
check_pattern "Config router registered" "src/finagent/main.py" "app.include_router(config.router)"
check_pattern "Models router registered" "src/finagent/main.py" "app.include_router(models.router)"
check_pattern "Documents router registered" "src/finagent/main.py" "app.include_router(documents.router)"

# Database Migration
check "Migration script exists" "test -f src/finagent/database/migrations/004_web_ui_tables.sql"
check_pattern "Migration has document_versions table" "src/finagent/database/migrations/004_web_ui_tables.sql" "CREATE TABLE.*document_versions"
check_pattern "Migration has query_templates table" "src/finagent/database/migrations/004_web_ui_tables.sql" "CREATE TABLE.*query_templates"
check_pattern "Migration has wiki_pages table" "src/finagent/database/migrations/004_web_ui_tables.sql" "CREATE TABLE.*wiki_pages"

# CORS Configuration
check_pattern "CORS middleware configured" "src/finagent/main.py" "CORSMiddleware"

# Backend syntax check
check "Backend Python syntax valid" "uv run python -m py_compile src/finagent/main.py"
check "Backend can import main module" "uv run python -c 'from finagent.main import app'"

echo ""
echo "=== Frontend Checks ==="
echo ""

# Frontend project structure
check "Frontend directory exists" "test -d frontend"
check "Frontend package.json exists" "test -f frontend/package.json"
check "Frontend node_modules exists" "test -d frontend/node_modules"

# Frontend dependencies
check_pattern "React installed" "frontend/package.json" '"react":'
check_pattern "React Router installed" "frontend/package.json" '"react-router-dom":'
check_pattern "Tailwind CSS installed" "frontend/package.json" '"tailwindcss":'
check_pattern "React Query installed" "frontend/package.json" '"@tanstack/react-query":'
check_pattern "Zustand installed" "frontend/package.json" '"zustand":'

# Frontend configuration
check "Vite config exists" "test -f frontend/vite.config.ts"
check "Tailwind config exists" "test -f frontend/tailwind.config.js"
check "PostCSS config exists" "test -f frontend/postcss.config.js"
check_pattern "Vite proxy configured" "frontend/vite.config.ts" "proxy:"
check_pattern "API proxy target set" "frontend/vite.config.ts" "localhost:8000"

# Frontend layout
check "Main layout component exists" "test -f frontend/src/layouts/MainLayout.tsx"
check_pattern "Layout has header" "frontend/src/layouts/MainLayout.tsx" "<header"
check_pattern "Layout has sidebar navigation" "frontend/src/layouts/MainLayout.tsx" "<nav"
check_pattern "Layout has router outlet" "frontend/src/layouts/MainLayout.tsx" "<Outlet"

# Frontend pages
check "Query page exists" "test -f frontend/src/pages/QueryPage.tsx"
check "Config page exists" "test -f frontend/src/pages/ConfigPage.tsx"
check "Models page exists" "test -f frontend/src/pages/ModelsPage.tsx"
check "Documents page exists" "test -f frontend/src/pages/DocumentsPage.tsx"

# Frontend services
check "API service exists" "test -f frontend/src/services/api.ts"
check "WebSocket service exists" "test -f frontend/src/services/websocket.ts"
check_pattern "API client has health check" "frontend/src/services/api.ts" "health()"
check_pattern "WebSocket has reconnection logic" "frontend/src/services/websocket.ts" "reconnect"

# App routing
check_pattern "React Router setup in App" "frontend/src/App.tsx" "BrowserRouter"
check_pattern "Query route defined" "frontend/src/App.tsx" 'path="query"'
check_pattern "Config route defined" "frontend/src/App.tsx" 'path="config"'
check_pattern "Models route defined" "frontend/src/App.tsx" 'path="models"'
check_pattern "Documents route defined" "frontend/src/App.tsx" 'path="documents"'

# Frontend build test
check "Frontend builds successfully" "npm --prefix frontend run build"

echo ""
echo "=== E2E Testing Framework ==="
echo ""

check "Playwright installed" "test -f frontend/node_modules/@playwright/test/package.json"
check "Playwright config exists" "test -f frontend/playwright.config.ts"
check "E2E test directory exists" "test -d frontend/e2e"
check "Alpha.1 E2E tests exist" "test -f frontend/e2e/alpha1.spec.ts"
check_pattern "E2E tests navigation" "frontend/e2e/alpha1.spec.ts" "should navigate"
check_pattern "E2E tests layout" "frontend/e2e/alpha1.spec.ts" "main layout"

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
    echo -e "${GREEN}✓ All alpha.1 validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Commit changes to feature/web-ui-alpha.1 branch"
    echo "2. Create PR to develop branch"
    echo "3. Tag as v0.1.0-alpha.1"
    echo "4. Begin alpha.2 (Query Feature) implementation"
    exit 0
else
    echo -e "${RED}✗ $FAIL validation(s) failed${NC}"
    echo ""
    echo "Please fix the failing checks before proceeding."
    exit 1
fi
