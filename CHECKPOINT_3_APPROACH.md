# Checkpoint 3: Wiki Generation System - Implementation Approach

**Date:** 2025-11-18
**Status:** 🚧 In Progress
**Goal:** Build document wiki with categories, statistics, and relationships

---

## Overview

Checkpoint 3 builds on the extracted metadata from Checkpoint 2 to create a hierarchical wiki system that organizes documents by various dimensions (authority, institution, violation type, document type) and provides statistics and relationship detection.

## Architecture

### Design Philosophy

**Reuse Existing Schema:** The database already has `concepts` and `document_concepts` tables that can serve our wiki needs. We'll adapt these existing tables rather than creating new wiki-specific tables.

**Mapping:**
- `concepts` table = Wiki categories
- `document_concepts` table = Document-category mappings
- `concept_type` field = Category hierarchy type

### Category Types

We'll use `concept_type` to distinguish different category hierarchies:

1. **`authority`** - 按主管機關 (By Authority)
   - 金管會, 中央銀行, 公平會, etc.

2. **`institution`** - 按金融機構 (By Institution)
   - 玉山銀行, 國泰世華銀行, etc.

3. **`violation`** - 按違規類型 (By Violation Type)
   - 洗錢防制, 內部控制, 內線交易, etc.

4. **`doc_type`** - 按文件類型 (By Document Type)
   - 裁罰書, 判決書, 法規, etc.

### Component Breakdown

#### 1. CategoryBuilder

**Purpose:** Build hierarchical categories from document metadata

**Key Functions:**
- `build_authority_categories()` - Extract from `issuing_authority` field
- `build_institution_categories()` - Extract from `related_institutions` JSON
- `build_violation_categories()` - Extract from `violation_types` JSON
- `build_doctype_categories()` - Extract from `document_type` field
- `update_concept()` - Insert/update concept in database

**Algorithm:**
1. Query all documents with metadata
2. Extract unique values for each category type
3. Count documents per category
4. Insert/update concepts table
5. Create document_concepts mappings

#### 2. StatisticsEngine

**Purpose:** Calculate statistics and metrics

**Key Statistics:**
- **Total counts:** Documents, categories, institutions
- **Distribution:** By authority, institution, violation type, year
- **Timeline:** Documents per year, month
- **Top entities:** Most penalized institutions, most common violations

**Storage:** Use concepts.metadata JSON field to store statistics

#### 3. RelationshipMapper

**Purpose:** Detect relationships between documents

**Relationship Types:**
1. **Same Institution + Violation** - Related cases
2. **Temporal** - Same institution, close dates (amendments/updates)
3. **Citation** - One document references another

**Algorithm:**
1. For each document, find candidates with:
   - Same institution (check `related_institutions` overlap)
   - Same violation type (check `violation_types` overlap)
   - Similar date (within 1 year)
2. Calculate relationship strength score (0.0-1.0):
   - Institution match: +0.3
   - Violation match: +0.3
   - Date proximity: +0.2 (closer = higher)
   - Same authority: +0.2
3. Store relationships with strength >= 0.3

**Storage:** Use document_concepts with relevance_score for relationship strength

#### 4. WikiGenerator

**Purpose:** Orchestrate the entire wiki generation process

**Workflow:**
```
1. Clear existing wiki data (optional)
2. Run CategoryBuilder for all category types
3. Run StatisticsEngine to calculate metrics
4. Run RelationshipMapper to detect relationships
5. Validate results
6. Log completion
```

**Performance Target:** <10s for full rebuild with 494 documents

---

## Database Usage

### Concepts Table

| Field | Usage |
|-------|-------|
| `concept_name` | Category name (e.g., "金管會", "玉山銀行") |
| `concept_type` | Category hierarchy (`authority`, `institution`, `violation`, `doc_type`) |
| `description` | Brief description of category |
| `keywords` | Related keywords (JSON array) |
| `document_count` | Auto-updated via trigger |
| `metadata` | Statistics data (JSON) |

### Document_Concepts Table

| Field | Usage |
|-------|-------|
| `doc_id` | Document ID |
| `concept_id` | Category/concept ID |
| `relevance_score` | 1.0 for category membership, 0.3-0.9 for relationships |

**Dual Purpose:**
- `relevance_score = 1.0` → Document belongs to this category
- `relevance_score < 1.0` → Document is related to another document (concept_id refers to related doc)

---

## Implementation Plan

### Phase 1: CategoryBuilder (Priority 1)

**File:** `src/finagent/wiki/category_builder.py`

**Classes:**
```python
class CategoryBuilder:
    def __init__(self, db: DocumentDatabase):
        self.db = db

    def build_all_categories(self) -> dict:
        """Build all category types"""

    def build_authority_categories(self) -> int:
        """Extract from issuing_authority field"""

    def build_institution_categories(self) -> int:
        """Extract from related_institutions JSON"""

    def build_violation_categories(self) -> int:
        """Extract from violation_types JSON"""

    def build_doctype_categories(self) -> int:
        """Extract from document_type field"""

    def _create_or_update_concept(
        self, name: str, concept_type: str, description: str = None
    ) -> int:
        """Create or update concept in database"""

    def _link_document_to_concept(
        self, doc_id: str, concept_id: int, relevance: float = 1.0
    ):
        """Create document-concept mapping"""
```

**Estimated Time:** 3 hours

### Phase 2: StatisticsEngine (Priority 2)

**File:** `src/finagent/wiki/statistics.py`

