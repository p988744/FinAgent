#!/usr/bin/env python3
"""Test complete workflow with all three enhancements:
1. Enhanced Planning Agent with query analysis
2. Hard Search Method with grep-based file search
3. Query Memo System with database tracking
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.agents.query_memo import QueryMemoLogger
from finagent.models.queries import Query

console = Console()

# Test queries with different complexity levels
TEST_QUERIES = [
    ("玉山銀行洗錢防制裁罰", "simple", "Simple query, no hard search expected"),
    (
        "金管會對創投公司的裁罰有哪些？",
        "complex",
        "Complex query, hard search should trigger",
    ),
    ("2020年證券期貨局的裁罰案件", "medium", "Medium query with time period"),
]


async def test_query(query_text: str, expected_complexity: str, description: str):
    """Test a single query through complete workflow."""

    console.print()
    console.print("=" * 100, style="bold cyan")
    console.print(f"TEST: {query_text}", style="bold cyan")
    console.print(f"Description: {description}", style="dim")
    console.print(f"Expected Complexity: {expected_complexity}", style="dim")
    console.print("=" * 100, style="bold cyan")
    console.print()

    try:
        # Initialize orchestrator (with query logging enabled)
        orchestrator = AgentOrchestrator(enable_query_logging=True)

        # Create query
        query = Query(text=query_text)

        # Process query
        console.print("[dim]Processing query...[/dim]")
        result = await orchestrator.process_query(query)

        # Display processing steps
        if result and hasattr(result, "processing_steps"):
            console.print()
            console.print("[bold]📋 Processing Steps:[/bold]")
            for i, step in enumerate(result.processing_steps, 1):
                console.print(f"  {i}. {step}")

        # Display results
        if result:
            console.print()
            console.print(
                Panel.fit(
                    f"[bold green]✅ Query Processed[/bold green]",
                    border_style="green",
                )
            )
            console.print()

            # Create results table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Citations", str(len(result.citations) if result.citations else 0))
            table.add_row("Confidence", result.confidence_score.value if result.confidence_score else "N/A")
            table.add_row("Processing Time", f"{result.processing_time_ms}ms" if result.processing_time_ms else "N/A")

            console.print(table)

            # Show some citations
            if result.citations:
                console.print()
                console.print("[bold]📄 Documents Found (first 5):[/bold]")
                for i, citation in enumerate(result.citations[:5], 1):
                    console.print(f"  {i}. {citation.title}")

        else:
            console.print(
                Panel.fit("[bold red]❌ No Answer[/bold red]", border_style="red")
            )

    except Exception as e:
        console.print()
        console.print(
            Panel.fit(
                f"[bold red]❌ Error[/bold red]\n\n{str(e)}", border_style="red"
            )
        )

        import traceback

        console.print("[dim]" + traceback.format_exc() + "[/dim]")

    console.print()


async def show_query_history():
    """Display query history from database."""

    console.print()
    console.print("=" * 100, style="bold green")
    console.print("📊 QUERY HISTORY FROM DATABASE", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()

    logger = QueryMemoLogger()

    # Get recent queries
    history = logger.get_query_history(limit=10)

    if not history:
        console.print("[yellow]No query history found[/yellow]")
        return

    # Create history table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Query", style="white", width=30)
    table.add_column("Confidence", style="green", width=10)
    table.add_column("Citations", style="yellow", width=10)
    table.add_column("Iterations", style="blue", width=10)
    table.add_column("Strategy", style="magenta", width=10)
    table.add_column("Hard Search", style="red", width=12)
    table.add_column("Time (s)", style="cyan", width=10)

    for record in history[:10]:  # Show last 10
        hard_search = "✅" if record.get("hard_chunks_count", 0) > 0 else "❌"
        time_str = f"{record.get('processing_time_seconds', 0):.1f}" if record.get('processing_time_seconds') else "N/A"

        table.add_row(
            str(record.get("id", "")),
            record.get("query", "")[:30] + "..." if len(record.get("query", "")) > 30 else record.get("query", ""),
            record.get("confidence_level", "N/A"),
            str(record.get("citations_count", 0)),
            str(record.get("search_iterations", 0)),
            record.get("search_strategy", "N/A"),
            hard_search,
            time_str,
        )

    console.print(table)

    # Show statistics
    stats = logger.get_query_stats()

    if stats:
        console.print()
        console.print("[bold]📈 Statistics:[/bold]")
        console.print(f"  Total Queries: {stats.get('total_queries', 0)}")
        console.print(f"  Success Rate: {stats.get('success_rate', 0):.1%}")
        console.print(f"  Avg Processing Time: {stats.get('average_processing_time_seconds', 0):.2f}s")
        console.print(f"  Hard Search Usage: {stats.get('hard_search_usage_rate', 0):.1%}")
        console.print(f"  Avg Iterations: {stats.get('average_search_iterations', 0):.2f}")

        confidence_dist = stats.get("confidence_distribution", {})
        if confidence_dist:
            console.print()
            console.print("[bold]Confidence Distribution:[/bold]")
            for level, count in confidence_dist.items():
                if level:  # Skip None
                    console.print(f"  {level}: {count}")


async def main():
    """Run all tests."""

    console.print()
    console.print("=" * 100, style="bold green")
    console.print("🧪 COMPLETE WORKFLOW TEST", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()

    console.print("[bold]Testing all three enhancements:[/bold]")
    console.print("  1. ✅ Enhanced Planning Agent (query analysis, TODO list)")
    console.print("  2. ✅ Hard Search Method (grep-based file search)")
    console.print("  3. ✅ Query Memo System (database tracking)")
    console.print()

    # Run test queries
    for query_text, expected_complexity, description in TEST_QUERIES:
        await test_query(query_text, expected_complexity, description)

    # Show query history
    await show_query_history()

    console.print()
    console.print("=" * 100, style="bold green")
    console.print("✅ ALL TESTS COMPLETE", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()


if __name__ == "__main__":
    asyncio.run(main())
