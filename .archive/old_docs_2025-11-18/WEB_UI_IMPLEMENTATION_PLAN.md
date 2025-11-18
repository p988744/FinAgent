# FinAgent Web UI - Final Implementation Plan

**Version:** 1.0 (Final)
**Created:** 2025-11-17
**Approach:** Functional-First Development
**Testing:** Playwright E2E + Automated Validation Scripts

---

## Executive Summary

**Scope:** 4 core features (Wiki deferred to v0.2.0)
**Timeline:** 12 weeks (15 weeks with buffer)
**Methodology:** Each version delivers complete, testable functionality

---

## Milestone Overview

| Version | Feature | Days | Test Focus |
|---------|---------|------|------------|
| **alpha.1** | Infrastructure | 5 | Environment setup |
| **alpha.2** | Query + Monitoring | 10 | WebSocket, real-time UI |
| **alpha.3** | Config Management | 7 | CRUD operations |
| **alpha.4** | Model Management | 7 | Model switching, stats |
| **alpha.5** | Document Management | 10 | File operations, indexing |
| **beta.1** | Integration | 10 | Cross-feature testing |
| **v0.1.0** | Release | 5 | Production readiness |
| **Total** | | **54 days** | |

**With 20% buffer: 65 days (~13 weeks)**

---

## v0.1.0-alpha.1: Infrastructure Foundation

**Timeline:** 5 days
**Goal:** Development environment fully operational

### Backend Deliverables

```bash
src/finagent/api/routes/
├── config.py      # Empty stubs
├── models.py      # Empty stubs
└── documents.py   # Empty stubs

src/finagent/database/
└── migrations/
    └── 002_web_ui_tables.sql  # New tables
```

**Tasks:**
- [ ] Create API route files (empty with TODOs)
- [ ] Add database migration script
- [ ] Configure CORS for localhost:5173
- [ ] Verify health check works
- [ ] Add python-multipart dependency

### Frontend Deliverables

```bash
frontend/
├── src/
│   ├── App.tsx              # Router setup
│   ├── main.tsx             # Entry point
│   ├── components/
│   │   └── layout/
│   │       ├── Layout.tsx
│   │       ├── Header.tsx
│   │       └── Sidebar.tsx
│   ├── pages/
│   │   ├── QueryPage.tsx    # Empty
│   │   ├── ConfigPage.tsx   # Empty
│   │   ├── ModelsPage.tsx   # Empty
│   │   └── DocumentsPage.tsx # Empty
│   ├── services/
│   │   ├── api.ts           # Axios client
│   │   └── websocket.ts     # WS connection
│   └── types/               # TypeScript interfaces
├── package.json
├── tsconfig.json
├── vite.config.ts           # Proxy to backend
├── tailwind.config.js
└── playwright.config.ts     # E2E setup
```

**Tasks:**
- [ ] Initialize Vite + React + TypeScript
- [ ] Configure Tailwind CSS
- [ ] Install shadcn/ui
- [ ] Set up React Router with empty pages
- [ ] Create API client with error handling
- [ ] Create WebSocket service (connection only)
- [ ] Configure Vite proxy to :8000
- [ ] Build layout components
- [ ] Set up Playwright
- [ ] Create first E2E test (smoke test)

### Database Schema

```sql
-- 002_web_ui_tables.sql

-- Document versions for version control
CREATE TABLE IF NOT EXISTS document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    checksum TEXT,
    changelog TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, version)
);

-- Query templates for saved queries
CREATE TABLE IF NOT EXISTS query_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template TEXT NOT NULL,
    description TEXT,
    category TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Validation Script

```bash
#!/bin/bash
# scripts/validate_v0.1.0-alpha.1.sh

echo "=== v0.1.0-alpha.1: Infrastructure Validation ==="

PASS=0
FAIL=0

check() {
    if eval "$2" > /dev/null 2>&1; then
        echo "✓ $1"
        PASS=$((PASS + 1))
    else
        echo "✗ $1"
        FAIL=$((FAIL + 1))
    fi
}

# Backend
check "Config API route exists" "test -f src/finagent/api/routes/config.py"
check "Models API route exists" "test -f src/finagent/api/routes/models.py"
check "Documents API route exists" "test -f src/finagent/api/routes/documents.py"
check "Migration script exists" "test -f src/finagent/database/migrations/002_web_ui_tables.sql"
check "Backend starts" "timeout 10 uv run python -c 'from finagent.main import app'"

