# LLM-Based Document Metadata Generation

## Overview

The `/init` command now uses **LLM (Large Language Model)** to automatically analyze documents and extract metadata. This dramatically improves the user experience by reducing manual input from ~2 minutes per document to ~10-20 seconds.

## Key Features

✅ **Automatic Analysis**: LLM reads document content and extracts metadata
✅ **Smart Extraction**: Identifies document type, dates, institutions, penalties
✅ **Review & Confirm**: User reviews generated metadata before saving
✅ **Fallback Option**: Manual input still available with `--manual` flag
✅ **Traditional Chinese**: Optimized for Taiwan legal documents

## How It Works

### 1. LLM-Based Initialization (Default)

```bash
finagent> /init 玉山銀行洗錢防制裁罰.txt

🤖 使用 LLM 分析文件中...
文件: 玉山銀行洗錢防制裁罰.txt

✓ LLM 已生成元資料

文件: 玉山銀行洗錢防制裁罰.txt
描述: 金管會針對玉山商業銀行洗錢防制內控缺失，於2020年9月15日開罰2.5億元
類型: 裁罰書
關鍵字: 玉山銀行, 洗錢防制, 裁罰, 金管會, 2.5億元
日期: 2020-09-15
發布機關: 金管會
相關機構: 玉山商業銀行, 玉山銀行
裁罰金額: 2.5億元
違規類型: 洗錢防制, 法規遵循

是否要儲存這些元資料？ [Y/n]: y

✅ 元資料已儲存
📖 更新文件目錄...
✅ 文件目錄已更新: TABLE_OF_CONTENTS.md
```

### 2. Manual Input Mode (Optional)

If you prefer manual input or LLM fails:

```bash
finagent> /init 文件.txt --manual

# Goes through 6-step manual wizard
步驟 1/6: 文件描述
步驟 2/6: 文件類型
步驟 3/6: 關鍵字
...
```

## What LLM Extracts

The LLM analyzes document content and extracts:

| Field | Description | Example |
|-------|-------------|---------|
| **description** | 1-2 sentence summary | "金管會針對玉山商業銀行洗錢防制內控缺失開罰2.5億元" |
| **document_type** | Document category | 裁罰書, 判決書, 法規條文 |
| **keywords** | 5-10 key terms | 玉山銀行, 洗錢防制, 裁罰, 金管會 |
| **date** | Document date (YYYY-MM-DD) | 2020-09-15 |
| **issuing_authority** | Authority | 金管會, 中央銀行, 最高法院 |
| **related_institutions** | Banks/institutions | 玉山商業銀行, 玉山銀行 |
| **penalty_amount** | Penalty (if applicable) | 2.5億元 |
| **violation_types** | Violation categories | 洗錢防制, 內線交易, 法規遵循 |

## LLM Configuration

The system uses the LLM configured in `/config llm`:

### OpenAI (Default)
```
Model: gpt-4o-mini (from .env)
Temperature: 0.0 (deterministic)
Output: Structured JSON
```

### Local LLM (Ollama)
```
Model: qwen2.5:7b (or configured model)
Base URL: http://localhost:11434/v1
Output: Structured JSON
```

## Workflow Integration

### During `/init`

```bash
# Default: LLM-based
finagent> /init document.txt
🤖 LLM analyzes → Shows results → Confirm → Save

# Manual fallback
finagent> /init document.txt --manual
📝 6-step wizard → Manual input → Save
```

### During `/reindex`

When reindexing, uninitialized documents are automatically prompted with **LLM initialization**:

```bash
finagent> /reindex

📄 載入文件...
✅ 找到 3 個文件

發現 2 個未初始化的文件
建議先初始化文件描述以提升檢索準確度

文件: document1.txt
是否要初始化此文件？ [Y/n]: y

🤖 使用 LLM 分析文件中...
✓ LLM 已生成元資料
[Shows generated metadata]
是否要儲存這些元資料？ [Y/n]: y
✅ 元資料已儲存

文件: document2.txt
是否要初始化此文件？ [Y/n]: n
跳過初始化，將以原始文件內容索引

🔍 建立索引...
📋 已索引: document1.txt (45 chunks)  ← with metadata
📄 已索引: document2.txt (38 chunks)  ← without metadata
```

## Benefits

### 1. **Time Savings**
- **Before**: ~2 minutes manual input per document
- **After**: ~10-20 seconds LLM + review
- **Savings**: 85-90% reduction in time

### 2. **Accuracy**
- LLM extracts precise dates, amounts, institutions from content
- Consistent keyword selection
- Proper document type classification

### 3. **Consistency**
- Standardized extraction logic
- Less human error
- Better metadata quality

### 4. **User Experience**
- Simple workflow: select document → confirm → done
- No need to remember 6-step wizard
- Still allows manual override when needed

## Error Handling

### LLM Analysis Fails

If LLM fails (network issue, API error, etc.):

```bash
❌ LLM 分析失敗: Connection timeout
提示: 您可以使用 /init --manual 手動輸入元資料
```

**Solutions**:
1. Check internet connection (for OpenAI)
2. Check Ollama is running (for local LLM)
3. Use manual mode: `/init document.txt --manual`
4. Skip initialization: answer "n" during `/reindex`

