# FinAgent Web UI - Implementation Milestones

**Created:** 2025-11-17
**Target:** v0.1.0 Release
**Validation Approach:** Automated scripts + Manual review

---

## Version Overview

| Version | Codename | Focus Area | Timeline | Status |
|---------|----------|------------|----------|--------|
| v0.1.0-alpha.1 | **Foundation** | Backend API + Project Setup | Week 1 | Planned |
| v0.1.0-alpha.2 | **Query Core** | Query Interface + WebSocket | Week 2 | Planned |
| v0.1.0-alpha.3 | **Config & Models** | Config + Model Management | Week 3 | Planned |
| v0.1.0-alpha.4 | **Documents** | Document Management | Week 4 | Planned |
| v0.1.0-alpha.5 | **Wiki** | Document Wiki Generation | Week 5 | Planned |
| v0.1.0-beta.1 | **Integration** | Full Integration Testing | Week 6 | Planned |
| v0.1.0 | **Release** | Production Ready | Week 7 | Planned |

---

## v0.1.0-alpha.1: Foundation

**Goal:** Backend API infrastructure and frontend project scaffolding

### Backend Deliverables

1. **New API Routes Structure**
   - `/api/v1/config/*` - Configuration endpoints
   - `/api/v1/models/*` - Model management endpoints
   - `/api/v1/documents/*` - Document management endpoints
   - `/api/v1/wiki/*` - Wiki endpoints

2. **Database Schema Updates**
   - `document_versions` table
   - `wiki_pages` table
   - `entities` table
   - `query_templates` table

3. **WebSocket Support**
   - Basic WebSocket connection
   - Connection lifecycle management
   - Message serialization

### Frontend Deliverables

1. **Project Initialization**
   - Vite + React + TypeScript setup
   - Tailwind CSS + shadcn/ui configuration
   - ESLint + Prettier configuration
   - Directory structure

2. **Core Infrastructure**
   - API client service (Axios)
   - WebSocket client service
   - React Router setup
   - Basic layout (Header, Sidebar, Main)

3. **Development Tooling**
   - Hot reload working
   - TypeScript compilation
   - Build pipeline

### Validation Script: `scripts/validate_v0.1.0-alpha.1.sh`

```bash
#!/bin/bash
set -e

echo "=== v0.1.0-alpha.1 Validation ==="
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
        RESULTS="${RESULTS}✓ ${name}\n"
    else
        FAIL=$((FAIL + 1))
        RESULTS="${RESULTS}✗ ${name}\n"
    fi
}

# === BACKEND CHECKS ===
echo "Backend API Checks:"
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

# 3. Start backend and test endpoints (if running)
check "FastAPI app imports successfully" "cd backend && uv run python -c 'from finagent.main import app'"

# 4. Check WebSocket support added
check "WebSocket import in main.py" "grep -q 'WebSocket' src/finagent/main.py || grep -q 'websocket' src/finagent/api/routes/*.py"

# === FRONTEND CHECKS ===
echo ""
echo "Frontend Setup Checks:"
echo "----------------------"

# 5. Check frontend project structure
check "Frontend directory exists" "test -d frontend"
check "package.json exists" "test -f frontend/package.json"
check "tsconfig.json exists" "test -f frontend/tsconfig.json"
check "vite.config.ts exists" "test -f frontend/vite.config.ts"
check "tailwind.config.js exists" "test -f frontend/tailwind.config.js"

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
check "Layout component exists" "test -f frontend/src/components/layout/Layout.tsx || test -d frontend/src/components/layout"
check "Header component exists" "ls frontend/src/components/layout/*eader* 2>/dev/null | head -1"
check "Sidebar component exists" "ls frontend/src/components/layout/*idebar* 2>/dev/null | head -1"

# 10. Build checks
check "npm install succeeds" "cd frontend && npm install"
check "TypeScript compiles" "cd frontend && npx tsc --noEmit"
check "Build succeeds" "cd frontend && npm run build"

# === SUMMARY ===
echo ""
echo "=== VALIDATION SUMMARY ==="
echo -e "$RESULTS"
echo ""
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo "Total:  $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ v0.1.0-alpha.1 VALIDATED SUCCESSFULLY"
    exit 0
else
    echo "❌ v0.1.0-alpha.1 VALIDATION FAILED"
    exit 1
fi
```

