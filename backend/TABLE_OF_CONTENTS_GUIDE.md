# Table of Contents (TOC) Guide

## Overview

The system automatically generates and maintains a **Table of Contents** that provides a comprehensive overview of all indexed documents. This TOC is particularly useful for workflow agents that need to quickly understand what documents are available before diving into details.

## Location

The TOC is automatically generated at:
```
backend/data/TABLE_OF_CONTENTS.md
```

## When It's Updated

The TOC is **automatically updated** in these situations:

1. **After `/init`** - When you initialize a document's metadata
2. **After `/reindex`** - When you reindex all documents

You don't need to manually update it - the system handles this automatically!

## Structure

The TOC contains three main sections:

### 1. 📊 統計資訊 (Statistics)

Quick overview of document counts by type:

```markdown
| 文件類型 | 數量 |
|---------|------|
| 裁罰書   | 25   |
| 判決書   | 12   |
| 法規條文 | 8    |
```

### 2. 📋 快速索引 (Quick Reference)

Compact table with essential information for all documents:

```markdown
| 檔名 | 類型 | 日期 | 關鍵摘要 |
|------|------|------|----------|
| 玉山銀行洗錢防制裁罰.txt | 裁罰書 | 2020-09-15 | 玉山商業銀行, 罰2.5億元 |
| 國泰世華裁罰.txt | 裁罰書 | 2019-03-20 | 國泰世華銀行, 罰1.8億元 |
```

**Purpose:** Allows agents to quickly scan all documents at a glance.

### 3. 📚 詳細目錄 (Detailed Catalog)

Complete information for each document, grouped by type:

```markdown
### 裁罰書 (25 份)

#### 1. 玉山銀行洗錢防制裁罰.txt

**描述:** 金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元

- **日期:** 2020-09-15
- **發布機關:** 金管會
- **相關機構:** 玉山商業銀行, 玉山銀行
- **裁罰金額:** 2.5億元
- **違規類型:** 洗錢防制, 法規遵循
- **關鍵字:** 玉山銀行, 洗錢防制, 裁罰, 金管會, 2.5億元

**文件ID:** `doc_玉山銀行洗錢防制裁罰_abc123`

---
```

**Purpose:** Provides complete context for each document.

## Benefits for Workflow Agents

### 1. **Quick Overview**

Instead of reading every document, agents can:
- Read the TOC first (one file)
- Understand what documents are available
- Identify relevant documents quickly

### 2. **Efficient Document Selection**

Agents can use the TOC to:
- Filter by document type (e.g., only 裁罰書)
- Filter by date range (e.g., 2020-2023)
- Filter by institution (e.g., all 玉山銀行 documents)
- Filter by violation type (e.g., all 洗錢防制 cases)

### 3. **Reduced API Calls**

Instead of:
```
1. List all documents
2. Read each document's metadata
3. Filter relevant documents
4. Read document content
```

Now:
```
1. Read TOC (single file)
2. Identify relevant documents
3. Read only those documents
```

This **reduces API calls by ~90%** for initial document discovery.

### 4. **Structured Information**

The TOC provides:
- **Document IDs** for precise retrieval
- **Filenames** for reference
- **Metadata** for filtering
- **Descriptions** for relevance assessment

## Example: Agent Workflow

### Scenario: Find all penalty documents from 2020 with amounts > 2億元

**Without TOC:**
```python
# Agent needs to:
1. List all files in data/documents/ (50+ files)
2. Read metadata for each file (50+ reads)
3. Filter by year and amount (compute-intensive)
4. Read relevant documents (5 reads)

Total operations: ~105
```

**With TOC:**
```python
# Agent workflow:
1. Read TABLE_OF_CONTENTS.md (1 read)
2. Parse markdown to find relevant documents
   - Filter: 類型 = "裁罰書"
   - Filter: 日期 starts with "2020"
   - Filter: 裁罰金額 contains "億" and value >= 2
3. Read identified documents (5 reads)

Total operations: ~6
```

**Improvement: 94% reduction in operations!**

## Example TOC Content

Here's what a generated TOC looks like:

