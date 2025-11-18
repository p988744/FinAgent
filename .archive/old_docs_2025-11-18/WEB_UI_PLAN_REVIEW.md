# Web UI Plan Review & Consolidation

**Date:** 2025-11-17
**Status:** Plan Review - Functional-First Approach

---

## Current Documentation Status

| Document | Purpose | Status |
|----------|---------|--------|
| `WEB_UI_SPEC.md` | Feature specifications | ✓ Complete |
| `WEB_UI_MILESTONES.md` | Original enhancement-based plan | ⚠ Deprecated |
| `WEB_UI_CLARIFICATIONS.md` | Risk analysis & ambiguities | ✓ Valid (needs update) |
| `WEB_UI_FUNCTIONAL_MILESTONES.md` | New functional-first plan | ✓ **Authoritative** |

**Recommendation:** Use `WEB_UI_FUNCTIONAL_MILESTONES.md` as the primary implementation guide.

---

## Plan Comparison

### Old Approach (WEB_UI_MILESTONES.md)
```
alpha.1 → alpha.2 → alpha.3 → alpha.4 → alpha.5 → beta.1 → v0.1.0
  ↓         ↓         ↓         ↓         ↓         ↓
Setup    Query     Config    Models     Docs      Wiki    Release
         (Basic)   (Basic)   (Basic)   (Basic)   (Basic)
                      ↓         ↓         ↓         ↓
                   Enhanced  Enhanced  Enhanced  Enhanced (in beta.1)
```
**Problem:** Features split across versions, hard to test

### New Approach (WEB_UI_FUNCTIONAL_MILESTONES.md)
```
alpha.1 → alpha.2 → alpha.3 → alpha.4 → alpha.5 → alpha.6 → beta.1 → v0.1.0
  ↓         ↓         ↓         ↓         ↓         ↓         ↓
Setup   Query     Config    Models     Docs      Wiki    Integration
        (FULL)    (FULL)    (FULL)    (FULL)    (FULL)
```
**Benefit:** Each feature 100% complete and testable

---

## Critical Review: Issues Found

### Issue 1: Version Numbering Inconsistency

**Old Plan:** 5 alphas + 1 beta
```
alpha.1, alpha.2, alpha.3, alpha.4, alpha.5, beta.1
```

**New Plan:** 6 alphas + 1 beta
```
alpha.1, alpha.2, alpha.3, alpha.4, alpha.5, alpha.6, beta.1
```

**Decision:** New plan adds alpha.6 for Wiki (correct - more granular)

---

### Issue 2: Scope Creep Risk in alpha.2

**Full Query Feature includes:**
- WebSocket streaming
- Agent stepper (with timing, details, expand)
- Todo panel (with progress %, timing)
- Activity log (with colors, auto-scroll)
- Results rendering (markdown, citations)
- Export JSON

**Risk:** Too much for single version

**Mitigation Options:**

**Option A: Split Query into 2 versions**
```
alpha.2a: Query Core (input → results, no monitoring)
alpha.2b: Query Monitoring (stepper, todos, log)
```

**Option B: Keep as single version but reduce scope**
```
alpha.2: Query with monitoring
- Stepper: 4 steps, colors, timing (NO expandable details)
- Todos: List, status (NO sub-tasks display)
- Log: Append-only (NO filtering, NO export)
```

**Recommendation:** Option B - Simpler monitoring, still functional

---

### Issue 3: Missing Infrastructure Details in alpha.1

**Currently alpha.1 includes:**
- API route stubs
- Database schema
- Frontend build

**Missing critical items:**
- [ ] CORS configuration
- [ ] Vite proxy setup for API calls
- [ ] Environment variable management (.env.local)
- [ ] TypeScript path aliases
- [ ] API error handling base
- [ ] WebSocket connection setup (not streaming)

**Recommendation:** Add these to alpha.1 checklist

---

### Issue 4: Document Management Complexity

**alpha.5 (Documents) includes:**
- File upload
- Version control
- Reindex operations
- Delete cascade

**Dependency Issue:** Requires RAG pipeline working correctly

