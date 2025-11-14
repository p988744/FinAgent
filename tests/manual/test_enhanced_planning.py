#!/usr/bin/env python3
"""Test enhanced planning agent with query analysis display."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query

console = Console()

# Test queries with different complexity levels
TEST_QUERIES = [
    ("金管會對創投公司的裁罰有哪些？", "complex"),  # Complex: entity type + must-have keywords
    ("玉山銀行洗錢防制裁罰", "simple"),  # Simple: specific institution
    ("2020年證券期貨局的裁罰案件", "medium"),  # Medium: jurisdiction + time
]


async def test_planning(query_text: str, expected_complexity: str):
    """Test planning agent with a single query."""

    console.print()
    console.print("=" * 100, style="bold cyan")
    console.print(f"TEST: {query_text}", style="bold cyan")
    console.print(f"Expected Complexity: {expected_complexity}", style="dim")
    console.print("=" * 100, style="bold cyan")
    console.print()

    try:
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()

        # Create query
        query = Query(text=query_text)

        # Process query (will show planning output in logs)
        console.print("[dim]Processing query...[/dim]")
        result = await orchestrator.process_query(query)

        # Display results
        if result:
            console.print()
            console.print(
                Panel.fit(
                    "[bold green]✅ Query Processed[/bold green]",
                    border_style="green",
                )
            )
            console.print()

            console.print(f"[bold]Citations:[/bold] {len(result.citations) if result.citations else 0}")
            console.print(
                f"[bold]Confidence:[/bold] {result.confidence_score.value if result.confidence_score else 'N/A'}"
            )
            console.print()

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


async def main():
    """Test all queries."""

    console.print()
    console.print("=" * 100, style="bold green")
    console.print("ENHANCED PLANNING AGENT TEST", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()

    console.print("[bold]What to look for in logs:[/bold]")
    console.print("  1. 📋 查詢分析結果 section")
    console.print("  2. Keywords, entity type, jurisdiction identified")
    console.print("  3. 📝 研究任務清單 with TODO items")
    console.print("  4. Complexity level: simple/medium/complex")
    console.print("  5. Deep search flag for complex queries")
    console.print()

    for query_text, expected_complexity in TEST_QUERIES:
        await test_planning(query_text, expected_complexity)

    console.print("=" * 100, style="bold green")
    console.print("ALL TESTS COMPLETE", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()


if __name__ == "__main__":
    asyncio.run(main())
