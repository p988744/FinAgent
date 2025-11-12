"""Test ESC key cancellation functionality."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from finagent.cli.keyboard_handler import CancellationToken
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def test_esc_cancellation():
    """Test ESC key cancellation during a long operation."""

    console.print()
    console.print("[bold cyan]ESC Key Cancellation Test[/bold cyan]")
    console.print()
    console.print("[yellow]模擬長時間執行的任務...[/yellow]")
    console.print("[yellow]按 ESC 鍵取消操作[/yellow]")
    console.print()

    try:
        # Create cancellation token
        token = CancellationToken()

        with token, Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]執行中... (按 ESC 取消)",
                total=10
            )

            # Simulate long-running operation
            for i in range(10):
                # Check if cancelled
                if token.is_cancelled():
                    console.print()
                    console.print("[red]✗ 操作已被取消 (ESC 鍵)[/red]")
                    console.print()
                    return False

                # Simulate work
                time.sleep(0.5)
                progress.update(task, advance=1)

            progress.update(task, completed=True)

        console.print()
        console.print("[green]✓ 操作完成（未取消）[/green]")
        console.print()
        return True

    except KeyboardInterrupt:
        console.print()
        console.print("[red]✗ 操作已中斷 (Ctrl+C)[/red]")
        console.print()
        return False


if __name__ == "__main__":
    console.print()
    console.print("=" * 60)
    console.print("Testing ESC Key Cancellation")
    console.print("=" * 60)
    console.print()
    console.print("[bold]Instructions:[/bold]")
    console.print("  1. The test will run for 5 seconds")
    console.print("  2. Press ESC at any time to cancel")
    console.print("  3. Or wait for completion")
    console.print()
    console.print("[dim]Note: This test requires a TTY terminal[/dim]")
    console.print()

    input("Press ENTER to start the test...")

    result = test_esc_cancellation()

    console.print("=" * 60)
    if result:
        console.print("[green]Test completed without cancellation[/green]")
    else:
        console.print("[yellow]Test was cancelled[/yellow]")
    console.print("=" * 60)
    console.print()
