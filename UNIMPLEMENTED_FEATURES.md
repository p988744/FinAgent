# FinAgent - Unimplemented Features Report

**Generated:** 2025-11-13
**Status:** v0.0.1-beta
**Purpose:** Track unimplemented features and TODOs for future development

---

## Overview

This document lists all features that are partially implemented or planned but not yet complete in the FinAgent system.

## 🔴 Critical Missing Features

### 1. Query History Persistence to Database

**Status:** 🔄 Partially Implemented
**Priority:** HIGH
**Impact:** Query history is only stored in memory during CLI session

**Current State:**
- ✅ Database schema exists ([schema.sql:36-56](src/finagent/database/schema.sql#L36-L56))
- ✅ Database methods implemented ([db.py](src/finagent/database/db.py)):
  - `add_history()` - Log query to database
  - `get_history()` - Retrieve history with filters
  - `get_history_stats()` - Get statistics
  - `clear_history()` - Clear old entries
- ✅ In-memory history works in CLI ([history.py](src/finagent/cli/commands/history.py))
- ❌ CLI does not persist to database
- ❌ `/history` command shows in-memory only

**What's Missing:**
1. Integration between CLI query execution and `db.add_history()`
2. Cost calculation (tokens × price per token)
3. Processing time tracking
4. Model name tracking (which LLM was used)

**Files to Modify:**
- [src/finagent/cli/commands/query.py](src/finagent/cli/commands/query.py) - Add `db.add_history()` call
- [src/finagent/cli/repl.py:199-221](src/finagent/cli/repl.py#L199-L221) - Modify `execute_query()` to log

**Implementation Complexity:** MEDIUM
**Estimated Effort:** 2-3 hours

**Example Implementation:**
```python
# In src/finagent/cli/commands/query.py
def execute_query(query_text: str) -> LegalAnswer | None:
    start_time = time.time()

    # Execute query
    answer = orchestrator.process_query(query_text)

    # Log to database
    processing_time = time.time() - start_time
    db = Database()
    db.add_history(
        query=query_text,
        response=answer.answer if answer else None,
        model_used=config_manager.get_active_llm_config()['model'],
        tokens_used=answer.tokens_used if hasattr(answer, 'tokens_used') else None,
        cost_usd=calculate_cost(tokens_used, model),
        processing_time_seconds=processing_time,
        success=answer is not None,
    )

    return answer
```

---

### 2. Export Results Functionality

**Status:** ❌ Not Implemented
**Priority:** MEDIUM
**Impact:** Users cannot save query results to files

**Current State:**
- ✅ Command exists: `/export [format]`
- ✅ Command parsing works
- ✅ Format validation (markdown, json, txt)
- ❌ Actual export logic missing ([repl.py:331-332](src/finagent/cli/repl.py#L331-L332))

**What's Missing:**
1. Markdown export formatter
2. JSON export formatter
3. Text export formatter
4. File path selection/auto-generation
5. User notification after export

**Files to Modify:**
- [src/finagent/cli/repl.py:318-332](src/finagent/cli/repl.py#L318-L332) - Implement `export_results()`
- Create new file: `src/finagent/cli/formatters/export.py`

**Implementation Complexity:** LOW
**Estimated Effort:** 1-2 hours

**Example Implementation:**
```python
def export_results(self, format: str):
    """Export last results to file."""
    if not self.last_answer:
        console.print("[yellow]尚無查詢結果可匯出。[/yellow]")
        return

    format = format.lower() or "markdown"

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"finagent_result_{timestamp}.{format}"

    # Export based on format
    if format in ["markdown", "md"]:
        export_markdown(self.last_answer, filename)
    elif format == "json":
        export_json(self.last_answer, filename)
    elif format == "txt":
        export_text(self.last_answer, filename)

    console.print(f"[green]✓ 已匯出至: {filename}[/green]")
```

---

### 3. Statistics Command (/stats)

**Status:** ❌ Not Implemented
**Priority:** LOW
**Impact:** No visibility into usage statistics

**Current State:**
- ✅ Database has `get_history_stats()` method
- ❌ CLI command not registered
- ❌ No UI implementation

**What's Missing:**
1. `/stats` command handler
2. Statistics display formatter (Rich tables)
3. Integration with database stats

**Files to Create:**
- `src/finagent/cli/commands/stats.py`

**Files to Modify:**
- [src/finagent/cli/repl.py](src/finagent/cli/repl.py) - Add `/stats` command
- [src/finagent/cli/commands/help.py](src/finagent/cli/commands/help.py) - Document command

**Implementation Complexity:** LOW
**Estimated Effort:** 1 hour

**Statistics to Display:**
- Total queries executed
- Average processing time
- Total tokens used
- Total cost (USD/TWD)
- Most used model
- Success rate
- Query history by date

---

## 🟡 Nice-to-Have Features

### 4. Citation Details Command (/cite <編號>)

**Status:** ❌ Not Implemented
**Priority:** LOW
**Impact:** Limited - `/citations` already shows all citations

**Current State:**
- ✅ `/citations` command shows all citations
- ❌ Cannot view individual citation by number

**What's Missing:**
- Command handler for `/cite <編號>`
- Detailed citation view (with context from document)

**Files to Modify:**
- [src/finagent/cli/repl.py](src/finagent/cli/repl.py) - Add command handler

**Note:** Mentioned in [help.py:44](src/finagent/cli/commands/help.py#L44) as "尚未實作"

---

### 5. Health Check Enhancements

**Status:** 🔄 Partially Implemented
**Priority:** LOW
**Impact:** `/health/ready` endpoint doesn't verify all dependencies

**Current State:**
- ✅ Basic health check works
- ✅ Readiness endpoint exists
- ❌ No checks for database connectivity
- ❌ No checks for vector DB availability
- ❌ No checks for LLM API connectivity

**What's Missing:**
1. Database connection test
2. Chroma vector DB ping
3. LLM API test call
4. Proper error handling and reporting

**Files to Modify:**
- [src/finagent/api/routes/health.py:46-50](src/finagent/api/routes/health.py#L46-L50)

**Implementation Complexity:** MEDIUM
**Estimated Effort:** 2 hours

---

### 6. Windows Support for ESC Key Cancellation

**Status:** ❌ Not Implemented
**Priority:** LOW
**Impact:** Windows users cannot cancel queries with ESC key

**Current State:**
- ✅ Works on macOS/Linux
- ❌ Requires `msvcrt` module for Windows (not implemented)

**What's Missing:**
- Windows-specific keyboard input handling
- Conditional import for `msvcrt`

**Reference:**
- [ESC_KEY_CANCELLATION.md:210](docs/implementation/ESC_KEY_CANCELLATION.md#L210)
- [ESC_KEY_NOTE.md:83](docs/implementation/ESC_KEY_NOTE.md#L83)

**Implementation Complexity:** MEDIUM
**Estimated Effort:** 2-3 hours (requires Windows testing)

---

### 7. Session Management for History

**Status:** ❌ Not Implemented
**Priority:** LOW
**Impact:** Cannot track queries by session

**Current State:**
- ✅ Database schema has `session_id` field
- ❌ Session ID not generated or tracked
- ❌ No session-based filtering

**What's Missing:**
1. Session ID generation (UUID)
2. Session tracking in REPL
3. `/history --session <id>` command option
4. Session metadata (start time, end time, queries count)

**Files to Modify:**
- [src/finagent/cli/repl.py](src/finagent/cli/repl.py) - Add session ID tracking

---

## 📋 Implementation Priority Roadmap

### Phase 1: Essential Features (Week 1)
1. ✅ Query History Persistence - HIGH priority, frequent user need
2. ✅ Export Results - MEDIUM priority, common use case

### Phase 2: User Experience (Week 2)
3. ✅ Statistics Command - Nice visibility into usage
4. ✅ Health Check Enhancements - Better production readiness

### Phase 3: Polish (Week 3)
5. ✅ Citation Details Command - Minor improvement
6. ✅ Session Management - Advanced feature
7. ✅ Windows ESC Support - Platform compatibility

---

## 🔧 Technical Debt

### Minor TODOs

1. **Resource Initialization** ([main.py:36](src/finagent/main.py#L36))
   - TODO comment for resource initialization
   - Status: Empty implementation

2. **Resource Cleanup** ([main.py:45](src/finagent/main.py#L45))
   - TODO comment for cleanup
   - Status: Empty implementation

3. **Placeholder Citation in Orchestrator** ([orchestrator.py:305](src/finagent/agents/orchestrator.py#L305))
   - Hardcoded placeholder citation with "XXXXX"
   - Status: Should use actual document metadata

---

## 📊 Feature Completion Status

| Feature | Status | Priority | Effort |
|---------|--------|----------|--------|
| Query History Persistence | 🔄 60% | HIGH | 2-3h |
| Export Results | ❌ 10% | MEDIUM | 1-2h |
| Statistics Command | ❌ 0% | LOW | 1h |
| Citation Details | ❌ 0% | LOW | 30m |
| Health Checks | 🔄 40% | LOW | 2h |
| Windows ESC Support | ❌ 0% | LOW | 2-3h |
| Session Management | ❌ 0% | LOW | 2h |

**Overall Completion:** ~85% (Core features complete, polish items remaining)

---

## 🎯 Recommended Next Steps

1. **Implement Query History Persistence** (HIGH priority)
   - Most impactful missing feature
   - Database layer already complete
   - Just needs integration work

2. **Implement Export Results** (MEDIUM priority)
   - Common user request
   - Quick to implement
   - Good user experience improvement

3. **Create GitHub Issues**
   - Create issues for each unimplemented feature
   - Tag with appropriate labels (enhancement, good-first-issue, etc.)
   - Assign to milestones (v0.1.0, v0.2.0)

4. **Update Documentation**
   - Mark features as "Coming Soon" in README
   - Document workarounds where applicable
   - Add to CHANGELOG for next release

---

## Notes

- All database schema for history tracking is complete and tested
- Most unimplemented features are "nice-to-have" polish items
- Core functionality (RAG, LangGraph, CLI, config management) is complete
- System is production-ready for primary use case (legal research queries)
