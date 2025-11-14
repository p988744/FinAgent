"""Test 6 queries to verify semantic concepts system end-to-end."""

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.document_processing.semantic_mapper import expand_query_with_concepts
from finagent.models.queries import Query

console = Console()


async def test_query(query_text: str, orchestrator: AgentOrchestrator):
    """Test a single query and show expansion + results."""
    console.print(f"\n[yellow]{'='*80}[/yellow]")
    console.print(f"[cyan]Query {test_query.counter}:[/cyan] [bold]{query_text}[/bold]")
    console.print(f"[yellow]{'='*80}[/yellow]\n")
    test_query.counter += 1

    # Step 1: Show query expansion
    console.print("[magenta]Step 1: Query Expansion[/magenta]")
    expansion = expand_query_with_concepts(query_text)

    console.print(f"  Original terms: {', '.join(expansion['original_terms'])}")

    if expansion["concepts"]:
        console.print(f"\n  [green]✓ Matched {len(expansion['concepts'])} concept(s):[/green]")
        for concept_key, concept_name, synonyms in expansion["concept_details"]:
            console.print(f"    • {concept_name} ({concept_key})")
            console.print(f"      Synonyms: {', '.join(synonyms[:8])}")
            if len(synonyms) > 8:
                console.print(f"      ... and {len(synonyms) - 8} more")

        console.print(f"\n  [blue]Total expanded keywords: {len(expansion['search_keywords'])}[/blue]")
    else:
        console.print("  [dim]No semantic concepts matched (using standard retrieval)[/dim]")

    # Step 2: Execute query
    console.print(f"\n[magenta]Step 2: Query Execution[/magenta]")
    query = Query(text=query_text)

    try:
        answer = await orchestrator.process_query(query)

        # Show results
        console.print(f"  [green]✓ Query completed successfully[/green]")
        console.print(f"  Processing steps: {len(answer.processing_steps)}")
        console.print(f"  Citations found: {len(answer.citations)}")
        confidence = getattr(answer, "confidence_level", getattr(answer, "confidence", "N/A"))
        console.print(f"  Confidence level: {confidence}")

        # Show summary
        if answer.summary:
            summary_preview = answer.summary[:300] + "..." if len(answer.summary) > 300 else answer.summary
            panel = Panel(
                summary_preview,
                title="[cyan]Answer Summary[/cyan]",
                border_style="green",
                padding=(1, 2),
            )
            console.print(f"\n{panel}")

        # Show citations
        if answer.citations:
            console.print(f"\n[cyan]Top Citations:[/cyan]")
            for i, citation in enumerate(answer.citations[:3], 1):
                console.print(f"  [{i}] {citation.title}")
                if citation.source:
                    console.print(f"      Source: {citation.source[:60]}...")

        # Show key findings
        if answer.key_findings:
            console.print(f"\n[cyan]Key Findings ({len(answer.key_findings)}):[/cyan]")
            for i, finding in enumerate(answer.key_findings[:3], 1):
                finding_preview = finding[:80] + "..." if len(finding) > 80 else finding
                console.print(f"  {i}. {finding_preview}")

        return {
            "query": query_text,
            "concepts": len(expansion["concepts"]),
            "expanded_keywords": len(expansion["search_keywords"]),
            "citations": len(answer.citations),
            "confidence": answer.confidence_level,
            "success": True,
        }

    except Exception as e:
        console.print(f"  [red]✗ Error: {str(e)[:200]}[/red]")
        return {
            "query": query_text,
            "concepts": len(expansion["concepts"]),
            "expanded_keywords": len(expansion["search_keywords"]),
            "citations": 0,
            "confidence": "N/A",
            "success": False,
            "error": str(e)[:100],
        }


# Initialize counter
test_query.counter = 1


async def main():
    """Run all 6 test queries."""
    console.print("\n[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]")
    console.print("[cyan bold]        Semantic Concepts System - 6 Query Test        [/cyan bold]")
    console.print("[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]\n")

    # Test queries covering different concepts
    test_queries = [
        "洗錢防制案件有哪些？",  # AML
        "銀行內部控制缺失的裁罰",  # Internal control + Bank
        "金管會對保險公司的裁罰",  # Regulatory authority + Insurance
        "內線交易案件",  # Insider trading
        "資訊揭露違規",  # Information disclosure
        "市場操縱裁罰案例",  # Market manipulation
    ]

    orchestrator = AgentOrchestrator()
    results = []

    for query_text in test_queries:
        result = await test_query(query_text, orchestrator)
        results.append(result)
        await asyncio.sleep(0.5)  # Brief pause between queries

    # Summary table
    console.print(f"\n[yellow]{'='*80}[/yellow]")
    console.print("[cyan bold]Summary of All Queries[/cyan bold]")
    console.print(f"[yellow]{'='*80}[/yellow]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", width=3, justify="right")
    table.add_column("Query", style="yellow", width=25)
    table.add_column("Concepts", justify="right", style="green")
    table.add_column("Keywords", justify="right", style="blue")
    table.add_column("Citations", justify="right", style="magenta")
    table.add_column("Confidence", style="white")
    table.add_column("Status", width=10)

    for i, result in enumerate(results, 1):
        query_short = result["query"][:23] + "..." if len(result["query"]) > 25 else result["query"]
        status = "[green]✓[/green]" if result["success"] else "[red]✗[/red]"

        table.add_row(
            str(i),
            query_short,
            str(result["concepts"]),
            str(result["expanded_keywords"]),
            str(result["citations"]),
            result["confidence"],
            status,
        )

    console.print(table)

    # Statistics
    successful = sum(1 for r in results if r["success"])
    total_concepts = sum(r["concepts"] for r in results)
    total_keywords = sum(r["expanded_keywords"] for r in results)
    total_citations = sum(r["citations"] for r in results)

    console.print(f"\n[cyan]Overall Statistics:[/cyan]")
    console.print(f"  Success rate: {successful}/{len(results)} ({successful/len(results)*100:.0f}%)")
    console.print(f"  Total concepts matched: {total_concepts}")
    console.print(f"  Total keywords expanded: {total_keywords}")
    console.print(f"  Total citations found: {total_citations}")
    console.print(f"  Avg keywords per query: {total_keywords/len(results):.1f}")
    console.print(f"  Avg citations per query: {total_citations/len(results):.1f}")

    if successful == len(results):
        console.print(f"\n[green bold]✓ All {len(results)} queries executed successfully![/green bold]\n")
    else:
        console.print(f"\n[yellow]⚠ {len(results) - successful} queries failed[/yellow]\n")


if __name__ == "__main__":
    asyncio.run(main())
