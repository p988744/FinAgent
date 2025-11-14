# Semantic Concept Extraction - Design Document

**Date:** 2025-11-14
**Purpose:** Redesign concept extraction to use abstract semantic concepts instead of literal keywords
**Problem:** Current system uses exact keyword matching which misses relevant documents with variations

---

## Problem Analysis

### Current Approach (Literal Keywords)

**Example from current system:**
```python
# Document mentions: "洗錢防制缺失"
# Extracted concept: "洗錢防制" (exact match)
# Query: "AML violations"
# Result: MISS - no match because different wording
```

**Issues:**
1. **Exact Matching** - Misses synonyms (洗錢 vs AML vs 反洗錢)
2. **Term Variations** - Misses related terms (洗錢防制 vs 洗錢防制作業 vs 洗錢防制法)
3. **Language Mixing** - Chinese vs English terms not linked
4. **Specificity** - Too specific (玉山銀行) vs too broad need
5. **Keyword Dependency** - Relies on exact text presence

---

## New Approach (Semantic Concepts)

### Principle: Abstract Over Concrete

Map surface-level terms → Abstract semantic concepts → Related surface terms

**Example:**
```
Surface Terms          Semantic Concept              Retrieval Expands To
-------------          ----------------              --------------------
洗錢防制                → ANTI_MONEY_LAUNDERING    → [洗錢, AML, 反洗錢, 可疑交易,
洗錢                                                    洗錢防制法, KYC]
AML
反洗錢

玉山銀行                → COMMERCIAL_BANK          → [銀行, 商業銀行, bank,
台新銀行                  + SPECIFIC_INSTITUTION      financial institution]
中國信託                  (with institution_id)
```

---

## Semantic Concept Taxonomy

### Level 1: Domain Categories (Broadest)

```
REGULATORY_COMPLIANCE      - 法規遵循相關
FINANCIAL_CRIME           - 金融犯罪相關
MARKET_INTEGRITY          - 市場完整性
CONSUMER_PROTECTION       - 消費者保護
OPERATIONAL_RISK          - 作業風險
CORPORATE_GOVERNANCE      - 公司治理
```

### Level 2: Violation Categories (Specific)

```
ANTI_MONEY_LAUNDERING     - 洗錢防制
  ↳ Synonyms: 洗錢, AML, 反洗錢, 洗錢防制法, KYC, 可疑交易

INSIDER_TRADING           - 內線交易
  ↳ Synonyms: 內線, insider, 重大訊息, 內部人交易

INFORMATION_DISCLOSURE    - 資訊揭露
  ↳ Synonyms: 資訊公開, 揭露義務, disclosure, 財報揭露

MARKET_MANIPULATION       - 市場操縱
  ↳ Synonyms: 炒作, 操縱股價, manipulation, 不當交易

FRAUD                     - 詐欺
  ↳ Synonyms: 欺詐, fraud, 詐騙, 不實陳述

CUSTOMER_SUITABILITY      - 適合性原則
  ↳ Synonyms: 客戶適合性, suitability, KYC, 投資人保護

RELATED_PARTY_TRANSACTION - 關係人交易
  ↳ Synonyms: 利害關係人, 關聯交易, related party
```

### Level 3: Entity Categories

```
REGULATORY_AUTHORITY
  ↳ 金管會 (FSC)
  ↳ 中央銀行 (CBC)
  ↳ 公平會 (FTC)
  ↳ Sub-bureaus: 銀行局, 證期局, 保險局

COMMERCIAL_BANK
  ↳ Synonyms: 銀行, 商業銀行, bank
  ↳ Specific institutions indexed separately

SECURITIES_FIRM
  ↳ Synonyms: 證券商, broker, 證券公司

INSURANCE_COMPANY
  ↳ Synonyms: 保險公司, insurer, 壽險, 產險

INVESTMENT_TRUST
  ↳ Synonyms: 投信, 證券投資信託, fund management

VENTURE_CAPITAL
  ↳ Synonyms: 創投, 創業投資, VC
```

---

## Implementation Strategy

### 1. Concept Mapping Table

**Database Schema:**

```sql
CREATE TABLE semantic_concepts (
    id INTEGER PRIMARY KEY,
    concept_key TEXT UNIQUE NOT NULL,  -- e.g., 'ANTI_MONEY_LAUNDERING'
    concept_level INTEGER,              -- 1=domain, 2=violation, 3=entity
    parent_concept_key TEXT,            -- hierarchical relationship
    name_zh TEXT NOT NULL,              -- 洗錢防制
    name_en TEXT,                       -- Anti-Money Laundering
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE concept_synonyms (
    id INTEGER PRIMARY KEY,
    concept_key TEXT NOT NULL,
    synonym TEXT NOT NULL,              -- 洗錢, AML, 反洗錢, etc.
    synonym_type TEXT,                  -- zh/en/abbreviation/variant
    weight REAL DEFAULT 1.0,            -- relevance weight (0-1)
    FOREIGN KEY (concept_key) REFERENCES semantic_concepts(concept_key)
);

CREATE INDEX idx_synonym_lookup ON concept_synonyms(synonym);
```

