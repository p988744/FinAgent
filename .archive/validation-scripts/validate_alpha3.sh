#!/bin/bash
# FinAgent Web UI v0.1.0-alpha.3 Validation Script
# This script validates that all alpha.3 deliverables are complete

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
echo "FinAgent Web UI v0.1.0-alpha.3 Validation"
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

echo "=== Backend Config API Checks ==="
echo ""

# Config API endpoints
check "Config route file exists" "test -f src/finagent/api/routes/config.py"
check_pattern "GET /settings endpoint" "src/finagent/api/routes/config.py" "@router.get.*settings"
check_pattern "PUT /settings/{key} endpoint" "src/finagent/api/routes/config.py" "@router.put.*settings"
check_pattern "GET /settings/{category} endpoint" "src/finagent/api/routes/config.py" "get_settings_by_category"
check_pattern "POST /settings/bulk endpoint" "src/finagent/api/routes/config.py" "bulk_update_settings"

# Preset management
check_pattern "GET /presets endpoint" "src/finagent/api/routes/config.py" "async def list_presets"
check_pattern "POST /presets endpoint" "src/finagent/api/routes/config.py" "async def create_preset"
check_pattern "DELETE /presets/{id} endpoint" "src/finagent/api/routes/config.py" "@router.delete.*presets"
check_pattern "POST /presets/{id}/activate endpoint" "src/finagent/api/routes/config.py" "activate_preset"
check_pattern "GET /presets/active endpoint" "src/finagent/api/routes/config.py" "get_active_presets"

# Reload functionality
check_pattern "POST /reload endpoint" "src/finagent/api/routes/config.py" "reload_from_env"
check_pattern "GET /model-choices endpoint" "src/finagent/api/routes/config.py" "get_model_choices"

# Config manager integration
check_pattern "Uses ConfigManager" "src/finagent/api/routes/config.py" "get_config_manager"
check_pattern "API key masking" "src/finagent/api/routes/config.py" "mask_api_key"
check_pattern "SettingResponse model" "src/finagent/api/routes/config.py" "class SettingResponse"
check_pattern "PresetResponse model" "src/finagent/api/routes/config.py" "class PresetResponse"
check_pattern "PresetCreate model" "src/finagent/api/routes/config.py" "class PresetCreate"

# Backend imports
check "Backend config API imports successfully" "uv run python -c 'from finagent.api.routes.config import router'"

echo ""
echo "=== Frontend Config Components ==="
echo ""

# TypeScript types
check "Config types file exists" "test -f frontend/src/types/config.ts"
check_pattern "SettingResponse type defined" "frontend/src/types/config.ts" "interface SettingResponse"
check_pattern "PresetResponse type defined" "frontend/src/types/config.ts" "interface PresetResponse"
check_pattern "PresetCreate type defined" "frontend/src/types/config.ts" "interface PresetCreate"
check_pattern "ModelChoices type defined" "frontend/src/types/config.ts" "interface ModelChoices"
check_pattern "SettingCategory type defined" "frontend/src/types/config.ts" "type SettingCategory"

# UI Components
check "SettingsForm component exists" "test -f frontend/src/components/config/SettingsForm.tsx"
check "PresetManager component exists" "test -f frontend/src/components/config/PresetManager.tsx"

# SettingsForm features
check_pattern "SettingsForm has category navigation" "frontend/src/components/config/SettingsForm.tsx" "CATEGORY_LABELS"
check_pattern "SettingsForm handles setting updates" "frontend/src/components/config/SettingsForm.tsx" "onUpdate"
check_pattern "SettingsForm has reload button" "frontend/src/components/config/SettingsForm.tsx" "onReload"
check_pattern "SettingsForm validates temperature" "frontend/src/components/config/SettingsForm.tsx" "llm_temperature"
check_pattern "SettingsForm masks API keys" "frontend/src/components/config/SettingsForm.tsx" "type=\"password\""
check_pattern "SettingsForm shows save status" "frontend/src/components/config/SettingsForm.tsx" "已儲存"

# PresetManager features
check_pattern "PresetManager lists presets" "frontend/src/components/config/PresetManager.tsx" "llmPresets.map"
check_pattern "PresetManager has create form" "frontend/src/components/config/PresetManager.tsx" "CreatePresetForm"
check_pattern "PresetManager handles activate" "frontend/src/components/config/PresetManager.tsx" "onActivate"
check_pattern "PresetManager handles delete" "frontend/src/components/config/PresetManager.tsx" "onDelete"
check_pattern "PresetManager shows active indicator" "frontend/src/components/config/PresetManager.tsx" "使用中"
check_pattern "PresetManager separates LLM and Embedding" "frontend/src/components/config/PresetManager.tsx" "config_type.*embedding"

# ConfigPage integration
check_pattern "ConfigPage uses SettingsForm" "frontend/src/pages/ConfigPage.tsx" "<SettingsForm"
check_pattern "ConfigPage uses PresetManager" "frontend/src/pages/ConfigPage.tsx" "<PresetManager"
check_pattern "ConfigPage fetches settings" "frontend/src/pages/ConfigPage.tsx" "fetch.*settings"
check_pattern "ConfigPage fetches presets" "frontend/src/pages/ConfigPage.tsx" "fetch.*presets"
check_pattern "ConfigPage handles update" "frontend/src/pages/ConfigPage.tsx" "handleUpdateSetting"
check_pattern "ConfigPage handles reload" "frontend/src/pages/ConfigPage.tsx" "handleReload"
check_pattern "ConfigPage handles create preset" "frontend/src/pages/ConfigPage.tsx" "handleCreatePreset"
check_pattern "ConfigPage handles activate preset" "frontend/src/pages/ConfigPage.tsx" "handleActivatePreset"
check_pattern "ConfigPage handles delete preset" "frontend/src/pages/ConfigPage.tsx" "handleDeletePreset"
check_pattern "ConfigPage shows success messages" "frontend/src/pages/ConfigPage.tsx" "showSuccess"
check_pattern "ConfigPage shows error messages" "frontend/src/pages/ConfigPage.tsx" "showError"

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
    echo -e "${GREEN}✓ All alpha.3 validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test with actual backend (uv run uvicorn finagent.main:app)"
    echo "2. Manual E2E testing:"
    echo "   - View settings by category"
    echo "   - Edit temperature value"
    echo "   - Create preset 'Test'"
    echo "   - Activate preset"
    echo "   - Delete preset"
    echo "   - Reload from .env"
    echo "3. Commit changes to feature/web-ui-alpha.3 branch"
    echo "4. Create PR to develop branch"
    echo "5. Tag as v0.1.0-alpha.3"
    echo "6. Begin alpha.4 (Model Management) implementation"
    exit 0
else
    echo -e "${RED}✗ $FAIL validation(s) failed${NC}"
    echo ""
    echo "Please fix the failing checks before proceeding."
    exit 1
fi
