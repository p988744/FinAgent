# Web UI Milestone Analysis & Clarifications

**Created:** 2025-11-17
**Purpose:** Identify ambiguities, risks, and clarify implementation details

---

## Critical Issues Found

### 1. Missing Dependency: Backend for alpha.2 before alpha.1 complete

**Issue:** alpha.2 requires WebSocket streaming, but alpha.1 only has "basic WebSocket connection"

**Clarification:**
- alpha.1: WebSocket infrastructure (connection/disconnect only)
- alpha.2: WebSocket message streaming with callbacks

**Decision:** alpha.1 must include WebSocket message serialization framework, alpha.2 adds actual streaming logic

---

### 2. Unclear: "Stub" vs "Full Implementation"

**Issue:** alpha.1 says "API routes (stub)" but validation checks for file existence only

**Clarification:**
- **Stub** = File exists with route definitions, returns mock/empty responses
- **Partial** = Core logic implemented, not all edge cases
- **Full** = Production-ready with validation, error handling

**Updated Definitions:**

| Version | Backend Implementation Level |
|---------|------------------------------|
| alpha.1 | Stub (file exists, empty routes) |
| alpha.2 | Partial (research endpoints functional) |
| alpha.3 | Partial (config/models functional) |
| alpha.4 | Partial (documents functional) |
| alpha.5 | Partial (wiki functional) |
| beta.1 | Full (all endpoints complete) |

---

### 3. Missing: Frontend-Backend Contract

**Issue:** No OpenAPI/TypeScript type synchronization specified

**Clarification:**
- Backend generates OpenAPI spec (`/openapi.json`)
- Frontend uses `openapi-typescript-codegen` to generate types
- Types must match between frontend and backend

**Add to alpha.1:**
```bash
# Generate TypeScript types from OpenAPI
npx openapi-typescript-codegen --input http://localhost:8000/openapi.json --output ./src/types/api
```

---

### 4. Unclear: Database Migration Strategy

**Issue:** alpha.1 adds 4 new tables but no migration script mentioned

**Clarification:**
- Option A: Manual SQL execution (risky)
- Option B: Alembic migrations (recommended)
- Option C: Schema recreation (data loss)

**Decision:** Use manual SQL with versioned migration scripts:
```
src/finagent/database/migrations/
├── 001_initial_schema.sql       # Existing
└── 002_web_ui_tables.sql        # New (alpha.1)
```

**Add to validation:**
```bash
check "Migration script exists" "test -f src/finagent/database/migrations/002_web_ui_tables.sql"
```

---

### 5. Ambiguous: "Real-time Monitoring Panel" Scope

**Issue:** Section 1.1 specifies 3 subcomponents but unclear if ALL required for alpha.2

**Clarification:**

| Component | alpha.2 | beta.1 |
|-----------|---------|--------|
| Agent Workflow Stepper | ✓ Required | Enhanced |
| Todo List Panel | ✓ Required | Enhanced |
| Activity Log | ✓ Basic (static list) | Full (filtering, search) |

**Minimum Viable for alpha.2:**
- Steps: Show 4 steps with status colors
- Todos: Show list, update on WebSocket message
- Log: Append-only list, no filtering
`
**Enhancement Strategy (Base → Enhanced):**
```typescript
// alpha.2: Base Implementation
<AgentWorkflowStepper steps={steps} />
// - Static step names
// - Basic color changes (pending/active/done)
// - No animations

// beta.1: Enhanced Implementation (extends base)
<AgentWorkflowStepper
  steps={steps}
  showElapsedTime={true}      // NEW: timing display
  expandable={true}           // NEW: click to show details
  animated={true}             // NEW: pulse animation
  showIteration={true}        // NEW: re-search counter