**Classes:**
```python
class StatisticsEngine:
    def __init__(self, db: DocumentDatabase):
        self.db = db

    def calculate_all_statistics(self) -> dict:
        """Calculate all statistics"""

    def calculate_document_stats(self) -> dict:
        """Total docs, by type, by authority, etc."""

    def calculate_timeline_stats(self) -> dict:
        """Documents by year, month"""

    def calculate_top_entities(self) -> dict:
        """Top institutions, violations"""

    def store_statistics(self, stats: dict):
        """Store in concepts.metadata"""
```

**Estimated Time:** 2 hours

### Phase 3: RelationshipMapper (Priority 3)

**File:** `src/finagent/wiki/relationship_mapper.py`

**Classes:**
```python
class RelationshipMapper:
    def __init__(self, db: DocumentDatabase):
        self.db = db

    def detect_all_relationships(self) -> int:
        """Detect relationships for all documents"""

    def find_related_documents(self, doc_id: str) -> list:
        """Find documents related to given document"""

    def calculate_relationship_strength(
        self, doc1: dict, doc2: dict
    ) -> float:
        """Calculate relationship strength score (0.0-1.0)"""

    def _has_institution_overlap(self, doc1: dict, doc2: dict) -> bool:
        """Check if documents share institutions"""

    def _has_violation_overlap(self, doc1: dict, doc2: dict) -> bool:
        """Check if documents share violation types"""

    def _calculate_date_proximity(self, doc1: dict, doc2: dict) -> float:
        """Calculate date proximity score (0.0-1.0)"""
```

**Estimated Time:** 3 hours

### Phase 4: WikiGenerator (Priority 4)

**File:** `src/finagent/wiki/generator.py`

**Classes:**
```python
class WikiGenerator:
    def __init__(self, db: DocumentDatabase):
        self.db = db
        self.category_builder = CategoryBuilder(db)
        self.statistics_engine = StatisticsEngine(db)
        self.relationship_mapper = RelationshipMapper(db)

    def generate_wiki(
        self, clear_existing: bool = False, include_relationships: bool = True
    ) -> dict:
        """Generate complete wiki"""

    def validate_wiki(self) -> dict:
        """Validate wiki data quality"""
```

**Estimated Time:** 2 hours

### Phase 5: CLI & Testing (Priority 5)

**Files:**
- `scripts/generate_wiki.py` - CLI script for wiki generation
- `scripts/verify_wiki_counts.py` - Validation script
- `tests/test_category_builder.py` - Unit tests
- `tests/test_relationship_mapper.py` - Unit tests

**Estimated Time:** 2 hours

---

## Success Criteria

✅ **Completeness:**
- [ ] All documents belong to at least one category
- [ ] Category counts are accurate
- [ ] No orphaned documents
- [ ] All 4 category types populated

✅ **Performance:**
- [ ] Wiki generation time <10s for 494 documents
- [ ] Database queries optimized with proper indexes

✅ **Quality:**
- [ ] Relationship strength scores are reasonable (0.3-0.9)
- [ ] Statistics calculations are accurate
- [ ] Timeline data covers full date range

✅ **Testing:**
- [ ] Unit tests for all components
- [ ] Integration test for full wiki generation
- [ ] Validation scripts confirm data quality

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| CategoryBuilder | 3 hours | 🚧 Next |
| StatisticsEngine | 2 hours | ⏳ Pending |
| RelationshipMapper | 3 hours | ⏳ Pending |
| WikiGenerator | 2 hours | ⏳ Pending |
| CLI & Testing | 2 hours | ⏳ Pending |
| **Total** | **12 hours** | **~0% complete** |

---

## Technical Decisions

### Decision 1: Reuse Existing Schema

**Choice:** Use `concepts` and `document_concepts` tables instead of creating new wiki tables

**Rationale:**
- Avoid schema duplication
- Leverage existing triggers for document_count
- Simpler database structure
- Less migration complexity

**Impact:** ✅ Faster implementation, cleaner architecture

### Decision 2: Category Type Enum

**Choice:** Use string values for `concept_type` (`authority`, `institution`, `violation`, `doc_type`)

**Rationale:**
- Clear semantic meaning
- Easy to query and filter
- Extensible for future category types

**Impact:** ✅ Readable queries, maintainable code

### Decision 3: Relationship Storage

**Choice:** Store relationships in `document_concepts` with `relevance_score < 1.0`

**Rationale:**
- Reuse existing table
- Differentiate from category membership (score = 1.0)
- Leverage existing indexes

**Impact:** ⚠️ Dual-purpose table requires careful querying

---

## Risks and Mitigation

### Risk 1: Performance with Large Document Sets

**Risk:** Wiki generation might be slow with 10,000+ documents

**Mitigation:**
- Batch database operations
- Use prepared statements
- Optimize queries with indexes
- Cache intermediate results

### Risk 2: Relationship Detection Accuracy

**Risk:** Too many false positive relationships

**Mitigation:**
- Tune relationship strength threshold (default: 0.3)
- Allow manual review and adjustment
- Provide confidence scores

### Risk 3: Category Name Variations

**Risk:** Same entity with different names (e.g., "玉山銀行" vs. "玉山商業銀行")

**Mitigation:**
- Use extracted `related_institutions` from metadata (already normalized)
- Store aliases in `keywords` JSON field
- Implement fuzzy matching if needed

---

## Next Steps

1. ✅ Create wiki module structure
2. 🎯 **Implement CategoryBuilder** (current focus)
3. Implement StatisticsEngine
4. Implement RelationshipMapper
5. Implement WikiGenerator
6. Create CLI and testing scripts
7. Run full wiki generation with real data
8. Document completion

---

**Status:** 🚧 In Progress
**Current Focus:** CategoryBuilder implementation
**Estimated Completion:** 2025-11-19 (12 hours remaining)
