"""Test query analysis with human-in-the-loop clarification.

This script tests the query analysis feature with different query types:
1. Clear queries (no clarification needed)
2. Ambiguous queries (clarification requested)
3. Over-broad queries (clarification requested)
"""

import asyncio

from rich.console import Console

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.cli.formatters.query_analysis import handle_cli_clarification
from finagent.models.queries import Query

console = Console()


async def test_query_analysis():
    """Test query analysis with various query types."""
    console.print("\n[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]")
    console.print("[cyan bold]      Query Analysis & Human-in-Loop Test              [/cyan bold]")
    console.print("[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]\n")

    # Create orchestrator with CLI clarification handler
    async def cli_clarification_handler(clarification_request):
        return await handle_cli_clarification(clarification_request, console)

    orchestrator = AgentOrchestrator(
        clarification_handler=cli_clarification_handler
    )

    # Test queries
    test_queries = [
        {
            "text": "玉山銀行2020年洗錢防制裁罰",
            "description": "Clear query (specific bank, year, violation type)",
            "expected": "No clarification needed",
        },
        {
            "text": "最近的裁罰案件",
            "description": "Ambiguous time range ('最近' unclear)",
            "expected": "Clarification requested",
        },
        {
            "text": "銀行洗錢",
            "description": "Ambiguous entity ('銀行' - which bank?)",
            "expected": "May request clarification",
        },
        {
            "text": "金融違規",
            "description": "Over-broad query (too many violation types)",
            "expected": "Clarification requested",
        },
        {
            "text": "內線交易案件2019-2021",
            "description": "Clear query (specific violation + time range)",
            "expected": "No clarification needed",
        },
    ]

    for i, test_case in enumerate(test_queries, 1):
        console.print(f"\n[yellow]{'='*80}[/yellow]")
        console.print(f"[cyan]Test {i}/{len(test_queries)}:[/cyan] {test_case['description']}")
        console.print(f"[yellow]{'='*80}[/yellow]\n")

        console.print(f"[bold]Query:[/bold] {test_case['text']}")
        console.print(f"[dim]Expected:[/dim] {test_case['expected']}\n")

        query = Query(text=test_case['text'])

        try:
            # Process query (may request clarification)
            console.print("[cyan]Processing query...[/cyan]\n")

            answer = await orchestrator.process_query(query)

            # Show results
            console.print(f"\n[green]✓ Query completed successfully[/green]")
            console.print(f"  Processing steps: {len(answer.processing_steps)}")
            console.print(f"  Citations found: {len(answer.citations)}")

            # Show processing steps
            console.print(f"\n[cyan]Processing Steps:[/cyan]")
            for step in answer.processing_steps[:5]:  # Show first 5
                console.print(f"  • {step}")
            if len(answer.processing_steps) > 5:
                console.print(f"  ... and {len(answer.processing_steps) - 5} more steps")

        except Exception as e:
            console.print(f"[red]✗ Error: {str(e)[:200]}[/red]")

        # Pause between queries
        if i < len(test_queries):
            console.print(f"\n[dim]Press Enter to continue to next test...[/dim]")
            input()

    console.print(f"\n[yellow]{'='*80}[/yellow]")
    console.print("[green bold]✓ All query analysis tests complete![/green bold]")
    console.print(f"[yellow]{'='*80}[/yellow]\n")


async def test_query_analysis_simple():
    """Simple test with just one ambiguous query."""
    console.print("\n[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]")
    console.print("[cyan bold]      Query Analysis - Simple Test                      [/cyan bold]")
    console.print("[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]\n")

    # Create orchestrator with CLI clarification handler
    async def cli_clarification_handler(clarification_request):
        return await handle_cli_clarification(clarification_request, console)

    orchestrator = AgentOrchestrator(
        clarification_handler=cli_clarification_handler
    )

    # Test with an ambiguous query
    console.print("[bold]Testing with ambiguous query:[/bold] '最近的裁罰案件'\n")

    query = Query(text="最近的裁罰案件")

    try:
        answer = await orchestrator.process_query(query)

        console.print(f"\n[green]✓ Query completed![/green]")
        console.print(f"  Processing steps: {len(answer.processing_steps)}")
        console.print(f"  Citations: {len(answer.citations)}")

        # Try to get summary (may be in different attributes)
        summary = getattr(answer, "summary", None) or getattr(answer, "answer", None)
        if summary:
            console.print(f"\n[cyan]Answer Summary:[/cyan]")
            summary_preview = summary[:200] + "..." if len(summary) > 200 else summary
            console.print(f"  {summary_preview}")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")

    console.print()


if __name__ == "__main__":
    import sys

    # Check command line argument
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        asyncio.run(test_query_analysis_simple())
    else:
        asyncio.run(test_query_analysis())
