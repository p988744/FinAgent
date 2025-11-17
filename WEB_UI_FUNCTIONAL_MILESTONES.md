# Web UI Functional Milestones

**Approach:** Feature-Complete Per Version
**Principle:** Each version delivers USABLE features that can be fully tested

---

## Core Principle: Functional Completeness

**NOT This (Enhancement-based):**
```
alpha.2: Basic stepper (colors only)
beta.1:  Enhanced stepper (add timing, expand)
```

**THIS (Feature-complete):**
```
alpha.2: Complete Query UI (input → submit → results)
alpha.3: Complete Config UI (view → edit → save)
```

Each version = **Complete vertical slice** that users can actually USE and TEST.

---

## Restructured Milestones

### v0.1.0-alpha.1: Infrastructure Only (No UI Features)

**Deliverable:** Development environment ready, NO user features

**Backend:**
- [ ] API route files exist (empty stubs)
- [ ] Database schema updated
- [ ] CORS configured
- [ ] Health check works

**Frontend:**
- [ ] Project builds
- [ ] Can fetch from backend API
- [ ] Empty pages with routes

**Validation Test:**
```bash
# Can backend start?
curl http://localhost:8000/health → 200 OK

# Can frontend build?
npm run build → success

# Can frontend call backend?
Browser console: fetch('/api/v1/health') → 200 OK
```

**User Can Test:** Nothing (infrastructure only)

---

### v0.1.0-alpha.2: Complete Query Feature

**Deliverable:** User can submit query and see FULL results with monitoring

**Complete Feature Set:**
1. Input query text → Submit
2. See real-time agent steps (Planning → Action → Validation → Answer)
3. See real-time todo list updates
4. See activity log entries
5. See final results with citations
6. Export results to JSON

**ALL monitoring components COMPLETE:**
- Agent Stepper: Steps + status + timing + expandable details
- Todo Panel: List + progress % + timing
- Activity Log: Entries + timestamps + colors + auto-scroll

**Validation Test:**
```bash
# End-to-end query test
1. Open http://localhost:5173/query
2. Enter: "玉山銀行洗錢防制"
3. Click Submit
4. VERIFY:
   - [ ] Stepper shows Planning → (active)
   - [ ] Todos appear and update
   - [ ] Log entries append
   - [ ] Stepper advances to Action
   - [ ] Results display with citations
   - [ ] Export JSON downloads file
5. Time: Should complete in ~40s
```

**Automated Validation:**
```bash
#!/bin/bash
# Test query flow
check "Query input accepts text" "..."
check "Submit button triggers WebSocket" "..."
check "Stepper updates in real-time" "..."
check "Results contain citations" "..."
check "Export JSON creates valid file" "..."
```

**User Can Test:**
- Submit real queries
- Watch real-time progress
- Verify results accuracy
- Export for review

---

### v0.1.0-alpha.3: Complete Config Management Feature

**Deliverable:** User can fully manage all configuration

**Complete Feature Set:**
1. View ALL settings by category
2. Edit ANY setting value with validation
3. Save current config as named preset
4. Load any saved preset (becomes active)
5. Delete presets
6. See which preset is currently active
7. Reload config from .env file

**ALL config operations COMPLETE:**
- CRUD for settings: Create, Read, Update, Delete
- Preset lifecycle: Save, Load, Activate, Delete
- Validation: Real-time input validation with error messages
- Persistence: Changes saved to database immediately

**Validation Test:**
```bash
# End-to-end config test
1. Open http://localhost:5173/config
2. VERIFY Settings:
   - [ ] See LLM category with all settings
   - [ ] Edit temperature value → validation works
   - [ ] Save changes → persisted
3. VERIFY Presets:
   - [ ] Click "Save Preset" → enter name "Test"
   - [ ] Preset appears in list
   - [ ] Create another preset "Production"
   - [ ] Click "Load" on "Test" → settings change
   - [ ] Active indicator shows "Test ✓"
   - [ ] Delete "Test" → removed from list
4. VERIFY Reload:
   - [ ] Click "Reload from .env"
   - [ ] Settings update from file
```

**User Can Test:**
- Configure LLM settings
- Switch between configurations
- Organize presets for different use cases

---

### v0.1.0-alpha.4: Complete Model Management Feature

**Deliverable:** User can fully manage LLM and Embedding models

**Complete Feature Set:**
1. View available LLM models (from model_config.yml)
2. Select and activate different LLM model
3. Test LLM connection with actual API call
4. View available embedding models
5. Select embedding model
6. See current usage statistics (tokens, cost)
7. Cost calculator for model comparison

**ALL model operations COMPLETE:**
- Model selection with immediate activation
- Connection test with real feedback
- Usage tracking with actual data
- Cost comparison with real pricing

**Validation Test:**
```bash
# End-to-end model test
1. Open http://localhost:5173/models
2. VERIFY LLM:
   - [ ] See list: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
   - [ ] Select gpt-3.5-turbo
   - [ ] Click "Test Connection"
   - [ ] See success/failure message
   - [ ] Model saved as active
3. VERIFY Embedding:
   - [ ] See embedding models list
   - [ ] Select different model
   - [ ] Changes saved
4. VERIFY Stats:
   - [ ] See token usage chart
   - [ ] See cost breakdown
   - [ ] Cost calculator works
5. Go back to Query page:
   - [ ] New model is used for query
```

**User Can Test:**
- Switch between models
- Verify connection works
- Compare costs
- Track usage

---

### v0.1.0-alpha.5: Complete Document Management Feature

**Deliverable:** User can fully manage document lifecycle

**Complete Feature Set:**
1. Upload new documents (drag-drop or click)
2. See all documents with metadata
3. View document content
4. Upload new version of existing document
5. See version history with diff
6. Reindex single document
7. Reindex all documents (batch)
8. Delete document (with confirmation)
9. See index status (indexed/pending/error)