/>
// - Same component, more props
// - Backward compatible
// - Feature flags for new capabilities
```

---

### 6. Missing: Error Recovery Strategy

**Issue:** What happens if WebSocket disconnects mid-query?

**Clarification:**
- Auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- Display "Reconnecting..." status in UI
- Cache last known state locally
- Fallback to REST polling if WebSocket fails completely

**Add to alpha.2 deliverables:**
- WebSocket reconnection logic
- Connection status indicator
- Graceful degradation to REST

---

### 7. Unclear: File Upload Size Limits

**Issue:** alpha.4 mentions "File upload" but no size limits specified

**Clarification:**
- Maximum file size: 50MB (configurable)
- Allowed types: TXT, PDF, HTML, DOCX
- Concurrent uploads: Max 5 files
- Total batch size: 200MB

**Add to validation:**
```bash
check "File size limit configured" "grep -q 'max_size\\|MAX_FILE_SIZE' src/finagent/api/routes/documents.py"
```

---

### 8. Missing: Authentication/Authorization

**Issue:** No auth mentioned in any milestone

**Clarification:**
- v0.1.0: No authentication (single-user, local deployment)
- v0.2.0+: Add JWT authentication
- v0.3.0+: Add RBAC (role-based access control)

**Document in alpha.1:**
```python
# Note: Authentication is NOT implemented in v0.1.0
# All endpoints are open access for single-user deployment
# Future: Add JWT middleware in v0.2.0
```

---

### 9. Ambiguous: "Wiki Page Auto-Generation"

**Issue:** When are wiki pages generated? Real-time or batch?

**Clarification:**
- **On Document Upload:** Generate stub wiki page
- **On Reindex:** Update with entity extraction
- **Manual Trigger:** User can regenerate

**Workflow:**
1. Document uploaded → Create wiki_pages entry with basic metadata
2. Document indexed → Extract entities, update wiki page
3. User clicks "Regenerate" → Re-run entity extraction

---

### 10. Missing: Deployment Configuration

**Issue:** How to run frontend and backend together?

**Clarification:**

**Development Mode:**
```bash
# Terminal 1: Backend
uv run uvicorn finagent.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev  # Runs on :5173, proxies API to :8000
```

**Production Mode:**
```bash
# Option A: Serve frontend from FastAPI
# Backend serves static files from frontend/dist/

# Option B: Separate servers with nginx reverse proxy
```

**Add to alpha.1:**
- `frontend/vite.config.ts` with proxy configuration
- `src/finagent/main.py` with static file serving (optional)

---

## Risk Assessment

### High Risk Items

1. **WebSocket Complexity** (alpha.2)
   - Risk: Callback orchestration difficult to debug
   - Mitigation: Add extensive logging, timeout handling

2. **Entity Extraction Accuracy** (alpha.5)
   - Risk: NLP extraction may miss important entities
   - Mitigation: Start with rule-based extraction, add ML later

3. **File Upload Security** (alpha.4)
   - Risk: Malicious file upload, path traversal
   - Mitigation: Validate file types, sanitize filenames, virus scan

### Medium Risk Items

4. **State Synchronization** (alpha.2)
   - Risk: Frontend/backend state drift
   - Mitigation: Single source of truth (backend), frontend only renders

5. **Performance** (beta.1)
   - Risk: Large document lists slow to render
   - Mitigation: Virtual scrolling, pagination, lazy loading

### Low Risk Items

6. **Type Safety** (all versions)
   - Risk: TypeScript compilation errors
   - Mitigation: Strict mode, automated type generation

---

## Validation Script Improvements

### Current Issues

1. **Silent failures:** `eval "$cmd" > /dev/null 2>&1` hides errors
2. **No timeout:** Commands can hang indefinitely
3. **No prerequisites check:** Assumes npm, uv installed
4. **No cleanup:** Leaves processes running

### Improved Validation Framework

```bash
#!/bin/bash
# Improved validation with better error handling

set -euo pipefail

# Timeout for long-running commands
TIMEOUT_SECONDS=60

# Check prerequisites
check_prereqs() {
    command -v npm >/dev/null 2>&1 || { echo "npm not found"; exit 1; }
    command -v uv >/dev/null 2>&1 || { echo "uv not found"; exit 1; }
}

# Check with timeout and error capture
check_with_timeout() {
    local name="$1"
    local cmd="$2"
    local timeout="${3:-$TIMEOUT_SECONDS}"

    if timeout "$timeout" bash -c "$cmd" 2>&1 | head -20; then
        echo "✓ $name"
        return 0
    else
        echo "✗ $name"
        return 1
    fi
}