**Current backend status:**
- ✓ Document loading works
- ✓ Chunking works
- ✓ Embedding works
- ✓ Indexing works
- ✗ No file upload API
- ✗ No version control
- ✗ No web-triggered reindex

**Effort Estimate:** 7-10 days (largest feature)

**Recommendation:** May need to be split:
```
alpha.5a: Document Upload + Index
alpha.5b: Version Control + Delete
```
Or accept longer timeline.

---

### Issue 5: Wiki Auto-Generation Unclear

**Question:** How are wiki pages generated?

**Options:**
1. **On-Upload:** Extract metadata immediately
2. **On-Index:** Use LLM to extract entities after indexing
3. **Batch Job:** Scheduled regeneration
4. **Manual Trigger:** User clicks "Generate Wiki"

**Current Backend:** No entity extraction service exists

**Recommendation:**
- alpha.6 (Wiki) focuses on display only
- Entity extraction as future enhancement
- Use existing document metadata for now

---

### Issue 6: Testing Strategy Not Defined

**Functional-first requires:**
- End-to-end tests per feature
- User acceptance criteria
- Performance benchmarks

**Missing:**
- [ ] E2E test framework (Playwright? Cypress?)
- [ ] Test data setup scripts
- [ ] CI/CD pipeline for automated testing
- [ ] Performance monitoring

**Recommendation:** Add E2E framework setup to alpha.1

---

## Revised Milestone Plan (Functional-First)

### v0.1.0-alpha.1: Development Foundation
**Timeline:** 5 days
**Deliverable:** Dev environment ready for feature development

**Backend:**
- [ ] 4 API route files (empty stubs)
- [ ] Database migration script (new tables)
- [ ] CORS configured for frontend
- [ ] Health check endpoint

**Frontend:**
- [ ] Vite + React + TypeScript project
- [ ] Tailwind CSS configured
- [ ] React Router with empty pages
- [ ] API client service (with error handling)
- [ ] WebSocket service (connection only)
- [ ] Vite proxy to backend API
- [ ] Basic layout (header, sidebar)

**Testing:**
- [ ] E2E framework setup (Playwright)
- [ ] Backend test fixtures
- [ ] CI script placeholder

**Validation:**
```bash
curl http://localhost:8000/health → 200
npm run build → success
E2E: Can navigate to empty pages
```

**User Can Test:** Nothing (infrastructure)

---

### v0.1.0-alpha.2: Complete Query Feature
**Timeline:** 7-10 days
**Deliverable:** Fully functional query with monitoring

**Backend:**
- [ ] WebSocket streaming endpoint
- [ ] WebSocketUICallback implementation
- [ ] Query history persistence
- [ ] Results caching

**Frontend (Query Page):**
- [ ] Query input with validation
- [ ] Submit button (WebSocket or REST fallback)
- [ ] Agent Pipeline Stepper
  - 4 steps: Planning → Action → Validation → Answer
  - Status colors: pending/active/done/error
  - Elapsed time per step
  - Current step description
- [ ] Todo List Panel
  - Task list from WebSocket
  - Status icons
  - Progress percentage
  - Total elapsed time
- [ ] Activity Log
  - Append-only entries
  - Timestamps
  - Color-coded by type
  - Auto-scroll
- [ ] Results Panel
  - Executive summary
  - Key findings with citations
  - Confidence score bar
  - Citation list (clickable)
- [ ] Export to JSON button

**Testing:**
```bash
E2E Test Script:
1. Navigate to /query
2. Enter "玉山銀行洗錢防制"
3. Click submit
4. Verify WebSocket connection opens
5. Verify stepper updates (4 transitions)
6. Verify todos appear and update
7. Verify log entries append
8. Verify results display
9. Verify export downloads JSON file
10. Total time < 60 seconds
```

**User Can Test:**
- Submit real legal research queries
- Watch agent workflow in real-time
- Verify results are accurate
- Export results for review

---

### v0.1.0-alpha.3: Complete Config Management
**Timeline:** 5-7 days
**Deliverable:** Full configuration CRUD

