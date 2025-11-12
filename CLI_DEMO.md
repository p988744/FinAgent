# FinAgent CLI Demo

## Visual Tour of the REPL Interface

### 1. Starting the REPL

```bash
$ uv run finagent
```

### 2. Welcome Screen

```
╭────────────────────────────────────────────────────────────────╮
│                                                                │
│  # FinAgent - 法律研究代理系統                                  │
│                                                                │
│  歡迎使用 FinAgent 互動式命令列界面！                          │
│                                                                │
│  **功能：**                                                    │
│  - 搜尋台灣銀行裁罰案件                                        │
│  - 分析法規執行行動                                            │
│  - 檢索法律判例                                                │
│                                                                │
│  **指令：**                                                    │
│  - 直接輸入查詢或使用 `/query <文字>`                          │
│  - `/help` - 顯示所有可用指令                                  │
│  - `/history` - 查看查詢歷史                                   │
│  - `/exit` - 離開程式                                          │
│                                                                │
│  **範例查詢：**                                                │
│  ```                                                           │
│  玉山銀行洗錢防制裁罰                                          │
│  2020年金管會裁罰案件                                          │
│  國泰世華銀行法規違規                                          │
│  ```                                                           │
│                                                                │
╰────────────────────────────────────────────────────────────────╯

finagent>
```

### 3. Making a Query

```bash
finagent> 玉山銀行洗錢防制裁罰
```

**Loading State:**
```
正在處理查詢... ⠋
```

### 4. Query Results (Rich Format)

```
╭─────────────────────── 執行摘要 ───────────────────────╮
│ 玉山商業銀行於民國109年因洗錢防制內控缺失，遭金管會│
│ 重罰新台幣2.5億元。此案為當年度金融業最高罰款，主  │
│ 要違規事項包括客戶盡職調查不確實、可疑交易監控系統│
│ 缺陷，以及內部控制機制失靈。                        │
╰────────────────────────────────────────────────────────╯

關鍵發現 ● ● ●

  • 裁罰金額: 新台幣2.5億元 [引用1，第3頁]
  • 違規類型: 洗錢防制法第6條 [引用1]
  • 裁罰日期: 民國109年9月15日 [引用2]
  • 主要缺失: 客戶盡職調查不確實、可疑交易監控系統缺陷 [引用1，第四章]
  • 後續處分: 要求6個月內完成改善 [引用1]

╭─────────────────────── 詳細分析 ───────────────────────╮
│                                                        │
│ ## 違規事實                                            │
│                                                        │
│ 根據金管會裁罰書（金管銀法字第10900123456號），玉山 │
│ 商業銀行主要違規事項如下：                             │
│                                                        │
│ 1. **客戶盡職調查（CDD）缺失**                        │
│    - 未能確實執行加強客戶審查（EDD）                  │
│    - 高風險客戶身分驗證程序不足                       │
│    - 實質受益人資訊更新不及時                         │
│                                                        │
│ 2. **可疑交易監控系統**                               │
│    - 警示參數設定不當，導致漏報                       │
│    - 人工審查機制不健全                               │
│    - 未能即時申報可疑交易                             │
│                                                        │
│ 3. **內部控制缺失**                                   │
│    - 洗錢防制專責人員配置不足                         │
│    - 教育訓練不完整                                   │
│    - 稽核機制未能及時發現缺失                         │
│                                                        │
│ ## 法律依據                                            │
│                                                        │
│ - 洗錢防制法第6條：金融機構應建立洗錢防制內控機制    │
│ - 銀行法第125條：主管機關得對違法銀行處以罰鍰        │
│                                                        │
│ ## 影響評估                                            │
│                                                        │
│ 此案對玉山銀行造成重大影響，包括財務損失、聲譽受損，│
│ 以及需要投入大量資源改善內控系統。                     │
│                                                        │
╰────────────────────────────────────────────────────────╯

判例比較

┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ 案件         ┃ 日期       ┃ 裁罰金額   ┃ 違規類型     ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 玉山銀行     │ 2020-09-15 │ 2.5億元    │ 洗錢防制     │
│ 國泰世華銀行 │ 2020-03-10 │ 1.5億元    │ 洗錢防制     │
│ 兆豐銀行     │ 2019-08-20 │ 1.8億元    │ 洗錢防制     │
└──────────────┴────────────┴────────────┴──────────────┘

引用清單 (3 個來源)

[1] 金管會裁罰書 - 金管銀法字第10900123456號
    enforcement_document | primary | 2020-09-15
    https://www.fsc.gov.tw/ch/home.jsp?id=96&...

[2] 最高法院判決 - 110年台上字第1234號
    judgment | primary | 2021-03-20
    https://law.judicial.gov.tw/...

[3] 洗錢防制法第6條
    statute | primary | 2020-01-01
    https://law.moj.gov.tw/...

╭─────────────────────── 信心評分 ───────────────────────╮
│ ████████████████░░░░ 高 (80%)                          │
│ 基於多個主要來源，所有關鍵事實已驗證                   │
╰────────────────────────────────────────────────────────╯

╭─────────────────────── 限制說明 ───────────────────────╮
│ 本分析基於公開資訊，實際裁罰內容以金管會正式裁罰書為│
│ 準。部分內部改善措施細節未能取得，僅能根據公開資訊│
│ 推論。                                                  │
╰────────────────────────────────────────────────────────╯

處理時間: 12.34 秒

finagent>
```

