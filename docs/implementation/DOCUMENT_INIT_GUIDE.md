# Document Initialization Guide

## Overview

The `/init` command allows you to add descriptive metadata to your documents **before** indexing them. This significantly improves search accuracy and prevents misunderstandings by providing the system with context about each document.

## Why Initialize Documents?

Without metadata, the system only has the raw document text to work with. This can lead to:
- **Irrelevant results**: Documents about different topics may match due to similar keywords
- **Missed results**: Important documents may be overlooked if their content doesn't contain exact query keywords
- **Misinterpretation**: The system may not understand the document's context, date, or authority

With proper initialization:
- ✅ **Better search accuracy**: Metadata helps filter and rank results
- ✅ **Contextual understanding**: System knows document type, date, authority
- ✅ **Entity recognition**: Related institutions and keywords are explicitly tagged
- ✅ **Improved relevance**: Descriptions help semantic search understand document purpose

## Usage

### 1. List All Documents

```bash
finagent> /init
```

Shows a table of all documents with their initialization status:
- ✓ 已初始化 (Initialized) - Document has metadata
- 待初始化 (Pending) - Document needs metadata

### 2. Initialize a Specific Document

```bash
finagent> /init 玉山銀行洗錢防制裁罰.txt
```

Or select interactively:

```bash
finagent> /init
# Choose from the numbered list
```

### 3. Interactive Wizard

The wizard guides you through 6 steps:

#### **Step 1/6: Document Description** (Required)
Provide a 1-2 sentence description of the document content.

**Example:**
```
金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元
```

**Tips:**
- Be specific about the main topic
- Include key facts (dates, amounts, institutions)
- Use Traditional Chinese
- Keep it concise but informative

#### **Step 2/6: Document Type** (Required)
Choose the document type:
1. 裁罰書 (Penalty Document)
2. 判決書 (Court Judgment)
3. 法規條文 (Laws/Regulations)
4. 新聞報導 (News Article)
5. 監管公告 (Regulatory Announcement)
6. 銀行聲明 (Bank Statement)
7. 分析報告 (Analysis Report)
8. 其他 (Other - allows custom input)

**Why this matters:**
- Helps filter by document type
- Different types have different weights in relevance scoring
- Primary sources (裁罰書, 判決書) rank higher than secondary sources

#### **Step 3/6: Keywords** (Required)
Enter comma-separated keywords that represent the document's main topics.

**Example:**
```
玉山銀行,洗錢防制,裁罰,金管會,2.5億元
```

**Tips:**
- Include institution names
- Include violation types
- Include key amounts or dates
- Use terms users might search for

#### **Step 4/6: Date and Authority** (Optional)
- **Document Date**: When the document was issued (YYYY-MM-DD)
- **Issuing Authority**: Which government body issued it

**Example:**
```
日期: 2020-09-15
發布機關: 金管會
```

**Why this matters:**
- Enables date-range filtering
- Shows authority level (金管會 > 地方法院)
- Helps with chronological sorting

#### **Step 5/6: Related Institutions** (Optional)
Enter comma-separated names of banks or institutions mentioned.

**Example:**
```
玉山商業銀行,玉山銀行
```

**Tips:**
- Include both official names and common names
- Include subsidiaries if relevant

#### **Step 6/6: Penalty Information** (Only for 裁罰書)
If document type is "裁罰書", provide:

**Penalty Amount:**
```
2.5億元
```

**Violation Types** (Multi-select):
1. 洗錢防制 (AML)
2. 內線交易 (Insider Trading)
3. 資訊揭露 (Information Disclosure)
4. 法規遵循 (Regulatory Compliance)
5. 作業風險 (Operational Risk)
6. 信用風險 (Credit Risk)
7. 市場操縱 (Market Manipulation)
8. 消費者保護 (Consumer Protection)
9. 其他 (Other - allows custom input)

**Example selection:**
```
請選擇違規類型: 1,4
# This selects: 洗錢防制, 法規遵循
```

## Complete Example

```bash
finagent> /init

[文件清單 table showing documents]

finagent> /init 玉山銀行洗錢防制裁罰.txt

# Step 1: Description
文件描述: 金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元

# Step 2: Type
請選擇文件類型: 1  # 裁罰書

# Step 3: Keywords
關鍵字: 玉山銀行,洗錢防制,裁罰,金管會,2.5億元,內控

# Step 4: Date & Authority
文件日期: 2020-09-15
請選擇發布機關: 1  # 金管會

# Step 5: Related Institutions
相關機構: 玉山商業銀行,玉山銀行

# Step 6: Penalty Information
裁罰金額: 2.5億元
請選擇違規類型: 1,4  # 洗錢防制, 法規遵循

✓ 文件初始化完成
```

## How Metadata Improves Search