### Invalid Metadata Generated

If LLM generates invalid data (wrong format, missing fields):

```bash
❌ LLM 分析失敗: Invalid date format
提示: 您可以使用 /init --manual 手動輸入元資料
```

The system validates all generated metadata before showing it to you.

## Prompt Engineering

The LLM uses a carefully crafted system prompt:

```
你是一個專業的法律文件分析助手，專門分析台灣的金融監管文件。

你的任務是：
1. 閱讀文件內容
2. 提取關鍵資訊
3. 以結構化的 JSON 格式回傳元資料

注意事項：
- description: 用1-2句話精確描述文件的核心內容
- document_type: 必須從提供的選項中選擇最符合的類型
- keywords: 提取5-10個最重要的關鍵字
- date: 轉換為 YYYY-MM-DD 格式（民國年份請轉換為西元年）
- issuing_authority: 識別發布機關
- related_institutions: 提取所有相關的銀行或金融機構名稱
- penalty_amount: 提取裁罰金額（保留原始格式）
- violation_types: 識別違規類型
```

## Advanced Usage

### Batch Processing with LLM

Initialize multiple documents efficiently:

```bash
# List all uninitialized documents
finagent> /init

# During reindex, LLM will prompt for each
finagent> /reindex
# Answer "y" for documents you want to auto-initialize
# Answer "n" for documents you want to skip

# Skip all prompts
finagent> /reindex --skip-init
```

### Reviewing Generated Metadata

Always review LLM output before confirming:

✅ **Check**:
- Description accurately summarizes content
- Date format is correct (YYYY-MM-DD)
- Penalty amount matches document
- Related institutions are complete

❌ **If incorrect**: Answer "n" and use manual mode:
```bash
finagent> /init document.txt --manual
```

### Updating Existing Metadata

If document already has metadata, LLM will prompt to update:

```bash
文件 'document.txt' 已有初始化資料
描述: 舊的描述內容

是否要更新？ [y/N]: y

🤖 使用 LLM 分析文件中...
[Generates new metadata]
```

## Cost Considerations

### OpenAI Pricing (gpt-4o-mini)

- **Input**: ~$0.15 per 1M tokens
- **Output**: ~$0.60 per 1M tokens

**Per document** (assuming 4000 tokens input, 500 tokens output):
- Input: 4000 tokens × $0.15/1M = $0.0006
- Output: 500 tokens × $0.60/1M = $0.0003
- **Total: ~$0.0009 USD (~NT$0.03) per document**

**For 100 documents**: ~NT$3

### Local LLM (Free)

If using Ollama with local models:
- **Cost**: Free (runs on your hardware)
- **Speed**: Depends on your GPU/CPU
- **Privacy**: Data stays local

## Troubleshooting

### Problem: LLM takes too long

**Cause**: Large document or slow model

**Solution**:
- Content is automatically truncated to 4000 chars
- Consider using faster model (gpt-4o-mini vs gpt-4o)
- Use local LLM with smaller model

### Problem: Generated metadata is incomplete

**Cause**: Document content doesn't contain all fields

**Expected**: Not all documents have all fields
- Legal regulations may not have "penalty_amount"
- News articles may not have "issuing_authority"

**Action**: Review and confirm anyway - partial metadata is still useful

### Problem: Wrong document type selected

**Cause**: Ambiguous document content

**Solution**:
1. Reject generated metadata (answer "n")
2. Use manual mode: `/init document.txt --manual`
3. Select correct document type manually

### Problem: Date not extracted

**Cause**: Date format in document is non-standard

**Examples**:
- "民國109年9月15日" → Should convert to "2020-09-15"
- "2020/9/15" → Should convert to "2020-09-15"
- "去年九月" → Cannot extract (no year)

**Solution**: LLM should handle most formats, but if missing, use manual mode

## Comparison: LLM vs Manual

| Aspect | LLM Mode | Manual Mode |
|--------|----------|-------------|
| **Time** | 10-20 seconds | 2 minutes |
| **Accuracy** | High (with review) | High (if careful) |
| **Ease** | Very easy | Requires attention |
| **Cost** | ~NT$0.03/doc | Free |
| **Best for** | Most documents | Edge cases, validation |

## Recommended Workflow

### For New Documents

```bash
1. Copy documents to data/documents/
2. Run: finagent> /reindex
3. Answer "y" for LLM initialization
4. Review generated metadata
5. Confirm if looks good
6. Done! Documents indexed with metadata
```

### For Existing Documents

```bash
# Update metadata with LLM
finagent> /init document.txt
是否要更新？ y
[Review new metadata]
是否要儲存這些元資料？ y

# Reindex to apply
finagent> /reindex
```

## Summary

The LLM-based metadata generation feature:

✅ **Saves time**: 85-90% faster than manual input
✅ **Maintains quality**: High accuracy with review step
✅ **Flexible**: Can fallback to manual mode
✅ **Integrated**: Works seamlessly with `/reindex`
✅ **Cost-effective**: ~NT$0.03 per document (OpenAI) or free (local)

**Default behavior**: `/init` now uses LLM
**Override**: Use `--manual` flag for manual input
**Best practice**: Let LLM generate → Review → Confirm → Save
