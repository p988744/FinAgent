"""
Process command - Full pipeline: load, extract metadata, chunk, and index
"""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from finagent.document_processing.loader import DocumentLoader
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.chunker import ChineseTextChunker
from finagent.document_processing.metadata_extractor import MetadataExtractor
from finagent.cli.utils.output import print_error, print_success, print_warning, console


@click.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--collection",
    default="legal_documents",
    help="Collection name"
)
@click.option(
    "--recursive", "-r",
    is_flag=True,
    help="Scan subdirectories"
)
@click.option(
    "--pattern",
    default="*.txt",
    help="File pattern (default: *.txt)"
)
@click.option(
    "--skip-metadata",
    is_flag=True,
    help="Skip metadata extraction"
)
@click.option(
    "--skip-indexing",
    is_flag=True,
    help="Only extract metadata without indexing"
)
@click.option(
    "--chunk-size",
    type=int,
    default=500,
    help="Chunk size in characters"
)
@click.option(
    "--chunk-overlap",
    type=int,
    default=50,
    help="Chunk overlap size"
)
def process(
    directory: str,
    collection: str,
    recursive: bool,
    pattern: str,
    skip_metadata: bool,
    skip_indexing: bool,
    chunk_size: int,
    chunk_overlap: int
):
    """
    Full pipeline - load, extract metadata, chunk, and index.
    
    This is the recommended command for complete document processing.
    
    Examples:
    
      \b
      # Full processing pipeline
      finagent process data/documents
      
      \b
      # Recursive scan with custom collection
      finagent process data/documents -r --collection legal_docs_2024
      
      \b
      # Metadata extraction only (no indexing)
      finagent process data/documents --skip-indexing
    """
    try:
        dir_path = Path(directory).resolve()
        
        # Display pipeline header
        console.print(Panel.fit(
            "[bold cyan]Document Processing Pipeline[/bold cyan]",
            border_style="cyan"
        ))
        console.print()
        
        # Initialize components
        loader = DocumentLoader(base_path=str(dir_path))
        
        if not skip_metadata:
            extractor = MetadataExtractor(use_new_model=True)
        
        if not skip_indexing:
            chunker = ChineseTextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            indexer = DocumentIndexer(collection_name=collection)
        
        # Phase 1: Loading documents
        console.print("[bold]Phase 1: Loading documents[/bold]")
        with console.status("[bold green]Scanning directory..."):
            documents = loader.load_directory(str(dir_path), recursive=recursive, pattern=pattern)
        
        if not documents:
            console.print("[yellow]No documents found[/yellow]")
            return
        
        console.print(f"  Found [green]{len(documents)}[/green] files in {dir_path}\n")
        
        # Statistics
        total_chunks = 0
        metadata_extracted = 0
        metadata_failed = 0
        indexing_errors = 0
        
        async def run_pipeline():
            nonlocal total_chunks, metadata_extracted, metadata_failed, indexing_errors
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                # Phase 2: Metadata extraction
                if not skip_metadata:
                    console.print("[bold]Phase 2: Extracting metadata[/bold]")
                    meta_task = progress.add_task(
                        "[cyan]Extracting metadata...",
                        total=len(documents)
                    )
                    
                    for doc in documents:
                        try:
                            result = await extractor.extract_new(
                                doc_id=doc.id,
                                filename=doc.metadata.get("filename", doc.id),
                                content=doc.content
                            )
                            if result.metadata:
                                doc.metadata.update(result.metadata.dict())
                                metadata_extracted += 1
                            else:
                                metadata_failed += 1
                        except Exception:
                            metadata_failed += 1
                        
                        progress.update(meta_task, advance=1)
                    
                    console.print(f"  Metadata extracted: [green]{metadata_extracted}[/green] ({metadata_failed} failed)\n")
                
                # Phase 3 & 4: Chunking and Indexing
                if not skip_indexing:
                    console.print("[bold]Phase 3 & 4: Chunking and Indexing[/bold]")
                    index_task = progress.add_task(
                        "[green]Indexing documents...",
                        total=len(documents)
                    )
                    
                    for doc in documents:
                        try:
                            chunk_count = await indexer.index_document(doc)
                            total_chunks += chunk_count
                        except Exception:
                            indexing_errors += 1
                        
                        progress.update(index_task, advance=1)
        
        # Run async pipeline
        import time
        start_time = time.time()
        asyncio.run(run_pipeline())
        processing_time = time.time() - start_time
        
        # Final summary
        console.print()
        console.print(Panel.fit(
            "[bold green]✓ Pipeline completed successfully[/bold green]",
            border_style="green"
        ))
        console.print()
        
        console.print("[bold]Final Summary:[/bold]")
        console.print(f"  Documents processed: [cyan]{len(documents)}[/cyan]")
        
        if not skip_metadata:
            console.print(f"  Metadata extracted: [green]{metadata_extracted}[/green] ({metadata_failed} failed)")
        
        if not skip_indexing:
            console.print(f"  Total chunks: [green]{total_chunks}[/green]")
            console.print(f"  Indexed successfully: [green]{total_chunks - indexing_errors}[/green]")
            if indexing_errors > 0:
                console.print(f"  Indexing errors: [red]{indexing_errors}[/red]")
        
        console.print(f"  Processing time: [cyan]{processing_time:.1f}s[/cyan]")
        
    except Exception as e:
        print_error(f"Pipeline failed: {str(e)}")
        raise click.Abort()