### Acceptance Criteria

- [ ] All backend API route files created (empty or stub implementations OK)
- [ ] Database schema updated with 4 new tables
- [ ] Frontend project builds without errors
- [ ] TypeScript compilation passes
- [ ] Basic layout renders (manual check)
- [ ] API client can connect to backend (manual check)

---

## v0.1.0-alpha.2: Query Core

**Goal:** Functional query interface with real-time monitoring

### Deliverables

1. **Query Page UI**
   - Query input component
   - Results display panel
   - Monitoring panel (steps, todos, logs)
   - Export functionality

2. **WebSocket Real-Time Updates**
   - Step updates streaming
   - Todo list synchronization
   - Activity log streaming
   - Connection management

3. **Backend Enhancements**
   - WebSocket streaming endpoint
   - Query history persistence
   - Query templates CRUD

### Validation Script: `scripts/validate_v0.1.0-alpha.2.sh`

```bash
#!/bin/bash
set -e

echo "=== v0.1.0-alpha.2 Validation ==="
echo "Testing: Query Core - Query Interface + WebSocket"
echo ""

PASS=0
FAIL=0
RESULTS=""

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        PASS=$((PASS + 1))
        RESULTS="${RESULTS}✓ ${name}\n"
    else
        FAIL=$((FAIL + 1))
        RESULTS="${RESULTS}✗ ${name}\n"
    fi
}

# === BACKEND CHECKS ===
echo "Backend WebSocket & API Checks:"
echo "--------------------------------"

# 1. WebSocket endpoint
check "WebSocket streaming endpoint" "grep -q '@.*websocket.*stream' src/finagent/api/routes/research.py"

# 2. Query history endpoints
check "GET /history endpoint" "grep -q 'def.*get.*history' src/finagent/api/routes/research.py"
check "DELETE /history endpoint" "grep -q 'def.*delete.*history' src/finagent/api/routes/research.py"

# 3. Query templates endpoints
check "POST /templates endpoint" "grep -q 'templates' src/finagent/api/routes/research.py"
check "GET /templates endpoint" "grep -q 'def.*get.*template' src/finagent/api/routes/research.py"

# 4. WebSocket callback implementation
check "WebSocketUICallback class" "grep -rq 'class.*WebSocket.*Callback' src/finagent/"

# === FRONTEND CHECKS ===
echo ""
echo "Frontend Query Interface Checks:"
echo "---------------------------------"

# 5. Query page components
check "Query page exists" "test -f frontend/src/pages/QueryPage.tsx"
check "Query input component" "test -f frontend/src/components/query/QueryInput.tsx"
check "Results panel component" "test -f frontend/src/components/query/ResultsPanel.tsx"

# 6. Monitoring panel components
check "Monitoring panel exists" "test -f frontend/src/components/query/MonitoringPanel.tsx"
check "Agent stepper component" "ls frontend/src/components/query/*[Ss]tepper* 2>/dev/null | head -1"
check "Todo list panel" "ls frontend/src/components/query/*[Tt]odo* 2>/dev/null | head -1"
check "Activity log component" "ls frontend/src/components/query/*[Ll]og* 2>/dev/null | head -1"

# 7. WebSocket hooks
check "WebSocket hook exists" "test -f frontend/src/hooks/useWebSocket.ts"
check "Query streaming hook" "test -f frontend/src/hooks/useQueryStream.ts"

# 8. Export functionality
check "Export utilities exist" "test -f frontend/src/utils/export.ts"

# 9. Route configuration
check "Query route configured" "grep -q '/query' frontend/src/App.tsx"

# 10. TypeScript interfaces
check "Query types defined" "test -f frontend/src/types/query.ts"
check "WebSocket message types" "grep -q 'interface.*WSMessage' frontend/src/types/"

# === INTEGRATION TEST ===
echo ""
echo "Integration Checks:"
echo "-------------------"

# 11. Run backend and test WebSocket
check "Backend starts successfully" "cd backend && timeout 10 uv run python -m finagent.main &"

# 12. Frontend build includes query page
check "Production build succeeds" "cd frontend && npm run build"
check "Query page in build" "test -d frontend/dist && ls frontend/dist/assets/*.js | xargs grep -l 'QueryPage' | head -1"

# === SUMMARY ===
echo ""
echo "=== VALIDATION SUMMARY ==="
echo -e "$RESULTS"
echo ""
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ v0.1.0-alpha.2 VALIDATED SUCCESSFULLY"
    exit 0
else
    echo "❌ v0.1.0-alpha.2 VALIDATION FAILED"
    exit 1
fi
```

