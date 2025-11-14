# Sequential Reindex Implementation Status

**Date:** 2025-11-13
**Status:** Phase 2 Complete ✅, Phase 3-5 Ready for Implementation

---

## ✅ COMPLETED

### Phase 1: Database Schema (100% Complete)
- ✅ Added `concepts` table to [schema.sql](src/finagent/database/schema.sql#L130-L141)
- ✅ Added `document_concepts` mapping table ([schema.sql](src/finagent/database/schema.sql#L149-L157))
- ✅ Added auto-update triggers for `document_count`
- ✅ Created Pydantic models: `Concept` and `DocumentConcept` in [models.py](src/finagent/database/models.py#L78-L99)

### Phase 2: Database Methods (100% Complete)
Added 14 new methods to [db.py](src/finagent/database/db.py#L733-L1089):

**Concept CRUD:**
- ✅ `add_concept()` - Create or update concept with UPSERT
- ✅ `get_concept()` - Get by ID
- ✅ `get_concept_by_name()` - Get by name
- ✅ `get_all_concepts()` - List all ordered by document_count
- ✅ `search_concepts()` - Search by keyword
- ✅ `get_top_concepts()` - Get top N by document count
- ✅ `get_concepts_by_type()` - Filter by type
- ✅ `delete_concept()` - Delete with cascading

**Document-Concept Mapping:**
- ✅ `link_document_concept()` - Create document-concept link
- ✅ `get_document_concepts()` - Get concepts for a document
- ✅ `get_concept_documents()` - Get documents for a concept
- ✅ `unlink_document_concept()` - Remove link
- ✅ `get_concept_statistics()` - Get concept stats

### Phase 4 (Partial): Concept Extraction Module
- ✅ Created [concept_extractor.py](src/finagent/document_processing/concept_extractor.py)
- ✅ `extract_document_concepts()` - Extract from metadata
- ✅ `infer_concept_type()` - Classify concepts
- ✅ `analyze_toc_for_concepts()` - LLM-based TOC analysis
- ✅ `extract_concepts_basic()` - Fallback without LLM

---

## 📋 TODO

### Phase 3: Sequential Reindex (Main Implementation)

**File:** `src/finagent/cli/commands/reindex.py`

**Tasks:**
1. Create new `reindex_documents_sequential()` function
2. Implement per-document processing loop:
   ```python
   for doc in documents:
       1. Check if already processed (skip if indexed=True and not clear_existing)
       2. Index to vector DB (chunks + embeddings)
       3. Generate metadata with LLM (or create minimal)
       4. Save metadata to database (indexed=True, chunk_count=N)
       5. Update TABLE_OF_CONTENTS.md
       6. Extract concepts from metadata
       7. Link document to concepts in database
       → Document immediately searchable, move to next
   ```

3. Add global concept analysis after all documents:
   ```python
   # After all documents processed
   global_concepts = analyze_toc_for_concepts(toc_path, llm_generator)
   for concept_data in global_concepts:
       db.add_concept(Concept(**concept_data))
   ```

4. Add command-line flags:
   - `--sequential`: Use new sequential flow (default)
   - `--skip-concepts`: Skip concept analysis
   - `--batch`: Use old batch flow (for comparison)

**Estimated Time:** 4 hours

### Phase 3b: TOC Compaction Logic

**File:** `src/finagent/document_processing/toc_generator.py`

**Tasks:**
1. Add `compact_toc_if_needed()` method to `TableOfContents` class
2. Check if TOC > 1000 lines
3. If yes, create compact version:
   ```markdown
   # 文件目錄 (精簡版)

   ## 統計
   - 總數: 492
   - 裁罰書: 350
   - 判決書: 100

   ## 快速索引
   完整索引請參閱: [TABLE_OF_CONTENTS_FULL.md](TABLE_OF_CONTENTS_FULL.md)
   ```
4. Move full index to `TABLE_OF_CONTENTS_FULL.md`

**Estimated Time:** 1 hour

### Phase 5: Query Integration

**File:** `src/finagent/agents/...` (query system)

**Tasks:**
1. Add concept-based pre-filtering to query flow:
   ```python
   def query_with_concepts(query_text: str):
       # 1. Extract key concepts from query
       query_concepts = extract_concepts_from_query(query_text)

       # 2. Find matching concepts in database
       concept_ids = []
       for concept_name in query_concepts:
           concept = db.get_concept_by_name(concept_name)
           if concept:
               concept_ids.append(concept.id)

       # 3. Get candidate documents from concepts
       candidate_docs = []
       for concept_id in concept_ids:
           docs = db.get_concept_documents(concept_id)
           candidate_docs.extend(docs)

       # 4. Do vector search ONLY on candidate documents
       if candidate_docs:
           # Filter vector search to these doc_ids
           results = vector_search(query_text, doc_ids=candidate_docs)
       else:
           # Fallback to full vector search
           results = vector_search(query_text)
   ```

2. Create `/concepts` CLI command to browse concepts:
   ```python
   def handle_concepts_command(args: str):
       if not args:
           # List top 20 concepts
           concepts = db.get_top_concepts(20)
           for concept in concepts:
               print(f"{concept.concept_name} ({concept.document_count} docs)")
       elif args.startswith("search "):
           # Search concepts
           keyword = args[7:]
           concepts = db.search_concepts(keyword)
       elif args.startswith("type "):
           # Filter by type
           concept_type = args[5:]
           concepts = db.get_concepts_by_type(concept_type)
   ```

3. Show concepts in query results

**Estimated Time:** 3 hours

---

## 📁 File Structure

```
src/finagent/
├── database/
│   ├── schema.sql ✅ (concepts tables added)
│   ├── models.py ✅ (Concept, DocumentConcept models added)
│   └── db.py ✅ (14 new methods added)
├── document_processing/
│   ├── concept_extractor.py ✅ (NEW - concept extraction logic)
│   ├── metadata_store.py (existing)
│   └── toc_generator.py ⏳ (TODO: add compaction)
├── cli/commands/
│   ├── reindex.py ⏳ (TODO: add sequential flow)
│   └── concepts.py ⏳ (TODO: NEW - /concepts command)
└── agents/
    └── ... ⏳ (TODO: integrate concept pre-filtering)
```

---

## 🧪 Testing Plan

### Test 1: Database Methods
```python
# Test concept CRUD
concept = Concept(
    concept_name="洗錢防制",
    concept_type="violation_type",
    description="洗錢防制相關違規",
    keywords=["AML", "反洗錢"]
)
db.add_concept(concept)
assert db.get_concept_by_name("洗錢防制") is not None

# Test document-concept mapping
db.link_document_concept("doc_id_123", concept.id, relevance_score=1.0)
concepts = db.get_document_concepts("doc_id_123")
assert len(concepts) == 1
```

### Test 2: Concept Extraction
```python
# Test from metadata
metadata = DocumentMetadata(
    doc_id="doc_test",
    filename="test.txt",
    description="Test",
    document_type="裁罰書",
    keywords=["洗錢防制", "玉山銀行"],
    issuing_authority="金管會",
    related_institutions=["玉山商業銀行"],
    violation_types=["洗錢防制法違規"],
    created_at=datetime.now().isoformat(),
    updated_at=datetime.now().isoformat(),
)

concepts = extract_document_concepts(metadata)
assert "洗錢防制法違規" in concepts
assert "金管會" in concepts
assert "玉山商業銀行" in concepts
```

### Test 3: Sequential Reindex
```bash
# Run sequential reindex on 2 test documents
finagent> /reindex --sequential --skip-concepts

# Verify:
# 1. Both documents indexed in vector DB
# 2. Both documents in database with indexed=1
# 3. TABLE_OF_CONTENTS.md updated with both
# 4. Concepts extracted and linked
```

### Test 4: Concept-Based Query
```python
# Test query performance improvement
query = "玉山銀行洗錢防制裁罰"

# Without concepts (baseline)
start = time.time()
results_without = vector_search(query)
time_without = time.time() - start

# With concepts (optimized)
start = time.time()
results_with = query_with_concepts(query)
time_with = time.time() - start

# Expect 5-10x speedup
assert time_with < time_without / 5
```

---

## 📊 Expected Performance

### Reindex Time (492 documents)

| Mode | Time | Notes |
|------|------|-------|
| Batch with LLM | ~25 min | Current implementation |
| Batch skip LLM | ~5 min | `--skip-init` |
| Sequential with LLM | ~25 min | New, but interruptible |
| Sequential skip LLM | ~5 min | New, best for initial setup |

### Query Performance

| Mode | Time | Chunks Searched |
|------|------|-----------------|
| Full vector search | 500-1000ms | All ~2,858 chunks |
| Concept pre-filtering | 50-150ms | ~150 chunks (5-10x faster!) |

---

## 🚀 Next Steps

**Immediate (Today):**
1. Implement `reindex_documents_sequential()` in [reindex.py](src/finagent/cli/commands/reindex.py)
2. Test with 2-5 documents
3. Add TOC compaction logic

**Short-term (This Week):**
4. Add `/concepts` command
5. Integrate concept pre-filtering in query system
6. Run full reindex on 492 documents
7. Benchmark query performance

**Medium-term:**
8. Add concept-based filtering in UI/CLI
9. Create concept analytics dashboard
10. Implement concept auto-suggestions in queries

---

## 📝 Implementation Guide

### To implement Phase 3 (Sequential Reindex):

1. **Open** `src/finagent/cli/commands/reindex.py`

2. **Add imports:**
```python
from finagent.document_processing.concept_extractor import (
    extract_document_concepts,
    infer_concept_type,
    analyze_toc_for_concepts,
)
from finagent.database.models import Concept
```

3. **Create new function** `reindex_documents_sequential()` following the design in [SEQUENTIAL_REINDEX_DESIGN.md](SEQUENTIAL_REINDEX_DESIGN.md)

4. **Update `execute_reindex()`** to call the new function:
```python
def execute_reindex(clear: bool = False, skip_init: bool = False, sequential: bool = True):
    if sequential:
        indexed, chunks = reindex_documents_sequential(
            clear_existing=clear,
            skip_metadata=skip_init,
        )
    else:
        indexed, chunks = reindex_documents(  # Old batch mode
            clear_existing=clear,
            prompt_init=not skip_init,
        )
```

5. **Test** with small dataset first

---

**Status:** Ready for Phase 3 implementation
**Blocker:** None - all dependencies complete
**Risk:** Low - incremental changes with fallback to old flow
