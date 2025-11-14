# Sequential Reindex Design with Concept Analysis

## Overview

Redesign `/reindex` workflow to process each document sequentially through ALL steps, then perform concept analysis at the end for faster retrieval.

## Current Flow (Batch Processing)

```
Phase 1: LLM Metadata Init (ALL documents)
  For each 492 documents:
    - Generate metadata with LLM
    - Save to database

Phase 2: Vector Indexing (ALL documents)
  For each 492 documents:
    - Chunk document
    - Generate embeddings
    - Index to vector DB
    - Update database indexed status

Phase 3: TOC Generation
  - Generate TABLE_OF_CONTENTS.md once at end
```

**Problems:**
- ❌ If Phase 1 fails at doc #250, lose all progress
- ❌ Cannot query until ALL documents finish
- ❌ TOC not updated incrementally
- ❌ No concept extraction for faster retrieval

## New Flow (Sequential Per-Document)

```
For each document (1-492):
  Step 1: Load file
  Step 2: Index to vector DB (chunks + embeddings)
  Step 3: Generate metadata with LLM
  Step 4: Save metadata to database
  Step 5: Update TABLE_OF_CONTENTS.md (with compaction if needed)
  Step 6: Link document concepts (from metadata)
  → Document immediately searchable, move to next

After ALL documents:
  Step 7: Analyze TABLE_OF_CONTENTS.md for global topics
  Step 8: Extract key concepts using LLM
  Step 9: Save/update concepts table
  Step 10: Update document-concept mappings
```

**Benefits:**
- ✅ Each document fully processed before next (atomic)
- ✅ Can interrupt and resume (know exactly where we stopped)
- ✅ Documents searchable immediately after processing
- ✅ TOC always up-to-date
- ✅ Concept extraction for faster retrieval

## Implementation Steps

### 1. Database Schema (DONE ✅)

**New Tables:**
- `concepts`: Store extracted topics/concepts
  - `concept_name`: e.g., "洗錢防制", "內線交易", "資訊揭露"
  - `concept_type`: "violation_type", "institution", "authority", "topic"
  - `keywords`: Related keywords
  - `document_count`: Auto-updated via trigger

- `document_concepts`: Many-to-many mapping
  - Links documents to concepts
  - `relevance_score`: How relevant (0-1)

### 2. Database Models (DONE ✅)

**New Pydantic Models:**
- `Concept`: Concept/topic model
- `DocumentConcept`: Document-concept mapping

### 3. Database Methods (TODO)

**Add to `db.py`:**
```python
# Concept CRUD
def add_concept(concept: Concept) -> Concept
def get_concept(concept_id: int) -> Concept | None
def get_concept_by_name(concept_name: str) -> Concept | None
def get_all_concepts() -> list[Concept]
def search_concepts(keyword: str) -> list[Concept]
def delete_concept(concept_id: int) -> bool

# Document-Concept mapping
def link_document_concept(doc_id: str, concept_id: int, relevance: float = 1.0) -> bool
def get_document_concepts(doc_id: str) -> list[Concept]
def get_concept_documents(concept_id: int) -> list[Document]
def unlink_document_concept(doc_id: str, concept_id: int) -> bool

# Concept analysis helpers
def get_top_concepts(limit: int = 50) -> list[Concept]
def get_concepts_by_type(concept_type: str) -> list[Concept]
```

### 4. TOC Compaction Logic (TODO)

**Problem:** TABLE_OF_CONTENTS.md gets too long (current: 494 lines)

**Solution:** Compact format when > 1000 lines

```python
def compact_toc_if_needed(toc_path: Path, max_lines: int = 1000):
    """
    If TOC exceeds max_lines, create compact version.

    Compact format:
    - Keep statistics section
    - Group documents by type/authority
    - Link to detailed index files
    """
    if count_lines(toc_path) > max_lines:
        create_compact_toc()
        # Move full index to TABLE_OF_CONTENTS_FULL.md
        # Keep summary in TABLE_OF_CONTENTS.md
```

**Compact format example:**
```markdown
# 文件目錄

更新: 2025-11-13
總數: 492 份

## 📊 統計

### 按文件類型
- 裁罰書: 350
- 判決書: 100
- 法規: 42

### 按監管機構
- 金管會: 300
- 中央銀行: 150
- 公平會: 42

### 按機構
- 玉山銀行: 25
- 國泰世華: 20
- ...

## 🔍 快速查詢

詳細索引請參閱:
- [完整文件索引](TABLE_OF_CONTENTS_FULL.md)
- [按類型分類](indexes/by_type/)
- [按機構分類](indexes/by_institution/)
```

