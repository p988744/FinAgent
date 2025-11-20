#!/bin/bash
# FinAgent Web UI v0.1.0-alpha.4 Validation Script
# This script validates that all alpha.4 deliverables are complete

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
echo "FinAgent Web UI v0.1.0-alpha.4 Validation"
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

echo "=== Backend Models API Checks ==="
echo ""

# Models API endpoints
check "Models route file exists" "test -f src/finagent/api/routes/models.py"
check_pattern "GET /llm/available endpoint" "src/finagent/api/routes/models.py" "async def get_available_llm_models"
check_pattern "GET /llm/active endpoint" "src/finagent/api/routes/models.py" "async def get_active_llm"
check_pattern "PUT /llm/active endpoint" "src/finagent/api/routes/models.py" "async def set_active_llm"
check_pattern "POST /llm/test endpoint" "src/finagent/api/routes/models.py" "async def test_llm_connection"
check_pattern "GET /embedding/available endpoint" "src/finagent/api/routes/models.py" "async def get_available_embedding_models"
check_pattern "GET /embedding/active endpoint" "src/finagent/api/routes/models.py" "async def get_active_embedding"
check_pattern "PUT /embedding/active endpoint" "src/finagent/api/routes/models.py" "async def set_active_embedding"
check_pattern "GET /stats endpoint" "src/finagent/api/routes/models.py" "async def get_usage_stats"
check_pattern "POST /cost/estimate endpoint" "src/finagent/api/routes/models.py" "async def estimate_cost"
check_pattern "GET /local-presets endpoint" "src/finagent/api/routes/models.py" "async def get_local_llm_presets"

# Config manager integration
check_pattern "Uses ConfigManager" "src/finagent/api/routes/models.py" "get_config_manager"
check_pattern "Reads from model_config.yml" "src/finagent/api/routes/models.py" "get_model_choices"
check_pattern "API key masking" "src/finagent/api/routes/models.py" "masked_key"
check_pattern "Connection test with httpx" "src/finagent/api/routes/models.py" "httpx.Client"
check_pattern "Latency measurement" "src/finagent/api/routes/models.py" "latency_ms"
check_pattern "Cost information" "src/finagent/api/routes/models.py" "COST_INFO"

# Pydantic models
check_pattern "LLMModel class" "src/finagent/api/routes/models.py" "class LLMModel"
check_pattern "EmbeddingModel class" "src/finagent/api/routes/models.py" "class EmbeddingModel"
check_pattern "ConnectionTestResult class" "src/finagent/api/routes/models.py" "class ConnectionTestResult"
check_pattern "UsageStats class" "src/finagent/api/routes/models.py" "class UsageStats"
check_pattern "CostEstimate class" "src/finagent/api/routes/models.py" "class CostEstimate"

# Backend imports
check "Backend models API imports successfully" "uv run python -c 'from finagent.api.routes.models import router'"

echo ""
echo "=== Frontend Models Components ==="
echo ""

# TypeScript types
check "Models types file exists" "test -f frontend/src/types/models.ts"
check_pattern "LLMModel interface defined" "frontend/src/types/models.ts" "interface LLMModel"
check_pattern "EmbeddingModel interface defined" "frontend/src/types/models.ts" "interface EmbeddingModel"
check_pattern "ConnectionTestResult interface defined" "frontend/src/types/models.ts" "interface ConnectionTestResult"
check_pattern "UsageStats interface defined" "frontend/src/types/models.ts" "interface UsageStats"
check_pattern "CostEstimate interface defined" "frontend/src/types/models.ts" "interface CostEstimate"

# UI Components
check "ModelSelector component exists" "test -f frontend/src/components/models/ModelSelector.tsx"
check "ConnectionTester component exists" "test -f frontend/src/components/models/ConnectionTester.tsx"
check "UsageStatsCard component exists" "test -f frontend/src/components/models/UsageStatsCard.tsx"
check "CostCalculator component exists" "test -f frontend/src/components/models/CostCalculator.tsx"

# ModelSelector features
check_pattern "ModelSelector shows model list" "frontend/src/components/models/ModelSelector.tsx" "models.map"
check_pattern "ModelSelector shows active indicator" "frontend/src/components/models/ModelSelector.tsx" "is_active"
check_pattern "ModelSelector shows recommended badge" "frontend/src/components/models/ModelSelector.tsx" "推薦"
check_pattern "ModelSelector shows cost info" "frontend/src/components/models/ModelSelector.tsx" "cost_per_1k"
check_pattern "ModelSelector handles selection" "frontend/src/components/models/ModelSelector.tsx" "onSelect"

