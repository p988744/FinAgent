"""
Index command - Index documents into ChromaDB vector store
"""

import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn

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
    help="Collection name (default: legal_documents)"
)
@click.option(
    "--chunk-size",
    type=int,
    default=500,
    help="Chunk size in characters (default: 500)"
)
@click.option(
    "--chunk-overlap",
    type=int,
    default=50,
    help="Overlap size in characters (default: 50)"
)
@click.option(
    "--extract-metadata",
    is_flag=True,
    help="Extract metadata before indexing"
)
@click.option(
    "--batch-size",
    type=int,
    default=10,
    help="Index N documents at a time (default: 10)"
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing collection before indexing"
)
@click.option(
    "--recursive", "-r",
    is_flag=True,
    help="Scan subdirectories"
)
def index(
    directory: str,
    collection: str,
    chunk_size: int,
    chunk_overlap: int,
    extract_metadata: bool,
    batch_size: int,
    clear: bool,
    recursive: bool
):
    """
    Index documents into ChromaDB vector store.
    
    Examples:
    
      \b
      # Index all documents
      finagent index data/documents
      
      \b
      # Clear and re-index with custom collection
      finagent index data/documents --collection my_docs --clear
      
      \b
      # Index with metadata extraction
      finagent index data/documents --extract-metadata
    """
    try:
        dir_path = Path(directory).resolve()
        console.print(f"[bold]Indexing documents from:[/bold] {dir_path}")
        console.print(f"[dim]Collection: {collection}, Chunk size: {chunk_size}, Overlap: {chunk_overlap}[/dim]\n")
        
        # Initialize components
        loader = DocumentLoader(base_path=str(dir_path))
        chunker = ChineseTextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        indexer = DocumentIndexer(collection_name=collection)
        
        if extract_metadata:
            extractor = MetadataExtractor(use_new_model=True)
        
        # Clear collection if requested
        if clear:
            with console.status("[bold yellow]Clearing collection..."):
                indexer.clear_collection()
            print_success(f"Cleared collection '{collection}'")
        
        # Load documents
        with console.status("[bold green]Loading documents..."):
            documents = loader.load_directory(str(dir_path), recursive=recursive)
        
        if not documents:
            console.print("[yellow]No documents found[/yellow]")
            return
        
        console.print(f"[green]Found {len(documents)} documents[/green]\n")
        
        # Process documents
        total_chunks = 0
        errors = 0
        
        async def process_documents():
            nonlocal total_chunks, errors

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total} ({task.percentage:>3.0f}%)"),
                TextColumn("|"),
                TimeElapsedColumn(),
                TextColumn("|"),
                TimeRemainingColumn(),
                TextColumn("|"),
                TextColumn("{task.fields[current_file]}"),
                console=console
            ) as progress:

                # ★★ 關鍵：這裡要先定義 current_file，不然會噴 KeyError ★★
                task = progress.add_task(
                    description="[green]Processing[/green]",
                    total=len(documents),
                    current_file=""     # ← 必須有這行
                )

                for i, doc in enumerate(documents, start=1):
                    try:
                        filename = doc.metadata.get("filename", doc.id)

                        # 更新 task 的 custom field
                        progress.update(
                            task,
                            current_file=f" {filename}"
                        )

                        # Metadata extraction
                        if extract_metadata:
                            result = await extractor.extract_new(
                                doc_id=doc.id,
                                filename=filename,
                                content=doc.content
                            )
                            if result.metadata:
                                doc.metadata.update(result.metadata.dict())

                        # Indexing
                        chunk_count = await indexer.index_document(doc)
                        total_chunks += chunk_count

                    except Exception as e:
                        errors += 1
                        console.print(f"[red]Error indexing {filename}: {str(e)}[/red]")

                    progress.update(task, advance=1)
        
        # Run async processing
        asyncio.run(process_documents())
        
        # Get collection stats
        stats = indexer.get_collection_stats()
        
        # Print summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Documents processed: [cyan]{len(documents)}[/cyan]")
        console.print(f"  Total chunks indexed: [green]{total_chunks}[/green]")
        console.print(f"  Average chunks per doc: [cyan]{total_chunks // len(documents) if documents else 0}[/cyan]")
        console.print(f"  Errors: [red]{errors}[/red]")
        console.print(f"  Collection total chunks: [cyan]{stats['total_chunks']}[/cyan]")
        
        if errors == 0:
            print_success("Indexing completed successfully")
        else:
            print_warning(f"Indexing completed with {errors} errors")
        
    except Exception as e:
        print_error(f"Indexing failed: {str(e)}")
        raise click.Abort()
