# Integrated Init + Reindex Workflow

## Overview

The `/reindex` command now **automatically prompts** you to initialize documents that don't have metadata. This creates a seamless workflow where you don't need to separately run `/init` - it's integrated into the indexing process.

## How It Works

When you run `/reindex`, the system will:

1. ✅ Load all documents from `data/documents/`
2. ✅ Check which documents don't have metadata
3. ✅ **Prompt you to initialize each uninitialized document**
4. ✅ Index documents (with metadata if initialized)

## Example Workflow

```bash
finagent> /reindex

📄 載入文件...
✅ 找到 3 個文件

發現 2 個未初始化的文件
建議先初始化文件描述以提升檢索準確度

文件: 玉山銀行洗錢防制裁罰.txt
是否要初始化此文件？ [Y/n]: y

# Interactive wizard starts
步驟 1/6: 文件描述
文件描述: 金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元

步驟 2/6: 文件類型
請選擇文件類型: 1  # 裁罰書

步驟 3/6: 關鍵字
關鍵字: 玉山銀行,洗錢防制,裁罰,金管會,2.5億元

步驟 4/6: 日期與機關
文件日期: 2020-09-15
請選擇發布機關: 1  # 金管會

步驟 5/6: 相關機構
相關機構: 玉山商業銀行,玉山銀行

步驟 6/6: 裁罰資訊
裁罰金額: 2.5億元
請選擇違規類型: 1,4

✓ 文件初始化完成

文件: 國泰世華銀行裁罰.txt
是否要初始化此文件？ [Y/n]: y

# ... repeat for next document ...

🔍 建立索引...
📋 已索引: 玉山銀行洗錢防制裁罰.txt (58 chunks)
📋 已索引: 國泰世華銀行裁罰.txt (42 chunks)
📄 已索引: 舊文件.txt (35 chunks)

✨ 索引完成！

📊 統計資訊：
  • 索引文件數: 3
  • 總片段數: 135
  • 平均每份文件: 45.0 片段
```

## Icons Explained

During indexing, you'll see different icons:

- **📋** = Document **with** metadata (initialized)
- **📄** = Document **without** metadata (not initialized)

This helps you quickly see which documents have enhanced metadata.

## Skipping Initialization

If you want to skip the initialization prompts and just index everything as-is:

```bash
finagent> /reindex --skip-init
```

Or:

```bash
finagent> /reindex --no-init
```

This is useful when:
- You're in a hurry and want to index quickly
- You plan to initialize documents later
- Documents are temporary and don't need metadata

## Combining Flags

You can combine flags:

```bash
# Clear index and skip init prompts
finagent> /reindex --clear --skip-init

# Clear index with init prompts (default)
finagent> /reindex --clear
```

## Answering Init Prompts

For each uninitialized document, you have two options:

### Option 1: Initialize Now (Recommended)
```
是否要初始化此文件？ [Y/n]: y
```
- Goes through the 6-step wizard
- Adds metadata to improve search accuracy
- Takes 1-2 minutes per document

### Option 2: Skip This Document
```
是否要初始化此文件？ [Y/n]: n
```
- Skips initialization for this document
- Document will be indexed without metadata
- You can initialize it later with `/init filename.txt`

## When to Initialize

**Recommended for:**
- ✅ Important documents (penalties, judgments)
- ✅ Frequently queried documents
- ✅ Primary sources (official documents)
- ✅ Documents with complex content

**Can skip for:**
- ❌ Temporary documents
- ❌ Test files
- ❌ Low-priority documents
- ❌ Documents you'll delete soon

## Best Practices

### 1. Initialize Important Documents First

If you have many documents, initialize the most important ones first:

```bash
# Initialize key documents
finagent> /init 玉山銀行裁罰.txt
finagent> /init 國泰世華裁罰.txt

# Then reindex (will only prompt for remaining documents)
finagent> /reindex
```

### 2. Use --skip-init for Bulk Import

If importing many documents at once:

```bash
# First pass: index everything quickly
finagent> /reindex --clear --skip-init

# Second pass: selectively initialize important documents
finagent> /init important_doc1.txt
finagent> /init important_doc2.txt

# Third pass: reindex with metadata
finagent> /reindex --clear
```

### 3. Update Metadata and Reindex

If you update metadata:

```bash
# Update metadata
finagent> /init filename.txt
是否要更新？ yes

# Reindex to apply changes
finagent> /reindex --clear
```

## Workflow Comparison

### Old Workflow (Manual)
```
1. Add documents
2. Run /init for each document
3. Run /reindex
```

### New Workflow (Integrated)
```
1. Add documents
2. Run /reindex
   → Automatically prompts for init if needed
   → All done!
```

Much simpler! 🎉

## Example: Adding New Documents

### Scenario: You have 3 new penalty documents

```bash
# Step 1: Copy files to data/documents/
cp *.txt backend/data/documents/

# Step 2: Run reindex (it will prompt for each)
finagent> /reindex

發現 3 個未初始化的文件
建議先初始化文件描述以提升檢索準確度

文件: doc1.txt
是否要初始化此文件？ [Y/n]: y
# ... fill in metadata ...
✓ 文件初始化完成

文件: doc2.txt
是否要初始化此文件？ [Y/n]: y
# ... fill in metadata ...
✓ 文件初始化完成

文件: doc3.txt
是否要初始化此文件？ [Y/n]: y
# ... fill in metadata ...
✓ 文件初始化完成

🔍 建立索引...
📋 已索引: doc1.txt (45 chunks)
📋 已索引: doc2.txt (52 chunks)
📋 已索引: doc3.txt (38 chunks)

✨ 索引完成！
```

All 3 documents are now indexed with metadata in a single workflow!

## Keyboard Shortcuts

During init prompts:
- `Enter` = Accept default (Yes)
- `n` + `Enter` = Skip this document
- `Ctrl+C` = Cancel entire reindex operation

## Summary

The integrated `/reindex` command now makes it easy to maintain high-quality metadata:

✅ **Automatic prompts** for uninitialized documents
✅ **Seamless workflow** - no need to separately run `/init`
✅ **Visual feedback** with 📋 and 📄 icons
✅ **Flexible** - can skip with `--skip-init` if needed

**Recommended workflow:**
```bash
# Just run reindex - it will handle everything!
finagent> /reindex
```

That's it! The system will guide you through initializing any documents that need metadata.
