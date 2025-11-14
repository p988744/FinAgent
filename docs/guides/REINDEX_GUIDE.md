# Reindex Guide - How to Use /reindex Command

## The Problem You Encountered

When you ran `/reindex`, it stopped at 11% during the **LLM metadata initialization phase**. This phase uses LLM to analyze each document and create enhanced metadata, which is:
- ⏰ **Slow**: ~1-2 seconds per document × 492 = ~8-16 minutes
- 💰 **Expensive**: ~492 LLM API calls
- ❌ **Interruptible**: You pressed Ctrl+C at 11%

## Solution: Use `--skip-init` Flag

```bash
finagent> /reindex --skip-init
```

This will:
- ✅ Skip the LLM metadata initialization phase
- ✅ Index all 492 documents directly to vector DB
- ✅ Create minimal metadata in database (with my fix!)
- ⚡ Fast: ~2-5 minutes for 492 documents

## Three Ways to Use /reindex

### Option 1: Fast Reindex (Recommended for Your Case)

```bash
finagent> /reindex --skip-init
```

**What happens:**
1. Loads 492 documents from filesystem
2. Skips LLM metadata initialization
3. Indexes all documents to vector DB
4. **Creates minimal metadata in database** (doc_id, filename, "未分類", indexed=True, chunk_count)
5. Done! ~2-5 minutes

**After this:**
- ✅ All 492 documents in database with `indexed=1`
- ✅ All ~2,858+ chunks in vector DB for search
- ✅ Can query: "玉山銀行洗錢防制裁罰"
- ⚠️ Metadata is basic ("未分類" type, no keywords)

### Option 2: Full Reindex with LLM Metadata (Slow but Rich Metadata)

```bash
finagent> /reindex
```

**What happens:**
1. Loads 492 documents from filesystem
2. **Uses LLM to analyze each document** (~8-16 minutes, ~$5-10 USD)
3. Creates enhanced metadata (description, keywords, document_type, etc.)
4. Indexes all documents to vector DB
5. Saves enhanced metadata to database

**After this:**
- ✅ All 492 documents in database with enhanced metadata
- ✅ All ~2,858+ chunks in vector DB
- ✅ Rich metadata for better filtering/search
- ⏰ Takes 8-16 minutes
- 💰 Costs ~$5-10 USD in LLM API calls

### Option 3: Clear and Rebuild

```bash
finagent> /reindex --clear
```

**What happens:**
1. **Clears all existing indexes and metadata** (asks for confirmation)
2. Then runs full reindex with LLM metadata initialization
3. Rebuilds everything from scratch

**Use this when:**
- You want to start fresh
- Vector DB and database are out of sync
- You changed document processing logic

## Recommended Workflow

### For Your Current Situation:

```bash
# Step 1: Fast reindex to get everything indexed
finagent> /reindex --skip-init

# Step 2 (Optional): Later, add enhanced metadata to specific documents
finagent> /init
# Select specific important documents to analyze with LLM
```

This way:
- ✅ You get all 492 documents indexed quickly (~5 minutes)
- ✅ All documents searchable immediately
- ✅ Can selectively add enhanced metadata later

### For Future Clean Setup:

```bash
# Option A: Fast setup (minimal metadata)
finagent> /reindex --skip-init

# Option B: Rich setup (enhanced metadata, but slow)
finagent> /reindex
```

## Verification After Reindex

After running `/reindex --skip-init`, verify your databases:

```bash
# Check document count
sqlite3 data/finagent.db "SELECT COUNT(*) FROM documents;"
# Expected: 492

# Check indexed status
sqlite3 data/finagent.db "SELECT indexed, COUNT(*) FROM documents GROUP BY indexed;"
# Expected: 1 | 492 (all indexed)

# Sample documents
sqlite3 -header -column data/finagent.db "SELECT filename, document_type, indexed, chunk_count FROM documents LIMIT 10;"
# Expected: All with indexed=1, document_type='未分類'
```