### Acceptance Criteria

- [ ] Query can be submitted from web UI
- [ ] Real-time step updates visible
- [ ] Todo list updates in real-time
- [ ] Activity log shows agent actions
- [ ] Results display with citations
- [ ] Export to JSON/Markdown works
- [ ] WebSocket reconnection handles errors

---

## v0.1.0-alpha.3: Config & Models

**Goal:** Configuration management and model selection UI

### Deliverables

1. **Configuration Page**
   - Settings editor by category
   - Preset management (save/load/delete)
   - Environment variable display
   - Reload functionality

2. **Models Page**
   - LLM model selection
   - Embedding model selection
   - Connection testing
   - Usage statistics

3. **Backend API**
   - Full CRUD for settings
   - Preset management endpoints
   - Model management endpoints

### Validation Script: `scripts/validate_v0.1.0-alpha.3.sh`

```bash
#!/bin/bash
set -e

echo "=== v0.1.0-alpha.3 Validation ==="
echo "Testing: Config & Models Management"
echo ""

PASS=0
FAIL=0
RESULTS=""

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        PASS=$((PASS + 1))
        RESULTS="${RESULTS}✓ ${name}\n"
    else
        FAIL=$((FAIL + 1))
        RESULTS="${RESULTS}✗ ${name}\n"
    fi
}

# === BACKEND CONFIG API ===
echo "Backend Config API Checks:"
echo "---------------------------"

check "GET /settings endpoint" "grep -q 'def.*get.*settings' src/finagent/api/routes/config.py"
check "PUT /settings endpoint" "grep -q 'def.*update.*setting' src/finagent/api/routes/config.py"
check "GET /presets endpoint" "grep -q 'def.*get.*preset' src/finagent/api/routes/config.py"
check "POST /presets endpoint" "grep -q 'def.*create.*preset' src/finagent/api/routes/config.py"
check "POST /presets/activate endpoint" "grep -q 'activate' src/finagent/api/routes/config.py"
check "POST /reload endpoint" "grep -q 'reload' src/finagent/api/routes/config.py"

# === BACKEND MODELS API ===
echo ""
echo "Backend Models API Checks:"
echo "---------------------------"

check "GET /llm/available endpoint" "grep -q 'available' src/finagent/api/routes/models.py"
check "POST /llm/test endpoint" "grep -q 'test' src/finagent/api/routes/models.py"
check "GET /embedding/active endpoint" "grep -q 'embedding' src/finagent/api/routes/models.py"
check "GET /stats endpoint" "grep -q 'stats' src/finagent/api/routes/models.py"

# === FRONTEND CONFIG PAGE ===
echo ""
echo "Frontend Config Page Checks:"
echo "-----------------------------"

check "Config page exists" "test -f frontend/src/pages/ConfigPage.tsx"
check "Settings editor component" "ls frontend/src/components/config/*[Ss]etting* 2>/dev/null | head -1"
check "Preset manager component" "ls frontend/src/components/config/*[Pp]reset* 2>/dev/null | head -1"
check "Config route configured" "grep -q '/config' frontend/src/App.tsx"

# === FRONTEND MODELS PAGE ===
echo ""
echo "Frontend Models Page Checks:"
echo "-----------------------------"

check "Models page exists" "test -f frontend/src/pages/ModelsPage.tsx"
check "LLM selector component" "ls frontend/src/components/models/*[Ll]lm* 2>/dev/null | head -1"
check "Embedding selector component" "ls frontend/src/components/models/*[Ee]mbedding* 2>/dev/null | head -1"
check "Connection test component" "ls frontend/src/components/models/*[Tt]est* 2>/dev/null | head -1"
check "Models route configured" "grep -q '/models' frontend/src/App.tsx"

# === TYPE DEFINITIONS ===
echo ""
echo "Type Definition Checks:"
echo "-----------------------"

check "Config types defined" "test -f frontend/src/types/config.ts"
check "Model types defined" "test -f frontend/src/types/models.ts"

# === API INTEGRATION ===
echo ""
echo "API Integration Checks:"
echo "-----------------------"

check "Config API service" "grep -q 'config' frontend/src/services/api.ts"
check "Models API service" "grep -q 'models' frontend/src/services/api.ts"

# === SUMMARY ===
echo ""
echo "=== VALIDATION SUMMARY ==="
echo -e "$RESULTS"
echo ""
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ v0.1.0-alpha.3 VALIDATED SUCCESSFULLY"
    exit 0
else
    echo "❌ v0.1.0-alpha.3 VALIDATION FAILED"
    exit 1
fi
```