# Cleanup on exit
cleanup() {
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

check_prereqs
# ... rest of validation
```

---

## Clarified Milestone Scope

### v0.1.0-alpha.1: Foundation

**Must Have:**
- [ ] 4 API route files (config, models, documents, wiki) with stub endpoints
- [ ] 4 new database tables with migration script
- [ ] Frontend project builds successfully
- [ ] Basic layout (header, sidebar) renders
- [ ] API client can make GET request to backend
- [ ] CORS configured for localhost:5173

**Nice to Have:**
- [ ] OpenAPI type generation
- [ ] shadcn/ui component library installed
- [ ] ESLint + Prettier configured

**Explicitly NOT Included:**
- No actual endpoint logic (stubs only)
- No authentication
- No file upload handling
- No WebSocket streaming (only connection)

---

### v0.1.0-alpha.2: Query Core

**Must Have:**
- [ ] Query input accepts text and submits
- [ ] WebSocket streams updates during query
- [ ] Agent pipeline stepper shows 4 steps
- [ ] Todo list displays and updates
- [ ] Activity log appends entries
- [ ] Results display with markdown
- [ ] Citations clickable

**Nice to Have:**
- [ ] Export to JSON
- [ ] Query history list
- [ ] Confidence score visualization

**Explicitly NOT Included:**
- No query templates (alpha.3)
- No PDF export (beta.1)
- No advanced log filtering (beta.1)

---

### v0.1.0-alpha.3: Config & Models

**Must Have:**
- [ ] Settings list by category (LLM, Embedding)
- [ ] Edit single setting value
- [ ] Save current config as preset
- [ ] Load preset by ID
- [ ] Delete preset
- [ ] Model list with selection
- [ ] Test connection button

**Nice to Have:**
- [ ] Side-by-side preset comparison
- [ ] Usage statistics chart
- [ ] Cost calculator

**Explicitly NOT Included:**
- No .env file editing (security risk)
- No bulk settings import
- No model benchmarking

---

### v0.1.0-alpha.4: Documents

**Must Have:**
- [ ] File upload via button click
- [ ] Drag-and-drop zone
- [ ] Document list with metadata
- [ ] Single document reindex
- [ ] Single document delete
- [ ] Batch select documents
- [ ] Batch reindex

**Nice to Have:**
- [ ] Version history view
- [ ] Batch delete
- [ ] Index progress indicator

**Explicitly NOT Included:**
- No PDF parsing (existing backend limitation)
- No document preview
- No full-text search within documents

---

### v0.1.0-alpha.5: Wiki

**Must Have:**
- [ ] Auto-generated wiki pages from documents
- [ ] Category sidebar navigation
- [ ] Tag cloud display
- [ ] Full-text search (basic)
- [ ] Markdown rendering of content

**Nice to Have:**
- [ ] Timeline view of documents
- [ ] Entity relationship display
- [ ] Cross-reference links

**Explicitly NOT Included:**
- No interactive graph visualization (future)
- No annotation system
- No versioned wiki pages

---

## Updated Timeline

| Version | Minimum Viable | Full Scope | Buffer |
|---------|----------------|------------|--------|
| alpha.1 | 3 days | 5 days | 2 days |
| alpha.2 | 5 days | 7 days | 2 days |
| alpha.3 | 4 days | 6 days | 1 day |
| alpha.4 | 5 days | 7 days | 2 days |
| alpha.5 | 4 days | 6 days | 1 day |
| beta.1 | 5 days | 7 days | 3 days |
| v0.1.0 | 2 days | 3 days | 2 days |

**Total: 28-41 days (4-6 weeks)** vs original 7 weeks

**Risk Buffer:** 15% additional time for unexpected issues

---

## Decision Points Needed

1. **Frontend Framework Choice**
   - Current: React + TypeScript + Vite
   - Alternative: Next.js (SSR benefits)
   - **Decision:** Stick with React + Vite (simpler, no SSR needed)

2. **State Management**
   - Current: Zustand or React Query
   - **Decision:** React Query for server state, Zustand for UI state

3. **Component Library**
   - Current: shadcn/ui
   - Alternative: Chakra UI, Material UI
   - **Decision:** shadcn/ui (Tailwind-based, tree-shaking)

4. **WebSocket Library**
   - Options: Native WebSocket, Socket.io, ws
   - **Decision:** Native WebSocket (simpler, no dependency)

5. **Entity Extraction Approach**
   - Options: Regex/Rule-based, SpaCy, OpenAI
   - **Decision:** Rule-based for alpha.5, OpenAI for beta (cost consideration)

---

## Summary

### Key Clarifications Made

1. **Stub vs Full** implementation clearly defined per milestone
2. **Minimum Viable** scope specified for each feature
3. **Error handling** and recovery strategies documented
4. **Migration strategy** for database schema changes
5. **Deployment configuration** for dev and prod
6. **Authentication** explicitly out of scope for v0.1.0
7. **File upload** constraints defined (50MB, specific types)
8. **WebSocket** reconnection strategy specified
9. **Wiki generation** timing (on upload, on index, on demand)
10. **Timeline** revised to 4-6 weeks with buffer

### Next Actions

1. Update `WEB_UI_MILESTONES.md` with clarified scope
2. Add migration script requirement to alpha.1 validation
3. Create issue templates with Must Have / Nice to Have sections
4. Set up frontend project with recommended configuration
5. Begin alpha.1 implementation

---

*Analysis Date: 2025-11-17*
*Author: Claude Code*
