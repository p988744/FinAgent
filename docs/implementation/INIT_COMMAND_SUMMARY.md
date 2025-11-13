# /init Command - Quick Summary

## What It Does

The `/init` command adds descriptive metadata to documents **before** indexing to improve search accuracy and prevent misunderstandings.

## Why You Need It

**Without `/init`:**
- Search relies only on raw text
- May return irrelevant results
- Can miss important documents
- No contextual understanding

**With `/init`:**
- ✅ Better search accuracy (metadata helps filter and rank)
- ✅ Contextual understanding (knows document type, date, authority)
- ✅ Entity recognition (institutions and keywords explicitly tagged)
- ✅ Prevents false positives

## Quick Start

### 1. View Documents
```bash
finagent> /init
```
Shows all documents with initialization status.

### 2. Initialize a Document
```bash
finagent> /init filename.txt
```
Follow the interactive wizard to add:
- Description (required)
- Document type (required)
- Keywords (required)
- Date & authority (optional)
- Related institutions (optional)
- Penalty info (for 裁罰書)

### 3. Reindex
```bash
finagent> /reindex
```
Applies metadata during indexing.

## Example

```bash
finagent> /init 玉山銀行洗錢防制裁罰.txt

# Wizard prompts:
文件描述: 金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元
文件類型: 1  # 裁罰書
關鍵字: 玉山銀行,洗錢防制,裁罰,金管會,2.5億元
文件日期: 2020-09-15
發布機關: 1  # 金管會
相關機構: 玉山商業銀行,玉山銀行
裁罰金額: 2.5億元
違規類型: 1,4  # 洗錢防制, 法規遵循

✓ 文件初始化完成
```

## Workflow

```
Add documents → /init → /reindex → Query
   (1)          (2)       (3)        (4)

1. Copy files to data/documents/
2. Initialize each document's metadata
3. Reindex to apply metadata
4. Run queries with improved accuracy
```

## Metadata Fields

| Field | Required | Example |
|-------|----------|---------|
| Description | Yes | 金管會針對玉山商業銀行洗錢防制內控缺失... |
| Document Type | Yes | 裁罰書 |
| Keywords | Yes | 玉山銀行,洗錢防制,裁罰 |
| Date | No | 2020-09-15 |
| Issuing Authority | No | 金管會 |
| Related Institutions | No | 玉山商業銀行 |
| Penalty Amount | No | 2.5億元 |
| Violation Types | No | 洗錢防制,法規遵循 |

## Document Types

- 裁罰書 (Penalty Document)
- 判決書 (Court Judgment)
- 法規條文 (Laws/Regulations)
- 新聞報導 (News Article)
- 監管公告 (Regulatory Announcement)
- 銀行聲明 (Bank Statement)
- 分析報告 (Analysis Report)
- 其他 (Other)

## How It Improves Search

### Example: Query "2020年玉山銀行裁罰"

**Before /init:**
```
Returns: All documents with "玉山" OR "銀行" OR "裁罰"
May miss: Documents without these exact keywords
False positives: Unrelated documents
```

**After /init:**
```
Returns: Documents matching:
  ✓ Date = 2020
  ✓ Institution = 玉山商業銀行
  ✓ Type = 裁罰書
  ✓ High relevance score
```

## Storage

Metadata is stored in:
```
backend/data/document_metadata.json
```

## Commands

| Command | Description |
|---------|-------------|
| `/init` | Show document list |
| `/init <filename>` | Initialize specific document |
| `/init list` | Show document list (same as `/init`) |
| `/reindex` | Apply metadata during indexing |

## Icons in /reindex

When you run `/reindex`, you'll see:
- 📋 = Document with metadata (initialized)
- 📄 = Document without metadata (not initialized)

## Best Practices

1. **Initialize before indexing**: Always run `/init` before `/reindex`
2. **Be specific**: Include exact dates, amounts, institution names
3. **Be consistent**: Use same names across documents
4. **Fill all fields**: More metadata = better accuracy
5. **Reindex after changes**: Run `/reindex` after adding/updating metadata

## Updating Metadata

To update existing metadata:
```bash
finagent> /init filename.txt
# System detects existing metadata
是否要更新？ yes
# Re-enter all fields
finagent> /reindex --clear
```

## Full Documentation

See [DOCUMENT_INIT_GUIDE.md](DOCUMENT_INIT_GUIDE.md) for complete guide with examples, troubleshooting, and best practices.

## Summary

The `/init` command is essential for maintaining high-quality search results. Always initialize documents before indexing!

**Workflow:**
1. Add documents to `data/documents/`
2. Run `/init filename.txt` for each document
3. Run `/reindex` to apply metadata
4. Enjoy accurate search results!