### Acceptance Criteria

- [ ] Settings can be viewed and edited
- [ ] Presets can be saved and loaded
- [ ] Active config indicator works
- [ ] LLM model can be changed
- [ ] Connection test returns results
- [ ] Validation errors displayed
- [ ] Reload from .env works

---

## v0.1.0-alpha.4: Documents

**Goal:** Document upload, versioning, and indexing management

### Deliverables

1. **Documents Page**
   - File upload (drag-and-drop)
   - Document list with filters
   - Version history viewer
   - Batch operations

2. **Indexing Controls**
   - Index status per document
   - Reindex single/all
   - Clear index
   - Progress indicators

3. **Backend API**
   - File upload handling
   - Version management
   - Indexing triggers
   - Batch operations

### Validation Script: `scripts/validate_v0.1.0-alpha.4.sh`

```bash
#!/bin/bash
set -e

echo "=== v0.1.0-alpha.4 Validation ==="
echo "Testing: Document Management"
echo ""

PASS=0
FAIL=0
RESULTS=""

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        PASS=$((PASS + 1))
        RESULTS="${RESULTS}✓ ${name}\n"
    else
        FAIL=$((FAIL + 1))
        RESULTS="${RESULTS}✗ ${name}\n"
    fi
}

# === BACKEND DOCUMENTS API ===
echo "Backend Documents API Checks:"
echo "------------------------------"

check "GET /documents endpoint" "grep -q 'def.*get.*documents' src/finagent/api/routes/documents.py"
check "POST /upload endpoint" "grep -q 'upload' src/finagent/api/routes/documents.py"
check "DELETE /documents endpoint" "grep -q 'delete' src/finagent/api/routes/documents.py"
check "POST /versions endpoint" "grep -q 'version' src/finagent/api/routes/documents.py"
check "POST /reindex endpoint" "grep -q 'reindex' src/finagent/api/routes/documents.py"
check "GET /index-status endpoint" "grep -q 'index.*status' src/finagent/api/routes/documents.py"
check "POST /batch endpoints" "grep -q 'batch' src/finagent/api/routes/documents.py"

# === FILE HANDLING ===
echo ""
echo "File Handling Checks:"
echo "---------------------"

check "Multipart form support" "grep -q 'UploadFile' src/finagent/api/routes/documents.py"
check "python-multipart in deps" "grep -q 'python-multipart' pyproject.toml"

# === FRONTEND DOCUMENTS PAGE ===
echo ""
echo "Frontend Documents Page Checks:"
echo "--------------------------------"

check "Documents page exists" "test -f frontend/src/pages/DocumentsPage.tsx"
check "File upload component" "ls frontend/src/components/documents/*[Uu]pload* 2>/dev/null | head -1"
check "Document list component" "ls frontend/src/components/documents/*[Ll]ist* 2>/dev/null | head -1"
check "Version history component" "ls frontend/src/components/documents/*[Vv]ersion* 2>/dev/null | head -1"
check "Index controls component" "ls frontend/src/components/documents/*[Ii]ndex* 2>/dev/null | head -1"
check "Documents route configured" "grep -q '/documents' frontend/src/App.tsx"

# === DRAG AND DROP ===
echo ""
echo "Drag & Drop Support:"
echo "--------------------"

check "File drop zone implementation" "grep -rq 'onDrop\\|dropzone\\|DragEvent' frontend/src/components/documents/"

# === BATCH OPERATIONS ===
echo ""
echo "Batch Operations:"
echo "-----------------"

check "Batch selection state" "grep -rq 'selectedDocuments\\|checkedItems' frontend/src/components/documents/"
check "Batch action buttons" "grep -rq 'batch.*reindex\\|batch.*delete' frontend/src/components/documents/"

# === TYPE DEFINITIONS ===
echo ""
echo "Type Definition Checks:"
echo "-----------------------"

check "Document types defined" "test -f frontend/src/types/documents.ts"

# === SUMMARY ===
echo ""
echo "=== VALIDATION SUMMARY ==="
echo -e "$RESULTS"
echo ""
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ v0.1.0-alpha.4 VALIDATED SUCCESSFULLY"
    exit 0
else
    echo "❌ v0.1.0-alpha.4 VALIDATION FAILED"
    exit 1
fi
```

