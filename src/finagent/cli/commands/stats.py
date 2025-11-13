"""Statistics command handler."""

from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from finagent.database.db import Database
from finagent.utils.cost_calculator import format_cost_twd, format_cost_usd

console = Console()


def show_statistics(days: int | None = None):
    """
    Display query statistics.

    Args:
        days: Optional number of days to show stats for (None = all time)
    """
    db = Database()

    # Get overall stats
    stats = db.get_history_stats()

    # Check if we have any data
    if stats["total_queries"] == 0:
        console.print("[yellow]尚無查詢歷史記錄。[/yellow]")
        return

    # Calculate success rate
    success_rate = (
        (stats["successful_queries"] / stats["total_queries"] * 100)
        if stats["total_queries"] > 0
        else 0
    )

    # Format values
    total_queries = stats["total_queries"]
    successful_queries = stats["successful_queries"]
    failed_queries = total_queries - successful_queries
    avg_time = stats["avg_processing_time"] or 0
    total_tokens = stats["total_tokens"] or 0
    total_cost = stats["total_cost_usd"] or 0
    avg_cost = total_cost / total_queries if total_queries > 0 else 0
    total_sessions = stats["total_sessions"]

    # Create main stats panel
    title = "查詢統計" if not days else f"查詢統計 (最近 {days} 天)"

    stats_text = Text()
    stats_text.append("總查詢次數: ", style="bold")
    stats_text.append(f"{total_queries}\n", style="cyan")

    stats_text.append("成功查詢: ", style="bold")
    stats_text.append(f"{successful_queries} ", style="green")
    stats_text.append(f"({success_rate:.1f}%)\n", style="dim green")

    if failed_queries > 0:
        stats_text.append("失敗查詢: ", style="bold")
        stats_text.append(f"{failed_queries} ", style="red")
        stats_text.append(f"({100 - success_rate:.1f}%)\n", style="dim red")

    stats_text.append("工作階段數: ", style="bold")
    stats_text.append(f"{total_sessions}\n", style="cyan")

    stats_text.append("平均處理時間: ", style="bold")
    stats_text.append(f"{avg_time:.1f} 秒\n", style="yellow")

    console.print(Panel(stats_text, title=title, border_style="blue"))

    # Cost statistics
    if total_cost > 0:
        cost_text = Text()
        cost_text.append("總 Token 數: ", style="bold")
        cost_text.append(f"{total_tokens:,}\n", style="cyan")

        cost_text.append("總成本: ", style="bold")
        cost_text.append(f"{format_cost_usd(total_cost)} ", style="green")
        cost_text.append(f"({format_cost_twd(total_cost)})\n", style="dim green")

        cost_text.append("平均每次查詢: ", style="bold")
        cost_text.append(f"{format_cost_usd(avg_cost)}", style="yellow")

        console.print(Panel(cost_text, title="成本統計", border_style="green"))

    # Model usage statistics
    model_stats = get_model_usage_stats(db)
    if model_stats:
        table = Table(title="最常用模型", show_header=True, header_style="bold magenta")
        table.add_column("模型", style="cyan", no_wrap=True)
        table.add_column("使用次數", justify="right", style="green")
        table.add_column("百分比", justify="right", style="yellow")
        table.add_column("總成本", justify="right", style="green")

        for model_name, count, percentage, cost in model_stats:
            table.add_row(
                model_name,
                str(count),
                f"{percentage:.1f}%",
                format_cost_usd(cost) if cost else "$0.00",
            )

        console.print(table)
        console.print()

    # Recent activity (last 7 days)
    recent_activity = get_recent_activity(db, days=7)
    if recent_activity:
        activity_text = Text()
        activity_text.append("最近 7 天查詢趨勢:\n\n", style="bold")

        max_count = max(count for _, count in recent_activity)
        for date_str, count in recent_activity:
            # Parse date and get day of week
            date = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = ["一", "二", "三", "四", "五", "六", "日"][date.weekday()]

            # Create bar chart
            bar_length = int((count / max_count) * 20) if max_count > 0 else 0
            bar = "█" * bar_length

            activity_text.append(f"  {day_name} ({date_str[-5:]})  ", style="dim")
            activity_text.append(bar, style="cyan")
            activity_text.append(f" {count}\n", style="bold")

        console.print(Panel(activity_text, title="查詢趨勢", border_style="cyan"))


def get_model_usage_stats(db: Database) -> list[tuple[str, int, float, float]]:
    """
    Get model usage statistics.

    Returns:
        List of (model_name, count, percentage, total_cost) tuples
    """
    with db.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                model_used,
                COUNT(*) as count,
                SUM(COALESCE(cost_usd, 0)) as total_cost
            FROM history
            GROUP BY model_used
            ORDER BY count DESC
            """
        )

        rows = cursor.fetchall()
        total_queries = sum(row["count"] for row in rows)

        return [
            (
                row["model_used"],
                row["count"],
                (row["count"] / total_queries * 100) if total_queries > 0 else 0,
                row["total_cost"] or 0,
            )
            for row in rows
        ]


def get_recent_activity(db: Database, days: int = 7) -> list[tuple[str, int]]:
    """
    Get recent query activity by day.

    Args:
        db: Database instance
        days: Number of days to look back

    Returns:
        List of (date_str, count) tuples for the last N days
    """
    with db.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                DATE(created_at) as query_date,
                COUNT(*) as count
            FROM history
            WHERE created_at >= datetime('now', '-' || ? || ' days')
            GROUP BY query_date
            ORDER BY query_date ASC
            """,
            (days,),
        )

        rows = cursor.fetchall()

        # Create a dict of dates with counts
        activity_dict = {row["query_date"]: row["count"] for row in rows}

        # Fill in missing days with 0
        result = []
        for i in range(days - 1, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            count = activity_dict.get(date_str, 0)
            result.append((date_str, count))

        return result
