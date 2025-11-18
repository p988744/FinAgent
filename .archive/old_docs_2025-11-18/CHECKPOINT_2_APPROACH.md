# Checkpoint 2: LLM Metadata Extraction - Implementation Approach

**Date:** 2025-11-18
**Status:** 🚧 In Progress

## Overview

Checkpoint 2 focuses on extracting structured metadata from documents using LLM, building on the database integration completed in Checkpoint 1.

## Current State

### Completed ✅

1. **New Metadata Model Created**
   - File: [src/finagent/document_processing/metadata_models.py](src/finagent/document_processing/metadata_models.py)
   - `DocumentMetadata` - Comprehensive Pydantic model with:
     - Required fields: title, description, document_type
     - Optional fields: issuing_authority, case_number, document_date
     - Lists: related_institutions, violation_types, keywords
     - Validation: extraction_confidence (0.0-1.0)
   - `MetadataExtractionResult` - Wrapper with success/error/timing info

2. **Existing Infrastructure**
   - Old metadata extractor: [src/finagent/document_processing/metadata_extractor.py](src/finagent/document_processing/metadata_extractor.py)
   - Old model: [src/finagent/models/document_metadata.py](src/finagent/models/document_metadata.py)
     (`ExtendedDocumentMetadata` - similar but different schema)

### Architectural Decision: Dual Model Approach

We have **two metadata models** serving different purposes:

| Model | Purpose | Location | Used By |
|-------|---------|----------|---------|
| `ExtendedDocumentMetadata` | Legacy model for existing tools | [models/document_metadata.py](src/finagent/models/document_metadata.py) | Existing metadata_extractor.py, research tools |
| `DocumentMetadata` | New model for wiki/checkpoint 2+ | [document_processing/metadata_models.py](src/finagent/document_processing/metadata_models.py) | Future wiki system, new extraction |

**Recommendation:** Keep both models for now to avoid breaking existing functionality. Gradually migrate to `DocumentMetadata` for new features.

## Implementation Plan

### Phase 1: Enhance Existing Extractor (Week 2, Days 1-2)

**Goal:** Improve existing [metadata_extractor.py](src/finagent/document_processing/metadata_extractor.py) without breaking compatibility.

**Tasks:**
1. Add support for new DocumentMetadata model alongside ExtendedDocumentMetadata
2. Enhance extraction prompt to include:
   - Better document type classification
   - Multiple violation types (list instead of single)
   - Keywords extraction (5-10 keywords)
   - Confidence scoring
3. Switch from LangChain to direct OpenAI client (matches ConfigManager)
4. Add error handling and fallback logic

**Implementation:**
```python
class MetadataExtractor:
    def __init__(self, use_new_model: bool = False):
        self.use_new_model = use_new_model
        self.config = ConfigManager()
        self.client = OpenAI(...)

    async def extract(self, filename: str, content: str) -> ExtendedDocumentMetadata | DocumentMetadata:
        # Extract using LLM
        # Return appropriate model based on use_new_model flag
```

### Phase 2: Integration with Indexer (Week 2, Days 3-4)

**Goal:** Integrate metadata extraction into the document indexing pipeline.

**Current Indexer:**
[src/finagent/document_processing/indexer.py](src/finagent/document_processing/indexer.py)

**Modifications Needed:**
```python
class DocumentIndexer:
    def __init__(
        self,
        # ... existing params
        extract_metadata: bool = False,
        metadata_extractor: MetadataExtractor | None = None,
    ):
        self.extract_metadata = extract_metadata
        self.metadata_extractor = metadata_extractor

    def index_document(self, document: Document) -> int:
        # ... existing chunking and embedding logic

        # NEW: Extract metadata if enabled
        if self.extract_metadata and self.metadata_extractor:
            metadata = await self.metadata_extractor.extract(
                filename=document.filename,
                content=document.content
            )

            # Store in database
            self.document_db.upsert_document(
                doc_id=document.id,
                # ... existing fields
                # NEW: metadata fields
                document_type=metadata.document_type,
                issuing_authority=metadata.issuing_authority,
                violation_types=json.dumps(metadata.violation_types),
                keywords=json.dumps(metadata.keywords),
                extraction_confidence=metadata.extraction_confidence,
            )
```

**Database Fields (Already in schema):**
- ✅ document_type
- ✅ issuing_authority
- ✅ case_number
- ✅ document_date
- ✅ related_institutions (JSON)
- ✅ violation_types (JSON)
- ✅ penalty_amount
- ✅ keywords (JSON)
- ✅ extraction_confidence

### Phase 3: CLI Integration (Week 2, Day 5)

**Goal:** Add metadata extraction flags to reindex command.

**Current Reindex Command:**
[src/finagent/cli/commands/init.py](src/finagent/cli/commands/init.py)