# Frontend
check "Frontend directory exists" "test -d frontend"
check "package.json exists" "test -f frontend/package.json"
check "React dependency" "grep -q 'react' frontend/package.json"
check "TypeScript dependency" "grep -q 'typescript' frontend/package.json"
check "Tailwind dependency" "grep -q 'tailwindcss' frontend/package.json"
check "Playwright dependency" "grep -q 'playwright' frontend/package.json"
check "Vite proxy configured" "grep -q 'proxy' frontend/vite.config.ts"
check "API service exists" "test -f frontend/src/services/api.ts"
check "WebSocket service exists" "test -f frontend/src/services/websocket.ts"
check "Layout component exists" "test -f frontend/src/components/layout/Layout.tsx"
check "Query page exists" "test -f frontend/src/pages/QueryPage.tsx"
check "npm install succeeds" "cd frontend && npm install"
check "TypeScript compiles" "cd frontend && npx tsc --noEmit"
check "Build succeeds" "cd frontend && npm run build"

# Integration
check "Backend health check" "curl -s http://localhost:8000/health | grep -q 'ok'"
check "Frontend dev server starts" "cd frontend && timeout 5 npm run dev &"

echo ""
echo "Passed: $PASS / $((PASS + FAIL))"
[ $FAIL -eq 0 ] && echo "✅ alpha.1 VALIDATED" || echo "❌ alpha.1 FAILED"
```

### E2E Test (Playwright)

```typescript
// frontend/e2e/alpha1.spec.ts
import { test, expect } from '@playwright/test';

test.describe('alpha.1 - Infrastructure', () => {
  test('frontend loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/FinAgent/);
  });

  test('navigation works', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Query');
    await expect(page).toHaveURL(/\/query/);
    await page.click('text=Config');
    await expect(page).toHaveURL(/\/config/);
  });

  test('API connection works', async ({ page }) => {
    await page.goto('/');
    const response = await page.request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
  });
});
```

### Acceptance Criteria

- [ ] Backend starts without errors
- [ ] Frontend builds successfully
- [ ] Can navigate between pages
- [ ] API health check returns 200
- [ ] Playwright tests pass
- [ ] No TypeScript errors

---

## v0.1.0-alpha.2: Complete Query Feature

**Timeline:** 10 days
**Goal:** Fully functional query with real-time monitoring

### Backend Deliverables

```python
# src/finagent/api/routes/research.py (enhanced)

@router.websocket("/query/stream")
async def query_stream(websocket: WebSocket):
    """Stream query execution in real-time."""
    pass

@router.get("/history")
async def get_query_history():
    """Get query history."""
    pass

@router.delete("/history/{query_id}")
async def delete_history_entry(query_id: str):
    """Delete history entry."""
    pass
```

**Tasks:**
- [ ] Implement WebSocket streaming endpoint
- [ ] Create WebSocketUICallback class
- [ ] Implement query history persistence
- [ ] Add query history CRUD endpoints
- [ ] Stream step updates
- [ ] Stream todo updates
- [ ] Stream activity log entries
- [ ] Handle WebSocket errors gracefully

### Frontend Deliverables

```bash
frontend/src/
├── pages/
│   └── QueryPage.tsx           # Main query page
├── components/
│   └── query/
│       ├── QueryInput.tsx      # Text input + submit
│       ├── ResultsPanel.tsx    # Answer display
│       ├── MonitoringPanel.tsx # Real-time monitoring
│       ├── AgentStepper.tsx    # Pipeline visualization
│       ├── TodoListPanel.tsx   # Task tracking
│       ├── ActivityLog.tsx     # Agent actions
│       ├── ConfidenceScore.tsx # Score visualization
│       └── CitationList.tsx    # Citations display
├── hooks/
│   ├── useQueryStream.ts       # WebSocket hook
│   └── useQueryHistory.ts      # History management
└── types/
    └── query.ts                # Query interfaces
