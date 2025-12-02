"""Output formatting utilities for CLI"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
import json as _json


console = Console()


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def print_table(data: list[dict[str, Any]], title: str = None):
    """Print data as a formatted table"""
    if not data:
        console.print("[yellow]No data to display[/yellow]")
        return
    
    table = Table(title=title, show_header=True, header_style="bold magenta")
    
    # Add columns from first row
    for key in data[0].keys():
        table.add_column(key.replace("_", " ").title())
    
    # Add rows
    for row in data:
        table.add_row(*[str(v) for v in row.values()])
    
    console.print(table)


def print_tree(root_path: Path, files: list[Path], title: str = "Files"):
    """Print files as a tree structure"""
    tree = Tree(f"[bold]{title}[/bold]")
    
    for file_path in files:
        rel_path = file_path.relative_to(root_path) if root_path in file_path.parents else file_path
        size = format_size(file_path.stat().st_size)
        tree.add(f"{rel_path} [dim]({size})[/dim]")
    
    console.print(tree)


def print_summary(stats: dict[str, Any]):
    """Print summary statistics"""
    console.print("\n[bold]Summary:[/bold]")
    for key, value in stats.items():
        formatted_key = key.replace("_", " ").title()
        console.print(f"  {formatted_key}: [cyan]{value}[/cyan]")


def print_json(data: Any, indent: int = 2):
    """Print data as JSON"""
    console.print_json(_json.dumps(data, ensure_ascii=False, indent=indent))


def print_success(message: str):
    """Print success message"""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print error message"""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"[yellow]⚠[/yellow] {message}")
