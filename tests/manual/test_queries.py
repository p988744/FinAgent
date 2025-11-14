#!/usr/bin/env python3
"""Test script to process multiple queries through FinAgent."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query

console = Console()

# Test queries
QUERIES = [
    "違反金控法利害關係人規定會受到什麼處罰？",
    "請問在證券因為專業投資人資格審核的裁罰有哪些？",
    "辦理共同行銷被裁罰的案例有哪些？",
    "金管會對創投公司的裁罰有哪些？",
    "證券商遭主管機關裁罰「警告」處分，有哪些業務會受限制？",
    "內線交易有罪判決所認定重大訊息成立的時點",
]


async def process_query(query_text: str, query_num: int, orchestrator: AgentOrchestrator) -> dict:
    """Process a single query through FinAgent."""

    console.print()
    console.print("=" * 100, style="bold cyan")
    console.print(f"QUERY {query_num}/6", style="bold cyan")
    console.print("=" * 100, style="bold cyan")
    console.print()

    console.print(Panel.fit(
        f"[bold]{query_text}[/bold]",
        title="Query",
        border_style="cyan"
    ))
    console.print()

    try:
        # Create query
        query = Query(text=query_text)

        # Process query
        console.print("[dim]Processing query through multi-agent workflow...[/dim]")
        console.print()

        result = await orchestrator.process_query(query)

        # Display answer
        if result:
            console.print(Panel.fit(
                "[bold green]✅ Query Processed Successfully[/bold green]",
                border_style="green"
            ))
            console.print()

            # Format answer as markdown
            # Convert key_findings list to string
            key_findings_str = "\n".join(f"- {finding}" for finding in result.key_findings) if result.key_findings else "無"

            answer_md = f"""## 執行摘要

{result.executive_summary or "無"}

## 關鍵發現

{key_findings_str}

## 詳細分析

{result.detailed_analysis or "無"}

## 信心評分

{result.confidence_score.value if result.confidence_score else "未評分"}

{result.confidence_explanation or ""}

## 引用來源

"""

            if result.citations:
                for i, citation in enumerate(result.citations, 1):
                    answer_md += f"\n[{i}] {citation.title or citation.document_id}\n"
                    if hasattr(citation, 'page_number') and citation.page_number:
                        answer_md += f"    頁數: {citation.page_number}\n"
                    if hasattr(citation, 'relevant_text') and citation.relevant_text:
                        answer_md += f"    摘要: {citation.relevant_text[:200]}...\n"
            else:
                answer_md += "\n無引用來源\n"

            console.print(Markdown(answer_md))

            # Summary stats
            console.print()
            console.print("[bold]Query Statistics:[/bold]")
            console.print(f"  • Citations: {len(result.citations) if result.citations else 0}")
            console.print(f"  • Confidence: {result.confidence_score.value if result.confidence_score else 'N/A'}")

            return {
                "query": query_text,
                "success": True,
                "citations_count": len(result.citations) if result.citations else 0,
                "confidence": result.confidence_score.value if result.confidence_score else None,
                "summary": result.executive_summary[:100] if result.executive_summary else None
            }
        else:
            console.print(Panel.fit(
                "[bold red]❌ No Answer Generated[/bold red]",
                border_style="red"
            ))
            return {
                "query": query_text,
                "success": False,
                "error": "No answer generated"
            }

    except Exception as e:
        console.print()
        console.print(Panel.fit(
            f"[bold red]❌ Error Processing Query[/bold red]\n\n{str(e)}",
            border_style="red"
        ))

        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")

        return {
            "query": query_text,
            "success": False,
            "error": str(e)
        }


async def main():
    """Process all queries and generate summary."""

    console.print()
    console.print("=" * 100, style="bold green")
    console.print("FINAGENT MULTI-QUERY TEST", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()

    console.print(f"[bold]Total Queries:[/bold] {len(QUERIES)}")
    console.print()

    # Initialize orchestrator once
    console.print("[dim]Initializing FinAgent orchestrator...[/dim]")
    orchestrator = AgentOrchestrator()
    console.print()

    results = []

    for i, query in enumerate(QUERIES, 1):
        result = await process_query(query, i, orchestrator)
        results.append(result)

        # Short pause between queries
        if i < len(QUERIES):
            console.print()
            console.print("[dim]Preparing next query...[/dim]")
            console.print()

    # Final summary
    console.print()
    console.print("=" * 100, style="bold green")
    console.print("FINAL SUMMARY", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    console.print(f"[bold]Results:[/bold]")
    console.print(f"  ✅ Successful: {successful}/{len(QUERIES)}")
    console.print(f"  ❌ Failed: {failed}/{len(QUERIES)}")
    console.print()

    if successful > 0:
        console.print("[bold]Successful Queries:[/bold]")
        for i, result in enumerate(results, 1):
            if result["success"]:
                console.print(f"  {i}. {result['query'][:60]}...")
                console.print(f"     Citations: {result.get('citations_count', 0)}, "
                            f"Confidence: {result.get('confidence', 'N/A')}")

    if failed > 0:
        console.print()
        console.print("[bold red]Failed Queries:[/bold red]")
        for i, result in enumerate(results, 1):
            if not result["success"]:
                console.print(f"  {i}. {result['query'][:60]}...")
                console.print(f"     Error: {result.get('error', 'Unknown error')}")

    console.print()

    return successful == len(QUERIES)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
