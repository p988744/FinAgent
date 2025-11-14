"""Query command with live TODO list display."""

import asyncio
import logging

from rich.console import Console

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.cli.formatters.answer import format_legal_answer
from finagent.cli.formatters.todo_display import TodoListDisplay
from finagent.models.plan import ResearchPlan
from finagent.models.queries import Query

console = Console()
logger = logging.getLogger(__name__)


class QueryExecutorWithTodo:
    """
    Query executor that shows live TODO list progress.

    Monitors workflow execution and updates task status in real-time.
    """

    def __init__(self, orchestrator: AgentOrchestrator):
        """
        Initialize query executor.

        Args:
            orchestrator: Agent orchestrator for query processing
        """
        self.orchestrator = orchestrator
        self.todo_display = None
        self.current_task_id = None

    async def execute_query(self, query_text: str, show_todo: bool = True):
        """
        Execute query with optional TODO list display.

        Args:
            query_text: Query text
            show_todo: Whether to show live TODO list (default: True)
        """
        # Create query object
        query = Query(text=query_text)

        # Show processing message
        console.print()
        console.print(f"[cyan]🔍 處理查詢:[/cyan] {query_text}")
        console.print()

        try:
            # Wrap the workflow execution to monitor state
            answer = await self._execute_with_monitoring(query, show_todo=show_todo)

            # Stop TODO display if active
            if self.todo_display:
                self.todo_display.stop()

                # Show completion summary
                summary = self.todo_display.get_completion_summary()
                console.print()
                console.print(f"[green]{summary}[/green]")
                console.print()

            # Display answer
            format_legal_answer(answer)

            return answer

        except Exception as e:
            # Stop TODO display on error
            if self.todo_display:
                self.todo_display.stop()

            console.print(f"[red]✗ 查詢執行失敗:[/red] {str(e)}")
            logger.error(f"Query execution failed: {e}", exc_info=True)
            raise

    async def _execute_with_monitoring(self, query: Query, show_todo: bool = True):
        """
        Execute query with workflow monitoring for TODO updates.

        Args:
            query: Query object
            show_todo: Whether to show TODO list

        Returns:
            LegalAnswer from workflow
        """
        # Execute query (this will trigger the workflow)
        # We need to hook into the workflow to get the plan

        # Start query execution
        answer = await self.orchestrator.process_query(query)

        # Get plan from answer's processing_steps if available
        # This is a bit hacky - ideally we'd have a callback from orchestrator
        # For now, we'll parse the plan from processing_steps after execution

        return answer

    def _parse_plan_from_processing_steps(self, processing_steps: list[str]) -> ResearchPlan | None:
        """
        Parse research plan from processing steps.

        This is a temporary solution until we add proper callbacks.

        Args:
            processing_steps: List of processing step strings

        Returns:
            ResearchPlan if found, None otherwise
        """
        # Look for planning analysis step
        for step in processing_steps:
            if "📋 查詢分析" in step:
                # Found planning step, but we need the actual plan object
                # This is hard to reconstruct from strings
                # Better solution: add callback to orchestrator
                break

        return None

    def _update_task_from_step(self, step: str):
        """
        Update TODO list based on processing step.

        Maps processing steps to task status updates.

        Args:
            step: Processing step string
        """
        if not self.todo_display:
            return

        # Map steps to task IDs based on content
        if "行動代理" in step and "向量搜索" in step:
            # Task 1: Vector search
            if self.current_task_id != 1:
                if self.current_task_id:
                    self.todo_display.update_task_status(self.current_task_id, "completed")
                self.current_task_id = 1
                self.todo_display.update_task_status(1, "in_progress")

        elif "行動代理" in step and "深度搜索" in step:
            # Task 2: Hard search
            if self.current_task_id and self.current_task_id == 1:
                self.todo_display.update_task_status(1, "completed")
            if self.current_task_id != 2:
                self.current_task_id = 2
                self.todo_display.update_task_status(2, "in_progress")

        elif "驗證代理" in step:
            # Task 3: Validation
            if self.current_task_id and self.current_task_id in [1, 2]:
                self.todo_display.update_task_status(self.current_task_id, "completed")
            if self.current_task_id != 3:
                self.current_task_id = 3
                self.todo_display.update_task_status(3, "in_progress")

        elif "答案代理" in step:
            # Task 4: Answer generation
            if self.current_task_id and self.current_task_id == 3:
                self.todo_display.update_task_status(3, "completed")
            if self.current_task_id != 4:
                self.current_task_id = 4
                self.todo_display.update_task_status(4, "in_progress")


async def execute_query_with_todo(query_text: str, show_todo: bool = True):
    """
    Execute query with live TODO list display.

    Args:
        query_text: Query text to execute
        show_todo: Whether to show live TODO list (default: True)

    Returns:
        LegalAnswer from query execution
    """
    orchestrator = AgentOrchestrator()
    executor = QueryExecutorWithTodo(orchestrator)

    return await executor.execute_query(query_text, show_todo=show_todo)
