#!/usr/bin/env python3
"""Test re-search flow with Query 4 (創投公司)."""

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

# Test query that should trigger re-search
TEST_QUERY = "金管會對創投公司的裁罰有哪些？"


async def test_research():
    """Test re-search flow."""

    console.print()
    console.print("=" * 100, style="bold green")
    console.print("RE-SEARCH FLOW TEST", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()

    console.print(
        Panel.fit(f"[bold]{TEST_QUERY}[/bold]", title="Test Query", border_style="cyan")
    )
    console.print()

    console.print("[bold]Expected Behavior:[/bold]")
    console.print("  1. First search (strict): Finds 證券投資信託 documents")
    console.print("  2. Validation: ⚠️ Entity type mismatch + missing keywords detected")
    console.print("  3. Reference Guard: Triggers re-search")
    console.print("  4. Second search (relaxed): Broader search for 創投 documents")
    console.print("  5. Validation: Check if better documents found")
    console.print("  6. Reference Guard: Decide whether to search again or proceed")
    console.print()

    try:
        # Initialize orchestrator
        console.print("[dim]Initializing FinAgent orchestrator...[/dim]")
        orchestrator = AgentOrchestrator()
        console.print()

        # Create query
        query = Query(text=TEST_QUERY)

        # Process query
        console.print("[dim]Processing query through multi-agent workflow...[/dim]")
        console.print()

        result = await orchestrator.process_query(query)

        # Display results
        if result:
            console.print()
            console.print(
                Panel.fit(
                    "[bold green]✅ Query Processed Successfully[/bold green]",
                    border_style="green",
                )
            )
            console.print()

            console.print("[bold]Search Statistics:[/bold]")
            console.print(f"  • Citations: {len(result.citations) if result.citations else 0}")
            console.print(
                f"  • Confidence: {result.confidence_score.value if result.confidence_score else 'N/A'}"
            )
            console.print()

            console.print("[bold]Executive Summary:[/bold]")
            console.print(result.executive_summary or "無")
            console.print()

            console.print("[bold]Citations:[/bold]")
            if result.citations:
                for i, citation in enumerate(result.citations, 1):
                    console.print(f"  [{i}] {citation.title or citation.document_id}")
            else:
                console.print("  無引用來源")
            console.print()

            # Check if re-search was triggered
            console.print("[bold]Test Results:[/bold]")
            console.print("  ✅ Test completed successfully")
            console.print()
            console.print(
                "[dim]Check logs above for re-search activity (look for 'Re-search iteration' messages)[/dim]"
            )

        else:
            console.print(
                Panel.fit(
                    "[bold red]❌ No Answer Generated[/bold red]", border_style="red"
                )
            )

    except Exception as e:
        console.print()
        console.print(
            Panel.fit(
                f"[bold red]❌ Error During Test[/bold red]\n\n{str(e)}",
                border_style="red",
            )
        )

        import traceback

        console.print("[dim]" + traceback.format_exc() + "[/dim]")

    console.print()


if __name__ == "__main__":
    asyncio.run(test_research())
