# Test Issues Summary - 10-Document Full Test

**Date**: 2025-11-14
**Test Script**: `test_10_docs_full.py`
**Status**: Multiple issues found during integration testing

---

## 🔍 Issues Found

### Issue #1: Import Error - Class Name Mismatch
**Severity**: High
**Component**: test_10_docs_full.py
**Error**: `ImportError: cannot import name 'DocumentMetadataGenerator'`

**Root Cause**: Class is named `MetadataGenerator`, not `DocumentMetadataGenerator`

**Fix Applied**: ✅
```python
# Before
from finagent.document_processing.metadata_generator import DocumentMetadataGenerator

# After
from finagent.document_processing.metadata_generator import MetadataGenerator
```

---

### Issue #2: API Usage Error - Missing Parameters
**Severity**: High
**Component**: test_10_docs_full.py
**Error**: `TypeError: MetadataGenerator.generate_metadata() missing 2 required positional arguments`

**Root Cause**: `generate_metadata()` requires `(doc_id, filename, content)` as separate parameters

**Fix Applied**: ✅
```python
# Before
metadata = metadata_gen.generate_metadata(doc)

# After
metadata = metadata_gen.generate_metadata(doc.id, doc.filename, doc.content)
```

---

### Issue #3: Attribute Error - Document.filename
**Severity**: High
**Component**: test_10_docs_full.py
**Error**: `AttributeError: 'Document' object has no attribute 'filename'`

**Root Cause**: Document model has `source` (file path) but not `filename` attribute

**Fix Applied**: ✅
```python
# Extract filename from source path
filename = Path(doc.source).name
metadata = metadata_gen.generate_metadata(doc.id, filename, doc.content)
```

---

### Issue #4: Attribute Error - DocumentMetadata Fields
**Severity**: High
**Component**: test_10_docs_full.py
**Error**: `AttributeError: 'DocumentMetadata' object has no attribute 'title'`

**Root Cause**: Field name mismatch between test expectations and actual model

**Actual DocumentMetadata Fields**:
- `description` (not `title`)
- `document_type`
- `keywords`
- `date`
- `issuing_authority` (not `authority`)
- `related_institutions` (not `entity`)
- `penalty_amount`
- `violation_types`

**Fix Needed**: ⚠️  NOT YET APPLIED
```python
# Current (INCORRECT)
doc.metadata.update({
    "title": metadata.title,  # ❌ Should be 'description'
    "date": metadata.date,
    "entity": metadata.entity,  # ❌ Should be 'related_institutions'
    "violation_type": metadata.violation_type,  # ❌ Should be 'violation_types' (plural)
    "penalty_amount": metadata.penalty_amount,
    "authority": metadata.authority  # ❌ Should be 'issuing_authority'
})

# Corrected
doc.metadata.update({
    "description": metadata.description,
    "document_type": metadata.document_type,
    "keywords": metadata.keywords,
    "date": metadata.date,
    "issuing_authority": metadata.issuing_authority,
    "related_institutions": metadata.related_institutions,
    "penalty_amount": metadata.penalty_amount,
    "violation_types": metadata.violation_types
})
```

---

## 📊 Test Progress Summary

### Completed Steps
1. ✅ **Step 1**: Backup and Clear - Successfully backed up 492 documents from previous test
2. ✅ **Step 2**: Select Documents - 10 representative documents selected:
   - 3 Banking violations (銀行局)
   - 2 Insurance violations (保險局)
   - 1 Securities violation (證券期貨局)
   - 4 Others
3. ✅ **Step 3**: Design Verification Steps - 13 verification checks across 3 categories

### Failed Step
4. ❌ **Step 4**: Build Index - Failed at metadata field mapping

### Pending Steps
5. ⏸️ **Step 5**: Query and Verify - Not reached yet
6. ⏸️ **Step 6**: Collect Issues - Not reached yet

---

## 🔧 Recommended Fixes

### Option 1: Fix Test Script (Recommended)
Update `test_10_docs_full.py` to use correct field names from `DocumentMetadata`:

