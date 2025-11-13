"""
Interactive REPL (Read-Eval-Print Loop) for FinAgent CLI.
"""

import sys
import uuid
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from finagent.cli.commands.config import handle_config_command
from finagent.cli.commands.help import show_help
from finagent.cli.commands.history import QueryHistory
from finagent.cli.commands.init import handle_init_command
from finagent.cli.commands.query import execute_query
from finagent.cli.commands.reindex import execute_reindex
from finagent.cli.formatters.answer import format_legal_answer
from finagent.cli.formatters.export import export_to_json, export_to_markdown, export_to_text
from finagent.config_manager import get_config_manager
from finagent.database.db import Database

console = Console()


class ReplSession:
    """Interactive REPL session for FinAgent."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())  # Generate unique session ID
        self.history = QueryHistory()
        self.prompt_history = InMemoryHistory()
        self.last_answer = None
        self.last_query = None  # Track last query text for export
        self.session_start = datetime.now()

        # Command completer
        self.commands = [
            "/help",
            "/h",
            "/?",
            "/query",
            "/q",
            "/history",
            "/hist",
            "/clear",
            "/cls",
            "/citations",
            "/cite",
            "/export",
            "/config",
            "/init",
            "/reindex",
            "/exit",
            "/quit",
            "/q!",
        ]
        self.completer = WordCompleter(self.commands, ignore_case=True, sentence=True)

        # Prompt style
        self.prompt_style = Style.from_dict(
            {
                "prompt": "#00aa00 bold",
            }
        )

    def show_welcome(self):
        """Display welcome banner."""
        welcome_text = """
# FinAgent - 法律研究代理系統

歡迎使用 FinAgent 互動式命令列界面！

**功能：**
- 搜尋台灣銀行裁罰案件
- 分析法規執行行動
- 檢索法律判例

**常用指令：**
- 直接輸入查詢或使用 `/query <文字>`
- `/help` - 顯示所有可用指令
- `/config llm` - 設定 LLM (OpenAI 或本地模型)
- `/history` - 查看查詢歷史
- `/reindex` - 重新索引文件
- `/exit` - 離開程式