### 5. Concept Extraction (TODO)

**From Document Metadata (Per-Document):**
```python
def extract_document_concepts(metadata: DocumentMetadata) -> list[str]:
    """Extract concepts from document metadata."""
    concepts = []

    # From violation_types
    concepts.extend(metadata.violation_types)

    # From issuing_authority
    if metadata.issuing_authority:
        concepts.append(metadata.issuing_authority)

    # From related_institutions
    concepts.extend(metadata.related_institutions)

    # From keywords (top concepts only)
    concepts.extend(metadata.keywords[:5])

    return list(set(concepts))  # Deduplicate
```

**From TABLE_OF_CONTENTS.md (Global Analysis):**
```python
def analyze_toc_for_concepts(toc_path: Path) -> list[Concept]:
    """
    Use LLM to analyze TABLE_OF_CONTENTS.md and extract key topics.

    Prompt:
    - Identify top 50 most important concepts
    - Group by type (violation, authority, institution, topic)
    - Provide description and keywords for each
    """
    toc_content = load_toc(toc_path)

    prompt = f'''
    分析以下法律文件目錄，提取關鍵概念：

    {toc_content}

    請提取：
    1. 前50個最重要的概念/主題
    2. 分類為：violation_type, authority, institution, topic
    3. 每個概念提供簡短描述和關鍵詞

    輸出格式（JSON）：
    [
      {{
        "concept_name": "洗錢防制",
        "concept_type": "violation_type",
        "description": "銀行未能建立完善的洗錢防制機制",
        "keywords": ["AML", "反洗錢", "可疑交易"]
      }},
      ...
    ]
    '''

    concepts = llm.generate(prompt)
    return parse_concepts(concepts)
```

### 6. Sequential Reindex Implementation (TODO)

**New `reindex_documents_sequential()` function:**

```python
def reindex_documents_sequential(
    clear_existing: bool = False,
    skip_metadata: bool = False,
    skip_concepts: bool = False
) -> tuple[int, int]:
    """
    Reindex documents sequentially with per-document processing.

    Args:
        clear_existing: Clear all indexes before starting
        skip_metadata: Skip LLM metadata generation
        skip_concepts: Skip concept analysis at end
    """
    # Initialize
    loader = DocumentLoader()
    indexer = DocumentIndexer()
    metadata_store = DocumentMetadataStore()
    metadata_generator = MetadataGenerator()
    toc = TableOfContents()
    db = Database()

    # Load documents
    documents = loader.load_directory(".", pattern="*.txt", recursive=True)

    total_indexed = 0
    total_chunks = 0

    with Progress(...) as progress:
        task = progress.add_task("Processing documents...", total=len(documents))

        for doc in documents:
            filename = doc.metadata.get("filename", "unknown")

            try:
                # Step 1: Check if already processed
                existing_meta = metadata_store.get_metadata(doc.id)
                if existing_meta and existing_meta.indexed and not clear_existing:
                    progress.update(task, advance=1, description=f"⏭️  Skip: {filename}")
                    continue

                # Step 2: Index to vector DB
                progress.update(task, description=f"📊 Indexing: {filename}")
                chunks = indexer.index_document(doc)
                total_chunks += chunks

                # Step 3: Generate metadata with LLM (if not skipped)
                if not skip_metadata:
                    progress.update(task, description=f"🤖 Analyzing: {filename}")
                    metadata = metadata_generator.generate_metadata(doc)
                else:
                    # Create minimal metadata
                    metadata = create_minimal_metadata(doc)

                # Step 4: Save metadata to database
                progress.update(task, description=f"💾 Saving: {filename}")
                file_path = doc.metadata.get("file_path") or doc.source
                metadata.indexed = True
                metadata.chunk_count = chunks
                metadata_store.add_metadata(metadata, file_path=file_path)

                # Step 5: Update TABLE_OF_CONTENTS.md
                progress.update(task, description=f"📝 TOC: {filename}")
                toc.add_document(metadata)
                toc.save()
                compact_toc_if_needed(toc.path)

                # Step 6: Link document concepts (from metadata)
                progress.update(task, description=f"🔗 Concepts: {filename}")
                doc_concepts = extract_document_concepts(metadata)
                for concept_name in doc_concepts:
                    # Get or create concept
                    concept = db.get_concept_by_name(concept_name)
                    if not concept:
                        concept = Concept(
                            concept_name=concept_name,
                            concept_type=infer_concept_type(concept_name, metadata)
                        )
                        concept = db.add_concept(concept)

                    # Link to document
                    db.link_document_concept(doc.id, concept.id)

                total_indexed += 1
                progress.update(task, advance=1, description=f"✅ Done: {filename}")

            except Exception as e:
                progress.update(task, advance=1, description=f"❌ Error: {filename}")
                console.print(f"[red]Error processing {filename}: {e}[/red]")

    # Step 7-10: Global concept analysis
    if not skip_concepts:
        console.print("\n[cyan]🧠 Analyzing concepts from TABLE_OF_CONTENTS.md...[/cyan]")
        global_concepts = analyze_toc_for_concepts(toc.path)

        for concept_data in global_concepts:
            # Save or update concept
            concept = db.get_concept_by_name(concept_data["concept_name"])
            if not concept:
                concept = Concept(**concept_data)
                db.add_concept(concept)
            else:
                # Update description and keywords
                concept.description = concept_data["description"]
                concept.keywords = concept_data["keywords"]
                db.update_concept(concept)

        console.print(f"[green]✅ Extracted {len(global_concepts)} global concepts[/green]")

    return total_indexed, total_chunks
```

