#!/usr/bin/env python3
"""Search documents by concept - faster than full vector search."""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finagent.database.db import Database

console = Console()


def search_by_concept(query: str, max_results: int = 10):
    """
    Search documents by concept name.

    This is much faster than vector search because we pre-filter documents
    based on concept matches before doing semantic search.

    Args:
        query: Concept to search for (e.g., "金管會", "洗錢防制")
        max_results: Maximum number of results to return
    """
    console.print()
    console.print(Panel.fit(f"🔍 Search by Concept: [cyan]{query}[/cyan]", style="bold yellow"))
    console.print()

    db = Database()

    # Step 1: Search for matching concepts
    console.print(f"[dim]Step 1: Searching for concepts matching '{query}'...[/dim]")
    matching_concepts = db.search_concepts(query)

    if not matching_concepts:
        console.print(f"[yellow]No concepts found matching '{query}'[/yellow]")
        console.print()
        console.print("[dim]Try one of these popular concepts:[/dim]")

        # Show top concepts
        top_concepts = db.get_top_concepts(10)
        for i, concept in enumerate(top_concepts, 1):
            console.print(f"  {i}. {concept.concept_name} [{concept.concept_type}] ({concept.document_count} docs)")

        console.print()
        return

    console.print(f"[green]✓ Found {len(matching_concepts)} matching concept(s)[/green]")
    console.print()

    # Show matching concepts
    concepts_table = Table(title="Matching Concepts", show_header=True)
    concepts_table.add_column("#", style="dim", width=4)
    concepts_table.add_column("Concept", style="cyan", width=40)
    concepts_table.add_column("Type", style="yellow", width=15)
    concepts_table.add_column("Documents", style="green", width=10)
    concepts_table.add_column("Description", style="blue", width=50)

    for i, concept in enumerate(matching_concepts[:5], 1):
        desc = (concept.description or "")[:47] + "..." if concept.description and len(concept.description) > 50 else (concept.description or "")
        concepts_table.add_row(
            str(i),
            concept.concept_name,
            concept.concept_type or "未分類",
            str(concept.document_count),
            desc
        )

    console.print(concepts_table)
    console.print()

    # Step 2: Get all documents for these concepts
    console.print(f"[dim]Step 2: Retrieving documents linked to these concepts...[/dim]")

    all_documents = []
    concept_doc_map = {}  # doc_id -> [concept_names]

    for concept in matching_concepts:
        docs = db.get_concept_documents(concept.id)
        for doc in docs:
            if doc.doc_id not in concept_doc_map:
                concept_doc_map[doc.doc_id] = []
                all_documents.append(doc)
            concept_doc_map[doc.doc_id].append(concept.concept_name)

    # Deduplicate and limit
    unique_docs = all_documents[:max_results]

    console.print(f"[green]✓ Found {len(all_documents)} document(s) ({len(unique_docs)} shown)[/green]")
    console.print()

    if not unique_docs:
        console.print("[yellow]No documents found for these concepts[/yellow]")
        console.print()
        return

    # Step 3: Display results
    console.print(Panel.fit("📄 SEARCH RESULTS", style="bold green"))
    console.print()

    results_table = Table(show_header=True)
    results_table.add_column("#", style="dim", width=4)
    results_table.add_column("Document", style="cyan", width=45)
    results_table.add_column("Type", style="yellow", width=10)
    results_table.add_column("Authority", style="green", width=12)
    results_table.add_column("Concepts", style="magenta", width=35)

    for i, doc in enumerate(unique_docs, 1):
        filename = doc.filename[:42] + "..." if len(doc.filename) > 45 else doc.filename
        dtype = (doc.document_type or "未分類")[:8]
        auth = (doc.issuing_authority or "未指定")[:10]

        # Get concepts for this doc
        doc_concepts = concept_doc_map.get(doc.doc_id, [])
        concepts_str = ", ".join(doc_concepts[:2])
        if len(doc_concepts) > 2:
            concepts_str += f" +{len(doc_concepts)-2}"
        concepts_str = concepts_str[:32] + "..." if len(concepts_str) > 35 else concepts_str

        results_table.add_row(
            str(i),
            filename,
            dtype,
            auth,
            concepts_str
        )

    console.print(results_table)
    console.print()

    # Show detailed info for first result
    if unique_docs:
        console.print(Panel.fit("📋 FIRST RESULT DETAILS", style="bold blue"))
        console.print()

        first_doc = unique_docs[0]

        console.print(f"[bold]Document:[/bold] {first_doc.filename}")
        console.print(f"[bold]Doc ID:[/bold] {first_doc.doc_id}")
        console.print(f"[bold]Type:[/bold] {first_doc.document_type or '未分類'}")
        console.print(f"[bold]Authority:[/bold] {first_doc.issuing_authority or '未指定'}")
        console.print(f"[bold]Penalty:[/bold] {first_doc.penalty_amount or 'N/A'}")
        console.print(f"[bold]Date:[/bold] {first_doc.document_date or 'N/A'}")
        console.print()

        if first_doc.description:
            console.print(f"[bold]Description:[/bold]")
            console.print(f"  {first_doc.description}")
            console.print()

        # Show all concepts for first doc
        all_doc_concepts = db.get_document_concepts(first_doc.doc_id)
        if all_doc_concepts:
            console.print(f"[bold]All Concepts ({len(all_doc_concepts)}):[/bold]")
            for concept in all_doc_concepts[:10]:
                console.print(f"  • {concept.concept_name} [{concept.concept_type}]")
            if len(all_doc_concepts) > 10:
                console.print(f"  ... and {len(all_doc_concepts) - 10} more")
            console.print()

        # Show keywords
        if first_doc.keywords:
            console.print(f"[bold]Keywords:[/bold]")
            console.print(f"  {', '.join(first_doc.keywords[:10])}")
            console.print()

        # Show violation types
        if first_doc.violation_types:
            console.print(f"[bold]Violation Types:[/bold]")
            console.print(f"  {', '.join(first_doc.violation_types)}")
            console.print()

    # Performance note
    console.print()
    console.print(Panel(
        f"[green]✨ Concept-based search[/green]\n"
        f"Pre-filtered to {len(all_documents)} documents using concepts\n"
        f"Much faster than searching all {db.get_document_statistics().get('total_documents', 0)} documents!",
        title="Performance",
        style="dim"
    ))
    console.print()

    return unique_docs