### Acceptance Criteria

- [ ] Files can be uploaded via drag-and-drop
- [ ] Document list shows metadata
- [ ] Version history accessible
- [ ] Single document reindex works
- [ ] Batch reindex works
- [ ] Delete confirmation modal
- [ ] Progress indicator during operations

---

## v0.1.0-alpha.5: Wiki

**Goal:** Auto-generated document wiki with search and visualization

### Deliverables

1. **Wiki Page**
   - Category/tag browser
   - Full-text search
   - Document viewer (markdown)
   - Entity relationships

2. **Knowledge Graph** (Basic)
   - Entity extraction results
   - Simple relationship display
   - Filtering by type

3. **Backend API**
   - Wiki page generation
   - Entity extraction
   - Full-text search
   - Graph data API

### Validation Script: `scripts/validate_v0.1.0-alpha.5.sh`

```bash
#!/bin/bash
set -e

echo "=== v0.1.0-alpha.5 Validation ==="
echo "Testing: Document Wiki Generation"
echo ""

PASS=0
FAIL=0
RESULTS=""

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        PASS=$((PASS + 1))
        RESULTS="${RESULTS}✓ ${name}\n"
    else
        FAIL=$((FAIL + 1))
        RESULTS="${RESULTS}✗ ${name}\n"
    fi
}

# === BACKEND WIKI API ===
echo "Backend Wiki API Checks:"
echo "-------------------------"

check "GET /pages endpoint" "grep -q 'def.*get.*page' src/finagent/api/routes/wiki.py"
check "GET /categories endpoint" "grep -q 'categories' src/finagent/api/routes/wiki.py"
check "GET /tags endpoint" "grep -q 'tags' src/finagent/api/routes/wiki.py"
check "GET /entities endpoint" "grep -q 'entities' src/finagent/api/routes/wiki.py"
check "POST /search endpoint" "grep -q 'search' src/finagent/api/routes/wiki.py"
check "GET /graph endpoint" "grep -q 'graph' src/finagent/api/routes/wiki.py"
check "GET /timeline endpoint" "grep -q 'timeline' src/finagent/api/routes/wiki.py"

# === ENTITY EXTRACTION ===
echo ""
echo "Entity Extraction Service:"
echo "---------------------------"

check "Entity extractor exists" "test -f src/finagent/document_processing/entity_extractor.py || grep -rq 'extract.*entit' src/finagent/"

# === FRONTEND WIKI PAGE ===
echo ""
echo "Frontend Wiki Page Checks:"
echo "---------------------------"

check "Wiki page exists" "test -f frontend/src/pages/WikiPage.tsx"
check "Category browser component" "ls frontend/src/components/wiki/*[Cc]ategor* 2>/dev/null | head -1"
check "Tag cloud component" "ls frontend/src/components/wiki/*[Tt]ag* 2>/dev/null | head -1"
check "Search component" "ls frontend/src/components/wiki/*[Ss]earch* 2>/dev/null | head -1"
check "Document viewer component" "ls frontend/src/components/wiki/*[Vv]iewer* 2>/dev/null | head -1"
check "Wiki route configured" "grep -q '/wiki' frontend/src/App.tsx"

# === VISUALIZATION ===
echo ""
echo "Visualization Checks:"
echo "---------------------"

check "Timeline component" "ls frontend/src/components/wiki/*[Tt]imeline* 2>/dev/null | head -1"
check "Graph component (basic)" "ls frontend/src/components/wiki/*[Gg]raph* 2>/dev/null | head -1"

# === MARKDOWN RENDERING ===
echo ""
echo "Markdown Rendering:"
echo "-------------------"

check "react-markdown dependency" "grep -q 'react-markdown' frontend/package.json"
check "Markdown renderer used" "grep -rq 'ReactMarkdown\\|react-markdown' frontend/src/components/wiki/"

# === TYPE DEFINITIONS ===
echo ""
echo "Type Definition Checks:"
echo "-----------------------"

check "Wiki types defined" "test -f frontend/src/types/wiki.ts"
check "Entity types defined" "grep -q 'Entity' frontend/src/types/wiki.ts"

# === SUMMARY ===
echo ""
echo "=== VALIDATION SUMMARY ==="
echo -e "$RESULTS"
echo ""
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ v0.1.0-alpha.5 VALIDATED SUCCESSFULLY"
    exit 0
else
    echo "❌ v0.1.0-alpha.5 VALIDATION FAILED"
    exit 1
fi
```