### 2. Document Concept Assignment

**During Indexing:**

```python
def assign_semantic_concepts(document_metadata: DocumentMetadata) -> list[str]:
    """
    Map document metadata to semantic concept keys.

    Returns:
        List of concept_keys like ['ANTI_MONEY_LAUNDERING', 'COMMERCIAL_BANK']
    """
    concepts = set()

    # From violation_types
    for violation in document_metadata.violation_types:
        concept_key = map_violation_to_concept(violation)
        if concept_key:
            concepts.add(concept_key)

    # From related_institutions
    for institution in document_metadata.related_institutions:
        concept_key = map_institution_to_concept(institution)
        if concept_key:
            concepts.add(concept_key)

    # From document type
    doc_type_concept = map_doctype_to_concept(document_metadata.document_type)
    if doc_type_concept:
        concepts.add(doc_type_concept)

    return list(concepts)


def map_violation_to_concept(violation_text: str) -> str | None:
    """
    Map violation text to semantic concept key.

    Examples:
        "洗錢防制作業缺失" → "ANTI_MONEY_LAUNDERING"
        "內線交易" → "INSIDER_TRADING"
        "AML violation" → "ANTI_MONEY_LAUNDERING"
    """
    # Query concept_synonyms table
    # SELECT concept_key FROM concept_synonyms WHERE synonym LIKE %violation_text%
    # Or use fuzzy matching / embedding similarity
    pass


def map_institution_to_concept(institution_text: str) -> str | None:
    """
    Map institution name to semantic concept key.

    Examples:
        "玉山銀行" → "COMMERCIAL_BANK"
        "國泰證券" → "SECURITIES_FIRM"
        "富邦創投" → "VENTURE_CAPITAL"
    """
    # First check for specific institution ID
    # Then fallback to institution type
    pass
```

### 3. Query Concept Expansion

**During Query Planning:**

```python
def expand_query_concepts(query_text: str) -> list[str]:
    """
    Expand user query to semantic concepts.

    Input: "玉山銀行洗錢防制裁罰"
    Output: ['ANTI_MONEY_LAUNDERING', 'COMMERCIAL_BANK', 'ENFORCEMENT']

    Then retrieve all documents tagged with ANY of these concepts.
    """
    concepts = set()

    # Extract key terms from query
    terms = extract_query_terms(query_text)

    # Map each term to concepts
    for term in terms:
        matched_concepts = lookup_concept_by_synonym(term)
        concepts.update(matched_concepts)

    return list(concepts)


def lookup_concept_by_synonym(term: str) -> list[str]:
    """
    Look up semantic concepts by synonym matching.

    Input: "洗錢"
    Output: ['ANTI_MONEY_LAUNDERING']

    Input: "銀行"
    Output: ['COMMERCIAL_BANK', 'CENTRAL_BANK']  # may return multiple
    """
    # SELECT DISTINCT concept_key FROM concept_synonyms
    # WHERE synonym LIKE %term% OR synonym = term
    pass
```

### 4. Retrieval Strategy

**Two-Stage Retrieval:**

```python
def retrieve_documents(query: str):
    # Stage 1: Concept-based pre-filtering
    concepts = expand_query_concepts(query)

    # Get all documents with ANY matching concept
    candidate_docs = get_documents_by_concepts(concepts)
    # This gives us documents tagged with ANTI_MONEY_LAUNDERING,
    # even if they say "AML" or "反洗錢" instead of "洗錢"

    # Stage 2: Vector search within candidates
    # Use semantic similarity on the candidate set
    chunks = vector_search(query, candidate_docs)

    return chunks
```

---

## Example Concept Mapping Data

### Violation Concepts

```python
VIOLATION_CONCEPTS = {
    "ANTI_MONEY_LAUNDERING": {
        "name_zh": "洗錢防制",
        "name_en": "Anti-Money Laundering",
        "level": 2,
        "parent": "FINANCIAL_CRIME",
        "synonyms": [
            ("洗錢", "zh", 1.0),
            ("洗錢防制", "zh", 1.0),
            ("洗錢防制法", "zh", 0.9),
            ("洗錢防制作業", "zh", 0.9),
            ("反洗錢", "zh", 1.0),
            ("AML", "en", 1.0),
            ("Anti-Money Laundering", "en", 1.0),
            ("可疑交易", "zh", 0.7),
            ("KYC", "en", 0.6),
            ("客戶盡職調查", "zh", 0.6),
        ]
    },

    "INSIDER_TRADING": {
        "name_zh": "內線交易",
        "name_en": "Insider Trading",
        "level": 2,
        "parent": "MARKET_INTEGRITY",
        "synonyms": [
            ("內線", "zh", 1.0),
            ("內線交易", "zh", 1.0),
            ("內部人交易", "zh", 0.9),
            ("insider trading", "en", 1.0),
            ("insider", "en", 0.8),
            ("重大訊息", "zh", 0.7),
            ("內部消息", "zh", 0.7),
        ]
    },

    "INFORMATION_DISCLOSURE": {
        "name_zh": "資訊揭露",
        "name_en": "Information Disclosure",
        "level": 2,
        "parent": "MARKET_INTEGRITY",
        "synonyms": [
            ("資訊揭露", "zh", 1.0),
            ("資訊公開", "zh", 0.9),
            ("財報揭露", "zh", 0.8),
            ("揭露義務", "zh", 0.8),
            ("disclosure", "en", 1.0),
            ("transparency", "en", 0.7),
            ("財務報告", "zh", 0.6),
        ]
    }
}
```

