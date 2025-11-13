"""
Interactive REPL (Read-Eval-Print Loop) for FinAgent CLI.
"""

import sys
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

console = Console()


class ReplSession:
    """Interactive REPL session for FinAgent."""

    def __init__(self):
        self.history = QueryHistory()
        self.prompt_history = InMemoryHistory()
        self.last_answer = None
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

            # Execute query
            answer = execute_query(query_text)

            if answer:
                # Save to history
                self.history.add(query_text, answer)
                self.last_answer = answer

                # Display answer
                format_legal_answer(answer)
            else:
                console.print("[red]查詢失敗，請稍後再試。[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]查詢已取消。[/yellow]")
        except Exception as e:
            console.print(f"[red]錯誤: {str(e)}[/red]")

    def show_history(self):
        """Display query history."""
        queries = self.history.get_all()

        if not queries:
            console.print("[yellow]尚無查詢歷史。[/yellow]")
            return

        table = Table(title="查詢歷史", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("查詢", style="white")
        table.add_column("時間", style="cyan", width=20)
        table.add_column("信心", style="green", width=10)

        for idx, (query, answer, timestamp) in enumerate(queries, 1):
            confidence = f"{answer.confidence_score:.0%}" if answer else "N/A"
            table.add_row(
                str(idx),
                query[:60] + "..." if len(query) > 60 else query,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                confidence,
            )

        console.print()
        console.print(table)
        console.print()

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

        format = format.lower() or "markdown"

        if format not in ["markdown", "json", "md", "txt"]:
            console.print(f"[red]不支援的格式: {format}[/red]")
            console.print("支援的格式: markdown, json")
            return

        # TODO: Implement export functionality
        console.print(f"[yellow]匯出功能尚未實作 (格式: {format})[/yellow]")

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
