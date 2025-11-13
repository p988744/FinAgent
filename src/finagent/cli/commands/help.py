"""Help command handler."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def show_help():
    """Display help information."""

    help_text = """
# FinAgent CLI 指令說明

## 基本指令

| 指令 | 說明 |
|------|------|
| `/help`, `/h`, `/?` | 顯示此說明 |
| `/exit`, `/quit`, `/q!` | 離開程式 |
| `/clear`, `/cls` | 清除螢幕 |

## 查詢指令

| 指令 | 說明 |
|------|------|
| `/query <文字>`, `/q <文字>` | 執行法律研究查詢 |
| `<直接輸入文字>` | 直接輸入查詢（自動使用 /query） |

**範例：**
```
/query 玉山銀行洗錢防制裁罰
2020年金管會裁罰案件
國泰世華銀行法規違規
```

## 歷史與結果

| 指令 | 說明 |
|------|------|
| `/history`, `/hist` | 顯示查詢歷史 |
| `/stats` | 顯示查詢統計（成本、成功率、趨勢） |
| `/stats <天數>` | 顯示最近 N 天的統計 |
| `/citations`, `/cite` | 顯示最後查詢的引用清單 |
| `/cite <編號>` | 查看特定引用詳情（尚未實作） |

## 文件管理

| 指令 | 說明 |
|------|------|
| `/init` | 顯示文件清單 |
| `/init <檔名>` | 使用 LLM 自動分析並初始化文件元資料 |
| `/init <檔名> --manual` | 手動輸入文件元資料（6步驟精靈） |
| `/reindex` | 重新索引文件（會用 LLM 提示初始化未設定的文件） |
| `/reindex --clear` | 清空並重新建立完整索引 |
| `/reindex --skip-init` | 跳過初始化提示，直接索引 |

## 設定與管理

| 指令 | 說明 |
|------|------|
| `/config` | 顯示目前 LLM 設定 |
| `/config llm` | 設定 LLM (OpenAI 或本地 LLM) |
| `/export <格式>` | 匯出結果 (markdown, json) |

## 快捷鍵

- `ESC` - 取消長時間執行的任務（如 LLM 分析）
- `Ctrl+C` - 強制中斷當前操作
- `↑/↓` - 瀏覽歷史指令
- `Tab` - 自動完成指令

## 提示

1. 使用 **繁體中文** 進行查詢以獲得最佳結果
2. 可以指定特定銀行、日期範圍或監管機構
3. 查詢結果包含正式法律引用和信心評分
4. 所有事實陳述都有來源引用
    """

    console.print(Panel(Markdown(help_text), border_style="cyan", title="說明", padding=(1, 2)))
