"""
Main entry point for FinAgent CLI.
"""

import click
from rich.console import Console

from finagent.cli.repl import start_repl

console = Console()


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx, version):
    """
    FinAgent - Taiwan Legal Research Agent System

    Interactive CLI for researching bank penalties, regulatory enforcement,
    and legal precedents in Taiwan.

    Examples:
        finagent                              # Start interactive REPL
        finagent query "玉山銀行洗錢防制裁罰"    # Single query mode
        finagent reindex --skip-init          # Reindex documents (fast mode)
    """
    if version:
        from finagent.cli import __version__

        console.print(f"FinAgent CLI v{__version__}", style="bold cyan")
        return

    if ctx.invoked_subcommand is None:
        # No subcommand - start REPL mode
        start_repl()


@cli.command()
@click.argument("text", required=True)
@click.option("--max-results", "-n", default=5, help="Maximum number of results (1-50)")
@click.option("--regulator", help="Filter by regulator (FSC, CBC, FTC)")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["rich", "json", "markdown"]),
    default="rich",
    help="Output format",
)
def query(text, max_results, regulator, start_date, end_date, format):
    """
    Submit a single legal research query.

    Examples:
        finagent query "玉山銀行洗錢防制裁罰"
        finagent query "2020年金管會裁罰案件" --max-results 10
        finagent query "國泰世華銀行" --regulator FSC --format json
    """
    from finagent.cli.commands.query import execute_single_query

    execute_single_query(
        text=text,
        max_results=max_results,
        regulator=regulator,
        start_date=start_date,
        end_date=end_date,
        output_format=format,
    )


@cli.command()
@click.option("--clear", is_flag=True, help="Clear existing index before reindexing")
@click.option("--skip-init", is_flag=True, help="Skip LLM metadata generation (faster)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def reindex(clear, skip_init, yes):
    """
    Reindex all documents in the data/documents directory.

    This command processes all documents sequentially:
    1. Load document
    2. Index to vector database
    3. Generate metadata (with LLM or basic)
    4. Save to database
    5. Extract and link concepts
    6. Update TABLE_OF_CONTENTS.md

    Examples:
        finagent reindex                    # Full reindex with LLM metadata
        finagent reindex --skip-init        # Fast reindex without LLM (~5 min)
        finagent reindex --clear            # Clear and rebuild from scratch
        finagent reindex --clear --yes      # Clear without confirmation
    """
    from finagent.cli.commands.reindex import execute_reindex

    # Handle confirmation for --clear
    if clear and not yes:
        console.print()
        console.print("[bold yellow]⚠️  Warning:[/bold yellow] This will delete all existing indexes and rebuild!")
        console.print()
        if not click.confirm("Continue?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    execute_reindex(clear=clear, skip_init=skip_init, use_sequential=True)


if __name__ == "__main__":
    cli()
