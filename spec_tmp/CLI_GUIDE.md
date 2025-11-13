# FinAgent CLI 使用指南

## 概述

FinAgent CLI 是一個互動式命令列介面（REPL），專為台灣法律研究代理系統設計，用於分析銀行裁罰、監管執法行動和法律判例。

## 安裝

確保您已經安裝了專案依賴：

```bash
cd backend
uv sync
```

## 啟動方式

### 1. 互動式 REPL 模式（推薦）

啟動互動式會話：

```bash
uv run finagent
```

或者如果已安裝到環境：

```bash
finagent
```

### 2. 單次查詢模式

直接執行查詢而不進入 REPL：

```bash
uv run finagent query "玉山銀行洗錢防制裁罰"
```

## REPL 模式使用

### 基本指令

啟動 REPL 後，您會看到歡迎訊息和提示符：

```
finagent>
```

#### 查詢指令

**方式 1：直接輸入查詢**
```
finagent> 玉山銀行洗錢防制裁罰
```

**方式 2：使用 /query 指令**
```
finagent> /query 2020年金管會裁罰案件
```

**方式 3：使用縮寫**
```
finagent> /q 國泰世華銀行法規違規
```

#### 說明與導覽

```bash
/help           # 顯示所有可用指令
/h              # help 的縮寫
/?              # help 的替代寫法
```

#### 歷史管理

```bash
/history        # 顯示所有查詢歷史
/hist           # history 的縮寫
```

歷史記錄會顯示：
- 查詢編號
- 查詢文字（最多 60 字）
- 查詢時間
- 信心評分

#### 引用檢視

```bash
/citations      # 顯示最後一次查詢的所有引用
/cite           # citations 的縮寫
```

引用清單包含：
- 引用編號
- 標題
- 類型（裁罰文件、判決書、法規等）
- 權威等級（主要、次要、第三級來源）
- 網址（如有）
- 日期

#### 匯出功能

```bash
/export markdown    # 匯出為 Markdown 格式
/export json        # 匯出為 JSON 格式
```

> **注意**：匯出功能目前尚未完全實作

#### 系統設定

```bash
/config         # 顯示當前系統設定
```

顯示內容：
- API 端點
- OpenAI 模型設定
- 嵌入模型
- 環境（開發/生產）
- 日誌層級

#### 其他指令

```bash
/clear          # 清除螢幕
/cls            # clear 的縮寫

/exit           # 離開 REPL
/quit           # 離開 REPL
/q!             # 強制離開
```

### 快捷鍵

- **Ctrl+C**: 取消當前操作（不會離開 REPL）
- **Ctrl+D**: 離開 REPL
- **↑ / ↓**: 瀏覽歷史指令
- **Tab**: 自動完成指令（輸入 `/` 後按 Tab）

### 自動完成功能

REPL 支援指令自動完成。輸入 `/` 後按 Tab 鍵，會顯示所有可用指令：

```
finagent> /<Tab>
/help  /query  /history  /clear  /citations  /export  /config  /exit
```

## 單次查詢模式

適合腳本化或快速查詢，不需要進入互動式會話。

### 基本語法

```bash
uv run finagent query [OPTIONS] TEXT
```

### 選項

- `-n, --max-results INTEGER`: 最大結果數量（1-50，預設 5）
- `--regulator TEXT`: 按監管機構篩選（FSC, CBC, FTC）
- `--start-date TEXT`: 開始日期（YYYY-MM-DD）
- `--end-date TEXT`: 結束日期（YYYY-MM-DD）
- `-f, --format [rich|json|markdown]`: 輸出格式（預設 rich）

### 範例

**基本查詢**
```bash
uv run finagent query "玉山銀行洗錢防制裁罰"
```

**指定最大結果數**
```bash
uv run finagent query "2020年金管會裁罰案件" --max-results 10
```

**按監管機構篩選**
```bash
uv run finagent query "國泰世華銀行" --regulator FSC
```