```

**Tasks:**
- [ ] Query input with validation (non-empty)
- [ ] Submit button triggers WebSocket connection
- [ ] Agent Pipeline Stepper
  - 4 steps with names
  - Status colors (pending/active/done/error)
  - Elapsed time per step
  - Current step description
- [ ] Todo List Panel
  - List from WebSocket updates
  - Status icons (○/●/✓/✗)
  - Progress percentage bar
  - Total elapsed time
- [ ] Activity Log
  - Append-only entries
  - Timestamps (HH:MM:SS.ms)
  - Color-coded by type
  - Auto-scroll to latest
- [ ] Results Panel
  - Markdown rendering (react-markdown)
  - Executive summary section
  - Key findings with citation links
  - Detailed analysis (collapsible)
  - Confidence score visualization
  - Citation list with source info
- [ ] Export to JSON button
- [ ] Query history dropdown
- [ ] Clear results button
- [ ] Error handling (connection lost, query failed)
- [ ] Loading states

### WebSocket Message Flow

```
Client                          Server
   |                               |
   |--- Connect WebSocket -------->|
   |                               |
   |--- Send Query --------------->|
   |                               |
   |<-- step_update (planning) ----|
   |<-- todo_update ---------------|
   |<-- activity_log --------------|
   |                               |
   |<-- step_update (action) ------|
   |<-- todo_update ---------------|
   |<-- activity_log --------------|
   |                               |
   |<-- step_update (validation) --|
   |<-- todo_update ---------------|
   |<-- activity_log --------------|
   |                               |
   |<-- step_update (answer) ------|
   |<-- todo_update ---------------|
   |<-- query_complete ------------|
   |                               |
   |--- Close WebSocket ---------->|
```

### Validation Script

```bash
#!/bin/bash
# scripts/validate_v0.1.0-alpha.2.sh

echo "=== v0.1.0-alpha.2: Query Feature Validation ==="

# Components exist
check "QueryPage exists" "test -f frontend/src/pages/QueryPage.tsx"
check "QueryInput exists" "test -f frontend/src/components/query/QueryInput.tsx"
check "AgentStepper exists" "test -f frontend/src/components/query/AgentStepper.tsx"
check "TodoListPanel exists" "test -f frontend/src/components/query/TodoListPanel.tsx"
check "ActivityLog exists" "test -f frontend/src/components/query/ActivityLog.tsx"
check "ResultsPanel exists" "test -f frontend/src/components/query/ResultsPanel.tsx"

# WebSocket
check "WebSocket endpoint exists" "grep -q 'websocket.*stream' src/finagent/api/routes/research.py"
check "useQueryStream hook" "test -f frontend/src/hooks/useQueryStream.ts"

# History
check "History GET endpoint" "grep -q 'get.*history' src/finagent/api/routes/research.py"
check "History DELETE endpoint" "grep -q 'delete.*history' src/finagent/api/routes/research.py"

# Export
check "Export utility exists" "test -f frontend/src/utils/export.ts"

# Build
check "Build succeeds" "cd frontend && npm run build"

# E2E
check "Query E2E tests pass" "cd frontend && npx playwright test e2e/query.spec.ts"

echo ""
echo "Passed: $PASS / $((PASS + FAIL))"
```

### E2E Test (Playwright)

```typescript
// frontend/e2e/query.spec.ts
import { test, expect } from '@playwright/test';

test.describe('alpha.2 - Query Feature', () => {
  test('complete query flow', async ({ page }) => {
    await page.goto('/query');

    // Input query
    await page.fill('[data-testid="query-input"]', '玉山銀行洗錢防制');
    await page.click('[data-testid="submit-button"]');

    // Verify stepper updates
    await expect(page.locator('[data-testid="step-planning"]')).toHaveClass(/active/);
    await expect(page.locator('[data-testid="step-planning"]')).toHaveClass(/done/, { timeout: 10000 });
    await expect(page.locator('[data-testid="step-action"]')).toHaveClass(/active/);

    // Verify todos appear
    await expect(page.locator('[data-testid="todo-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="todo-item"]')).toHaveCount({ minimum: 1 });

    // Verify activity log
    await expect(page.locator('[data-testid="activity-log"]')).toBeVisible();
    await expect(page.locator('[data-testid="log-entry"]')).toHaveCount({ minimum: 1 });

    // Wait for completion (max 60s)
    await expect(page.locator('[data-testid="results-panel"]')).toBeVisible({ timeout: 60000 });

    // Verify results
    await expect(page.locator('[data-testid="executive-summary"]')).not.toBeEmpty();
    await expect(page.locator('[data-testid="citations"]')).toBeVisible();

    // Test export
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="export-json"]')
    ]);
    expect(download.suggestedFilename()).toMatch(/\.json$/);
  });

  test('handles empty query', async ({ page }) => {
    await page.goto('/query');
    await page.click('[data-testid="submit-button"]');
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });

  test('handles WebSocket disconnect', async ({ page }) => {
    await page.goto('/query');
    await page.fill('[data-testid="query-input"]', 'test');
    await page.click('[data-testid="submit-button"]');

    // Simulate disconnect
    await page.evaluate(() => {
      (window as any).__TEST_WS_DISCONNECT__();
    });

    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Reconnecting');
  });
});
```

### Acceptance Criteria

- [ ] Can enter and submit query
- [ ] WebSocket connection established
- [ ] Stepper shows all 4 steps with transitions
- [ ] Todos appear and update in real-time
- [ ] Activity log entries append with timestamps
- [ ] Results display with markdown formatting
- [ ] Citations are clickable
- [ ] Export JSON downloads valid file
- [ ] Query history saves
- [ ] Error states handled gracefully
- [ ] Complete query in < 60 seconds

---

## v0.1.0-alpha.3: Complete Config Management

**Timeline:** 7 days
**Goal:** Full CRUD for configuration settings and presets

### Backend Deliverables

```python
# src/finagent/api/routes/config.py