def list_all_concepts(concept_type: str = None, limit: int = 50):
    """List all concepts, optionally filtered by type."""

    console.print()
    console.print(Panel.fit("📚 ALL CONCEPTS", style="bold yellow"))
    console.print()

    db = Database()

    if concept_type:
        concepts = db.get_concepts_by_type(concept_type)
        title = f"Concepts of Type: {concept_type}"
    else:
        concepts = db.get_all_concepts()
        title = "All Concepts"

    # Sort by document count
    concepts = sorted(concepts, key=lambda c: c.document_count, reverse=True)[:limit]

    if not concepts:
        console.print("[yellow]No concepts found[/yellow]")
        console.print()
        return

    console.print(f"[green]Found {len(concepts)} concepts[/green]")
    console.print()

    # Group by type
    by_type = {}
    for concept in concepts:
        ctype = concept.concept_type or "未分類"
        if ctype not in by_type:
            by_type[ctype] = []
        by_type[ctype].append(concept)

    # Display by type
    for ctype in ["violation_type", "authority", "institution", "topic", "未分類"]:
        if ctype not in by_type:
            continue

        type_concepts = by_type[ctype]

        console.print(f"[bold cyan]{ctype.upper()}[/bold cyan] ({len(type_concepts)} concepts)")
        console.print()

        table = Table(show_header=True, box=None)
        table.add_column("Concept", style="cyan", width=45)
        table.add_column("Docs", style="green", width=8)
        table.add_column("Description", style="yellow", width=50)

        for concept in type_concepts[:20]:
            name = concept.concept_name[:42] + "..." if len(concept.concept_name) > 45 else concept.concept_name
            desc = (concept.description or "")[:47] + "..." if concept.description and len(concept.description) > 50 else (concept.description or "")

            table.add_row(
                name,
                str(concept.document_count),
                desc
            )

        console.print(table)
        console.print()


def main():
    """Main entry point for concept search tool."""

    if len(sys.argv) < 2:
        console.print()
        console.print("[bold yellow]Concept Search Tool[/bold yellow]")
        console.print()
        console.print("[bold]Usage:[/bold]")
        console.print("  python search_by_concept.py <query>          # Search by concept")
        console.print("  python search_by_concept.py --list           # List all concepts")
        console.print("  python search_by_concept.py --list <type>    # List concepts by type")
        console.print()
        console.print("[bold]Examples:[/bold]")
        console.print("  python search_by_concept.py 金管會")
        console.print("  python search_by_concept.py 洗錢防制")
        console.print("  python search_by_concept.py 玉山銀行")
        console.print("  python search_by_concept.py --list")
        console.print("  python search_by_concept.py --list violation_type")
        console.print("  python search_by_concept.py --list authority")
        console.print()
        console.print("[bold]Concept Types:[/bold]")
        console.print("  • violation_type - Violation types (洗錢防制, 內線交易, etc.)")
        console.print("  • authority - Issuing authorities (金管會, 中央銀行, etc.)")
        console.print("  • institution - Institutions (玉山銀行, 國泰世華, etc.)")
        console.print("  • topic - General topics")
        console.print()
        return

    # Parse arguments
    if sys.argv[1] == "--list":
        if len(sys.argv) > 2:
            list_all_concepts(concept_type=sys.argv[2])
        else:
            list_all_concepts()
    else:
        query = " ".join(sys.argv[1:])
        search_by_concept(query)


if __name__ == "__main__":
    main()
