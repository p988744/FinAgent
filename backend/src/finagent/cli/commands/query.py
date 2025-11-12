"""Query execution command handlers."""

import json
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from finagent.cli.api_client import ApiClient
from finagent.cli.formatters.answer import format_legal_answer, format_answer_json, format_answer_markdown
from finagent.models.answers import LegalAnswer
from finagent.models.queries import Query

console = Console()


def execute_query(
    query_text: str,
    max_results: int = 5,
    regulator: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Optional[LegalAnswer]:
    """
    Execute a legal research query.

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
            end_date=end_date
        )

        # Create API client
        client = ApiClient()

        # Show loading spinner
        with Live(Spinner("dots", text="正在處理查詢..."), console=console):
            # Execute query
            answer = client.submit_query_sync(query)

        return answer

    except Exception as e:
        console.print(f"[red]查詢錯誤: {str(e)}[/red]")
        return None


def execute_single_query(
    text: str,
    max_results: int = 5,
    regulator: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_format: str = "rich"
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