**ALL document operations COMPLETE:**
- Upload with progress indicator
- Version control with history
- Indexing with real RAG pipeline
- Delete with cascade cleanup

**Validation Test:**
```bash
# End-to-end document test
1. Open http://localhost:5173/documents
2. VERIFY Upload:
   - [ ] Drag file to drop zone
   - [ ] Progress bar shows upload
   - [ ] Document appears in list
   - [ ] Status shows "Pending Index"
3. VERIFY Indexing:
   - [ ] Click "Reindex" on document
   - [ ] Progress indicator shows
   - [ ] Status changes to "Indexed ✓"
   - [ ] Chunk count displayed
4. VERIFY Version:
   - [ ] Click "Upload New Version"
   - [ ] Upload modified file
   - [ ] Version number increments
   - [ ] Click "History" → see versions
5. VERIFY Delete:
   - [ ] Click "Delete"
   - [ ] Confirmation modal appears
   - [ ] Confirm → document removed
   - [ ] Vector DB cleaned up
6. Test Query:
   - [ ] Go to Query page
   - [ ] Search for content in new document
   - [ ] Results include new document
```

**User Can Test:**
- Add new documents to knowledge base
- Update documents with new versions
- Remove outdated documents
- Verify documents are searchable

---

### v0.1.0-alpha.6: Complete Wiki Feature

**Deliverable:** User can browse auto-generated knowledge base

**Complete Feature Set:**
1. See auto-generated wiki pages for all documents
2. Browse by category (裁罰案件, 判決書, 法規)
3. Browse by tags (洗錢防制, 內線交易, etc.)
4. Full-text search across wiki
5. View individual wiki page with markdown
6. See extracted entities (banks, dates, amounts)
7. See document cross-references
8. Regenerate wiki page on demand

**ALL wiki features COMPLETE:**
- Auto-generation from document metadata
- Category/tag organization
- Search with results
- Entity extraction and display

**Validation Test:**
```bash
# End-to-end wiki test
1. Open http://localhost:5173/wiki
2. VERIFY Browse:
   - [ ] See category tree sidebar
   - [ ] Click "裁罰案件" → documents listed
   - [ ] See tag cloud
   - [ ] Click tag → filtered results
3. VERIFY Search:
   - [ ] Enter "玉山銀行"
   - [ ] Results show matching pages
   - [ ] Click result → page opens
4. VERIFY Page Content:
   - [ ] Title displayed
   - [ ] Markdown rendered properly
   - [ ] Entities highlighted (bank names, dates)
   - [ ] Cross-references clickable
5. VERIFY Generation:
   - [ ] Click "Regenerate"
   - [ ] Page updates with new extraction
```

**User Can Test:**
- Explore knowledge base
- Find related documents
- Understand entity relationships
- Search across all content

---

### v0.1.0-beta.1: Integration & Polish

**Deliverable:** All features work together seamlessly

**Integration Tests:**
1. Query uses documents from Document Manager
2. Config changes affect Query behavior
3. Model changes reflect in Query results
4. Wiki shows documents managed in Document Manager
5. All pages accessible from navigation
6. Error handling consistent across features
7. Performance acceptable (< 3s page load)

**Polish:**
- Loading spinners consistent
- Error messages in Chinese
- Responsive design works
- No console errors
- Bundle size optimized

---

## Validation Framework

### Per-Feature Validation Script

```bash
#!/bin/bash
# validate_feature.sh <feature_name>

FEATURE=$1

case $FEATURE in
  "query")
    echo "Testing Complete Query Feature..."
    test_query_input_submission
    test_websocket_streaming
    test_stepper_all_states
    test_todo_updates
    test_activity_log
    test_results_display
    test_export_json
    ;;
  "config")
    echo "Testing Complete Config Feature..."
    test_settings_crud
    test_preset_lifecycle
    test_validation_rules
    test_reload_env
    ;;
  "models")
    echo "Testing Complete Models Feature..."
    test_model_selection
    test_connection_test
    test_usage_stats
    test_cost_calculator
    ;;
  "documents")
    echo "Testing Complete Documents Feature..."
    test_file_upload
    test_version_control
    test_reindex_operations
    test_delete_cascade
    ;;
  "wiki")
    echo "Testing Complete Wiki Feature..."
    test_auto_generation
    test_category_browse
    test_full_text_search
    test_entity_extraction
    ;;
esac
```

### Feature Completeness Checklist

For each feature, verify:
- [ ] **Input:** User can provide all necessary input
- [ ] **Processing:** Backend handles request completely
- [ ] **Feedback:** User sees progress/status
- [ ] **Output:** Results are complete and usable
- [ ] **Persistence:** Changes are saved permanently
- [ ] **Error Handling:** Failures are handled gracefully
- [ ] **Edge Cases:** Boundary conditions work

---

## Summary: Feature-Complete Milestones

| Version | Complete Feature | User Can... |
|---------|-----------------|-------------|
| alpha.1 | Infrastructure | Nothing (dev setup) |
| alpha.2 | **Query + Monitoring** | Submit queries, see real-time progress |
| alpha.3 | **Config Management** | Manage all settings and presets |
| alpha.4 | **Model Management** | Switch models, test connections |
| alpha.5 | **Document Management** | Upload, version, index documents |
| alpha.6 | **Wiki Browser** | Browse and search knowledge base |
| beta.1 | **Integration** | Use all features together |

Each alpha version = ONE complete feature that is FULLY USABLE and TESTABLE.

No "basic now, enhance later" - each feature is DONE when delivered.

---

*Created: 2025-11-17*
*Approach: Functional-Complete per Version*