**範例查詢：**
```
玉山銀行洗錢防制裁罰
2020年金管會裁罰案件
國泰世華銀行法規違規
```
        """
        console.print(Panel(Markdown(welcome_text), border_style="cyan", padding=(1, 2)))
        console.print()

        # Display current configuration
        self.show_current_config()

    def show_current_config(self):
        """Display current LLM and embedding configuration."""
        try:
            config_manager = get_config_manager()

            # Get LLM configuration
            llm_config = config_manager.get_active_llm_config()

            # Get embedding configuration
            embedding_config = config_manager.get_active_embedding_config()

            console.print("[bold cyan]目前配置：[/bold cyan]")
            console.print()

            # Show LLM config source
            if llm_config.get("source") == "database":
                console.print(
                    f"  [green]✓[/green] 使用資料庫預設配置: [bold]{llm_config.get('config_name')}[/bold]"
                )
            else:
                console.print("  [yellow]![/yellow] 使用環境變數配置 (.env)")

            console.print(f"  [dim]LLM 端點:[/dim] {llm_config['base_url']}")
            console.print(f"  [dim]LLM 模型:[/dim] {llm_config['model']}")
            console.print(f"  [dim]溫度:[/dim] {llm_config['temperature']}")
            console.print()
            console.print(f"  [dim]嵌入端點:[/dim] {embedding_config['base_url']}")
            console.print(f"  [dim]嵌入模型:[/dim] {embedding_config['model']}")
            console.print()
            console.print("  [dim]使用 /config 指令可查看或更改配置[/dim]")
            console.print()

        except Exception as e:
            console.print(f"[yellow]警告: 無法載入配置資訊 - {str(e)}[/yellow]")
            console.print()

    def create_prompt_session(self) -> PromptSession:
        """Create prompt_toolkit session."""
        return PromptSession(
            history=self.prompt_history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer,
            style=self.prompt_style,
            enable_history_search=True,
        )

    def parse_command(self, user_input: str) -> tuple[str, str]:
        """
        Parse user input into command and arguments.

        Returns:
            (command, args) tuple
        """
        user_input = user_input.strip()

        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            return command, args
        else:
            # No command prefix - treat as query
            return "/query", user_input

    def handle_command(self, command: str, args: str) -> bool:
        """
        Handle a command.

        Returns:
            True to continue REPL, False to exit
        """
        # Help commands
        if command in ["/help", "/h", "/?"]:
            show_help()
            return True

        # Exit commands
        if command in ["/exit", "/quit", "/q!"]:
            console.print("\n[cyan]再見！感謝使用 FinAgent。[/cyan]\n")
            return False

        # Clear screen
        if command in ["/clear", "/cls"]:
            console.clear()
            self.show_welcome()
            return True

        # Query command
        if command in ["/query", "/q"]:
            if not args:
                console.print("[yellow]請提供查詢文字。[/yellow]")
                console.print("範例: /query 玉山銀行洗錢防制裁罰")
                return True

            self.execute_query(args)
            return True

        # History command
        if command in ["/history", "/hist"]:
            self.show_history()
            return True

        # Citations command
        if command in ["/citations", "/cite"]:
            self.show_citations(args)
            return True

        # Export command
        if command == "/export":
            self.export_results(args)
            return True

        # Config command
        if command == "/config":
            handle_config_command(args)
            return True

        # Init command
        if command == "/init":
            handle_init_command(args)
            return True

        # Reindex command
        if command == "/reindex":
            # Parse flags
            args_lower = args.strip().lower()
            clear = "--clear" in args_lower or "-c" in args_lower or args_lower == "clear"
            skip_init = "--skip-init" in args_lower or "--no-init" in args_lower
            execute_reindex(clear=clear, skip_init=skip_init)
            return True

        # Unknown command
        console.print(f"[red]未知指令: {command}[/red]")
        console.print("輸入 /help 查看可用指令")
        return True

    def execute_query(self, query_text: str):
        """Execute a legal research query."""
        try:
            console.print("\n[cyan]正在處理查詢...[/cyan]\n")

            # Execute query with session ID for database logging
            answer = execute_query(query_text, session_id=self.session_id)

            if answer:
                # Save to in-memory history (for backward compatibility)
                self.history.add(query_text, answer)
                self.last_answer = answer
                self.last_query = query_text  # Track for export

                # Display answer
                format_legal_answer(answer)
            else:
                console.print("[red]查詢失敗，請稍後再試。[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]查詢已取消。[/yellow]")
        except Exception as e:
            console.print(f"[red]錯誤: {str(e)}[/red]")

    def show_history(self):
        """Display query history from database."""
        try:
            # Get history from database (current session)
            db = Database()
            history_entries = db.get_history(limit=50, session_id=self.session_id)

            if not history_entries:
                console.print("[yellow]尚無查詢歷史。[/yellow]")
                return

            table = Table(
                title=f"查詢歷史 (Session: {self.session_id[:8]}...)",
                show_header=True,
                header_style="bold cyan",
            )
            table.add_column("#", style="dim", width=4)
            table.add_column("查詢", style="white", width=50)
            table.add_column("時間", style="cyan", width=20)
            table.add_column("處理時間", style="yellow", width=10)
            table.add_column("成本", style="green", width=10)
            table.add_column("狀態", style="magenta", width=6)

            for idx, entry in enumerate(history_entries, 1):
                # Format processing time
                proc_time = (
                    f"{entry.processing_time_seconds:.1f}s"
                    if entry.processing_time_seconds
                    else "N/A"
                )

                # Format cost
                cost = f"${entry.cost_usd:.4f}" if entry.cost_usd else "$0.00"

                # Format status
                status = "✓" if entry.success else "✗"
                status_style = "green" if entry.success else "red"

                # Parse timestamp
                from datetime import datetime

                if isinstance(entry.created_at, str):
                    timestamp = datetime.fromisoformat(entry.created_at.replace("Z", "+00:00"))
                else:
                    timestamp = entry.created_at

                table.add_row(
                    str(idx),
                    entry.query[:47] + "..." if len(entry.query) > 50 else entry.query,
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    proc_time,
                    cost,
                    f"[{status_style}]{status}[/{status_style}]",
                )

            console.print()
            console.print(table)
            console.print()

            # Show summary
            total_cost = sum(e.cost_usd for e in history_entries if e.cost_usd)
            success_count = sum(1 for e in history_entries if e.success)
            console.print(
                f"[dim]總查詢: {len(history_entries)} | 成功: {success_count} | 總成本: ${total_cost:.4f}[/dim]"
            )
            console.print()

        except Exception as e:
            console.print(f"[red]無法載入查詢歷史: {str(e)}[/red]")
            # Fallback to in-memory history
            console.print("[yellow]顯示本次會話的記憶體歷史...[/yellow]")
            queries = self.history.get_all()
            if queries:
                for idx, (query, answer, timestamp) in enumerate(queries, 1):
                    console.print(f"{idx}. {query} ({timestamp.strftime('%H:%M:%S')})")
            else:
                console.print("[dim]尚無歷史記錄[/dim]")

    def show_citations(self, args: str):
        """Display citations from last query."""
        if not self.last_answer:
            console.print("[yellow]尚無查詢結果。請先執行查詢。[/yellow]")
            return

        citations = self.last_answer.citations

        if not citations:
            console.print("[yellow]最後一次查詢無引用。[/yellow]")
            return

        console.print(f"\n[bold cyan]引用清單 ({len(citations)} 個來源):[/bold cyan]\n")

        for idx, citation in enumerate(citations, 1):
            authority_color = {"primary": "green", "secondary": "yellow", "tertiary": "blue"}.get(
                citation.authority.value, "white"
            )

            console.print(f"[bold white][{idx}][/bold white] {citation.title}")
            console.print(f"    [dim]類型:[/dim] {citation.type.value}")
            console.print(
                f"    [dim]權威:[/dim] [{authority_color}]{citation.authority.value}[/{authority_color}]"
            )
            if citation.url:
                console.print(f"    [dim]網址:[/dim] [link]{citation.url}[/link]")
            if citation.date:
                console.print(f"    [dim]日期:[/dim] {citation.date}")
            console.print()

    def export_results(self, format: str):
        """Export last results to file."""
        if not self.last_answer:
            console.print("[yellow]尚無查詢結果可匯出。[/yellow]")
            return

        if not self.last_query:
            console.print("[yellow]無法取得查詢文字。[/yellow]")
            return

        # Normalize format
        format = format.lower().strip() or "markdown"
        if format == "md":
            format = "markdown"

        if format not in ["markdown", "json", "txt"]:
            console.print(f"[red]不支援的格式: {format}[/red]")
            console.print("支援的格式: markdown (md), json, txt")
            return

        try:
            # Export based on format
            if format == "markdown":
                filepath = export_to_markdown(self.last_answer, self.last_query)
            elif format == "json":
                filepath = export_to_json(self.last_answer, self.last_query)
            elif format == "txt":
                filepath = export_to_text(self.last_answer, self.last_query)

            console.print(f"\n[green]✓ 已匯出至: {filepath.absolute()}[/green]\n")

        except Exception as e:
            console.print(f"[red]匯出失敗: {str(e)}[/red]")
            import traceback

            traceback.print_exc()

    def run(self):
        """Run the REPL loop."""
        self.show_welcome()
        session = self.create_prompt_session()

        while True:
            try:
                # Get user input
                user_input = session.prompt(
                    [("class:prompt", "finagent> ")],
                )

                # Skip empty input
                if not user_input.strip():
                    continue

                # Parse and handle command
                command, args = self.parse_command(user_input)
                should_continue = self.handle_command(command, args)

                if not should_continue:
                    break

            except KeyboardInterrupt:
                # Ctrl+C - just show a new prompt
                console.print()
                continue

            except EOFError:
                # Ctrl+D - exit gracefully
                console.print("\n[cyan]再見！感謝使用 FinAgent。[/cyan]\n")
                break

            except Exception as e:
                console.print(f"[red]錯誤: {str(e)}[/red]")
                import traceback

                console.print(f"[dim]{traceback.format_exc()}[/dim]")


def start_repl():
    """Start the REPL session."""
    repl = ReplSession()
    try:
        repl.run()
    except Exception as e:
        console.print(f"[red]REPL 錯誤: {str(e)}[/red]")
        sys.exit(1)
