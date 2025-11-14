"""Test semantic query expansion and concept-based retrieval."""

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from finagent.document_processing.semantic_mapper import (
    expand_query_with_concepts,
    get_documents_by_concepts,
)
from finagent.document_processing.retriever import DocumentRetriever
from finagent.models.queries import Query

console = Console()


def test_query_expansion():
    """Test query expansion with various queries."""
    console.print("\n[cyan]═══ Semantic Query Expansion Tests ═══[/cyan]\n")

    test_queries = [
        "洗錢防制案件",
        "銀行內部控制",
        "內線交易裁罰",
        "資訊揭露違規",
        "金管會對保險公司的裁罰",
    ]

    for query_text in test_queries:
        console.print(f"\n[yellow]Query:[/yellow] [bold]{query_text}[/bold]\n")

        # Expand query
        expansion = expand_query_with_concepts(query_text)

        # Display results
        console.print(f"  [cyan]Original terms extracted:[/cyan] {', '.join(expansion['original_terms'])}")

        if expansion["concepts"]:
            console.print(f"\n  [green]✓ Matched {len(expansion['concepts'])} concept(s):[/green]")
            for concept_key, concept_name, synonyms in expansion["concept_details"]:
                console.print(f"\n    • [bold]{concept_name}[/bold] ({concept_key})")
                console.print(f"      Synonyms ({len(synonyms)}): {', '.join(synonyms[:5])}")
                if len(synonyms) > 5:
                    console.print(f"      ... and {len(synonyms) - 5} more")

            console.print(f"\n  [magenta]Expanded search keywords ({len(expansion['search_keywords'])}):[/magenta]")
            console.print(f"    {', '.join(expansion['search_keywords'][:15])}")
            if len(expansion["search_keywords"]) > 15:
                console.print(f"    ... and {len(expansion['search_keywords']) - 15} more")

            # Get matching documents
            matching_docs = get_documents_by_concepts(expansion["concepts"])
            console.print(f"\n  [blue]📄 Matching documents: {len(matching_docs)}[/blue]")
            if matching_docs:
                for doc in matching_docs[:5]:
                    console.print(f"    - {doc}")
                if len(matching_docs) > 5:
                    console.print(f"    ... and {len(matching_docs) - 5} more")

        else:
            console.print("  [dim]No semantic concepts matched[/dim]")

        console.print("\n" + "─" * 80)


def test_concept_filtering_comparison():
    """Compare retrieval with and without concept filtering."""
    console.print("\n[cyan]═══ Concept Filtering Comparison ═══[/cyan]\n")

    test_queries = [
        "洗錢防制案件",
        "內部控制缺失",
        "資訊揭露違規",
    ]

    retriever = DocumentRetriever()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Query", style="yellow", width=20)
    table.add_column("Without Filtering", justify="right", style="white")
    table.add_column("With Filtering", justify="right", style="green")
    table.add_column("Concepts Used", style="dim", width=30)

    for query_text in test_queries:
        # Expand query to get concepts
        expansion = expand_query_with_concepts(query_text)
        concepts_str = ", ".join([name for _, name, _ in expansion["concept_details"]])

        try:
            # Standard retrieval (without filtering)
            standard_results = retriever.retrieve(query_text, n_results=10)
            standard_count = len(standard_results)
        except:
            standard_count = 0

        try:
            # Concept-filtered retrieval
            filtered_results = retriever.retrieve_with_concept_filtering(
                query_text, n_results=10, use_concept_filtering=True
            )
            filtered_count = len(filtered_results)
        except:
            filtered_count = 0

        table.add_row(
            query_text[:18] + "..." if len(query_text) > 20 else query_text,
            str(standard_count),
            str(filtered_count),
            concepts_str[:28] + "..." if len(concepts_str) > 30 else concepts_str,
        )

    console.print(table)
    console.print("\n[dim]Note: Filtered retrieval narrows search to concept-matched documents[/dim]")


async def test_end_to_end_query():
    """Test end-to-end query with planning agent integration."""
    console.print("\n[cyan]═══ End-to-End Query Test ═══[/cyan]\n")

    from finagent.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()

    test_queries = [
        "洗錢防制案件有哪些？",
        "銀行內部控制缺失的裁罰",
    ]

    for query_text in test_queries:
        console.print(f"\n[yellow]Query:[/yellow] [bold]{query_text}[/bold]\n")

        # Show query expansion
        expansion = expand_query_with_concepts(query_text)
        if expansion["concepts"]:
            console.print(f"  [green]Concepts matched:[/green] {', '.join([name for _, name, _ in expansion['concept_details']])}")
            console.print(f"  [magenta]Expanded keywords:[/magenta] {len(expansion['search_keywords'])} terms")

        # Execute query
        query = Query(text=query_text)
        try:
            answer = await orchestrator.process_query(query)

            # Show results
            console.print(f"\n  [cyan]Processing steps:[/cyan] {len(answer.processing_steps)}")
            console.print(f"  [cyan]Citations found:[/cyan] {len(answer.citations)}")
            console.print(f"  [cyan]Confidence:[/cyan] {answer.confidence}")

            # Show summary
            if answer.summary:
                panel = Panel(
                    answer.summary[:200] + "..." if len(answer.summary) > 200 else answer.summary,
                    title="Answer Summary",
                    border_style="green",
                )
                console.print(panel)

        except Exception as e:
            console.print(f"  [red]Error:[/red] {e}")

        console.print("\n" + "─" * 80)


def show_expansion_statistics():
    """Show overall statistics about query expansion coverage."""
    console.print("\n[cyan]═══ Query Expansion Statistics ═══[/cyan]\n")

    # Test various query patterns
    patterns = {
        "Violation types": ["洗錢", "內線交易", "資訊揭露", "市場操縱"],
        "Institutions": ["銀行", "證券商", "保險公司", "金控"],
        "Authorities": ["金管會", "中央銀行", "公平會"],
        "Mixed queries": ["銀行洗錢案件", "證券商內線交易", "保險公司資訊揭露"],
    }

    for category, queries in patterns.items():
        console.print(f"\n[yellow]{category}:[/yellow]")

        for query in queries:
            expansion = expand_query_with_concepts(query)
            concepts_count = len(expansion["concepts"])
            expanded_count = len(expansion["expanded_terms"])

            status = "[green]✓[/green]" if concepts_count > 0 else "[dim]○[/dim]"
            console.print(
                f"  {status} {query:20} → {concepts_count} concepts, {expanded_count} synonyms"
            )


if __name__ == "__main__":
    # Test 1: Query expansion
    test_query_expansion()

    # Test 2: Statistics
    show_expansion_statistics()

    # Test 3: Concept filtering comparison
    test_concept_filtering_comparison()

    # Test 4: End-to-end (async)
    print("\n")
    asyncio.run(test_end_to_end_query())

    console.print("\n[green]✓ All tests complete[/green]\n")
