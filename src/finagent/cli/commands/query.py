"""Query execution command handlers."""

import asyncio
import time

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.cli.formatters.answer import (
    format_answer_json,
    format_answer_markdown,
    format_legal_answer,
)
from finagent.cli.formatters.query_analysis import handle_cli_clarification
from finagent.config_manager import get_config_manager
from finagent.database.db import Database
from finagent.models.answers import LegalAnswer
from finagent.models.queries import Query
from finagent.utils.cost_calculator import calculate_total_cost

console = Console()

# Initialize orchestrator globally (singleton)
_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create orchestrator instance with CLI clarification handler."""
    global _orchestrator
    if _orchestrator is None:
        # Create clarification handler for CLI
        async def cli_clarification_handler(clarification_request):
            return await handle_cli_clarification(clarification_request, console)

        _orchestrator = AgentOrchestrator(
            clarification_handler=cli_clarification_handler
        )
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
    session_id: str | None = None,
) -> LegalAnswer | None:
    """
    Execute a legal research query using the orchestrator directly.

    Args:
        query_text: The query text
        max_results: Maximum number of results (1-50)
        regulator: Optional regulator filter
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        session_id: Optional session ID for history tracking

    Returns:
        LegalAnswer if successful, None otherwise
    """
    # Track processing time
    start_time = time.time()
    answer = None
    error_message = None

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
        error_message = str(e)
        console.print(f"[red]查詢錯誤: {error_message}[/red]")
        import traceback

        traceback.print_exc()
        return None

    finally:
        # Log to database (regardless of success/failure)
        processing_time = time.time() - start_time

        try:
            # Get current LLM configuration
            config_manager = get_config_manager()
            llm_config = config_manager.get_active_llm_config()
            model_used = llm_config.get("model", "unknown")

            # Extract token usage and calculate cost
            tokens_used = None
            cost_usd = None

            if answer and hasattr(answer, "metadata") and answer.metadata:
                # Try to get token count from metadata
                tokens_used = answer.metadata.get("total_tokens")
                if tokens_used:
                    cost_usd = calculate_total_cost(tokens_used, model_used)

            # Log to database
            db = Database()

            # Extract response text from answer (use executive_summary for new model structure)
            response_text = None
            if answer:
                if hasattr(answer, "executive_summary"):
                    response_text = answer.executive_summary
                elif hasattr(answer, "answer"):
                    response_text = answer.answer

            db.add_history(
                session_id=session_id,
                query=query_text,
                response=response_text,
                model_used=model_used,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                processing_time_seconds=processing_time,
                success=answer is not None,
                error_message=error_message,
                metadata=answer.metadata if answer and hasattr(answer, "metadata") else None,
            )
        except Exception as db_error:
            # Don't fail the query if logging fails
            console.print(f"[dim yellow]警告: 無法記錄查詢歷史 - {str(db_error)}[/dim yellow]")


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