**Backend:**
- [ ] GET /config/settings
- [ ] PUT /config/settings/{key}
- [ ] GET /config/presets
- [ ] POST /config/presets
- [ ] DELETE /config/presets/{id}
- [ ] POST /config/presets/{id}/activate
- [ ] POST /config/reload

**Frontend (Config Page):**
- [ ] Settings list by category
- [ ] Edit form with validation
- [ ] Save/Cancel buttons
- [ ] Preset list
- [ ] Save as preset button
- [ ] Load preset button
- [ ] Delete preset button
- [ ] Active preset indicator
- [ ] Reload from .env button
- [ ] Success/error toasts

**Testing:**
```bash
E2E Test Script:
1. Navigate to /config
2. Verify settings load
3. Edit temperature → 0.5
4. Save → verify persisted
5. Create preset "Test"
6. Verify preset in list
7. Load preset
8. Verify settings change
9. Delete preset
10. Verify removed
```

**User Can Test:**
- Change LLM settings
- Create configuration profiles
- Switch between profiles
- Persist preferences

---

### v0.1.0-alpha.4: Complete Model Management
**Timeline:** 5-7 days
**Deliverable:** Model selection and monitoring

**Backend:**
- [ ] GET /models/llm/available
- [ ] POST /models/llm/test
- [ ] PUT /models/llm/active
- [ ] GET /models/embedding/available
- [ ] GET /models/stats (usage data)

**Frontend (Models Page):**
- [ ] LLM model list with descriptions
- [ ] Model selection radio buttons
- [ ] Test connection button
- [ ] Connection status indicator
- [ ] Embedding model list
- [ ] Embedding model selection
- [ ] Usage statistics display
  - Token count this session
  - Cost estimate
  - Chart (optional)
- [ ] Save model selection

**Testing:**
```bash
E2E Test Script:
1. Navigate to /models
2. Verify model list loads
3. Select different LLM model
4. Click test connection
5. Verify success/failure message
6. Save selection
7. Go to /query
8. Submit query
9. Verify new model is used
```

**User Can Test:**
- Choose different LLM models
- Verify model connection works
- Monitor token usage
- Compare model costs

---

### v0.1.0-alpha.5: Complete Document Management
**Timeline:** 7-10 days
**Deliverable:** Document lifecycle management

**Backend:**
- [ ] POST /documents/upload (multipart)
- [ ] GET /documents
- [ ] GET /documents/{id}
- [ ] DELETE /documents/{id}
- [ ] POST /documents/{id}/reindex
- [ ] POST /documents/reindex (batch)
- [ ] GET /documents/index-status
- [ ] POST /documents/{id}/versions (upload new version)
- [ ] GET /documents/{id}/versions

**Frontend (Documents Page):**
- [ ] File upload drop zone
- [ ] Upload progress indicator
- [ ] Document list table
  - Name, size, date, status
  - Sortable columns
  - Pagination
- [ ] Document actions
  - View content
  - Reindex single
  - Delete with confirmation
  - Upload new version
- [ ] Version history modal
- [ ] Batch reindex button
- [ ] Index status summary

**Testing:**
```bash
E2E Test Script:
1. Navigate to /documents
2. Drag file to upload zone
3. Verify progress bar
4. Verify document appears in list
5. Click reindex
6. Verify status changes
7. Go to /query
8. Search for content in new document
9. Verify document is in results
10. Delete document
11. Verify removed from list
```

**User Can Test:**
- Add documents to knowledge base
- Monitor indexing progress
- Update documents
- Remove outdated content

---

### v0.1.0-alpha.6: Complete Wiki Browser
**Timeline:** 5-7 days
**Deliverable:** Knowledge base visualization

**Backend:**
- [ ] GET /wiki/pages
- [ ] GET /wiki/pages/{id}
- [ ] GET /wiki/categories
- [ ] GET /wiki/tags
- [ ] POST /wiki/search
- [ ] Auto-generate wiki page on document index

**Frontend (Wiki Page):**
- [ ] Category tree sidebar
- [ ] Tag cloud
- [ ] Search input with results
- [ ] Wiki page viewer
  - Title
  - Metadata (date, source)
  - Markdown content
  - Entity highlights (if available)
  - Related documents
