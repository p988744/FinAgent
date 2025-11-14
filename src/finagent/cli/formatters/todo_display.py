"""Live TODO list display for REPL interface."""

import sys
from datetime import datetime

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from finagent.models.plan import PlanTask, ResearchPlan

console = Console()


class TodoListDisplay:
    """
    Live TODO list display that updates task status in real-time.

    Shows tasks with checkboxes (☐ = pending, ⏳ = in progress, ✓ = completed, ✗ = failed).
    """

    def __init__(self, plan: ResearchPlan):
        """
        Initialize TODO list display with research plan.

        Args:
            plan: Research plan with tasks to display
        """
        self.plan = plan
        self.tasks = {task.id: task for task in plan.tasks}
        self.start_time = datetime.now()
        self.live_display = None

    def _create_table(self) -> Table:
        """
        Create Rich table with current task status.

        Returns:
            Rich Table with tasks and status
        """
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
        table.add_column("狀態", width=4, justify="center")
        table.add_column("ID", width=3, justify="right")
        table.add_column("任務", style="white")
        table.add_column("預估", width=8, justify="right", style="dim")

        for task in self.plan.tasks:
            # Status symbol
            if task.status == "completed":
                status_symbol = "[green]✓[/green]"
            elif task.status == "in_progress":
                status_symbol = "[yellow]⏳[/yellow]"
            elif task.status == "failed":
                status_symbol = "[red]✗[/red]"
            else:  # pending
                status_symbol = "[dim]☐[/dim]"

            # Task symbol based on search method
            if task.search_method == "hard_search":
                task_symbol = "⏱"  # Hard search takes time
            elif task.search_method == "hybrid":
                task_symbol = "🔄"  # Hybrid
            else:
                task_symbol = "🔍"  # Vector search

            # Task text with status color
            if task.status == "completed":
                task_text = f"[green]{task_symbol} {task.task}[/green]"
            elif task.status == "in_progress":
                task_text = f"[yellow]{task_symbol} {task.task}[/yellow]"
            elif task.status == "failed":
                task_text = f"[red]{task_symbol} {task.task}[/red]"
            else:
                task_text = f"{task_symbol} {task.task}"

            # Estimated time
            time_str = f"~{task.estimated_time}s" if task.estimated_time else ""

            table.add_row(
                status_symbol,
                str(task.id),
                task_text,
                time_str
            )

        return table

    def _create_panel(self) -> Panel:
        """
        Create panel with TODO list and progress info.

        Returns:
            Rich Panel with TODO list
        """
        table = self._create_table()

        # Calculate progress
        total_tasks = len(self.plan.tasks)
        completed_tasks = sum(1 for t in self.plan.tasks if t.status == "completed")
        failed_tasks = sum(1 for t in self.plan.tasks if t.status == "failed")
        in_progress_tasks = sum(1 for t in self.plan.tasks if t.status == "in_progress")

        # Progress bar
        progress_percentage = completed_tasks / total_tasks if total_tasks > 0 else 0
        bar_length = 40
        filled = int(progress_percentage * bar_length)
        bar_chars = "█" * filled + "░" * (bar_length - filled)

        # Elapsed time
        elapsed = (datetime.now() - self.start_time).total_seconds()
        elapsed_str = f"{elapsed:.0f}秒"

        # Title with progress
        title = f"[cyan]📝 研究任務進度[/cyan] [white]{completed_tasks}/{total_tasks}[/white]"

        # Progress bar line
        progress_line = Text()
        progress_line.append(bar_chars, style="cyan")
        progress_line.append(f" {progress_percentage:.0%}", style="white")

        # Status line
        status_line = Text()
        if in_progress_tasks > 0:
            status_line.append("進行中: ", style="yellow")
            status_line.append(str(in_progress_tasks), style="yellow bold")
            status_line.append(" | ", style="dim")
        if failed_tasks > 0:
            status_line.append("失敗: ", style="red")
            status_line.append(str(failed_tasks), style="red bold")
            status_line.append(" | ", style="dim")
        status_line.append("已用時間: ", style="dim")
        status_line.append(elapsed_str, style="dim")

        # Group all renderables
        content = Group(
            table,
            Text(""),  # Blank line
            progress_line,
            status_line
        )

        return Panel(
            content,
            title=title,
            border_style="cyan",
            padding=(1, 2)
        )

    def start(self):
        """Start live display (non-blocking)."""
        self.live_display = Live(
            self._create_panel(),
            console=console,
            refresh_per_second=4,
            transient=False  # Keep display after done
        )
        self.live_display.start()

    def stop(self):
        """Stop live display."""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None

    def update_task_status(self, task_id: int, status: str):
        """
        Update task status and refresh display.

        Args:
            task_id: Task ID to update
            status: New status (pending/in_progress/completed/failed)
        """
        if task_id in self.tasks:
            self.tasks[task_id].status = status

            # Update in plan tasks list too
            for task in self.plan.tasks:
                if task.id == task_id:
                    task.status = status
                    break

            # Refresh live display
            if self.live_display:
                self.live_display.update(self._create_panel())

    def display_static(self):
        """Display static (non-live) TODO list."""
        console.print(self._create_panel())

    def get_completion_summary(self) -> str:
        """
        Get summary of task completion.

        Returns:
            Summary string with completion stats
        """
        total = len(self.plan.tasks)
        completed = sum(1 for t in self.plan.tasks if t.status == "completed")
        failed = sum(1 for t in self.plan.tasks if t.status == "failed")
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if failed > 0:
            return (
                f"✓ 完成 {completed}/{total} 項任務，{failed} 項失敗 "
                f"（{elapsed:.0f}秒）"
            )
        else:
            return f"✓ 完成所有 {total} 項任務（{elapsed:.0f}秒）"


def display_todo_list(plan: ResearchPlan, show_live: bool = False) -> TodoListDisplay:
    """
    Display TODO list from research plan.

    Args:
        plan: Research plan with tasks
        show_live: Whether to show live updating display (default: False)

    Returns:
        TodoListDisplay instance for status updates
    """
    display = TodoListDisplay(plan)

    if show_live:
        display.start()
    else:
        display.display_static()

    return display