Or use the verification script:
```bash
./verify_reindex.sh
```

## Expected Output

### With `--skip-init`:

```
finagent> /reindex --skip-init

🚀 開始重新索引文件...

📄 載入文件...
✅ 找到 492 個文件

🔍 建立索引...
📄 已索引: 0001_20230101_金管會_玉山銀行.txt... (5 chunks)
📄 已索引: 0002_20230102_金管會_國泰世華.txt... (6 chunks)
...
✅ 完成！已索引 492 個文件，建立 2858 個文本片段
⏭️  跳過 0 個已索引文件
```

### Without `--skip-init` (with LLM):

```
finagent> /reindex

🚀 開始重新索引文件...

📄 載入文件...
✅ 找到 492 個文件

🤖 發現 492 個未初始化的文件
使用 LLM 自動分析並初始化元資料...
提示: 按 Ctrl+C 取消整個操作

🤖 分析: 0001_20230101_金管會_玉山銀行.txt...  1%
🤖 分析: 0002_20230102_金管會_國泰世華.txt...  2%
...
✅ 初始化完成！已分析 492 個文件

🔍 建立索引...
📋 已索引: 0001_20230101_金管會_玉山銀行.txt... (5 chunks)
📋 已索引: 0002_20230102_金管會_國泰世華.txt... (6 chunks)
...
✅ 完成！已索引 492 個文件，建立 2858 個文本片段
```

## Database Schema After Reindex

### With `--skip-init` (Minimal Metadata):

```sql
-- Example document record
{
  "doc_id": "doc_玉山銀行_洗錢防制裁罰_2020_e11b9d82",
  "filename": "玉山銀行_洗錢防制裁罰_2020.txt",
  "file_path": "/Users/.../data/documents/裁罰歷史資料/玉山銀行_洗錢防制裁罰_2020.txt",
  "description": "Auto-indexed document: 玉山銀行_洗錢防制裁罰_2020.txt",
  "document_type": "未分類",  // "Uncategorized"
  "keywords": [],
  "indexed": true,
  "chunk_count": 5
}
```

### With LLM Metadata (Enhanced):

```sql
-- Example document record
{
  "doc_id": "doc_玉山銀行_洗錢防制裁罰_2020_e11b9d82",
  "filename": "玉山銀行_洗錢防制裁罰_2020.txt",
  "file_path": "/Users/.../data/documents/裁罰歷史資料/玉山銀行_洗錢防制裁罰_2020.txt",
  "description": "金管會對玉山銀行因洗錢防制缺失開罰的裁罰文件",
  "document_type": "裁罰書",
  "keywords": ["玉山銀行", "洗錢防制", "金管會", "裁罰"],
  "issuing_authority": "金管會",
  "related_institutions": ["玉山商業銀行"],
  "penalty_amount": "2500萬元",
  "violation_types": ["洗錢防制法違規"],
  "indexed": true,
  "chunk_count": 5
}
```

## Summary

| Command | Speed | Cost | Metadata Quality | When to Use |
|---------|-------|------|------------------|-------------|
| `/reindex --skip-init` | ⚡ Fast (~5 min) | 💰 Free | Basic | **First time setup, quick index** |
| `/reindex` | 🐌 Slow (~15 min) | 💰💰 $5-10 | Rich | Full metadata needed |
| `/reindex --clear` | 🐌 Slow | 💰💰 $5-10 | Rich | Start fresh, rebuild all |

## Next Steps

**Run this command now:**

```bash
finagent> /reindex --skip-init
```

This will:
1. Index all 492 documents (~5 minutes)
2. Save all documents to database with minimal metadata
3. Make all documents searchable
4. Allow you to start querying immediately!

After indexing completes, try a query:
```bash
finagent> 玉山銀行洗錢防制裁罰
```

---

**Date:** 2025-11-13
**Author:** Claude Code