@router.get("/settings")
async def get_all_settings():
    """Get all settings grouped by category."""
    pass

@router.put("/settings/{key}")
async def update_setting(key: str, value: Any):
    """Update single setting with validation."""
    pass

@router.get("/presets")
async def list_presets():
    """List all saved presets."""
    pass

@router.post("/presets")
async def create_preset(name: str):
    """Save current settings as preset."""
    pass

@router.post("/presets/{id}/activate")
async def activate_preset(id: int):
    """Load and activate a preset."""
    pass

@router.delete("/presets/{id}")
async def delete_preset(id: int):
    """Delete a preset."""
    pass

@router.post("/reload")
async def reload_from_env():
    """Reload settings from .env file."""
    pass
```

### Frontend Deliverables

```bash
frontend/src/
├── pages/
│   └── ConfigPage.tsx          # Config management
├── components/
│   └── config/
│       ├── SettingsEditor.tsx  # Form-based editor
│       ├── SettingField.tsx    # Single setting input
│       ├── PresetList.tsx      # Preset management
│       ├── PresetCard.tsx      # Single preset display
│       └── ValidationError.tsx # Error display
└── types/
    └── config.ts               # Config interfaces
```

**Tasks:**
- [ ] Settings grouped by category (tabs)
- [ ] Form inputs for each setting type
- [ ] Real-time validation
- [ ] Save/Cancel buttons per section
- [ ] Preset list with active indicator
- [ ] Save as preset modal
- [ ] Load preset button
- [ ] Delete preset with confirmation
- [ ] Reload from .env button
- [ ] Success/error toast notifications

### Validation Script

```bash
#!/bin/bash
# scripts/validate_v0.1.0-alpha.3.sh

# API endpoints
check "GET /settings" "grep -q 'get_all_settings' src/finagent/api/routes/config.py"
check "PUT /settings/{key}" "grep -q 'update_setting' src/finagent/api/routes/config.py"
check "GET /presets" "grep -q 'list_presets' src/finagent/api/routes/config.py"
check "POST /presets" "grep -q 'create_preset' src/finagent/api/routes/config.py"
check "DELETE /presets/{id}" "grep -q 'delete_preset' src/finagent/api/routes/config.py"
check "POST /presets/{id}/activate" "grep -q 'activate_preset' src/finagent/api/routes/config.py"
check "POST /reload" "grep -q 'reload_from_env' src/finagent/api/routes/config.py"

# Frontend
check "ConfigPage exists" "test -f frontend/src/pages/ConfigPage.tsx"
check "SettingsEditor exists" "test -f frontend/src/components/config/SettingsEditor.tsx"
check "PresetList exists" "test -f frontend/src/components/config/PresetList.tsx"

