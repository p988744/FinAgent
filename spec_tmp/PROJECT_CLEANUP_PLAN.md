# Project Structure Cleanup Plan

## Current Issues

### 1. Documentation Fragmentation (20+ MD files)
**Problem**: Documentation is scattered across 20+ markdown files, causing:
- Difficulty finding information
- Duplicate/overlapping content
- No clear documentation hierarchy
- Hard to maintain consistency

**Root Docs** (12 files):
- CLAUDE.md
- CLI_DEMO.md
- CLI_GUIDE.md
- CLI_IMPLEMENTATION_SUMMARY.md
- CLI_QUICK_REFERENCE.md
- IMPLEMENTATION_STATUS.md
- IMPORT_DOCUMENTS.md
- MVP_PLAN.md
- QUICKSTART.md
- RAG_QUICKSTART.md
- README.md
- TEST_RESULTS.md

**Backend Docs** (13 files):
- AUTOMATED_REINDEX.md
- BOUNDARY_TESTS.md
- DOCUMENT_INIT_GUIDE.md
- EMBEDDING_FIX.md
- ESC_KEY_CANCELLATION.md
- ESC_KEY_NOTE.md
- INIT_COMMAND_SUMMARY.md
- LANGGRAPH_IMPLEMENTATION.md
- LLM_CONFIG.md
- LLM_METADATA_GENERATION.md
- MODEL_CONFIG_GUIDE.md
- REINDEX_WITH_INIT.md
- TABLE_OF_CONTENTS_GUIDE.md
- TEST_RESULTS.md

**Chinese Doc** (1 file):
- 法律研究代理系統規格書.md

### 2. Temporary Test Files in Root
**Problem**: Test files should be in `tests/` directory, not backend root

Files to move/remove:
- backend/patch_ctrl_c.py (temporary patch, should be deleted)
- backend/test_ctrl_c_fix.py (ad-hoc test, should be deleted)
- backend/test_esc_cancellation.py (ad-hoc test, should be deleted)
- backend/test_langgraph.py (should move to tests/)
- backend/test_llm_metadata.py (should move to tests/)

### 3. Build Artifacts
**Problem**: `.next/` build artifacts shouldn't be in version control

Files to gitignore:
- frontend/.next/

### 4. No Clear Documentation Structure
**Problem**: No `/docs` directory or organized documentation hierarchy

## Proposed Reorganization

### A. Consolidate Documentation

#### New Structure: `/docs` Directory

```
docs/
├── README.md                          # Documentation index
├── getting-started/
│   ├── quickstart.md                  # Quick start guide (merge QUICKSTART + RAG_QUICKSTART)
│   ├── installation.md                # Installation instructions
│   └── importing-documents.md         # Document import guide (from IMPORT_DOCUMENTS)
├── user-guide/
│   ├── cli-usage.md                   # CLI usage (merge CLI_GUIDE + CLI_QUICK_REFERENCE)
│   ├── config-llm.md                  # LLM configuration (merge LLM_CONFIG + MODEL_CONFIG_GUIDE)
│   ├── document-management.md         # Document init & reindex (merge multiple)
│   └── querying.md                    # How to query the system
├── architecture/
│   ├── overview.md                    # System architecture
│   ├── langgraph-workflow.md          # LangGraph implementation (from LANGGRAPH_IMPLEMENTATION)
│   ├── rag-pipeline.md                # RAG pipeline details
│   └── multi-agent-system.md          # Agent architecture
├── development/
│   ├── setup.md                       # Dev environment setup
│   ├── testing.md                     # Testing guide (merge TEST_RESULTS files)
│   ├── contributing.md                # Contribution guidelines
│   └── implementation-notes.md        # Implementation details (from IMPLEMENTATION_STATUS)
├── reference/
│   ├── cli-commands.md                # Complete CLI command reference
│   ├── configuration-options.md       # All config options
│   ├── api-reference.md               # API documentation
│   └── model-config-schema.md         # model_config.yml schema
└── zh-tw/                             # Traditional Chinese docs
    └── specification.md               # 法律研究代理系統規格書
```

#### Consolidation Map