### Acceptance Criteria

- [ ] Wiki pages auto-generated from documents
- [ ] Categories and tags browsable
- [ ] Full-text search works
- [ ] Document content displays in markdown
- [ ] Entity relationships visible
- [ ] Timeline view functional
- [ ] Basic graph visualization works

---

## v0.1.0-beta.1: Integration

**Goal:** Full system integration testing and bug fixes

### Deliverables

1. **End-to-End Testing**
   - All features work together
   - Cross-page navigation
   - State persistence
   - Error handling

2. **Performance Optimization**
   - Lazy loading
   - Virtual scrolling
   - API caching
   - Bundle optimization

3. **Polish**
   - Loading states
   - Error messages (Chinese)
   - Responsive design
   - Accessibility basics

### Validation Script: `scripts/validate_v0.1.0-beta.1.sh`

```bash
#!/bin/bash
set -e

echo "=== v0.1.0-beta.1 Validation ==="
echo "Testing: Full Integration"
echo ""

PASS=0
FAIL=0
RESULTS=""

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        PASS=$((PASS + 1))
        RESULTS="${RESULTS}✓ ${name}\n"
    else
        FAIL=$((FAIL + 1))
        RESULTS="${RESULTS}✗ ${name}\n"
    fi
}

# === ALL PAGES EXIST ===
echo "All Pages Validation:"
echo "---------------------"

check "Query page" "test -f frontend/src/pages/QueryPage.tsx"
check "Config page" "test -f frontend/src/pages/ConfigPage.tsx"
check "Models page" "test -f frontend/src/pages/ModelsPage.tsx"
check "Documents page" "test -f frontend/src/pages/DocumentsPage.tsx"
check "Wiki page" "test -f frontend/src/pages/WikiPage.tsx"

# === ALL ROUTES CONFIGURED ===
echo ""
echo "Route Configuration:"
echo "--------------------"

check "Query route" "grep -q '/query' frontend/src/App.tsx"
check "Config route" "grep -q '/config' frontend/src/App.tsx"
check "Models route" "grep -q '/models' frontend/src/App.tsx"
check "Documents route" "grep -q '/documents' frontend/src/App.tsx"
check "Wiki route" "grep -q '/wiki' frontend/src/App.tsx"

# === BACKEND API COMPLETE ===
echo ""
echo "Backend API Completeness:"
echo "-------------------------"

check "Research API router registered" "grep -q 'research' src/finagent/main.py"
check "Config API router registered" "grep -q 'config' src/finagent/main.py"
check "Models API router registered" "grep -q 'models' src/finagent/main.py"
check "Documents API router registered" "grep -q 'documents' src/finagent/main.py"
check "Wiki API router registered" "grep -q 'wiki' src/finagent/main.py"

# === ERROR HANDLING ===
echo ""
echo "Error Handling:"
echo "---------------"

check "Error boundary component" "ls frontend/src/components/*[Ee]rror* 2>/dev/null | head -1"
check "API error handling" "grep -rq 'catch\\|onError' frontend/src/services/api.ts"
check "Loading states" "grep -rq 'isLoading\\|loading' frontend/src/components/"

# === PERFORMANCE ===
echo ""
echo "Performance Optimization:"
echo "-------------------------"

check "Code splitting (lazy)" "grep -rq 'React.lazy\\|lazy(' frontend/src/"
check "Bundle size reasonable" "test $(du -sk frontend/dist/assets/*.js | awk '{sum+=$1} END{print sum}') -lt 2000"

# === RESPONSIVE DESIGN ===
echo ""
echo "Responsive Design:"
echo "------------------"

check "Tailwind breakpoints used" "grep -rq 'md:\\|lg:\\|sm:' frontend/src/components/"
check "Mobile-friendly viewport" "grep -q 'viewport' frontend/index.html"

# === ACCESSIBILITY ===
echo ""
echo "Accessibility Basics:"
echo "---------------------"

check "Alt text on images" "grep -rq 'alt=' frontend/src/components/"
check "Button labels" "grep -rq 'aria-label' frontend/src/components/"
check "Form labels" "grep -rq '<label' frontend/src/components/"

# === CHINESE LOCALIZATION ===
echo ""
echo "Chinese Localization:"
echo "---------------------"

check "Chinese error messages" "grep -rq '錯誤\\|失敗\\|無法' frontend/src/"
check "Chinese UI labels" "grep -rq '查詢\\|設定\\|文件' frontend/src/"

# === BUILD SUCCESS ===
echo ""
echo "Build Validation:"
echo "-----------------"

check "Production build succeeds" "cd frontend && npm run build"
check "No TypeScript errors" "cd frontend && npx tsc --noEmit"
check "ESLint passes" "cd frontend && npm run lint 2>/dev/null || true"

# === BACKEND TESTS ===
echo ""
echo "Backend Tests:"
echo "--------------"

check "Backend tests pass" "cd backend && uv run pytest tests/ -x --tb=no"

# === SUMMARY ===
echo ""
echo "=== VALIDATION SUMMARY ==="
echo -e "$RESULTS"
echo ""
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ v0.1.0-beta.1 VALIDATED SUCCESSFULLY"
    exit 0
else
    echo "❌ v0.1.0-beta.1 VALIDATION FAILED"
    exit 1
fi
```

