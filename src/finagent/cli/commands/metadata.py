"""
Metadata command - Extract metadata from documents using LLM
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from finagent.document_processing.loader import DocumentLoader
from finagent.document_processing.metadata_extractor import MetadataExtractor
from finagent.cli.utils.output import print_error, print_success, print_warning, console


@click.command()
@click.option(
    "--file", "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Single file path"
)
@click.option(
    "--dir", "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory path"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file (JSON format)"
)
@click.option(
    "--batch-size",
    type=int,
    default=5,
    help="Process N files at a time"
)
@click.option(
    "--confidence-threshold",
    type=float,
    default=0.5,
    help="Minimum confidence score (0.0-1.0)"
)
@click.option(
    "--recursive", "-r",
    is_flag=True,
    help="Scan subdirectories (only with --dir)"
)
def metadata(
    file: Optional[str],
    dir: Optional[str],
    output: Optional[str],
    batch_size: int,
    confidence_threshold: float,
    recursive: bool
):
    """
    Extract metadata from documents using LLM.
    
    Examples:
    
      \b
      # Extract metadata from single file
      finagent metadata -f data/documents/doc1.txt
      
      \b
      # Process entire directory and save to JSON
      finagent metadata -d data/documents -o metadata.json
      
      \b
      # Recursive scan with custom batch size
      finagent metadata -d data/documents -r --batch-size 10
    """
    if not file and not dir:
        print_error("Either --file or --dir must be specified")
        raise click.Abort()
    
    if file and dir:
        print_error("Cannot specify both --file and --dir")
        raise click.Abort()
    
    try:
        # Collect files
        files_to_process = []
        if file:
            files_to_process = [Path(file)]
        else:
            dir_path = Path(dir)
            if recursive:
                files_to_process = list(dir_path.rglob("*.txt"))
            else:
                files_to_process = list(dir_path.glob("*.txt"))
        
        if not files_to_process:
            console.print("[yellow]No files found to process[/yellow]")
            return
        
        console.print(f"[bold]Processing {len(files_to_process)} files[/bold]")
        console.print(f"[dim]Batch size: {batch_size}, Confidence threshold: {confidence_threshold}[/dim]\n")
        
        # Initialize extractor
        extractor = MetadataExtractor(use_new_model=True)
        
        # Process files
        results = []
        failed_files = []
        
        async def process_files():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    "[green]Extracting metadata...",
                    total=len(files_to_process)
                )
                
                for file_path in files_to_process:
                    try:
                        # Read file content
                        content = file_path.read_text(encoding="utf-8")
                        
                        # Extract metadata
                        result = await extractor.extract_new(
                            doc_id=file_path.stem,
                            filename=file_path.name,
                            content=content
                        )
                        
                        # Check confidence
                        if result.metadata and result.metadata.extraction_confidence >= confidence_threshold:
                            results.append({
                                "filename": file_path.name,
                                "path": str(file_path),
                                "success": True,
                                "metadata": result.metadata.dict() if hasattr(result.metadata, 'dict') else result.metadata,
                                "processing_time": result.processing_time,
                            })
                        else:
                            confidence = result.metadata.extraction_confidence if result.metadata else 0.0
                            failed_files.append({
                                "filename": file_path.name,
                                "reason": f"Low confidence: {confidence:.2f} < {confidence_threshold}",
                            })
                        
                    except Exception as e:
                        failed_files.append({
                            "filename": file_path.name,
                            "reason": str(e),
                        })
                    
                    progress.update(task, advance=1)
        
        # Run async processing
        asyncio.run(process_files())
        
        # Print summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Processed: [cyan]{len(files_to_process)}[/cyan]")
        console.print(f"  Successful: [green]{len(results)}[/green]")
        console.print(f"  Failed: [red]{len(failed_files)}[/red]")
        
        # Show failed files
        if failed_files:
            console.print("\n[yellow]Failed files:[/yellow]")
            for failed in failed_files[:5]:
                console.print(f"  - {failed['filename']}: {failed['reason']}")
            if len(failed_files) > 5:
                console.print(f"  ... and {len(failed_files) - 5} more")
        
        # Save to file if requested
        if output:
            output_data = {
                "processed": len(files_to_process),
                "successful": len(results),
                "failed": len(failed_files),
                "confidence_threshold": confidence_threshold,
                "results": results,
                "failed_files": failed_files,
            }
            
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2))
            
            print_success(f"Results saved to {output}")
        
    except Exception as e:
        print_error(f"Metadata extraction failed: {str(e)}")
        raise click.Abort()