### 5. Viewing History

```bash
finagent> /history
```

**Output:**

```
查詢歷史
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ #  ┃ 查詢                             ┃ 時間               ┃ 信心   ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 1  │ 玉山銀行洗錢防制裁罰             │ 2025-01-12 14:30:45│ 80%    │
│ 2  │ 國泰世華銀行法規違規             │ 2025-01-12 14:35:20│ 75%    │
│ 3  │ 2020年金管會裁罰案件             │ 2025-01-12 14:40:15│ 85%    │
└────┴──────────────────────────────────┴────────────────────┴────────┘

finagent>
```

### 6. Viewing Citations

```bash
finagent> /citations
```

**Output:**

```
引用清單 (3 個來源):

[1] 金管會裁罰書 - 金管銀法字第10900123456號
    類型: enforcement_document
    權威: primary
    日期: 2020-09-15
    網址: https://www.fsc.gov.tw/ch/home.jsp?id=96&...

[2] 最高法院判決 - 110年台上字第1234號
    類型: judgment
    權威: primary
    日期: 2021-03-20
    網址: https://law.judicial.gov.tw/...

[3] 洗錢防制法第6條
    類型: statute
    權威: primary
    日期: 2020-01-01
    網址: https://law.moj.gov.tw/...

finagent>
```

### 7. Getting Help

```bash
finagent> /help
```

**Output:**

```
╭─────────────────────── 說明 ───────────────────────────╮
│                                                        │
│  # FinAgent CLI 指令說明                              │
│                                                        │
│  ## 基本指令                                          │
│                                                        │
│  | 指令 | 說明 |                                       │
│  |------|------|                                      │
│  | `/help`, `/h`, `/?` | 顯示此說明 |                 │
│  | `/exit`, `/quit`, `/q!` | 離開程式 |              │
│  | `/clear`, `/cls` | 清除螢幕 |                      │
│                                                        │
│  ## 查詢指令                                          │
│                                                        │
│  | 指令 | 說明 |                                       │
│  |------|------|                                      │
│  | `/query <文字>`, `/q <文字>` | 執行法律研究查詢 | │
│  | `<直接輸入文字>` | 直接輸入查詢（自動使用 /query）│
│                                                        │
│  **範例：**                                           │
│  ```                                                  │
│  /query 玉山銀行洗錢防制裁罰                          │
│  2020年金管會裁罰案件                                 │
│  國泰世華銀行法規違規                                 │
│  ```                                                  │
│                                                        │
│  [... more help content ...]                          │
│                                                        │
╰────────────────────────────────────────────────────────╯

finagent>
```

### 8. Viewing Configuration

```bash
finagent> /config
```

**Output:**

```
系統設定
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 設定項目   ┃ 值                               ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ API 端點   │ http://localhost:8000            │
│ OpenAI 模型│ gpt-4-turbo-preview              │
│ 嵌入模型   │ text-embedding-3-small           │
│ 環境       │ development                      │
│ 日誌層級   │ INFO                             │
└────────────┴──────────────────────────────────┘

finagent>
```

### 9. Auto-completion Demo

```bash
finagent> /<Tab>

# Shows all available commands:
/help  /h  /?  /query  /q  /history  /hist  /clear  /cls
/citations  /cite  /export  /config  /exit  /quit  /q!

finagent> /h<Tab>
# Completes to:
finagent> /help
```