### Entity Concepts

```python
ENTITY_CONCEPTS = {
    "COMMERCIAL_BANK": {
        "name_zh": "商業銀行",
        "name_en": "Commercial Bank",
        "level": 3,
        "parent": "FINANCIAL_INSTITUTION",
        "synonyms": [
            ("銀行", "zh", 1.0),
            ("商業銀行", "zh", 1.0),
            ("bank", "en", 1.0),
            ("commercial bank", "en", 1.0),
            ("銀行業", "zh", 0.9),
        ]
    },

    "SECURITIES_FIRM": {
        "name_zh": "證券商",
        "name_en": "Securities Firm",
        "level": 3,
        "parent": "FINANCIAL_INSTITUTION",
        "synonyms": [
            ("證券商", "zh", 1.0),
            ("證券公司", "zh", 1.0),
            ("券商", "zh", 0.9),
            ("securities firm", "en", 1.0),
            ("broker", "en", 0.8),
            ("brokerage", "en", 0.8),
        ]
    },

    "VENTURE_CAPITAL": {
        "name_zh": "創業投資",
        "name_en": "Venture Capital",
        "level": 3,
        "parent": "INVESTMENT_FIRM",
        "synonyms": [
            ("創投", "zh", 1.0),
            ("創業投資", "zh", 1.0),
            ("創投公司", "zh", 1.0),
            ("創業投資事業", "zh", 1.0),
            ("VC", "en", 1.0),
            ("venture capital", "en", 1.0),
        ]
    }
}
```

---

## Benefits of Semantic Concepts

### 1. Recall Improvement

**Before (Literal Keywords):**
```
Query: "創投公司裁罰"
Extracted keywords: ["創投公司"]
Search: Documents containing exact text "創投公司"
Results: 2 documents
MISSED: Documents saying "創業投資事業" (5 docs)
```

**After (Semantic Concepts):**
```
Query: "創投公司裁罰"
Mapped to concepts: [VENTURE_CAPITAL, ENFORCEMENT]
Search: Documents tagged with VENTURE_CAPITAL concept
Expands to: ["創投", "創業投資", "創投公司", "創業投資事業", "VC"]
Results: 7 documents ✓
```

### 2. Cross-Language Support

```
Query: "AML violations"
Mapped to: [ANTI_MONEY_LAUNDERING]
Retrieves: Documents in Chinese about "洗錢防制"
```

### 3. Synonym Handling

```
Query: "銀行洗錢"
Concepts: [COMMERCIAL_BANK, ANTI_MONEY_LAUNDERING]
Matches docs with: "洗錢防制", "反洗錢", "AML", "可疑交易報告"
```

### 4. Hierarchical Expansion

```
Query: "金融犯罪"
Concept: FINANCIAL_CRIME (level 1)
Expands to child concepts:
  - ANTI_MONEY_LAUNDERING
  - FRAUD
  - MARKET_MANIPULATION
  - etc.
```

---

## Migration Path

### Phase 1: Build Concept Taxonomy (Week 1)
1. Define core semantic concepts (20-30 concepts)
2. Create concept mapping table in database
3. Populate synonym table from existing data

### Phase 2: Index Documents with Concepts (Week 2)
1. Add `semantic_concepts` column to documents table
2. Run concept assignment on all documents
3. Create concept index for fast lookup

### Phase 3: Update Query Pipeline (Week 3)
1. Add concept expansion to planning agent
2. Update retriever to use concept filtering
3. Test with existing queries

### Phase 4: Refinement (Week 4)
1. Analyze missed queries
2. Add missing synonyms
3. Tune concept weights
4. A/B test against keyword system

---

## Success Metrics

**Before Semantic Concepts:**
- Query: "創投公司裁罰" → 3 results (all literal matches)
- Query: "AML violations" → 0 results (no English docs)
- Query: "銀行反洗錢" → 2 results (exact "反洗錢" only)

**Target After Implementation:**
- Query: "創投公司裁罰" → 8 results (includes "創業投資事業")
- Query: "AML violations" → 15 results (maps to Chinese equivalents)
- Query: "銀行反洗錢" → 20 results (includes "洗錢防制", "AML", "可疑交易")

**KPIs:**
- Recall +150% (from 40% to 100% on test queries)
- Precision maintained at >90%
- Zero-result queries reduced from 20% to <5%

---

## Next Steps

1. ✅ Design complete
2. ⏸ Build concept taxonomy database schema
3. ⏸ Create concept mapping rules
4. ⏸ Test with sample documents
5. ⏸ Integrate with query pipeline

---

**Design Date:** 2025-11-14
**Status:** 📋 DESIGN COMPLETE
**Next:** Database schema and taxonomy creation