**New Flags:**
```bash
# Full reindex with metadata extraction
uv run finagent reindex --extract-metadata

# Skip metadata extraction (fast mode)
uv run finagent reindex --skip-metadata

# Clear and rebuild with metadata
uv run finagent reindex --clear --extract-metadata --yes
```

**Implementation:**
```python
@init_command.command()
@click.option("--extract-metadata", is_flag=True, help="Extract metadata using LLM")
@click.option("--skip-metadata", is_flag=True, help="Skip metadata extraction (fast)")
def reindex(
    extract_metadata: bool,
    skip_metadata: bool,
    # ... existing params
):
    # Initialize indexer with metadata extraction
    if extract_metadata:
        from finagent.document_processing.metadata_extractor import MetadataExtractor
        extractor = MetadataExtractor()
        indexer = DocumentIndexer(
            extract_metadata=True,
            metadata_extractor=extractor,
            ...
        )
```

### Phase 4: Quality Validation & Testing (Week 2, Days 6-7)

**Create Validation Scripts:**

1. **tests/test_metadata_extraction.py** - Unit tests
   ```python
   def test_extract_document_metadata():
       extractor = MetadataExtractor()
       content = load_sample_document()
       result = await extractor.extract("test.txt", content)

       assert result.success
       assert result.metadata.extraction_confidence > 0.8
       assert result.metadata.document_type in VALID_DOCUMENT_TYPES
   ```

2. **scripts/check_metadata_quality.py** - Quality analysis
   ```python
   # Check all documents in database
   # Report:
   # - % with metadata extracted
   # - Average confidence score
   # - Distribution of document types
   # - Missing required fields
   # - Low confidence documents (<0.7)
   ```

3. **scripts/verify_metadata_sample.py** - Manual verification
   ```python
   # Sample 50 random documents
   # Display extracted metadata
   # Allow manual correction
   # Calculate accuracy rate
   ```

## Success Criteria (from V1_0_RELEASE_PLAN.md)

- [ ] >90% accuracy on manual validation (sample 50 documents)
- [ ] >85% average confidence score
- [ ] <5% extraction failures
- [ ] All document_type values are valid categories
- [ ] Extraction time <10s per document
- [ ] Metadata extracted for 100% of documents

## Testing Strategy

### Unit Tests
```bash
# Test metadata models
uv run pytest tests/test_metadata_models.py

# Test extraction on sample documents
uv run pytest tests/test_metadata_extraction.py
```

### Integration Tests
```bash
# Test full reindex with metadata
uv run finagent reindex --clear --extract-metadata --yes

# Verify database content
sqlite3 data/finagent.db "SELECT COUNT(*) FROM documents WHERE document_type IS NOT NULL;"

# Check quality
uv run python scripts/check_metadata_quality.py
```

### Manual Validation
```bash
# Review sample of extractions
uv run python scripts/verify_metadata_sample.py
```

## Estimated Timeline

| Task | Duration | Status |
|------|----------|--------|
| Create new metadata models | 1 hour | ✅ Done |
| Enhance metadata extractor | 4 hours | 🚧 In Progress |
| Integrate with indexer | 3 hours | ⏳ Pending |
| Add CLI flags | 2 hours | ⏳ Pending |
| Write tests | 3 hours | ⏳ Pending |
| Quality validation | 2 hours | ⏳ Pending |
| Documentation | 1 hour | ⏳ Pending |
| **Total** | **16 hours** | **~10% complete** |

## Next Steps

1. ✅ Complete new metadata models (DONE)
2. 🚧 Enhance existing metadata_extractor.py to support new model
3. Test extraction on 2-3 sample documents
4. Integrate into DocumentIndexer
5. Add CLI flags
6. Run full reindex with metadata extraction
7. Validate quality and document completion

## Files Modified/Created

### Created ✅
- `src/finagent/document_processing/metadata_models.py`

### To Modify
- `src/finagent/document_processing/metadata_extractor.py`
- `src/finagent/document_processing/indexer.py`
- `src/finagent/cli/commands/init.py`

### To Create
- `tests/test_metadata_extraction.py`
- `scripts/check_metadata_quality.py`
- `scripts/verify_metadata_sample.py`
- `CHECKPOINT_2_COMPLETE.md`

## Related Documentation

- [V1_0_RELEASE_PLAN.md](V1_0_RELEASE_PLAN.md#checkpoint-2-llm-metadata-extraction-week-2) - Full checkpoint spec
- [CHECKPOINT_1_COMPLETE.md](CHECKPOINT_1_COMPLETE.md) - Foundation database integration
- [CHECKPOINT_REVIEW.md](CHECKPOINT_REVIEW.md) - Impact analysis

---

**Status:** Metadata models created, extractor enhancement in progress.
**Next Action:** Complete extractor enhancement and test on sample documents.