**指定日期範圍**
```bash
uv run finagent query "銀行裁罰" --start-date 2020-01-01 --end-date 2020-12-31
```

**JSON 輸出（適合腳本處理）**
```bash
uv run finagent query "玉山銀行" --format json > result.json
```

**Markdown 輸出**
```bash
uv run finagent query "國泰世華銀行" --format markdown > report.md
```

## 查詢結果格式

### Rich 格式（預設）

查詢結果以美觀的終端機格式顯示：

1. **執行摘要**：藍色面板，概述主要發現
2. **關鍵發現**：要點列表，包含內嵌引用（如 [引用1]）
3. **詳細分析**：完整分析，Markdown 格式
4. **判例比較**：表格形式（如有）
5. **引用清單**：所有來源引用，帶編號
6. **信心評分**：視覺化進度條
   - 綠色：高信心（0.8+）
   - 黃色：中信心（0.5-0.8）
   - 紅色：低信心（<0.5）
7. **限制說明**：黃色面板（如有）
8. **處理時間**：灰色文字

### JSON 格式

結構化 JSON 輸出，適合程式處理：

```json
{
  "executive_summary": "...",
  "key_findings": ["...", "..."],
  "detailed_analysis": "...",
  "citations": [
    {
      "title": "...",
      "type": "enforcement_document",
      "authority": "primary",
      "url": "...",
      "date": "2020-09-15"
    }
  ],
  "confidence_score": 0.92,
  "confidence_level": "HIGH/高",
  "confidence_explanation": "...",
  "processing_time": 12.3
}
```

### Markdown 格式

適合生成報告或文件：

```markdown
# 法律研究結果

## 執行摘要
...

## 關鍵發現
- ...
- ...

## 詳細分析
...

## 引用清單 (3 個來源)
### [1] 金管會裁罰書
- **類型**: enforcement_document
- **權威**: primary
...
```

## 範例查詢

### 特定機構查詢

```
玉山銀行洗錢防制裁罰
國泰世華銀行法規違規
台新銀行內線交易案件
```

### 時間範圍查詢

```
2020年金管會裁罰案件
2019-2021年銀行業洗錢防制違規
民國109年裁罰案例
```

### 違規類型查詢

```
洗錢防制法違規案件
內線交易裁罰
資訊揭露違規
不當銷售金融商品
```

### 監管機構查詢

```
金管會銀行業裁罰
中央銀行執法行動
公平會金融業處分
```

### 法規查詢

```
銀行法第125條相關案件
洗錢防制法第6條裁罰
證券交易法內線交易判例
```

## 配置

### 環境變數

CLI 會讀取以下環境變數：

```bash
# 後端 API URL（預設：http://localhost:8000）
export FINAGENT_API_URL=http://localhost:8000

# OpenAI API Key（必需）
export OPENAI_API_KEY=your_api_key_here
```

### 建議設定

在您的 `.bashrc` 或 `.zshrc` 中添加別名：

```bash
# 簡化 finagent 指令
alias fa='uv run finagent'
alias faq='uv run finagent query'

# 常用查詢縮寫
alias fa-help='uv run finagent query --help'
```

使用範例：
```bash
fa                              # 啟動 REPL
faq "玉山銀行"                   # 快速查詢
faq "國泰世華" --format json    # JSON 輸出
```

## 後端整合

### 啟動後端服務

CLI 需要後端 API 服務運行。啟動方式：

**方式 1：使用 uvicorn（開發）**
```bash
cd backend
uv run uvicorn finagent.main:app --reload --host 0.0.0.0 --port 8000
```

**方式 2：使用 Docker Compose**
```bash
docker-compose up
```

### 檢查連線

在 REPL 中，您可以使用 `/config` 指令查看後端連線狀態。如果後端未運行，查詢會失敗並顯示連線錯誤。

## 故障排除

### CLI 無法啟動