| New File | Source Files | Action |
|----------|--------------|--------|
| `docs/getting-started/quickstart.md` | QUICKSTART.md, RAG_QUICKSTART.md | Merge |
| `docs/getting-started/importing-documents.md` | IMPORT_DOCUMENTS.md | Move |
| `docs/user-guide/cli-usage.md` | CLI_GUIDE.md, CLI_QUICK_REFERENCE.md, CLI_DEMO.md | Merge |
| `docs/user-guide/config-llm.md` | LLM_CONFIG.md, MODEL_CONFIG_GUIDE.md | Merge |
| `docs/user-guide/document-management.md` | DOCUMENT_INIT_GUIDE.md, INIT_COMMAND_SUMMARY.md, REINDEX_WITH_INIT.md, AUTOMATED_REINDEX.md, TABLE_OF_CONTENTS_GUIDE.md | Merge |
| `docs/architecture/langgraph-workflow.md` | LANGGRAPH_IMPLEMENTATION.md | Move |
| `docs/development/testing.md` | TEST_RESULTS.md, BOUNDARY_TESTS.md | Merge |
| `docs/development/implementation-notes.md` | IMPLEMENTATION_STATUS.md, CLI_IMPLEMENTATION_SUMMARY.md, EMBEDDING_FIX.md, ESC_KEY_CANCELLATION.md, ESC_KEY_NOTE.md | Merge |
| `docs/zh-tw/specification.md` | 法律研究代理系統規格書.md | Move |
| Root `README.md` | Keep, update with new structure | Update |
| `CLAUDE.md` | Keep (project instructions for Claude) | Keep |
| `MVP_PLAN.md` | Archive or delete (outdated) | Archive |

**Result**: 25 files → 15 files (~40% reduction)

### B. Clean Up Test Files

#### Move to tests/
```bash
mv backend/test_langgraph.py backend/tests/integration/
mv backend/test_llm_metadata.py backend/tests/unit/
```

#### Delete Temporary Files
```bash
rm backend/patch_ctrl_c.py
rm backend/test_ctrl_c_fix.py
rm backend/test_esc_cancellation.py
```

### C. Update .gitignore

Add to `.gitignore`:
```gitignore
# Frontend build artifacts
frontend/.next/
frontend/out/
frontend/.vercel/

# Test artifacts
backend/test_*.py  # Exclude ad-hoc test files in root
!backend/tests/   # But keep tests/ directory

# Temporary files
backend/patch_*.py
*.pyc
__pycache__/
```

### D. Create Documentation Index

New `docs/README.md`:
```markdown
# FinAgent Documentation

## Getting Started
- [Quick Start Guide](getting-started/quickstart.md)
- [Installation](getting-started/installation.md)
- [Importing Documents](getting-started/importing-documents.md)

## User Guide
- [CLI Usage](user-guide/cli-usage.md)
- [LLM Configuration](user-guide/config-llm.md)
- [Document Management](user-guide/document-management.md)
- [Querying the System](user-guide/querying.md)

## Architecture
- [System Overview](architecture/overview.md)
- [LangGraph Workflow](architecture/langgraph-workflow.md)
- [RAG Pipeline](architecture/rag-pipeline.md)
- [Multi-Agent System](architecture/multi-agent-system.md)

## Development
- [Development Setup](development/setup.md)
- [Testing](development/testing.md)
- [Contributing](development/contributing.md)
- [Implementation Notes](development/implementation-notes.md)

## Reference
- [CLI Commands](reference/cli-commands.md)
- [Configuration Options](reference/configuration-options.md)
- [API Reference](reference/api-reference.md)
- [Model Config Schema](reference/model-config-schema.md)

## 繁體中文文件
- [系統規格書](zh-tw/specification.md)
```

## Implementation Steps

### Phase 1: Create Structure (10 min)
```bash
mkdir -p docs/{getting-started,user-guide,architecture,development,reference,zh-tw}
touch docs/README.md
```

### Phase 2: Move & Consolidate (30 min)
For each target file:
1. Copy relevant sections from source files
2. Remove duplicate content
3. Update cross-references
4. Add table of contents
5. Move to new location

