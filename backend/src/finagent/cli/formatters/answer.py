"""Formatters for LegalAnswer display."""

import json
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table

from finagent.models.answers import LegalAnswer, ConfidenceLevel

console = Console()


def format_legal_answer(answer: LegalAnswer):
    """
    Format and display a LegalAnswer with rich formatting.

    Args:
        answer: LegalAnswer to display
    """
    # Main panel with executive summary
    console.print()
    console.print(Panel(
        f"[bold white]{answer.executive_summary}[/bold white]",
        title="[cyan]執行摘要[/cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()

    # Key findings section
    if answer.key_findings:
        console.print("[bold cyan]關鍵發現 ● ● ●[/bold cyan]\n")
        for finding in answer.key_findings:
            console.print(f"  • {finding}")
        console.print()

    # Detailed analysis section
    if answer.detailed_analysis:
        console.print(Panel(
            Markdown(answer.detailed_analysis),
            title="[cyan]詳細分析[/cyan]",
            border_style="blue",
            padding=(1, 2)
        ))
        console.print()

    # Precedent comparison table (if available)
    if answer.precedent_comparison:
        console.print("[bold cyan]判例比較[/bold cyan]\n")
        precedent_table = Table(show_header=True, header_style="bold cyan")
        precedent_table.add_column("案件", style="white")
        precedent_table.add_column("日期", style="cyan", width=12)
        precedent_table.add_column("裁罰金額", style="green", justify="right")
        precedent_table.add_column("違規類型", style="yellow")

        for case in answer.precedent_comparison.get("cases", []):
            precedent_table.add_row(
                case.get("name", "N/A"),
                case.get("date", "N/A"),
                case.get("penalty", "N/A"),
                case.get("violation_type", "N/A")
            )

        console.print(precedent_table)
        console.print()

    # Citations section
    if answer.citations:
        console.print(f"[bold cyan]引用清單 ({len(answer.citations)} 個來源)[/bold cyan]\n")

        for idx, citation in enumerate(answer.citations, 1):
            # Determine authority color
            authority_color = {
                "primary": "green",
                "secondary": "yellow",
                "tertiary": "blue"
            }.get(citation.authority.value, "white")

            console.print(f"[bold white][{idx}][/bold white] {citation.title}")
            console.print(f"    [dim]{citation.type.value}[/dim] | [{authority_color}]{citation.authority.value}[/{authority_color}]", end="")

            if citation.date:
                console.print(f" | [dim]{citation.date}[/dim]", end="")

            console.print()

            if citation.url:
                console.print(f"    [link]{citation.url}[/link]")

            console.print()

    # Confidence score with visual bar
    confidence_info = format_confidence_score(answer.confidence_score)
    console.print(confidence_info)
    console.print()

    # Limitations (if any)
    if answer.limitations:
        limitations_text = "\n".join(f"• {lim}" for lim in answer.limitations)
        console.print(Panel(
            limitations_text,
            title="[yellow]限制說明[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
        console.print()

    # Processing time
    if answer.processing_time_ms:
        processing_time_s = answer.processing_time_ms / 1000
        console.print(f"[dim]處理時間: {processing_time_s:.2f} 秒[/dim]")
        console.print()


def format_confidence_score(score: ConfidenceLevel) -> Panel:
    """
    Format confidence score as a visual bar.

    Args:
        score: Confidence level enum (高/中/低)

    Returns:
        Panel with confidence visualization
    """
    # Map level to color and numeric score
    level_info = {
        ConfidenceLevel.HIGH: ("green", 0.85, "基於多個主要來源，所有關鍵事實已驗證"),
        ConfidenceLevel.MEDIUM: ("yellow", 0.65, "大部分事實來自主要來源，部分細節待確認"),
        ConfidenceLevel.LOW: ("red", 0.40, "依賴次要來源，建議進一步驗證")
    }

    color, numeric_score, explanation = level_info.get(score, ("white", 0.5, ""))

    # Create progress bar
    bar_length = 20
    filled = int(numeric_score * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)

    # Format text
    percentage = f"{numeric_score:.0%}"
    level_text = score.value  # Chinese text (高/中/低)

    content = f"[{color}]{bar}[/{color}] [{color}]{level_text}[/{color}] ({percentage})"
    content += f"\n[dim]{explanation}[/dim]"

    return Panel(
        content,
        title="[cyan]信心評分[/cyan]",
        border_style=color,
        padding=(0, 2)
    )


def format_answer_json(answer: LegalAnswer) -> str:
    """
    Format LegalAnswer as JSON string.

    Args:
        answer: LegalAnswer to format

    Returns:
        JSON string
    """
    return answer.model_dump_json(indent=2, exclude_none=True)


def format_answer_markdown(answer: LegalAnswer) -> str:
    """
    Format LegalAnswer as Markdown.

    Args:
        answer: LegalAnswer to format

    Returns:
        Markdown string
    """
    lines = []

    # Title
    lines.append("# 法律研究結果\n")

    # Executive summary
    lines.append("## 執行摘要\n")
    lines.append(f"{answer.executive_summary}\n")

    # Key findings
    if answer.key_findings:
        lines.append("## 關鍵發現\n")
        for finding in answer.key_findings:
            lines.append(f"- {finding}")
        lines.append("")

    # Detailed analysis
    if answer.detailed_analysis:
        lines.append("## 詳細分析\n")
        lines.append(f"{answer.detailed_analysis}\n")

    # Precedent comparison
    if answer.precedent_comparison:
        lines.append("## 判例比較\n")
        lines.append("| 案件 | 日期 | 裁罰金額 | 違規類型 |")
        lines.append("|------|------|----------|----------|")
        for case in answer.precedent_comparison.get("cases", []):
            lines.append(f"| {case.get('name', 'N/A')} | {case.get('date', 'N/A')} | {case.get('penalty', 'N/A')} | {case.get('violation_type', 'N/A')} |")
        lines.append("")

    # Citations
    if answer.citations:
        lines.append(f"## 引用清單 ({len(answer.citations)} 個來源)\n")
        for idx, citation in enumerate(answer.citations, 1):
            lines.append(f"### [{idx}] {citation.title}\n")
            lines.append(f"- **類型**: {citation.type.value}")
            lines.append(f"- **權威**: {citation.authority.value}")
            if citation.date:
                lines.append(f"- **日期**: {citation.date}")
            if citation.url:
                lines.append(f"- **網址**: {citation.url}")
            lines.append("")

    # Confidence
    level_text = answer.confidence_level.value.split("/")[0]
    lines.append(f"## 信心評分: {level_text} ({answer.confidence_score:.0%})\n")
    lines.append(f"{answer.confidence_explanation}\n")

    # Limitations
    if answer.limitations:
        lines.append("## 限制說明\n")
        lines.append(f"{answer.limitations}\n")

    # Processing time
    if answer.processing_time:
        lines.append(f"*處理時間: {answer.processing_time:.2f} 秒*\n")

    return "\n".join(lines)
