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


if __name__ == "__main__":
    cli()