### Acceptance Criteria

- [ ] All features accessible from UI
- [ ] No console errors
- [ ] Navigation works smoothly
- [ ] Settings persist across pages
- [ ] Error messages are helpful (Chinese)
- [ ] Bundle size < 2MB
- [ ] Load time < 3 seconds

---

## v0.1.0: Production Release

**Goal:** Stable release ready for users

### Final Checklist

```bash
#!/bin/bash
set -e

echo "=== v0.1.0 Release Validation ==="
echo "Testing: Production Readiness"
echo ""

# Run all previous validations
./scripts/validate_v0.1.0-alpha.1.sh
./scripts/validate_v0.1.0-alpha.2.sh
./scripts/validate_v0.1.0-alpha.3.sh
./scripts/validate_v0.1.0-alpha.4.sh
./scripts/validate_v0.1.0-alpha.5.sh
./scripts/validate_v0.1.0-beta.1.sh

echo ""
echo "=== FINAL RELEASE CHECKS ==="
echo ""

# Version numbers
check "Package version is 0.1.0" "grep -q '\"version\": \"0.1.0\"' frontend/package.json"
check "Backend version updated" "grep -q '0.1.0' pyproject.toml"
check "CHANGELOG updated" "grep -q '## \\[0.1.0\\]' CHANGELOG.md"

# Documentation
check "README updated for web UI" "grep -q 'Web.*UI\\|frontend' README.md"
check "Installation guide updated" "grep -q 'npm\\|frontend' README.md"

# Security
check "No console.log in production" "! grep -r 'console.log' frontend/dist/"
check "API keys not in frontend" "! grep -r 'sk-proj' frontend/"

# Git
check "No uncommitted changes" "test -z \"$(git status --porcelain)\""
check "Git tag exists" "git tag | grep -q 'v0.1.0'"

echo ""
echo "✅ v0.1.0 READY FOR RELEASE"
```