### Phase 3: Clean Up (5 min)
```bash
# Delete old docs (after verifying new ones are complete)
rm QUICKSTART.md RAG_QUICKSTART.md CLI_GUIDE.md CLI_QUICK_REFERENCE.md
rm CLI_DEMO.md IMPLEMENTATION_STATUS.md IMPORT_DOCUMENTS.md
rm CLI_IMPLEMENTATION_SUMMARY.md TEST_RESULTS.md MVP_PLAN.md

rm backend/AUTOMATED_REINDEX.md backend/BOUNDARY_TESTS.md
rm backend/DOCUMENT_INIT_GUIDE.md backend/EMBEDDING_FIX.md
rm backend/ESC_KEY_CANCELLATION.md backend/ESC_KEY_NOTE.md
rm backend/INIT_COMMAND_SUMMARY.md backend/LANGGRAPH_IMPLEMENTATION.md
rm backend/LLM_CONFIG.md backend/LLM_METADATA_GENERATION.md
rm backend/REINDEX_WITH_INIT.md backend/TABLE_OF_CONTENTS_GUIDE.md
rm backend/TEST_RESULTS.md

# Delete temporary test files
rm backend/patch_ctrl_c.py
rm backend/test_ctrl_c_fix.py
rm backend/test_esc_cancellation.py

# Move integration tests
mv backend/test_langgraph.py backend/tests/integration/
mv backend/test_llm_metadata.py backend/tests/unit/

# Move Chinese doc
mv 法律研究代理系統規格書.md docs/zh-tw/specification.md
```

### Phase 4: Update References (15 min)
Update links in:
- Root README.md
- CLAUDE.md (update file paths)
- Any remaining docs

### Phase 5: Update .gitignore (2 min)
Add frontend build artifacts and test file patterns

### Phase 6: Commit (5 min)
```bash
git add .
git commit -m "refactor: consolidate and organize project documentation

- Created /docs directory with clear hierarchy
- Consolidated 25 files into 15 organized docs (~40% reduction)
- Moved test files to proper locations
- Cleaned up temporary files
- Updated .gitignore for build artifacts
- Added comprehensive documentation index

Structure:
- docs/getting-started/ - Installation & quick start
- docs/user-guide/ - CLI usage, config, document management
- docs/architecture/ - System design & implementation
- docs/development/ - Dev setup, testing, contributing
- docs/reference/ - Complete command & config reference
- docs/zh-tw/ - Traditional Chinese documentation

Breaking changes: None (old files deleted, new locations)"
```

## Benefits

### 1. Discoverability
- Clear documentation hierarchy
- Single entry point (`docs/README.md`)
- Logical grouping by user type (user vs developer)

### 2. Maintainability
- No duplicate content
- Clear ownership of topics
- Easier to update

### 3. Professionalism
- Industry-standard `/docs` structure
- Cleaner repository root
- Better for open source contributors

### 4. Size Reduction
- 25 → 15 documentation files (40% reduction)
- Removed 5 temporary test files
- Excluded build artifacts from git

## Alternative: Minimal Cleanup

If full reorganization is too much work, here's a minimal cleanup:

### Quick Wins (15 minutes)

1. **Delete temporary files** (5 min):
   ```bash
   rm backend/patch_ctrl_c.py
   rm backend/test_ctrl_c_fix.py
   rm backend/test_esc_cancellation.py
   ```

2. **Move test files** (3 min):
   ```bash
   mv backend/test_langgraph.py backend/tests/integration/
   mv backend/test_llm_metadata.py backend/tests/unit/
   ```

3. **Update .gitignore** (2 min):
   Add `frontend/.next/` and `backend/test_*.py`

4. **Create simple doc index** (5 min):
   Add `DOCS.md` to root with links to all documentation

### Result
- Cleaner repository
- No breaking changes
- Minimal effort

## Recommendation

**Start with minimal cleanup** (15 min), then gradually move to full reorganization over time.

Priority order:
1. ✅ Delete temporary files (immediate)
2. ✅ Move test files (immediate)
3. ✅ Update .gitignore (immediate)
4. ⏳ Create docs index (quick win)
5. ⏳ Consolidate related docs (gradual)
6. ⏳ Full /docs restructure (when time permits)

This allows you to get immediate benefits without disrupting current workflow.
