# Automated Reindex with LLM Initialization

## Overview

The `/reindex` command now **automatically initializes** all uninitialized documents with LLM analysis. No more manual confirmations - just run `/reindex` and let it handle everything!

## What Changed

### Before (Manual Confirmation)

```bash
finagent> /reindex

發現 5 個未初始化的文件

文件: document1.txt
是否要初始化此文件？ [Y/n]: y
🤖 分析中...
✓ 已初始化

文件: document2.txt
是否要初始化此文件？ [Y/n]: y
🤖 分析中...
✓ 已初始化

# ... repeat for each document ...
```

❌ **Problems**:
- Need to confirm each document individually
- Slow and tedious for many documents
- Can't leave it running unattended

### After (Automated)

```bash
finagent> /reindex

🤖 發現 5 個未初始化的文件
使用 LLM 自動分析並初始化元資料...
提示: 按 Ctrl+C 取消整個操作

⠋ 🤖 初始化文件元資料... ███████████████░░░ 85%

✅ 初始化完成: 5 個文件

🔍 建立索引... ████████████████████ 100%

✨ 索引完成！
```

✅ **Benefits**:
- Fully automated - no confirmations needed
- Progress bar shows real-time status
- Press Ctrl+C to cancel entire operation
- Much faster for batch operations

## Usage

### Basic Reindex (Recommended)

```bash
finagent> /reindex
```

This will:
1. Load all documents
2. **Auto-initialize uninitialized documents with LLM**
3. Index all documents with metadata
4. Update table of contents

### Skip Initialization

If you want to skip LLM initialization:

```bash
finagent> /reindex --skip-init
```

This will:
1. Load all documents
2. Skip initialization
3. Index with existing metadata only

### Clear and Rebuild

To clear existing index and rebuild:

```bash
finagent> /reindex --clear
```

This will:
1. Clear all existing indexes
2. Auto-initialize uninitialized documents
3. Rebuild complete index

### Combine Flags

```bash
# Clear and skip init
finagent> /reindex --clear --skip-init
```

## Progress Display

### Initialization Phase

```
🤖 發現 10 個未初始化的文件
使用 LLM 自動分析並初始化元資料...
提示: 按 Ctrl+C 取消整個操作

⠋ 🤖 分析: document_005.txt... ████████░░░░ 50%

# Shows:
# - Current document being processed
# - Overall progress percentage
# - Animated spinner
```

### Results Summary

```
✅ 初始化完成: 8 個文件
⚠️  跳過: 2 個文件

# Then continues to indexing...
```

### Indexing Phase

```
🔍 建立索引... ████████████████████ 100%

📋 已索引: doc1.txt (45 chunks)  ← with metadata
📋 已索引: doc2.txt (52 chunks)  ← with metadata
📄 已索引: doc3.txt (38 chunks)  ← without metadata (skipped)
```

Icons:
- 📋 = Document with metadata
- 📄 = Document without metadata

## Cancellation

### Cancel Entire Operation

Press **Ctrl+C** to stop the entire reindex:

```
⠋ 🤖 初始化文件元資料... 45%

# Press Ctrl+C
^C
⏸️  索引已中斷
```

## Error Handling

### LLM Errors

If LLM fails for a document, it's automatically skipped:

```
⠋ 🤖 分析: bad_document.txt...

✗ 失敗: bad_document.txt...

# Continues with next document
```

The document will still be indexed, just without metadata.

### Network Errors

If OpenAI API is unreachable:

```
🤖 發現 5 個未初始化的文件
使用 LLM 自動分析並初始化元資料...

✗ 失敗: document1.txt...
✗ 失敗: document2.txt...

⚠️  跳過: 5 個文件

# Continues to indexing phase
```

All documents will be indexed without metadata.

## Cost Estimation

For automated batch initialization:

| Documents | LLM Calls | Cost (OpenAI gpt-4o-mini) | Time |
|-----------|-----------|---------------------------|------|
| 10 docs | 10 calls | ~NT$0.30 | ~2-3 min |
| 50 docs | 50 calls | ~NT$1.50 | ~10-15 min |
| 100 docs | 100 calls | ~NT$3.00 | ~20-30 min |
| 500 docs | 500 calls | ~NT$15.00 | ~2-3 hours |

**Note**: Cost is per run. Documents already initialized are not re-processed.

## Performance

### Speed

- **Initialization**: ~10-20 seconds per document
- **Indexing**: ~1-2 seconds per document
- **Total**: ~12-22 seconds per uninitialized document

### Parallelization

Currently sequential (one document at a time). Future enhancement:

```python
# Future: Parallel initialization (5 concurrent)
⠋ 🤖 初始化文件元資料... ████████░░░░ 60% (3/5 running)
```

## Table of Contents

After reindex, a **compact, grep-friendly** TOC is automatically generated.

### New Format

