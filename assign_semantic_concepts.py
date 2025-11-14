"""Batch assign semantic concepts to all indexed documents."""

import sqlite3
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from finagent.document_processing.metadata_store import DocumentMetadata
from finagent.document_processing.semantic_mapper import (
    assign_concepts_to_document,
    get_document_concepts,
)

console = Console()


def get_all_documents(db_path: str = "data/finagent.db") -> list[tuple[str, dict]]:
    """
    Get all documents from database with their metadata.

    Returns:
        List of (filename, metadata_dict) tuples
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT filename, document_type, keywords, issuing_authority,
               related_institutions, violation_types
        FROM documents
        WHERE indexed = 1
        ORDER BY filename
    """
    )

    documents = []
    for row in cursor.fetchall():
        filename, doc_type, keywords, authority, institutions, violations = row

        # Parse JSON fields
        import json

        try:
            keywords_list = json.loads(keywords) if keywords else []
        except:
            keywords_list = []

        try:
            institutions_list = json.loads(institutions) if institutions else []
        except:
            institutions_list = []

        try:
            violations_list = json.loads(violations) if violations else []
        except:
            violations_list = []

        metadata_dict = {
            "filename": filename,
            "document_type": doc_type or "",
            "keywords": keywords_list,
            "issuing_authority": authority or "",
            "related_institutions": institutions_list,
            "violation_types": violations_list,
        }

        documents.append((filename, metadata_dict))

    conn.close()
    return documents


def main(db_path: str = "data/finagent.db", verbose: bool = True):
    """
    Assign semantic concepts to all indexed documents.

    Args:
        db_path: Path to database
        verbose: Show detailed progress
    """
    console.print("\n[cyan]📚 Semantic Concept Assignment[/cyan]\n")

    # Get all documents
    console.print("[yellow]Fetching documents from database...[/yellow]")
    documents = get_all_documents(db_path)
    console.print(f"[green]✓[/green] Found {len(documents)} indexed documents\n")

    if not documents:
        console.print("[yellow]No documents to process[/yellow]")
        return

    # Process documents with progress bar
    total_mappings = 0
    successful = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Assigning concepts...", total=len(documents))

        for filename, metadata_dict in documents:
            try:
                # Assign concepts using metadata fields
                assigned = assign_concepts_to_document(
                    filename=filename,
                    violation_types=metadata_dict["violation_types"],
                    related_institutions=metadata_dict["related_institutions"],
                    issuing_authority=metadata_dict["issuing_authority"],
                    keywords=metadata_dict["keywords"],
                    db_path=db_path,
                )

                if assigned:
                    total_mappings += len(assigned)
                    successful += 1

                    if verbose:
                        concept_summary = ", ".join(
                            [f"{key} ({conf:.1f})" for key, conf in assigned[:3]]
                        )
                        if len(assigned) > 3:
                            concept_summary += f" +{len(assigned) - 3} more"
                        console.print(
                            f"  [green]✓[/green] {filename[:50]:50} → [{concept_summary}]"
                        )
                else:
                    if verbose:
                        console.print(f"  [dim]○[/dim] {filename[:50]:50} → [dim]No concepts[/dim]")

            except Exception as e:
                failed += 1
                console.print(f"  [red]✗[/red] {filename[:50]:50} → Error: {e}")

            progress.update(task, advance=1)

    # Summary
    console.print("\n[cyan]Summary:[/cyan]")
    console.print(f"  Total documents: {len(documents)}")
    console.print(f"  [green]Successfully assigned: {successful}[/green]")
    console.print(f"  [yellow]No concepts found: {len(documents) - successful - failed}[/yellow]")
    if failed > 0:
        console.print(f"  [red]Failed: {failed}[/red]")
    console.print(f"  [cyan]Total concept mappings: {total_mappings}[/cyan]")

    # Show statistics by concept
    console.print("\n[cyan]Concept Distribution:[/cyan]")
    show_concept_statistics(db_path)


def show_concept_statistics(db_path: str = "data/finagent.db"):
    """Show statistics of concept assignments."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT sc.name_zh, sc.concept_key, COUNT(DISTINCT dsc.filename) as doc_count,
               AVG(dsc.confidence) as avg_confidence
        FROM semantic_concepts sc
        LEFT JOIN document_semantic_concepts dsc ON sc.concept_key = dsc.concept_key
        GROUP BY sc.concept_key, sc.name_zh
        HAVING doc_count > 0
        ORDER BY doc_count DESC
        LIMIT 15
    """
    )

    results = cursor.fetchall()
    conn.close()

    if results:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Concept", style="cyan", width=25)
        table.add_column("Key", style="dim", width=30)
        table.add_column("Documents", justify="right", style="green")
        table.add_column("Avg Confidence", justify="right", style="yellow")

        for name_zh, concept_key, doc_count, avg_conf in results:
            table.add_row(name_zh, concept_key, str(doc_count), f"{avg_conf:.2f}")

        console.print(table)
    else:
        console.print("[dim]No concept assignments found[/dim]")


def test_assignment_sample(db_path: str = "data/finagent.db", limit: int = 5):
    """
    Test concept assignment on a sample of documents.

    Args:
        db_path: Path to database
        limit: Number of documents to test
    """
    console.print("\n[cyan]🧪 Testing Concept Assignment (Sample)[/cyan]\n")

    documents = get_all_documents(db_path)[:limit]

    for filename, metadata_dict in documents:
        console.print(f"\n[yellow]Document:[/yellow] {filename}")
        console.print(f"  Type: {metadata_dict['document_type']}")
        console.print(f"  Authority: {metadata_dict['issuing_authority']}")
        console.print(f"  Violations: {metadata_dict['violation_types']}")
        console.print(f"  Institutions: {metadata_dict['related_institutions']}")

        # Assign concepts
        assigned = assign_concepts_to_document(
            filename=filename,
            violation_types=metadata_dict["violation_types"],
            related_institutions=metadata_dict["related_institutions"],
            issuing_authority=metadata_dict["issuing_authority"],
            keywords=metadata_dict["keywords"],
            db_path=db_path,
        )

        if assigned:
            console.print(f"\n  [green]✓ Assigned {len(assigned)} concepts:[/green]")
            for concept_key, confidence in assigned:
                console.print(f"    • {concept_key:30} (confidence: {confidence:.2f})")
        else:
            console.print(f"\n  [dim]No concepts assigned[/dim]")

        # Verify in database
        db_concepts = get_document_concepts(filename, db_path)
        if db_concepts:
            console.print(f"\n  [cyan]Database verification:[/cyan]")
            for concept_key, name_zh, confidence in db_concepts:
                console.print(f"    • {name_zh:15} ({concept_key:30}) - {confidence:.2f}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode: process sample and show details
        test_assignment_sample(limit=10)
    else:
        # Production mode: process all documents
        main(verbose=False)  # Set verbose=True to see each document