- [ ] Breadcrumb navigation
- [ ] "Back to list" button

**Testing:**
```bash
E2E Test Script:
1. Navigate to /wiki
2. Verify categories load
3. Click category → filter documents
4. Click tag → filter documents
5. Search "玉山銀行"
6. Verify results
7. Click result
8. Verify page content renders
9. Verify markdown formatted
10. Click related document → navigate
```

**User Can Test:**
- Browse knowledge base
- Find related documents
- Search across all content
- Read document summaries

---

### v0.1.0-beta.1: Integration & Polish
**Timeline:** 7-10 days
**Deliverable:** All features work together

**Integration Tests:**
- [ ] Query → uses documents from Document Manager
- [ ] Config → affects Query behavior (model, temperature)
- [ ] Models → selection persists across pages
- [ ] Documents → appear in Wiki
- [ ] Wiki → links to Documents
- [ ] Navigation → all pages accessible
- [ ] State → persists across page changes
- [ ] Errors → handled consistently

**Polish:**
- [ ] Loading spinners
- [ ] Error messages (Chinese)
- [ ] Responsive design
- [ ] Bundle size < 2MB
- [ ] No console errors
- [ ] Accessibility basics

**Testing:**
```bash
Full Integration Test:
1. Upload document (Documents)
2. Reindex (Documents)
3. View in Wiki (Wiki)
4. Change model (Models)
5. Update temperature (Config)
6. Query new document (Query)
7. Verify results use new settings
8. Export results
9. Verify all data consistent
```

---

### v0.1.0: Production Release
**Timeline:** 3-5 days
**Deliverable:** Stable release

- [ ] Version numbers updated
- [ ] CHANGELOG updated
- [ ] README updated
- [ ] No console.log in production
- [ ] Security review (no API keys exposed)
- [ ] Performance acceptable
- [ ] Git tag created
- [ ] Release notes written

---

## Updated Timeline Summary

| Version | Focus | Days | Cumulative |
|---------|-------|------|------------|
| alpha.1 | Infrastructure | 5 | 5 |
| alpha.2 | Query (FULL) | 10 | 15 |
| alpha.3 | Config (FULL) | 7 | 22 |
| alpha.4 | Models (FULL) | 7 | 29 |
| alpha.5 | Documents (FULL) | 10 | 39 |
| alpha.6 | Wiki (FULL) | 7 | 46 |
| beta.1 | Integration | 10 | 56 |
| v0.1.0 | Release | 5 | **61 days** |

**Total: ~61 working days (12-13 weeks)**

**Risk Buffer:** +20% = **73 days (15 weeks)**

---

## Action Items

1. **Consolidate Documents**
   - [ ] Rename `WEB_UI_FUNCTIONAL_MILESTONES.md` → `WEB_UI_IMPLEMENTATION_PLAN.md`
   - [ ] Archive `WEB_UI_MILESTONES.md` (old enhancement-based)
   - [ ] Update `WEB_UI_CLARIFICATIONS.md` with new timeline

2. **Update Validation Scripts**
   - [ ] Rewrite `validate_v0.1.0-alpha.1.sh` for functional approach
   - [ ] Create alpha.2 validation with E2E tests
   - [ ] Add performance benchmarks

3. **Create GitHub Issues**
   - [ ] One issue per feature (not per file)
   - [ ] Include acceptance criteria
   - [ ] Include E2E test requirements

4. **Decide on Scope**
   - [ ] Is 15 weeks acceptable?
   - [ ] Reduce scope (remove Wiki? Simplify monitoring?)
   - [ ] Add more resources?

---

## Recommendations

1. **Accept longer timeline** - 15 weeks is realistic for functional-complete approach

2. **Start with alpha.1 immediately** - Infrastructure has no dependencies

3. **Parallel backend/frontend work** - Different developers can work simultaneously

4. **Weekly validation** - Run validation scripts every week

5. **User testing after each alpha** - Get feedback early

6. **Document as you go** - Update specs with learnings

---

*Review Date: 2025-11-17*
*Status: Ready for Approval*
