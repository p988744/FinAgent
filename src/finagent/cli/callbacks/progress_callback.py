"""CLI progress callback with Rich terminal UI."""

from typing import Any, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from finagent.agents.ui_callback import UICallback
from finagent.models.answers import LegalAnswer
from finagent.models.citations import LegalCitation
from finagent.models.queries import Query
from finagent.models.resolution_plan import ResolutionPlan
from finagent.models.todo_item import TodoItem


class CLIProgressCallback(UICallback):
    """
    CLI progress callback with Rich terminal UI.

    Displays real-time progress updates with:
    - Live todo list with status indicators
    - Progress bars
    - Color-coded status
    - Emoji indicators
    """

    def __init__(self, console: Optional[Console] = None, verbose: bool = False):
        """
        Initialize CLI progress callback.

        Args:
            console: Rich console instance (creates new if None)
            verbose: Whether to show verbose progress updates
        """
        self.console = console or Console()
        self.verbose = verbose
        self.todos: list[TodoItem] = []
        self.live_display: Optional[Live] = None

    async def on_analysis_start(self, query: Query):
        """Display analysis start."""
        self.console.print("\n[cyan]🔍 分析查詢中...[/cyan]")

    async def on_analysis_complete(self, analysis: dict[str, Any]):
        """Display analysis results."""
        intent = analysis.get("intent", "未知")
        complexity = analysis.get("complexity", "moderate")
        entities = analysis.get("entities", [])

        complexity_cn = {
            "simple": "簡單",
            "moderate": "中等",
            "complex": "複雜",
        }.get(complexity, complexity)

        self.console.print(f"[green]✓ 查詢分析完成[/green]")
        self.console.print(f"  意圖: {intent}")
        self.console.print(f"  實體: {', '.join(entities) if entities else '無'}")
        self.console.print(f"  複雜度: {complexity_cn}\n")

    async def on_clarification_request(self, questions: list[str]) -> Optional[str]:
        """Request clarification from user."""
        self.console.print("\n[yellow]❓ 需要進一步澄清：[/yellow]")
        for i, question in enumerate(questions, 1):
            self.console.print(f"  {i}. {question}")

        try:
            response = self.console.input("\n[bold]請提供澄清資訊 (按 Enter 跳過): [/bold]")
            return response if response.strip() else None
        except KeyboardInterrupt:
            return None

    async def on_plan_created(self, plan):
        """Display execution plan."""
        self.console.print("[cyan]📋 執行計劃[/cyan]")
        # Handle both ResolutionPlan (with describe()) and ResearchPlan (from planning agent)
        if hasattr(plan, 'describe'):
            self.console.print(f"  {plan.describe()}\n")
        elif hasattr(plan, 'analysis'):
            # ResearchPlan from planning agent
            analysis = plan.analysis
            self.console.print(f"  複雜度: {analysis.complexity}")
            self.console.print(f"  關鍵字: {', '.join(analysis.keywords[:5])}")
            if analysis.must_have_keywords:
                self.console.print(f"  必要關鍵字: {', '.join(analysis.must_have_keywords)}")
            self.console.print(f"  任務數量: {len(plan.tasks)}\n")
        else:
            self.console.print(f"  計劃已建立\n")

    async def on_todo_list_created(self, todos: list[TodoItem]):
        """Display todo list."""
        self.todos = todos

        self.console.print("[cyan]📝 任務清單：[/cyan]")
        for i, todo in enumerate(todos, 1):
            status_icon = "[ ]"
            self.console.print(f"  {status_icon} {i}. {todo.content}")
        self.console.print()

    async def on_todo_started(self, todo: TodoItem):
        """Update when todo starts."""
        if self.verbose:
            self.console.print(f"[yellow]⏳ {todo.active_form}...[/yellow]")

    async def on_todo_progress(self, todo: TodoItem, percentage: int, message: str = ""):
        """Update todo progress."""
        if self.verbose and message:
            self.console.print(f"   {message} ({percentage}%)")

    async def on_todo_completed(self, todo: TodoItem):
        """Display todo completion."""
        # Find todo in list and update
        for i, t in enumerate(self.todos, 1):
            if t.id == todo.id:
                duration_str = (
                    f"{todo.duration_seconds:.1f}s" if todo.duration_seconds else ""
                )

                # Show result summary if available
                result_summary = ""
                if todo.result:
                    if isinstance(todo.result, dict):
                        count = todo.result.get("count", "")
                        if count:
                            result_summary = f" (找到 {count} 個區塊)"

                self.console.print(
                    f"[green]  [✓] {i}. {todo.content}{result_summary} {duration_str}[/green]"
                )
                break

    async def on_todo_failed(self, todo: TodoItem, error: str):
        """Display todo failure."""
        for i, t in enumerate(self.todos, 1):
            if t.id == todo.id:
                self.console.print(f"[red]  [✗] {i}. {todo.content} - 失敗: {error}[/red]")
                break

    async def on_retrieval_start(self, query: str, strategy: str, max_results: int):
        """Display retrieval start."""
        if self.verbose:
            self.console.print(f"[cyan]🔍 開始檢索: {strategy} (最多 {max_results} 筆)[/cyan]")

    async def on_retrieval_result(self, strategy: str, count: int, total: int):
        """Display retrieval results."""
        strategy_cn = {
            "vector": "向量搜尋",
            "concept": "概念分析",
            "parallel": "並行檢索",
            "conservative": "保守策略",
            "balanced": "平衡策略",
            "aggressive": "積極策略",
        }.get(strategy, strategy)

        if self.verbose:
            self.console.print(
                f"[cyan]   {strategy_cn}: 找到 {count} 份相關文件 (總計 {total} 筆)[/cyan]"
            )

    async def on_validation_start(self):
        """Display validation start."""
        if self.verbose:
            self.console.print("[cyan]🔍 驗證引用完整性...[/cyan]")

    async def on_validation_complete(self, passed: bool, issues: list[str]):
        """Display validation results."""
        if passed:
            self.console.print("[green]✓ 驗證通過[/green]")
        else:
            self.console.print(f"[yellow]⚠ 驗證發現 {len(issues)} 個問題[/yellow]")
            if self.verbose:
                for issue in issues[:3]:  # Show first 3 issues
                    self.console.print(f"   - {issue}")

    async def on_answer_generation_start(self):
        """Display answer generation start."""
        self.console.print("\n[cyan]🤖 合成答案中...[/cyan]")

    async def on_citations_extracted(self, citations: list[LegalCitation]):
        """Display citations extracted."""
        if self.verbose:
            self.console.print(
                f"[cyan]   提取 {len(citations)} 個引用來源[/cyan]"
            )

    async def on_answer_generation_complete(self, answer: LegalAnswer):
        """Display answer generation complete."""
        self.console.print("[green]✓ 答案生成完成[/green]")

    async def on_citations_formatted(self, citations: list[LegalCitation]):
        """Display citations count."""
        if self.verbose:
            self.console.print(
                f"[cyan]   格式化 {len(citations)} 個引用來源[/cyan]"
            )

    async def on_answer_complete(self, answer: LegalAnswer):
        """Display answer completion."""
        self.console.print("[green]✨ 答案已生成[/green]\n")

    async def on_error(self, error: str, context: Optional[dict[str, Any]] = None):
        """Display error."""
        self.console.print(f"[red]❌ 錯誤: {error}[/red]")
        if context and self.verbose:
            self.console.print(f"[dim]   上下文: {context}[/dim]")

    def render_todo_table(self) -> Table:
        """
        Render todo list as a Rich table.

        Returns:
            Rich table with todo status
        """
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("狀態", width=6)
        table.add_column("#", width=4)
        table.add_column("任務", width=50)
        table.add_column("進度", width=20)

        for i, todo in enumerate(self.todos, 1):
            # Status icon
            if todo.status == "completed":
                status = "[green]✓[/green]"
            elif todo.status == "in_progress":
                status = "[yellow]⏳[/yellow]"
            elif todo.status == "failed":
                status = "[red]✗[/red]"
            else:
                status = "[ ]"

            # Progress indicator
            if todo.status == "in_progress":
                progress = f"{todo.progress_percentage}%"
            elif todo.status == "completed":
                progress = "完成"
            elif todo.status == "failed":
                progress = "失敗"
            else:
                progress = "待執行"

            table.add_row(status, str(i), todo.content, progress)

        return table

    def display_todo_table(self):
        """Display current todo table."""
        self.console.print(self.render_todo_table())