# E2E
check "Config E2E tests pass" "cd frontend && npx playwright test e2e/config.spec.ts"
```

### E2E Test (Playwright)

```typescript
// frontend/e2e/config.spec.ts
test.describe('alpha.3 - Config Management', () => {
  test('CRUD settings', async ({ page }) => {
    await page.goto('/config');

    // View settings
    await expect(page.locator('[data-testid="settings-list"]')).toBeVisible();

    // Edit setting
    await page.fill('[data-testid="setting-temperature"]', '0.5');
    await page.click('[data-testid="save-settings"]');
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();

    // Verify persisted
    await page.reload();
    await expect(page.locator('[data-testid="setting-temperature"]')).toHaveValue('0.5');
  });

  test('preset lifecycle', async ({ page }) => {
    await page.goto('/config');

    // Create preset
    await page.click('[data-testid="save-preset-button"]');
    await page.fill('[data-testid="preset-name-input"]', 'TestPreset');
    await page.click('[data-testid="confirm-save-preset"]');
    await expect(page.locator('text=TestPreset')).toBeVisible();

    // Modify setting
    await page.fill('[data-testid="setting-temperature"]', '0.9');
    await page.click('[data-testid="save-settings"]');

    // Load preset (reverts change)
    await page.click('[data-testid="preset-TestPreset"] >> text=Load');
    await expect(page.locator('[data-testid="setting-temperature"]')).toHaveValue('0.5');
    await expect(page.locator('[data-testid="active-preset"]')).toContainText('TestPreset');

    // Delete preset
    await page.click('[data-testid="preset-TestPreset"] >> text=Delete');
    await page.click('[data-testid="confirm-delete"]');
    await expect(page.locator('text=TestPreset')).not.toBeVisible();
  });
});
```

### Acceptance Criteria

- [ ] All settings visible by category
- [ ] Can edit any setting
- [ ] Validation prevents invalid values
- [ ] Changes persist to database
- [ ] Can save current config as preset
- [ ] Can load preset (becomes active)
- [ ] Can delete preset
- [ ] Active preset indicator visible
- [ ] Reload from .env works
- [ ] Toast notifications for success/error

---

## v0.1.0-alpha.4: Complete Model Management

**Timeline:** 7 days
**Goal:** Model selection, testing, and usage monitoring

### Backend Deliverables

```python
# src/finagent/api/routes/models.py

@router.get("/llm/available")
async def list_available_llms():
    """List available LLM models from model_config.yml."""
    pass

@router.post("/llm/test")
async def test_llm_connection():
    """Test LLM API connection."""
    pass

@router.put("/llm/active")
async def set_active_llm(model: str, temperature: float):
    """Set active LLM model."""
    pass

@router.get("/embedding/available")
async def list_available_embeddings():
    """List available embedding models."""
    pass

@router.get("/stats")
async def get_usage_stats():
    """Get token usage and cost statistics."""
    pass
```

### Frontend Deliverables

```bash
frontend/src/
├── pages/
│   └── ModelsPage.tsx          # Model management
├── components/
│   └── models/
│       ├── LLMSelector.tsx     # LLM model selection
│       ├── EmbeddingSelector.tsx # Embedding selection
│       ├── ConnectionTest.tsx  # Test button + status
│       ├── UsageStats.tsx      # Token/cost display
│       └── ModelCard.tsx       # Single model info
└── types/
    └── models.ts               # Model interfaces
```

### E2E Test (Playwright)

```typescript
// frontend/e2e/models.spec.ts
test.describe('alpha.4 - Model Management', () => {
  test('select and test LLM', async ({ page }) => {
    await page.goto('/models');

    // View models
    await expect(page.locator('[data-testid="llm-list"]')).toBeVisible();

    // Select model
    await page.click('[data-testid="model-gpt-3.5-turbo"]');

    // Test connection
    await page.click('[data-testid="test-connection"]');
    await expect(page.locator('[data-testid="connection-status"]')).toContainText(/success|connected/i, { timeout: 10000 });

    // Save selection
    await page.click('[data-testid="save-model"]');
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
  });

  test('view usage stats', async ({ page }) => {
    await page.goto('/models');
    await expect(page.locator('[data-testid="usage-stats"]')).toBeVisible();
    await expect(page.locator('[data-testid="token-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="cost-estimate"]')).toBeVisible();
  });
});
```

### Acceptance Criteria

- [ ] LLM model list displays
- [ ] Can select different model
- [ ] Test connection works
- [ ] Connection status shows success/failure
- [ ] Embedding models selectable
- [ ] Usage statistics visible
- [ ] Token count displayed
- [ ] Cost estimate calculated
- [ ] Model selection persists

---

## v0.1.0-alpha.5: Complete Document Management

**Timeline:** 10 days
**Goal:** Full document lifecycle (upload, version, index, delete)

### Backend Deliverables

```python
# src/finagent/api/routes/documents.py

@router.post("/upload")
async def upload_document(file: UploadFile):
    """Upload new document."""
    pass