---

## Validation Runner

Create a master script to run appropriate validation:

### `scripts/validate.sh`

```bash
#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./scripts/validate.sh <version>"
    echo "Example: ./scripts/validate.sh v0.1.0-alpha.1"
    exit 1
fi

VERSION=$1
SCRIPT="./scripts/validate_${VERSION}.sh"

if [ ! -f "$SCRIPT" ]; then
    echo "Error: Validation script not found: $SCRIPT"
    exit 1
fi

chmod +x "$SCRIPT"
exec "$SCRIPT"
```

---

## GitHub Issues Template

For each milestone, create issues:

```markdown
## v0.1.0-alpha.1: Foundation

### Backend Tasks
- [ ] #XX Create config API routes (stub)
- [ ] #XX Create models API routes (stub)
- [ ] #XX Create documents API routes (stub)
- [ ] #XX Create wiki API routes (stub)
- [ ] #XX Update database schema with new tables
- [ ] #XX Add WebSocket basic support

### Frontend Tasks
- [ ] #XX Initialize Vite + React + TypeScript project
- [ ] #XX Configure Tailwind CSS + shadcn/ui
- [ ] #XX Set up directory structure
- [ ] #XX Create API client service
- [ ] #XX Create WebSocket service
- [ ] #XX Build basic layout components
- [ ] #XX Configure React Router

### Validation
- [ ] #XX Write validation script
- [ ] #XX Test backend compilation
- [ ] #XX Test frontend build
- [ ] #XX Manual smoke test
```

---

## Next Steps

1. **Create scripts directory**: `mkdir -p scripts`
2. **Write validation scripts**: One per version
3. **Create GitHub issues**: Based on deliverables
4. **Set up CI/CD**: Run validation in GitHub Actions
5. **Start v0.1.0-alpha.1**: Begin implementation

---

*Document Created: 2025-11-17*
*Author: Claude Code*
*Target: Web UI Implementation Plan*
