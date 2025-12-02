"""
FinAgent CLI - Document Processing Pipeline

Main entry point for the CLI tool.
"""

import click
from rich.console import Console

from finagent.cli import __version__
from finagent.cli.commands.load import load
from finagent.cli.commands.metadata import metadata
from finagent.cli.commands.index import index
from finagent.cli.commands.process import process

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="finagent")
@click.pass_context
def cli(ctx):
    """
    FinAgent CLI - Document Processing Pipeline
    
    Process legal documents: load, extract metadata, chunk, and index.
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(load)
cli.add_command(metadata)
cli.add_command(index)
cli.add_command(process)


@cli.command()
def version():
    """Show version information"""
    console.print(f"[bold green]FinAgent CLI[/bold green] version {__version__}")


if __name__ == "__main__":
    cli()
