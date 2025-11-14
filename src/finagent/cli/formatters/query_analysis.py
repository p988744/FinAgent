"""Formatters for displaying query analysis and clarification requests in CLI/REPL."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt


def display_query_analysis(clarification_request: dict, console: Console) -> None:
    """Display query analysis results.

    Args:
        clarification_request: Dict with analysis results
        console: Rich console for output
    """
    needs_clarification = clarification_request.get("needs_clarification", False)
    understood_intent = clarification_request.get("understood_intent", "")
    confidence = clarification_request.get("confidence", "unknown")

    # Map confidence to Chinese
    confidence_map = {"high": "高", "medium": "中", "low": "低"}
    confidence_zh = confidence_map.get(confidence, confidence)

    # Create panel content
    if needs_clarification:
        title = "[yellow]🤔 查詢分析：需要澄清[/yellow]"
        border_style = "yellow"

        content = f"[bold]目前理解：[/bold]{understood_intent}\n"
        content += f"[bold]信心程度：[/bold][yellow]{confidence_zh}[/yellow]\n\n"
        content += f"[dim]系統需要更多資訊來提供精確的回答...[/dim]"
    else:
        title = "[green]✓ 查詢分析：理解清晰[/green]"
        border_style = "green"

        content = f"[bold]查詢意圖：[/bold]{understood_intent}\n"
        content += f"[bold]信心程度：[/bold][green]{confidence_zh}[/green]\n\n"
        content += f"[dim]系統將直接執行查詢...[/dim]"

    panel = Panel(content, title=title, border_style=border_style, padding=(1, 2))
    console.print(panel)


def request_clarification(clarification_request: dict, console: Console) -> str:
    """Request clarification from user.

    Args:
        clarification_request: Dict with clarification questions
        console: Rich console for output

    Returns:
        User's clarification response (or empty string if skipped)
    """
    reason = clarification_request.get("reason", "")
    questions = clarification_request.get("questions", [])

    console.print()
    console.print("[yellow]═══════════════════════════════════════════════════════[/yellow]")
    console.print("[yellow bold]                  需要您的協助                        [/yellow bold]")
    console.print("[yellow]═══════════════════════════════════════════════════════[/yellow]")
    console.print()

    if reason:
        console.print(f"[bold]原因：[/bold]{reason}\n")

    if questions:
        console.print("[bold]請協助回答以下問題：[/bold]\n")
        for i, question in enumerate(questions, 1):
            console.print(f"  [cyan]{i}.[/cyan] {question}")
        console.print()

    console.print("[dim]您可以：[/dim]")
    console.print("[dim]  • 回答上述問題以獲得更精確的結果[/dim]")
    console.print("[dim]  • 直接按 Enter 跳過，系統將使用目前理解執行查詢[/dim]")
    console.print()

    # Prompt for user input
    response = Prompt.ask(
        "[yellow]請輸入補充說明[/yellow] [dim](或按 Enter 跳過)[/dim]",
        default="",
    )

    if response.strip():
        console.print()
        console.print(f"[green]✓ 已收到補充說明[/green]")
        console.print(f"[dim]補充內容：{response[:100]}{'...' if len(response) > 100 else ''}[/dim]")
    else:
        console.print()
        console.print("[dim]已跳過澄清，將使用原查詢執行...[/dim]")

    console.print()
    console.print("[yellow]═══════════════════════════════════════════════════════[/yellow]")
    console.print()

    return response.strip()


def display_enriched_query(original_query: str, enriched_query: str, console: Console) -> None:
    """Display enriched query after clarification.

    Args:
        original_query: Original user query
        enriched_query: Enriched query with clarification
        console: Rich console for output
    """
    console.print()
    console.print("[cyan]查詢已強化：[/cyan]")
    console.print(f"  [dim]原查詢：[/dim]{original_query}")

    # Extract clarification from enriched query
    if "補充說明：" in enriched_query:
        clarification = enriched_query.split("補充說明：")[1].strip()
        console.print(f"  [green]補充說明：[/green]{clarification}")

    console.print()


async def handle_cli_clarification(clarification_request: dict, console: Console = None) -> str:
    """Async handler for CLI clarification requests.

    This is the handler passed to LegalResearchWorkflow for CLI/REPL interface.

    Args:
        clarification_request: Dict with clarification details
        console: Rich console for output (optional, creates new if not provided)

    Returns:
        User's clarification response
    """
    if console is None:
        console = Console()

    # Display analysis results
    display_query_analysis(clarification_request, console)

    # Request clarification
    response = request_clarification(clarification_request, console)

    return response
