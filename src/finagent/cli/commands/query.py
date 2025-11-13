"""Query execution command handlers."""

import asyncio

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.cli.formatters.answer import (
    format_answer_json,
    format_answer_markdown,
    format_legal_answer,
)
from finagent.models.answers import LegalAnswer
from finagent.models.queries import Query

console = Console()

# Initialize orchestrator globally (singleton)
_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


def reset_orchestrator():
    """Reset orchestrator to force reinitialization with new config."""
    global _orchestrator
    _orchestrator = None


def execute_query(
    query_text: str,
    max_results: int = 5,
    regulator: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> LegalAnswer | None:
    """
    Execute a legal research query using the orchestrator directly.

    Args:
        query_text: The query text
        max_results: Maximum number of results (1-50)
        regulator: Optional regulator filter
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        LegalAnswer if successful, None otherwise
    """
    try:
        # Create query object
        query = Query(
            text=query_text,
            max_results=max_results,
            regulator=regulator,
            start_date=start_date,
            end_date=end_date,
        )

        # Get orchestrator
        orchestrator = get_orchestrator()

        # Show loading spinner and execute query
        with Live(Spinner("dots", text="正在處理查詢..."), console=console):
            # Execute query through LangGraph workflow
            answer = asyncio.run(orchestrator.process_query(query))

        return answer

    except Exception as e:
        console.print(f"[red]查詢錯誤: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return None


def execute_single_query(
    text: str,
    max_results: int = 5,
    regulator: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    output_format: str = "rich",
):
    """
    Execute a single query and display results.

    Used for non-interactive mode (finagent query ...).

    Args:
        text: Query text
        max_results: Maximum results
        regulator: Regulator filter
        start_date: Start date filter
        end_date: End date filter
        output_format: Output format (rich, json, markdown)
    """
    answer = execute_query(text, max_results, regulator, start_date, end_date)

    if not answer:
        console.print("[red]查詢失敗。[/red]")
        return

    # Format output based on format type
    if output_format == "json":
        # JSON output
        output = format_answer_json(answer)
        console.print(output)
    elif output_format == "markdown":
        # Markdown output
        output = format_answer_markdown(answer)
        console.print(output)
    else:
        # Rich formatted output (default)
        format_legal_answer(answer)
