"""
Load command - Load documents from directory and display info
"""

from pathlib import Path

import click
from rich.console import Console

from finagent.cli.utils.output import (
    format_size,
    print_error,
    print_json,
    print_summary,
    print_table,
    print_tree,
)
from finagent.document_processing.loader import DocumentLoader

console = Console()


@click.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--recursive", "-r", is_flag=True, help="Scan subdirectories recursively")
@click.option("--pattern", default="*.txt", help="File pattern to match (default: *.txt)")
@click.option(
    "--output",
    type=click.Choice(["table", "tree", "json", "summary"]),
    default="summary",
    help="Output format"
)
@click.option("--dry-run", is_flag=True, help="Show what would be loaded without loading")
def load(directory: str, recursive: bool, pattern: str, output: str, dry_run: bool):
    """
    Load documents from DIRECTORY and display basic information.

    Examples:

      \b
      # Quick scan with summary
      finagent load data/documents

      \b
      # Recursive scan with tree view
      finagent load data/documents -r --output tree

      \b
      # Find all markdown files
      finagent load data/documents --pattern "*.md"
    """
    try:
        dir_path = Path(directory).resolve()
        console.print(f"[bold]Scanning directory:[/bold] {dir_path}")
        console.print(f"[dim]Pattern: {pattern}, Recursive: {recursive}[/dim]\n")

        # Find files using Path.glob
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        if not files:
            console.print(f"[yellow]No files found matching pattern '{pattern}'[/yellow]")
            return

        # Calculate statistics
        total_size = sum(f.stat().st_size for f in files)
        file_types = {}
        for f in files:
            ext = f.suffix or "no extension"
            file_types[ext] = file_types.get(ext, 0) + 1

        # Display based on output format
        if output == "tree":
            print_tree(dir_path, files, f"Found {len(files)} files")

        elif output == "table":
            data = [
                {
                    "filename": f.name,
                    "size": format_size(f.stat().st_size),
                    "path": str(f.relative_to(dir_path)),
                }
                for f in files[:50]  # Limit to 50 for readability
            ]
            print_table(data, title=f"Found {len(files)} files")
            if len(files) > 50:
                console.print(f"[dim]... and {len(files) - 50} more files[/dim]")

        elif output == "json":
            data = {
                "directory": str(dir_path),
                "pattern": pattern,
                "recursive": recursive,
                "files": [
                    {
                        "filename": f.name,
                        "path": str(f.relative_to(dir_path)),
                        "size": f.stat().st_size,
                        "extension": f.suffix,
                    }
                    for f in files
                ],
                "summary": {
                    "total_files": len(files),
                    "total_size_bytes": total_size,
                    "file_types": file_types,
                }
            }
            print_json(data)

        else:  # summary (default)
            console.print(f"[green]Found {len(files)} files[/green]\n")

            # Show first few files
            for f in files[:5]:
                size_str = format_size(f.stat().st_size)
                rel_path = f.relative_to(dir_path)
                console.print(f"  ├── {rel_path} [dim]({size_str})[/dim]")

            if len(files) > 5:
                console.print(f"  └── ... and {len(files) - 5} more files\n")
            else:
                console.print()

            # Print summary
            print_summary({
                "total_files": len(files),
                "total_size": format_size(total_size),
                "file_types": ", ".join(f"{ext} ({count})" for ext, count in file_types.items()),
            })

        if dry_run:
            console.print("\n[yellow]Dry run - no files were loaded[/yellow]")
        else:
            # Actually load documents
            with console.status("[bold green]Loading documents..."):
                loader = DocumentLoader(base_path=str(dir_path))
                documents = loader.load_directory(str(dir_path), recursive=recursive, pattern=pattern)

            console.print(f"\n[green]✓ Loaded {len(documents)} documents successfully[/green]")

    except Exception as e:
        print_error(f"Failed to load documents: {str(e)}")
        raise click.Abort()