```python
# In step4_build_index() function around line 254-260
doc.metadata.update({
    "description": metadata.description,
    "document_type": metadata.document_type,
    "keywords": metadata.keywords,
    "date": metadata.date,
    "issuing_authority": metadata.issuing_authority,
    "related_institutions": metadata.related_institutions,  # List[str]
    "penalty_amount": metadata.penalty_amount,
    "violation_types": metadata.violation_types  # List[str]
})

# Also update database INSERT statement to match (around line 272-287)
conn.execute(
    """INSERT INTO documents (
        id, filename, source, content_preview,
        description, document_type, date, issuing_authority,
        penalty_amount, indexed_at, chunk_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (
        doc.id,
        filename,
        doc.source,
        doc.content[:200],
        doc.metadata.get("description"),
        doc.metadata.get("document_type"),
        doc.metadata.get("date"),
        doc.metadata.get("issuing_authority"),
        doc.metadata.get("penalty_amount"),
        datetime.now().isoformat(),
        chunks
    )
)
```

### Option 2: Update Database Schema
Ensure `documents` table schema matches the metadata fields:

```sql
-- Check current schema
SELECT sql FROM sqlite_master WHERE type='table' AND name='documents';

-- May need to add columns:
ALTER TABLE documents ADD COLUMN description TEXT;
ALTER TABLE documents ADD COLUMN document_type TEXT;
ALTER TABLE documents ADD COLUMN issuing_authority TEXT;
```

---

## 🎯 Next Steps

1. **Apply Fix #4** to test script
2. **Verify database schema** matches metadata fields
3. **Re-run test** with all fixes applied
4. **Monitor LLM metadata generation** (will take 10-20 minutes for 10 documents)
5. **Test query execution** with 4 example queries
6. **Document final results**

---

## 💡 Lessons Learned

### API Compatibility Issues
- **Lesson**: Always check actual model/class signatures before using them
- **Impact**: Wasted 3 test iterations debugging simple API mismatches
- **Prevention**: Add type hints and API documentation to core modules

### Field Name Inconsistency
- **Lesson**: Maintain consistent naming conventions across models
- **Example**: `authority` vs `issuing_authority`, `entity` vs `related_institutions`
- **Prevention**: Define a data dictionary with canonical field names

### Test Design
- **Lesson**: Integration tests should validate API contracts first
- **Improvement**: Add unit tests for individual components before integration testing
- **Suggestion**: Create a "smoke test" that just imports and instantiates classes

---

## 📝 Test Execution Log

### Attempt #1 (15:01:54)
- ❌ Failed: Import error `DocumentMetadataGenerator`
- Duration: 4 seconds
- Fix: Changed to `MetadataGenerator`

### Attempt #2 (15:02:21)
- ❌ Failed: Missing parameters for `generate_metadata()`
- Duration: 5 seconds
- Fix: Pass `doc.id, filename, content` separately

### Attempt #3 (15:02:57)
- ❌ Failed: `Document` has no `filename` attribute
- Duration: 6 seconds
- Fix: Extract filename from `doc.source` path

### Attempt #4 (15:04:20)
- ❌ Failed: `DocumentMetadata` has no `title` attribute
- Duration: 8 seconds
- Fix: **PENDING** - Need to update field names

---

## 🔬 Additional Observations

### Performance Expectations
- **Metadata Generation**: ~1-2 minutes per document with LLM
- **Vector Indexing**: ~0.5-1 second per document
- **Total Estimated Time**: 15-25 minutes for 10 documents
- **Query Execution**: ~30-60 seconds per query

### Resource Usage
- **LLM API Calls**: 10 calls for metadata generation
- **Estimated Cost**: ~$0.01-0.02 USD
- **Vector DB Size**: ~50-100 chunks per document = 500-1000 total chunks

---

**Status**: Test incomplete, awaiting Fix #4 implementation
**Next Action**: Update test script with correct DocumentMetadata field mapping