@router.get("/")
async def list_documents():
    """List all documents with metadata."""
    pass

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Get document details."""
    pass

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete document and cleanup index."""
    pass

@router.post("/{doc_id}/reindex")
async def reindex_document(doc_id: str):
    """Reindex single document."""
    pass

@router.post("/reindex")
async def reindex_all():
    """Reindex all documents."""
    pass

@router.get("/index-status")
async def get_index_status():
    """Get indexing statistics."""
    pass

@router.post("/{doc_id}/versions")
async def upload_new_version(doc_id: str, file: UploadFile):
    """Upload new version of existing document."""
    pass

@router.get("/{doc_id}/versions")
async def get_version_history(doc_id: str):
    """Get version history."""
    pass
```

### Frontend Deliverables

```bash
frontend/src/
├── pages/
│   └── DocumentsPage.tsx       # Document management
├── components/
│   └── documents/
│       ├── FileUpload.tsx      # Drag-drop upload
│       ├── DocumentList.tsx    # Table with actions
│       ├── DocumentRow.tsx     # Single document
│       ├── VersionHistory.tsx  # Version modal
│       ├── IndexProgress.tsx   # Reindex progress
│       └── DeleteConfirm.tsx   # Delete modal
└── types/
    └── documents.ts            # Document interfaces
```

### E2E Test (Playwright)

```typescript
// frontend/e2e/documents.spec.ts
test.describe('alpha.5 - Document Management', () => {
  test('upload and index document', async ({ page }) => {
    await page.goto('/documents');

    // Upload
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('[data-testid="upload-zone"]');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles('test-data/sample.txt');

    // Verify in list
    await expect(page.locator('text=sample.txt')).toBeVisible();
    await expect(page.locator('[data-testid="status-pending"]')).toBeVisible();

    // Reindex
    await page.click('[data-testid="reindex-sample.txt"]');
    await expect(page.locator('[data-testid="status-indexed"]')).toBeVisible({ timeout: 30000 });

    // Delete
    await page.click('[data-testid="delete-sample.txt"]');
    await page.click('[data-testid="confirm-delete"]');
    await expect(page.locator('text=sample.txt')).not.toBeVisible();
  });

  test('version control', async ({ page }) => {
    await page.goto('/documents');

    // Upload initial
    // ... upload first version

    // Upload new version
    await page.click('[data-testid="upload-version-sample.txt"]');
    // ... upload second version

    // Check history
    await page.click('[data-testid="history-sample.txt"]');
    await expect(page.locator('[data-testid="version-item"]')).toHaveCount(2);
  });
});
```

### Acceptance Criteria

- [ ] Can upload file via drag-drop
- [ ] Can upload via click
- [ ] Upload progress shown
- [ ] Document appears in list
- [ ] Metadata displayed (size, date, status)
- [ ] Reindex single document works
- [ ] Reindex all documents works
- [ ] Index status updates
- [ ] Can view version history
- [ ] Can upload new version
- [ ] Delete removes from list
- [ ] Delete cleans up vector DB
- [ ] Confirmation modal prevents accidents

---

## v0.1.0-beta.1: Integration Testing

**Timeline:** 10 days
**Goal:** All features work together seamlessly

### Integration Tests

```typescript
// frontend/e2e/integration.spec.ts
test.describe('beta.1 - Full Integration', () => {
  test('document → query flow', async ({ page }) => {
    // 1. Upload document
    await page.goto('/documents');
    // ... upload test document

    // 2. Reindex
    // ... trigger reindex

    // 3. Query
    await page.goto('/query');
    await page.fill('[data-testid="query-input"]', 'content from test document');
    await page.click('[data-testid="submit-button"]');

    // 4. Verify results include new document
    await expect(page.locator('[data-testid="citations"]')).toContainText('test document');
  });

  test('config → query behavior', async ({ page }) => {
    // 1. Change temperature
    await page.goto('/config');
    await page.fill('[data-testid="setting-temperature"]', '0.0');
    await page.click('[data-testid="save-settings"]');

    // 2. Change model
    await page.goto('/models');
    await page.click('[data-testid="model-gpt-3.5-turbo"]');
    await page.click('[data-testid="save-model"]');

    // 3. Query
    await page.goto('/query');
    // ... submit query

    // 4. Verify settings applied (check logs)
    await expect(page.locator('[data-testid="activity-log"]')).toContainText('gpt-3.5-turbo');
  });

  test('navigation state persistence', async ({ page }) => {
    // 1. Start query
    await page.goto('/query');
    await page.fill('[data-testid="query-input"]', 'test');

    // 2. Navigate away
    await page.click('text=Config');

    // 3. Navigate back
    await page.click('text=Query');

    // 4. Input preserved
    await expect(page.locator('[data-testid="query-input"]')).toHaveValue('test');
  });
});
```

### Polish Checklist

- [ ] Consistent loading spinners
- [ ] Error messages in Chinese
- [ ] Responsive design (mobile-friendly)
- [ ] Bundle size < 2MB
- [ ] No console errors
- [ ] Accessibility basics (labels, alt text)
- [ ] Performance < 3s page load
- [ ] All routes reachable
- [ ] 404 page for invalid routes

### Validation Script

```bash
#!/bin/bash
# scripts/validate_v0.1.0-beta.1.sh

