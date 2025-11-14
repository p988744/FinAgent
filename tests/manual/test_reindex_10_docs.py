#!/usr/bin/env python3
"""Test full reindex workflow with just 10 documents."""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()

def test_reindex_10_docs():
    """Test reindex with 10 documents to verify full pipeline."""

    console.print("=" * 80, style="bold cyan")
    console.print("TEST: Full Reindex with 10 Documents", style="bold cyan")
    console.print("=" * 80, style="bold cyan")
    console.print()

    # Get paths
    base_dir = Path(__file__).parent
    docs_path = base_dir / "data" / "documents"
    db_path = base_dir / "data" / "finagent.db"
    vector_db_path = base_dir / "data" / "vector_db"

    # Step 1: Get first 10 TXT files
    console.print("[cyan]Step 1: Finding first 10 documents...[/cyan]")
    all_docs = sorted(docs_path.rglob("*.txt"))
    test_docs = all_docs[:10]

    console.print(f"  Total documents available: {len(all_docs)}")
    console.print(f"  Selected for test: {len(test_docs)}")
    console.print()
    console.print("  Test documents:")
    for i, doc in enumerate(test_docs, 1):
        console.print(f"    {i}. {doc.name}")
    console.print()

    # Step 2: Clear database for these 10 documents
    console.print("[cyan]Step 2: Clearing test documents from database...[/cyan]")

    from finagent.database.db import Database
    db = Database()

    # Get doc IDs for these files
    test_doc_ids = []
    for doc_path in test_docs:
        # Generate doc_id same way as loader does
        doc_id = f"doc_{doc_path.stem}"
        test_doc_ids.append(doc_id)

        # Delete from database
        try:
            db.delete_document(doc_id)
            console.print(f"  Deleted: {doc_id}")
        except Exception:
            console.print(f"  Not in DB: {doc_id}")

    console.print()

    # Step 3: Create temporary test by limiting document loading
    console.print("[cyan]Step 3: Running reindex on 10 documents...[/cyan]")
    console.print()

    from finagent.document_processing.loader import DocumentLoader
    from finagent.document_processing.indexer import DocumentIndexer
    from finagent.document_processing.metadata_generator import MetadataGenerator
    from finagent.document_processing.metadata_store import DocumentMetadataStore, DocumentMetadata
    from finagent.document_processing.toc_generator import TableOfContents
    from finagent.document_processing.concept_extractor import (
        extract_document_concepts,
        infer_concept_type,
    )
    from finagent.database.models import Concept
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

    # Initialize components
    loader = DocumentLoader(base_path=str(docs_path))
    indexer = DocumentIndexer(
        collection_name="legal_documents",
        persist_directory=str(vector_db_path)
    )
    metadata_generator = MetadataGenerator()
    metadata_store = DocumentMetadataStore()
    toc = TableOfContents()

    # Load only first 10 documents
    all_documents = loader.load_directory(".", pattern="*.txt", recursive=True)
    documents = all_documents[:10]

    console.print(f"[green]✅ Loaded {len(documents)} documents for testing[/green]")
    console.print()

    # Process documents
    total_indexed = 0
    total_chunks = 0
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing documents...", total=len(documents))

        for i, doc in enumerate(documents, 1):
            filename = doc.metadata.get("filename", "unknown")

            try:
                # Step 1: Index to vector DB
                progress.update(task, description=f"[blue]📊 Indexing: {filename[:40]}...")
                chunks = indexer.index_document(doc)
                total_chunks += chunks

                # Step 2: Generate metadata with LLM
                progress.update(task, description=f"[magenta]🤖 Analyzing: {filename[:40]}...")
                metadata = metadata_generator.generate_metadata(
                    doc_id=doc.id,
                    filename=filename,
                    content=doc.content
                )

                # Step 3: Save to database
                progress.update(task, description=f"[green]💾 Saving: {filename[:40]}...")
                file_path = doc.metadata.get("file_path") or doc.source or ""
                metadata.indexed = True
                metadata.chunk_count = chunks
                metadata_store.add_metadata(metadata, file_path=file_path)

                # Step 4: Extract and link concepts
                progress.update(task, description=f"[yellow]🔗 Concepts: {filename[:40]}...")
                doc_concepts = extract_document_concepts(metadata)

                linked_concepts = []
                for concept_name in doc_concepts[:5]:  # Limit to 5 concepts per doc for test
                    concept = db.get_concept_by_name(concept_name)
                    if not concept:
                        concept = Concept(
                            concept_name=concept_name,
                            concept_type=infer_concept_type(concept_name, metadata),
                            description=f"從文件元資料提取的概念",
                            keywords=[],
                        )
                        concept = db.add_concept(concept)

                    db.link_document_concept(doc.id, concept.id, relevance_score=1.0)
                    linked_concepts.append(concept_name)

                total_indexed += 1

                # Store result
                results.append({
                    "filename": filename,
                    "doc_id": doc.id,
                    "chunks": chunks,
                    "doc_type": metadata.document_type,
                    "authority": metadata.issuing_authority,
                    "penalty": metadata.penalty_amount,
                    "violations": metadata.violation_types,
                    "concepts": linked_concepts,
                    "keywords": metadata.keywords[:5],
                })

                progress.update(
                    task,
                    advance=1,
                    description=f"[green]✓ {filename[:40]}... ({chunks} chunks)",
                )

            except Exception as e:
                progress.update(
                    task,
                    advance=1,
                    description=f"[red]✗ {filename[:40]}...",
                )
                console.print(f"\n[red]Error processing {filename}: {e}[/red]")
                results.append({
                    "filename": filename,
                    "error": str(e),
                })

    # Update TABLE_OF_CONTENTS.md
    console.print()
    console.print("[cyan]Updating TABLE_OF_CONTENTS.md...[/cyan]")
    toc.save()

    # Print results
    console.print()
    console.print("=" * 80, style="bold green")
    console.print("TEST RESULTS", style="bold green")
    console.print("=" * 80, style="bold green")
    console.print()

    console.print(f"[bold]Summary:[/bold]")
    console.print(f"  ✅ Successfully indexed: {total_indexed} documents")
    console.print(f"  📦 Total chunks: {total_chunks}")
    console.print(f"  📊 Average chunks per doc: {total_chunks / total_indexed if total_indexed > 0 else 0:.1f}")
    console.print()

    # Show detailed results
    console.print(f"[bold]Detailed Results:[/bold]")
    console.print()

    for i, result in enumerate(results, 1):
        if "error" in result:
            console.print(f"{i}. [red]❌ {result['filename']}[/red]")
            console.print(f"   Error: {result['error']}")
        else:
            console.print(f"{i}. [green]✅ {result['filename']}[/green]")
            console.print(f"   Doc ID: {result['doc_id']}")
            console.print(f"   Chunks: {result['chunks']}")
            console.print(f"   Type: {result['doc_type']}")
            console.print(f"   Authority: {result['authority']}")
            console.print(f"   Penalty: {result['penalty']}")
            console.print(f"   Violations: {', '.join(result['violations']) if result['violations'] else 'None'}")
            console.print(f"   Concepts: {', '.join(result['concepts'][:3]) if result['concepts'] else 'None'}")
            console.print(f"   Keywords: {', '.join(result['keywords'][:3]) if result['keywords'] else 'None'}")
        console.print()

    # Verify database
    console.print("=" * 80, style="bold cyan")
    console.print("DATABASE VERIFICATION", style="bold cyan")
    console.print("=" * 80, style="bold cyan")
    console.print()

    # Check documents table
    all_db_docs = db.get_all_documents()
    indexed_docs = [d for d in all_db_docs if d.indexed]

    console.print(f"[bold]Documents in database:[/bold]")
    console.print(f"  Total documents: {len(all_db_docs)}")
    console.print(f"  Indexed documents: {len(indexed_docs)}")
    console.print(f"  Test documents: {total_indexed}")
    console.print()

    # Check concepts
    all_concepts = db.get_all_concepts()
    top_concepts = db.get_top_concepts(10)

    console.print(f"[bold]Concepts in database:[/bold]")
    console.print(f"  Total concepts: {len(all_concepts)}")
    console.print()
    console.print(f"  Top 10 concepts by document count:")
    for concept in top_concepts:
        console.print(f"    • {concept.concept_name} ({concept.concept_type}): {concept.document_count} docs")
    console.print()

    # Check vector DB
    try:
        with sqlite3.connect(vector_db_path / "chroma.sqlite3") as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
            embedding_count = cursor.fetchone()[0]
            console.print(f"[bold]Vector database:[/bold]")
            console.print(f"  Total embeddings: {embedding_count}")
            console.print()
    except Exception as e:
        console.print(f"[yellow]Could not check vector DB: {e}[/yellow]")
        console.print()

    # Final verdict
    console.print("=" * 80, style="bold green")

    success = total_indexed == len(documents) and total_indexed > 0

    if success:
        console.print("✅ TEST PASSED", style="bold green")
        console.print()
        console.print("All documents processed successfully with:")
        console.print("  ✅ Vector indexing")
        console.print("  ✅ LLM metadata generation")
        console.print("  ✅ Database storage")
        console.print("  ✅ Concept extraction")
        console.print("  ✅ TOC update")
    else:
        console.print("❌ TEST FAILED", style="bold red")
        console.print()
        console.print(f"Expected {len(documents)} documents, got {total_indexed}")

    console.print("=" * 80, style="bold green")

    return success


if __name__ == "__main__":
    try:
        success = test_reindex_10_docs()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        exit(1)
    except Exception as e:
        console.print(f"\n[red]Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        exit(1)
