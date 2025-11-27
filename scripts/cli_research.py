#!/usr/bin/env python3
"""
CLI Research Tool - Ask research questions and get comprehensive answers.

This uses the Plan-and-Execute workflow with Query Analyzer to provide
detailed research responses with proper planning and execution.

Usage:
    python scripts/cli_research.py "Your research question here"
    python scripts/cli_research.py  # Interactive mode
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query


def print_header():
    """Print CLI header."""
    print()
    print("=" * 80)
    print("  FinAgent Research CLI")
    print("  Plan-and-Execute Workflow with Query Analysis")
    print("=" * 80)
    print()


def print_query_insight(insight):
    """Print query insight in a nice format."""
    print()
    print("🔍 Query Understanding")
    print("─" * 80)
    print(f"  Type:       {insight.query_type}")
    print(f"  Strategy:   {insight.search_strategy}")
    print(f"  Complexity: {insight.complexity}")

    if insight.key_entities:
        entities_str = ", ".join(insight.key_entities[:5])
        if len(insight.key_entities) > 5:
            entities_str += f" (and {len(insight.key_entities) - 5} more)"
        print(f"  Entities:   {entities_str}")

    print()
    print(f"  💡 {insight.reasoning}")
    print()


def print_plan(plan):
    """Print research plan."""
    print()
    print("📋 Research Plan")
    print("─" * 80)
    print(f"  The system will execute {len(plan.tasks)} tasks:")
    print()

    for i, task in enumerate(plan.tasks, 1):
        tool_icon = {
            "retriever": "🔍",
            "hard_search": "🔎",
            "hybrid_search": "🔍🔎"
        }.get(task.tool, "⚙️ ")

        desc = task.description[:70] + "..." if len(task.description) > 70 else task.description
        print(f"  {i}. {tool_icon} [{task.tool}]")
        print(f"     {desc}")

    print()


def print_progress(task_num, total_tasks, task_desc):
    """Print task execution progress."""
    percentage = (task_num / total_tasks) * 100
    bar_length = 40
    filled = int(bar_length * task_num / total_tasks)
    bar = "█" * filled + "░" * (bar_length - filled)

    print(f"\r  Progress: [{bar}] {percentage:.0f}% ({task_num}/{total_tasks})", end="", flush=True)


async def research_query(query_text: str, verbose: bool = False):
    """
    Execute a research query.

    Args:
        query_text: The research question
        verbose: If True, show detailed progress
    """
    # Initialize orchestrator
    if verbose:
        print("Initializing FinAgent...")

    orchestrator = AgentOrchestrator()

    if not orchestrator.use_rag:
        print("❌ Error: Document index not available.")
        print("   Please run indexing first: uv run finagent reindex")
        return

    if verbose:
        print("✅ Ready\n")

    # Create query
    query = Query(text=query_text)

    print(f"Query: {query_text}")

    # Track state
    query_insight = None
    plan = None
    tasks_completed = 0
    total_tasks = 0
    final_response = None

    try:
        async for node_name, state_update in orchestrator.stream_query(
            query=query,
            use_plan_execute=True,
            enable_demo_delay=False
        ):
            # Handle query analyzer
            if node_name == "query_analyzer" and "query_insight" in state_update:
                query_insight = state_update["query_insight"]
                print_query_insight(query_insight)

            # Handle planner
            elif node_name == "planner" and "plan" in state_update:
                plan = state_update["plan"]
                total_tasks = len(plan.tasks)
                print_plan(plan)

                if not verbose:
                    print("⚙️  Executing research plan...")
                    print()

            # Handle executor
            elif node_name == "execute_task":
                tasks_completed += 1

                if verbose:
                    if "past_steps" in state_update and state_update["past_steps"]:
                        latest_step = state_update["past_steps"][-1]
                        task_dict, result = latest_step
                        task_desc = task_dict.get("description", "")[:50]
                        print(f"  ✓ Task {tasks_completed}/{total_tasks}: {task_desc}...")
                else:
                    print_progress(tasks_completed, total_tasks, "")

            # Handle reporter
            elif node_name == "reporter" and "response" in state_update:
                final_response = state_update["response"]

    except KeyError:
        # Ignore KeyError from other workflows
        pass
    except Exception as e:
        print()
        print(f"❌ Error during research: {e}")
        import traceback
        traceback.print_exc()
        return

    # Print final response
    if final_response:
        if not verbose:
            print()  # New line after progress bar

        print()
        print("📝 Research Results")
        print("=" * 80)
        print()
        print(final_response)
        print()
        print("=" * 80)
    else:
        print()
        print("⚠️  Warning: No response generated")


async def interactive_mode():
    """Interactive CLI mode."""
    print_header()

    print("Interactive Research Mode")
    print("─" * 80)
    print("Enter your research questions, or 'exit' to quit.")
    print()

    while True:
        try:
            query = input("\n🔍 Research question: ").strip()

            if not query:
                continue

            if query.lower() in ['exit', 'quit', 'q']:
                print("\nExiting...")
                break

            # Ask for verbose mode
            verbose_input = input("   Show detailed progress? (y/n) [n]: ").strip().lower()
            verbose = verbose_input == 'y'

            print()
            print("─" * 80)

            await research_query(query, verbose=verbose)

            print()
            input("Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Check for help flag first
        if "--help" in sys.argv or "-h" in sys.argv:
            print_header()
            print("Usage:")
            print("  python scripts/cli_research.py \"Your research question\" [options]")
            print()
            print("Options:")
            print("  --verbose, -v  Show detailed progress during execution")
            print("  --help, -h     Show this help message")
            print()
            print("Examples:")
            print("  python scripts/cli_research.py \"2020年玉山銀行洗錢防制裁罰\"")
            print("  python scripts/cli_research.py \"分析銀行業洗錢防制的主要問題\" --verbose")
            print()
            print("Interactive Mode:")
            print("  python scripts/cli_research.py")
            print()
            return

        # Command line mode
        query = " ".join(sys.argv[1:])

        # Check for flags
        verbose = "--verbose" in sys.argv or "-v" in sys.argv
        if verbose:
            query = query.replace("--verbose", "").replace("-v", "").strip()

        print_header()
        await research_query(query, verbose=verbose)
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