### 10. Exiting the REPL

```bash
finagent> /exit

再見！感謝使用 FinAgent。

$
```

## Single Query Mode Demo

### Basic Query

```bash
$ uv run finagent query "玉山銀行洗錢防制裁罰"

# Same rich output as REPL mode
╭─────────────────────── 執行摘要 ───────────────────────╮
│ ...                                                    │
╰────────────────────────────────────────────────────────╯
```

### JSON Output

```bash
$ uv run finagent query "玉山銀行" --format json

{
  "executive_summary": "玉山商業銀行於民國109年因洗錢防制內控缺失...",
  "key_findings": [
    "裁罰金額: 新台幣2.5億元 [引用1，第3頁]",
    "違規類型: 洗錢防制法第6條 [引用1]"
  ],
  "detailed_analysis": "...",
  "citations": [
    {
      "title": "金管會裁罰書 - 金管銀法字第10900123456號",
      "type": "enforcement_document",
      "authority": "primary",
      "url": "https://www.fsc.gov.tw/...",
      "date": "2020-09-15"
    }
  ],
  "confidence_score": 0.8,
  "confidence_level": "HIGH/高",
  "confidence_explanation": "基於多個主要來源，所有關鍵事實已驗證",
  "processing_time": 12.34
}
```

### Markdown Output

```bash
$ uv run finagent query "國泰世華銀行" --format markdown

# 法律研究結果

## 執行摘要

國泰世華商業銀行於民國109年3月因洗錢防制缺失，遭金管會裁罰...

## 關鍵發現

- 裁罰金額: 新台幣1.5億元 [引用1，第3頁]
- 違規類型: 洗錢防制法第6條 [引用1]
...

## 詳細分析

### 違規事實
...

## 引用清單 (3 個來源)

### [1] 金管會裁罰書
- **類型**: enforcement_document
- **權威**: primary
...
```

### Advanced Usage - Piping

```bash
# Extract all citation titles
$ uv run finagent query "玉山銀行" --format json | jq '.citations[].title'

"金管會裁罰書 - 金管銀法字第10900123456號"
"最高法院判決 - 110年台上字第1234號"
"洗錢防制法第6條"

# Count citations
$ uv run finagent query "國泰世華" --format json | jq '.citations | length'

3

# Get confidence score
$ uv run finagent query "台新銀行" --format json | jq '.confidence_score'

0.85

# Save to file
$ uv run finagent query "2020年裁罰" --format markdown > report.md
```

## Color Scheme

The CLI uses color coding to enhance readability:

- **Cyan** (`#00aaaa`): Titles, headers, system messages
- **Green** (`#00aa00`): Primary sources, high confidence, success messages
- **Yellow** (`#aaaa00`): Secondary sources, medium confidence, warnings
- **Red** (`#aa0000`): Low confidence, errors
- **Blue** (`#0000aa`): Tertiary sources, links
- **White** (`#ffffff`): Main content, citations
- **Dim/Gray**: Metadata, timestamps, processing info

## Keyboard Shortcuts Summary

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel current operation (doesn't exit) |
| `Ctrl+D` | Exit REPL |
| `↑` | Previous command in history |
| `↓` | Next command in history |
| `Tab` | Auto-complete command |
| `Ctrl+R` | Search command history |
| `Enter` | Execute command/query |

## Command Aliases Quick Reference

| Command | Aliases | Example |
|---------|---------|---------|
| `/help` | `/h`, `/?` | `/h` |
| `/query` | `/q` | `/q 玉山銀行` |
| `/history` | `/hist` | `/hist` |
| `/citations` | `/cite` | `/cite` |
| `/clear` | `/cls` | `/cls` |
| `/exit` | `/quit`, `/q!` | `/q!` |

## Tips for Best Experience

1. **Use Traditional Chinese** for queries - optimized for 繁體中文
2. **Be specific** - include institution names, dates, violation types
3. **Check citations** - verify source authority (green = primary)
4. **Use history** - navigate with ↑/↓ to repeat/modify queries
5. **Try auto-complete** - press Tab after `/` to see all commands
6. **Pipe JSON output** - for programmatic processing with jq
7. **Save important results** - use `--format markdown > file.md`

---

**Ready to try it yourself?**

```bash
cd backend
uv sync
uv run finagent
```

Type your first query in Traditional Chinese and explore Taiwan legal research! 🎉