```markdown
# 文件目錄 (Table of Contents)

**最後更新:** 2025-01-12 16:30:00
**總文件數:** 45

## 📊 統計資訊

| 文件類型 | 數量 |
|---------|------|
| 裁罰書   | 25   |
| 判決書   | 12   |
| 法規條文 | 5    |
| 新聞報導 | 3    |

## 📋 快速索引

| 檔名 | 類型 | 日期 | 關鍵摘要 |
|------|------|------|----------|
| 玉山銀行洗錢防制裁罰.txt | 裁罰書 | 2020-09-15 | 玉山商業銀行, 罰2.5億元, 洗錢防制 |
| 國泰世華裁罰.txt | 裁罰書 | 2019-03-20 | 國泰世華銀行, 罰1.8億元 |
| 中信銀行裁罰.txt | 裁罰書 | 2021-06-10 | 中信銀行, 罰3.2億元, 內線交易 |

## 📚 詳細目錄

### 裁罰書 (25 份)

#### 1. 玉山銀行洗錢防制裁罰.txt

**描述:** 金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元

- **日期:** 2020-09-15
- **發布機關:** 金管會
- **相關機構:** 玉山商業銀行, 玉山銀行
- **裁罰金額:** 2.5億元
- **違規類型:** 洗錢防制, 法規遵循
- **關鍵字:** 玉山銀行, 洗錢防制, 裁罰, 金管會, 2.5億元

**文件ID:** `doc_玉山銀行洗錢防制裁罰_abc123`

---

[... more documents ...]
```

## Usage in Workflow Agents

### Planning Agent

The Planning Agent can read the TOC to:
- Understand available resources
- Plan retrieval strategy
- Prioritize document types

```python
# Planning Agent pseudocode
toc = read_file("data/TABLE_OF_CONTENTS.md")

# Parse quick index
docs = parse_table(toc, "快速索引")

# Filter relevant documents
relevant = filter(docs,
    lambda d: d.type == "裁罰書" and
              d.date.startswith("2020"))

# Plan retrieval
plan = {
    "strategy": "targeted_retrieval",
    "documents": [d.filename for d in relevant],
    "expected_count": len(relevant)
}
```

### Action Agent

The Action Agent can use TOC for:
- Quick lookup by document ID
- Filtering before RAG retrieval
- Metadata-based selection

```python
# Action Agent pseudocode
toc = read_file("data/TABLE_OF_CONTENTS.md")

# Find documents by institution
docs = search_toc(toc, institution="玉山銀行")

# Use document IDs for precise retrieval
doc_ids = [d.doc_id for d in docs]
chunks = rag_retrieve(query, filter={"doc_id": doc_ids})
```

### Validation Agent

The Validation Agent can use TOC to:
- Verify document existence
- Check metadata consistency
- Validate date ranges

## Updating the TOC

The TOC is automatically updated, but you can also manually trigger an update:

```python
from finagent.document_processing.toc_generator import TableOfContents

# Generate and save TOC
toc = TableOfContents()
toc_path = toc.save()

print(f"TOC saved to: {toc_path}")
```

## TOC Statistics

You can get summary statistics without reading the full TOC:

```python
from finagent.document_processing.toc_generator import TableOfContents

toc = TableOfContents()
stats = toc.get_summary()

print(f"Total documents: {stats['total']}")
print(f"By type: {stats['by_type']}")
print(f"By authority: {stats['by_authority']}")
print(f"Date range: {stats['date_range']}")
```

Example output:
```python
{
    'total': 45,
    'by_type': {
        '裁罰書': 25,
        '判決書': 12,
        '法規條文': 5,
        '新聞報導': 3
    },
    'by_authority': {
        '金管會': 30,
        '中央銀行': 10,
        '最高法院': 5
    },
    'date_range': {
        'earliest': '2015-01-10',
        'latest': '2024-12-15'
    }
}
```

## Best Practices

### For Users

1. **Keep metadata up-to-date**: Run `/init` for all important documents
2. **Reindex regularly**: Run `/reindex` after adding new documents
3. **Check TOC**: Review `TABLE_OF_CONTENTS.md` to ensure all documents are included

### For Workflow Agents

1. **Read TOC first**: Always check TOC before querying documents
2. **Use document IDs**: Reference documents by ID for precision
3. **Filter by metadata**: Use type, date, authority for filtering
4. **Cache TOC**: Cache the TOC for the session to reduce reads

## Troubleshooting

### TOC not updating

**Cause**: Error during generation

**Fix**:
```bash
# Manually regenerate
uv run python -c "
from finagent.document_processing.toc_generator import TableOfContents
toc = TableOfContents()
toc.save()
print('TOC regenerated')
"
```

### TOC is empty

**Cause**: No documents have been initialized

**Fix**:
```bash
# Initialize documents first
finagent> /init
# Select and initialize documents
finagent> /reindex
```

### TOC has outdated information

**Cause**: Metadata was updated but TOC wasn't regenerated

**Fix**:
```bash
# Reindex to update TOC
finagent> /reindex --skip-init
```

## Summary

The Table of Contents is a powerful tool that:
- ✅ **Auto-generates** after `/init` and `/reindex`
- ✅ **Provides overview** of all documents
- ✅ **Reduces API calls** by ~90% for discovery
- ✅ **Enables filtering** by type, date, institution, etc.
- ✅ **Improves agent efficiency** with quick lookups

**Location**: `backend/data/TABLE_OF_CONTENTS.md`

**Use it to**: Quickly understand document collection before detailed analysis!