### 7. CLI Command Updates (TODO)

**Add new flags:**
```python
# /reindex --sequential (use new sequential flow)
# /reindex --skip-concepts (skip concept analysis)
# /reindex --compact-toc (force TOC compaction)
```

## Benefits

### Performance
- **Interruption-safe**: Can stop and resume at any document
- **Incremental progress**: Documents searchable immediately
- **Better progress tracking**: Show per-document steps

### Data Quality
- **Always up-to-date TOC**: Updated after each document
- **Concept extraction**: Faster retrieval via concepts table
- **Atomic operations**: Each document fully processed or not at all

### User Experience
- **Faster time-to-query**: Can query as soon as first documents indexed
- **Better error handling**: Failures don't lose all progress
- **Clearer progress**: See exactly what's happening per document

## Query Performance Improvement

### Before (Vector Search Only):
```sql
-- Find documents about "洗錢防制"
-- Must do vector similarity search on all 2,858 chunks
-- Slow: ~500-1000ms
```

### After (Concept-Based Pre-filtering):
```sql
-- 1. Find concept
SELECT id FROM concepts WHERE concept_name = '洗錢防制';  -- Fast: <10ms

-- 2. Get related documents
SELECT doc_id FROM document_concepts WHERE concept_id = 123;  -- Fast: <10ms
-- Returns: 25 documents

-- 3. Do vector search ONLY on those 25 documents' chunks (~150 chunks)
-- Fast: ~50-100ms (10x faster!)
```

**Query time improvement:**
- Before: 500-1000ms
- After: 50-150ms (5-10x faster!)

## Migration Path

### Phase 1: Database Schema (DONE ✅)
- Add concepts tables
- Add Pydantic models

### Phase 2: Database Methods
- Implement concept CRUD operations
- Implement document-concept mapping

### Phase 3: Sequential Reindex
- Implement per-document sequential processing
- Add TOC compaction logic
- Add per-document concept extraction

### Phase 4: Global Concept Analysis
- Implement TOC analysis with LLM
- Extract global concepts
- Update concept descriptions

### Phase 5: Query Integration
- Update query flow to use concepts for pre-filtering
- Add concept-based search commands
- Add `/concepts` CLI command to browse concepts

## Estimated Time

- Phase 2: 2 hours (database methods)
- Phase 3: 4 hours (sequential reindex)
- Phase 4: 2 hours (concept analysis)
- Phase 5: 3 hours (query integration)

**Total: ~11 hours of development**

## File Structure

```
src/finagent/
├── database/
│   ├── schema.sql (✅ DONE)
│   ├── models.py (✅ DONE)
│   └── db.py (TODO: Add concept methods)
├── document_processing/
│   ├── concept_extractor.py (TODO: NEW)
│   └── toc_generator.py (TODO: Update)
├── cli/commands/
│   ├── reindex.py (TODO: Add sequential flow)
│   └── concepts.py (TODO: NEW - /concepts command)
```

---

**Status:** Design complete, ready for implementation
**Next Step:** Implement database methods for concepts (Phase 2)