# Run ALL previous validations
./scripts/validate_v0.1.0-alpha.1.sh
./scripts/validate_v0.1.0-alpha.2.sh
./scripts/validate_v0.1.0-alpha.3.sh
./scripts/validate_v0.1.0-alpha.4.sh
./scripts/validate_v0.1.0-alpha.5.sh

# Integration tests
check "Integration tests pass" "cd frontend && npx playwright test e2e/integration.spec.ts"

# Performance
check "Bundle size < 2MB" "test $(du -sk frontend/dist | cut -f1) -lt 2000"
check "No console errors" "cd frontend && npm run lint"

# All routes work
check "Query route" "curl -s http://localhost:5173/query | grep -q 'html'"
check "Config route" "curl -s http://localhost:5173/config | grep -q 'html'"
check "Models route" "curl -s http://localhost:5173/models | grep -q 'html'"
check "Documents route" "curl -s http://localhost:5173/documents | grep -q 'html'"

echo "✅ beta.1 VALIDATED - Ready for release"
```

---

## v0.1.0: Production Release

**Timeline:** 5 days
**Goal:** Stable, documented release

### Release Checklist

- [ ] Version numbers updated (package.json, pyproject.toml)
- [ ] CHANGELOG.md updated with all features
- [ ] README.md updated with web UI instructions
- [ ] No console.log statements in production build
- [ ] No API keys exposed in frontend code
- [ ] Security review completed
- [ ] All E2E tests pass
- [ ] Performance benchmarks met
- [ ] Git tag created (v0.1.0)
- [ ] Release notes written
- [ ] GitHub release published

### Final Validation

```bash
#!/bin/bash
# scripts/validate_v0.1.0.sh

# All previous validations
./scripts/validate_v0.1.0-beta.1.sh

# Version check
check "Package version is 0.1.0" "grep -q '\"version\": \"0.1.0\"' frontend/package.json"
check "CHANGELOG has v0.1.0" "grep -q '## \\[0.1.0\\]' CHANGELOG.md"

# Security
check "No console.log in build" "! grep -r 'console.log' frontend/dist/"
check "No API keys in frontend" "! grep -r 'sk-' frontend/src/"

# Git
check "No uncommitted changes" "test -z \"$(git status --porcelain)\""
check "Tag exists" "git tag | grep -q 'v0.1.0'"

echo "✅ v0.1.0 READY FOR RELEASE"
```

---

## Deferred to v0.2.0 (Wiki Feature)

The Document Wiki feature is moved to v0.2.0 to:
1. Reduce v0.1.0 scope
2. Allow focus on core features
3. Gather user feedback first
4. Design entity extraction properly

**v0.2.0 will include:**
- Wiki page auto-generation
- Entity extraction
- Category/tag browsing
- Full-text search
- Knowledge graph visualization

---

## Summary

**v0.1.0 delivers:**
1. ✅ **Query with Monitoring** - Real-time agent tracking
2. ✅ **Config Management** - Full settings CRUD
3. ✅ **Model Management** - LLM/embedding selection
4. ✅ **Document Management** - Upload, version, index

**Testing approach:**
- Playwright E2E for user flows
- Bash scripts for file/code validation
- Integration tests for cross-feature
- Performance benchmarks

**Timeline:**
- 54 working days (~11 weeks)
- With 20% buffer: 65 days (~13 weeks)
- Conservative estimate: 15 weeks

Each milestone is **fully testable** and delivers **real user value**.

---

*Final Plan Version: 1.0*
*Date: 2025-11-17*
*Status: Approved for Implementation*
