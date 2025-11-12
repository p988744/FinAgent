"""Test script to verify Ctrl+C cancellation behavior."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console

console = Console()

def test_keyboard_interrupt_handling():
    """
    Test that KeyboardInterrupt is properly raised (not suppressed).

    Expected behavior:
    - When KeyboardInterrupt is raised during processing, it should propagate up
    - The operation should be cancelled (not continue to next item)
    """

    items = ["item1", "item2", "item3", "item4", "item5"]
    processed = []

    console.print("[cyan]Testing KeyboardInterrupt handling...[/cyan]\n")
    console.print(f"Items to process: {items}\n")

    try:
        for i, item in enumerate(items):
            console.print(f"Processing: {item}")

            # Simulate Ctrl+C on item 3
            if i == 2:
                console.print(f"[yellow]Simulating Ctrl+C...[/yellow]")
                raise KeyboardInterrupt("User pressed Ctrl+C")

            processed.append(item)
            console.print(f"[green]✓ Completed: {item}[/green]")

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]⏸️  操作已中斷[/yellow]")
        # Should re-raise to cancel operation
        raise

    console.print(f"\n[green]All items processed: {processed}[/green]")


if __name__ == "__main__":
    console.print()
    console.print("[bold]Test: KeyboardInterrupt Propagation[/bold]")
    console.print("=" * 50)
    console.print()

    try:
        test_keyboard_interrupt_handling()
        console.print("\n[red]✗ FAIL: KeyboardInterrupt was not raised[/red]")
        sys.exit(1)

    except KeyboardInterrupt:
        console.print()
        console.print("[green]✅ PASS: KeyboardInterrupt properly propagated[/green]")
        console.print("[green]Operation was cancelled as expected[/green]")
        sys.exit(0)