```markdown
# 文件目錄

更新: 2025-01-12 17:00
總數: 45 份

## 📊 統計

裁罰書: 25 | 判決書: 12 | 法規條文: 5 | 新聞報導: 3

## 📋 文件索引 (Grep-Friendly)

```
# Format: FILENAME | TYPE | DATE | AUTHORITY | INSTITUTIONS | PENALTY | VIOLATIONS | KEYWORDS
#
玉山銀行洗錢防制裁罰.txt | 裁罰書 | 2020-09-15 | 金管會 | 玉山商業銀行;玉山銀行 | 2.5億元 | 洗錢防制;法規遵循 | 玉山銀行;洗錢防制;裁罰
國泰世華裁罰.txt | 裁罰書 | 2019-03-20 | 金管會 | 國泰世華銀行 | 1.8億元 | 內線交易 | 國泰世華;內線交易;裁罰
```
```

### Grep Examples

```bash
# Find all documents from 2020
grep '2020-' TABLE_OF_CONTENTS.md

# Find all 玉山銀行 documents
grep '玉山' TABLE_OF_CONTENTS.md

# Find all penalties over 2億
grep '2\.._億元\|[3-9]億元\|[0-9][0-9]億元' TABLE_OF_CONTENTS.md

# Find all 洗錢防制 cases
grep '洗錢防制' TABLE_OF_CONTENTS.md

# Find documents from 金管會
grep '金管會' TABLE_OF_CONTENTS.md
```

### Compact Details

```markdown
## 📚 分類明細

### 裁罰書 (25)

- **玉山銀行洗錢防制裁罰.txt** · `2020-09-15` · 金管會 · [玉山商業銀行, 玉山銀行] · 💰2.5億元 · ⚠️洗錢防制, 法規遵循
  > 金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元

- **國泰世華裁罰.txt** · `2019-03-20` · 金管會 · [國泰世華銀行] · 💰1.8億元 · ⚠️內線交易
  > 金管會對國泰世華銀行內線交易案開罰1.8億元
```

**Benefits**:
- Much more compact than before
- One-line-per-document for grep
- Visual icons for quick scanning
- Truncated descriptions (max 100 chars)

## Best Practices

### 1. Regular Reindexing

Run reindex after adding new documents:

```bash
# Add documents
cp *.txt data/documents/

# Reindex (auto-initializes new ones)
finagent> /reindex
```

### 2. Use --skip-init for Testing

When testing or debugging:

```bash
finagent> /reindex --skip-init
```

This is faster and doesn't use LLM API.

### 3. Review Generated Metadata

Check the TOC to verify LLM-generated metadata:

```bash
cat data/TABLE_OF_CONTENTS.md
# or
grep 'document_name' data/TABLE_OF_CONTENTS.md
```

### 4. Manual Override

If LLM generated incorrect metadata:

```bash
# Re-initialize with manual mode
finagent> /init document.txt --manual

# Then reindex to update
finagent> /reindex
```

### 5. Batch Processing

For large batches, run overnight:

```bash
# Copy 500 documents
cp archive/*.txt data/documents/

# Start reindex (takes 2-3 hours)
finagent> /reindex

# Leave it running...
```

## Troubleshooting

### Problem: Initialization takes too long

**Cause**: Many documents to initialize

**Solution**:
- Use `--skip-init` if urgent
- Run during off-hours
- Consider chunking documents into batches

### Problem: Some documents failed

**Cause**: LLM errors or network issues

**Solution**: Documents are automatically skipped and indexed without metadata. You can:
1. Check the TOC to see which documents lack metadata
2. Re-initialize failed documents manually:
   ```bash
   finagent> /init failed_document.txt
   ```

### Problem: Want to stop and resume later

**Action**: Press `Ctrl+C` to stop

**Resume**: Just run `/reindex` again - already initialized documents are skipped!

```bash
# First run (stopped at 50%)
finagent> /reindex
# ... processes 25/50 documents ...
^C

# Later: Resume (skips already initialized)
finagent> /reindex
🤖 發現 25 個未初始化的文件  ← Only remaining documents
```

## Comparison

| Aspect | Old (Manual) | New (Automated) |
|--------|--------------|-----------------|
| **User interaction** | Confirm each document | One command |
| **Speed** | Slow (wait for each) | Fast (automated) |
| **Progress** | None | Real-time progress bar |
| **Cancellation** | Ctrl+C only | Ctrl+C (cancels all) |
| **Error handling** | Stops on error | Auto-skip and continue |
| **Resumable** | No | Yes (skips initialized) |
| **TOC format** | Verbose | Compact & grep-friendly |

## Summary

**New workflow is much simpler:**

```bash
# Before: Multi-step manual process
finagent> /init doc1.txt
# ... 6-step wizard ...
finagent> /init doc2.txt
# ... 6-step wizard ...
finagent> /init doc3.txt
# ... 6-step wizard ...
finagent> /reindex

# After: One automated command
finagent> /reindex
# ✨ Done! All documents auto-initialized and indexed
```

**Key improvements:**
- ⚡ Fully automated initialization
- 📊 Real-time progress display
- ⏸️ Ctrl+C to cancel entire operation
- 📋 Compact, grep-friendly TOC
- ♻️ Resumable (skips already initialized)
- 💰 Cost-effective (~NT$0.03 per document)

Just run `/reindex` and let the system handle the rest!