# ConnectionTester features
check_pattern "ConnectionTester has test button" "frontend/src/components/models/ConnectionTester.tsx" "測試連線"
check_pattern "ConnectionTester shows loading state" "frontend/src/components/models/ConnectionTester.tsx" "isTesting"
check_pattern "ConnectionTester shows success/fail" "frontend/src/components/models/ConnectionTester.tsx" "result.success"
check_pattern "ConnectionTester shows latency" "frontend/src/components/models/ConnectionTester.tsx" "latency_ms"

# UsageStatsCard features
check_pattern "UsageStatsCard shows tokens" "frontend/src/components/models/UsageStatsCard.tsx" "total_tokens"
check_pattern "UsageStatsCard shows cost" "frontend/src/components/models/UsageStatsCard.tsx" "total_cost"
check_pattern "UsageStatsCard shows queries count" "frontend/src/components/models/UsageStatsCard.tsx" "queries_count"
check_pattern "UsageStatsCard shows current models" "frontend/src/components/models/UsageStatsCard.tsx" "current_llm_model"

# CostCalculator features
check_pattern "CostCalculator has input fields" "frontend/src/components/models/CostCalculator.tsx" "inputTokens"
check_pattern "CostCalculator has model selector" "frontend/src/components/models/CostCalculator.tsx" "selectedModel"
check_pattern "CostCalculator shows estimate" "frontend/src/components/models/CostCalculator.tsx" "estimate.total_cost"
check_pattern "CostCalculator calculate button" "frontend/src/components/models/CostCalculator.tsx" "計算成本"

# ModelsPage integration
check_pattern "ModelsPage uses ModelSelector" "frontend/src/pages/ModelsPage.tsx" "<ModelSelector"
check_pattern "ModelsPage uses ConnectionTester" "frontend/src/pages/ModelsPage.tsx" "<ConnectionTester"
check_pattern "ModelsPage uses UsageStatsCard" "frontend/src/pages/ModelsPage.tsx" "<UsageStatsCard"
check_pattern "ModelsPage uses CostCalculator" "frontend/src/pages/ModelsPage.tsx" "<CostCalculator"
check_pattern "ModelsPage fetches LLM models" "frontend/src/pages/ModelsPage.tsx" "fetch.*llm/available"
check_pattern "ModelsPage fetches embedding models" "frontend/src/pages/ModelsPage.tsx" "fetch.*embedding/available"
check_pattern "ModelsPage fetches stats" "frontend/src/pages/ModelsPage.tsx" "fetch.*stats"
check_pattern "ModelsPage handles LLM selection" "frontend/src/pages/ModelsPage.tsx" "handleSelectLLM"
check_pattern "ModelsPage handles embedding selection" "frontend/src/pages/ModelsPage.tsx" "handleSelectEmbedding"
check_pattern "ModelsPage handles connection test" "frontend/src/pages/ModelsPage.tsx" "handleTestConnection"
check_pattern "ModelsPage handles cost calculation" "frontend/src/pages/ModelsPage.tsx" "handleCalculateCost"
check_pattern "ModelsPage shows success messages" "frontend/src/pages/ModelsPage.tsx" "showSuccess"
check_pattern "ModelsPage shows error messages" "frontend/src/pages/ModelsPage.tsx" "showError"

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
    echo -e "${GREEN}✓ All alpha.4 validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test with actual backend (uv run uvicorn finagent.main:app)"
    echo "2. Manual E2E testing:"
    echo "   - View LLM models list (gpt-4o, gpt-4o-mini, etc.)"
    echo "   - Select different LLM model"
    echo "   - Click 'Test Connection' button"
    echo "   - See success/failure message with latency"
    echo "   - View embedding models list"
    echo "   - Select different embedding model"
    echo "   - View usage statistics"
    echo "   - Use cost calculator"
    echo "3. Commit changes to feature/web-ui-alpha.4 branch"
    echo "4. Create PR to develop branch"
    echo "5. Tag as v0.1.0-alpha.4"
    echo "6. Begin alpha.5 (Document Management) implementation"
    exit 0
else
    echo -e "${RED}✗ $FAIL validation(s) failed${NC}"
    echo ""
    echo "Please fix the failing checks before proceeding."
    exit 1
fi