### Before Initialization:
```
Query: "2020年玉山銀行裁罰"
Results: Returns ALL documents containing "玉山" or "銀行" or "裁罰"
         May miss this document if it doesn't contain "2020" in the text
```

### After Initialization:
```
Query: "2020年玉山銀行裁罰"
Results:
  1. ✓ Matches date (2020-09-15)
  2. ✓ Matches institution (玉山商業銀行)
  3. ✓ Matches document type (裁罰書)
  4. ✓ High relevance score
```

### Metadata Fields in Vector Search

When you `/reindex` after initialization, each chunk gets enhanced metadata:
```json
{
  "chunk_text": "...",
  "description": "金管會針對玉山商業銀行洗錢防制內控缺失...",
  "document_type": "裁罰書",
  "keywords": "玉山銀行,洗錢防制,裁罰,金管會,2.5億元",
  "date": "2020-09-15",
  "issuing_authority": "金管會",
  "related_institutions": "玉山商業銀行,玉山銀行",
  "penalty_amount": "2.5億元",
  "violation_types": "洗錢防制,法規遵循"
}
```

This metadata:
1. **Enriches embeddings**: Description adds context for semantic search
2. **Enables filtering**: Can filter by date, institution, type
3. **Improves ranking**: Primary sources rank higher
4. **Prevents errors**: Clear document type prevents misinterpretation

## Workflow

### Recommended Process:

1. **Add new documents** to `data/documents/`
   ```bash
   cp new_penalty_doc.txt backend/data/documents/
   ```

2. **Initialize metadata** with `/init`
   ```bash
   finagent> /init
   # Select document and fill in metadata
   ```

3. **Reindex** to apply metadata
   ```bash
   finagent> /reindex
   ```

4. **Query** with improved accuracy
   ```bash
   finagent> 玉山銀行洗錢防制裁罰
   ```

### Bulk Initialization

For many documents:
```bash
finagent> /init list  # View all documents
finagent> /init doc1.txt
finagent> /init doc2.txt
# ... initialize each document
finagent> /reindex --clear  # Rebuild index with all metadata
```

## Storage

Metadata is stored in:
```
backend/data/document_metadata.json
```

**Format:**
```json
{
  "doc_玉山銀行洗錢防制裁罰_abc123": {
    "doc_id": "doc_玉山銀行洗錢防制裁罰_abc123",
    "filename": "玉山銀行洗錢防制裁罰.txt",
    "description": "金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元",
    "document_type": "裁罰書",
    "keywords": ["玉山銀行", "洗錢防制", "裁罰", "金管會", "2.5億元"],
    "date": "2020-09-15",
    "issuing_authority": "金管會",
    "related_institutions": ["玉山商業銀行", "玉山銀行"],
    "penalty_amount": "2.5億元",
    "violation_types": ["洗錢防制", "法規遵循"],
    "created_at": "2025-01-12T15:30:00",
    "updated_at": "2025-01-12T15:30:00"
  }
}
```

## Updating Metadata

To update existing metadata:
```bash
finagent> /init 玉山銀行洗錢防制裁罰.txt
# System detects existing metadata
是否要更新？ yes
# Re-enter all metadata (wizard will show current values)
```

## Best Practices

### 1. **Be Consistent**
- Use the same names for institutions across documents
- Use standard date format (YYYY-MM-DD)
- Use consistent violation type naming

### 2. **Be Specific**
- Include exact amounts (2.5億元, not "很多")
- Include exact dates (2020-09-15, not "2020年")
- Include official institution names

### 3. **Be Complete**
- Fill in all relevant fields
- Don't skip optional fields if you have the information
- Better metadata = better search results

### 4. **Initialize Before Indexing**
- Always run `/init` BEFORE `/reindex`
- Metadata is applied during indexing
- Re-indexing is required after adding/updating metadata

### 5. **Verify After Indexing**
When running `/reindex`, look for the icon:
- 📋 = Document with metadata (initialized)
- 📄 = Document without metadata (not initialized)

## Troubleshooting

### Issue: Metadata not showing in search results

**Cause**: Forgot to reindex after initializing

**Fix:**
```bash
finagent> /reindex --clear
```

### Issue: Wrong document type assigned

**Cause**: Selected wrong option in wizard

**Fix:**
```bash
finagent> /init filename.txt
是否要更新？ yes
# Re-enter correct information
finagent> /reindex --clear
```

### Issue: Can't find document in /init list

**Cause**: Document not in `data/documents/` directory

**Fix:**
```bash
# Copy document to correct location
cp document.txt backend/data/documents/
finagent> /init list
```

## Summary

The `/init` command is a powerful tool for improving search accuracy by adding structured metadata to documents. Always initialize documents before indexing for best results!

**Quick Reference:**
- `/init` - List all documents
- `/init <filename>` - Initialize specific document
- Fill in metadata through interactive wizard
- Run `/reindex` to apply metadata
- Enjoy improved search accuracy!