**問題**: `ModuleNotFoundError: No module named 'finagent.cli'`

**解決方案**:
```bash
cd backend
uv sync
```

### 後端連線失敗

**問題**: `查詢錯誤: Connection error`

**解決方案**:
1. 確認後端服務已啟動
2. 檢查 `FINAGENT_API_URL` 環境變數
3. 驗證網路連線

```bash
# 測試後端健康狀態
curl http://localhost:8000/health
```

### 查詢超時

**問題**: 查詢處理時間過長

**解決方案**:
1. 縮小查詢範圍
2. 減少 `--max-results` 數量
3. 指定更精確的日期範圍

### 中文顯示問題

**問題**: 中文字元顯示為亂碼

**解決方案**:
1. 確保終端機支援 UTF-8 編碼
2. 設定環境變數：
```bash
export LANG=zh_TW.UTF-8
export LC_ALL=zh_TW.UTF-8
```

## 高級用法

### 管道操作

將查詢結果導向到其他工具：

```bash
# 搜尋特定關鍵字
uv run finagent query "玉山銀行" --format json | jq '.citations[].title'

# 計算引用數量
uv run finagent query "國泰世華" --format json | jq '.citations | length'

# 儲存到檔案
uv run finagent query "2020年裁罰" --format markdown > report_2020.md
```

### 批次查詢

使用 shell 腳本進行批次查詢：

```bash
#!/bin/bash
# batch_query.sh

banks=("玉山銀行" "國泰世華銀行" "台新銀行" "中國信託")

for bank in "${banks[@]}"; do
    echo "查詢 $bank..."
    uv run finagent query "$bank 裁罰" --format json > "${bank}_penalties.json"
done
```

### 與其他工具整合

```bash
# 搭配 watch 持續監控
watch -n 3600 'uv run finagent query "最新裁罰案件" --format markdown'

# 搭配 cron 定期查詢
0 9 * * * uv run finagent query "昨日裁罰案件" --format markdown | mail -s "每日裁罰報告" user@example.com
```

## 開發與擴展

### 添加新指令

1. 在 `backend/src/finagent/cli/commands/` 中創建新的處理器
2. 在 `repl.py` 中的 `handle_command()` 添加指令邏輯
3. 更新 `commands` 列表以支援自動完成

### 自訂格式化器

在 `backend/src/finagent/cli/formatters/` 中添加新的格式化器：

```python
# custom_formatter.py
def format_custom(answer: LegalAnswer) -> str:
    # 您的自訂邏輯
    return formatted_output
```

## 最佳實踐

1. **使用繁體中文查詢**：系統針對繁體中文優化，獲得最佳結果
2. **具體明確**：包含機構名稱、日期範圍和違規類型
3. **檢查引用**：驗證所有引用來源的權威性
4. **保存重要結果**：使用 `/export` 保存研究成果
5. **善用歷史**：使用 `/history` 追蹤查詢軌跡

## 未來功能

計劃中的功能（尚未實作）：

- [ ] 會話持久化（保存/載入會話）
- [ ] 引用詳情查看（`/cite <編號>`）
- [ ] PDF 匯出支援
- [ ] 完整的匯出功能
- [ ] 互動式引用瀏覽
- [ ] 進階篩選選項
- [ ] 多語言支援（英文/中文切換）

## 取得協助

- **指令說明**: 在 REPL 中輸入 `/help`
- **指令用法**: `uv run finagent query --help`
- **版本資訊**: `uv run finagent --version`
- **專案文件**: 參見 `README.md` 和 `QUICKSTART.md`

## 版本資訊

- **目前版本**: 0.1.0-alpha
- **狀態**: 基礎 CLI 完成，核心功能開發中
- **相容性**: Python 3.11+, macOS/Linux/Windows

---

**提示**: 這是一個互動式工具，最好的學習方式是直接使用！啟動 REPL 並嘗試不同的查詢。
