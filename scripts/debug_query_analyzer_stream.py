"""
Debug script to simulate frontend integration with Query Analyzer.

This script shows exactly what the frontend will receive from the WebSocket stream,
including the query_analyzer node output with query insights.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query


def format_timestamp():
    """Get formatted timestamp."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def print_section(title: str, char: str = "="):
    """Print a section header."""
    print()
    print(char * 80)
    print(f" {title}")
    print(char * 80)
    print()


def print_node_event(node_name: str, state_update: dict, node_number: int):
    """Pretty print a node event."""
    timestamp = format_timestamp()
    print(f"[{timestamp}] 📦 Event #{node_number}: {node_name}")
    print("─" * 80)

    # Special handling for different node types
    if node_name == "query_analyzer" and "query_insight" in state_update:
        insight = state_update["query_insight"]
        print("🔍 QUERY ANALYZER OUTPUT:")
        print()
        print(f"  📊 Analysis Results:")
        print(f"     Query Type:       {insight.query_type}")
        print(f"     Search Strategy:  {insight.search_strategy}")
        print(f"     Complexity:       {insight.complexity}")

        if insight.key_entities:
            print(f"     Key Entities:     {', '.join(insight.key_entities)}")
        else:
            print(f"     Key Entities:     None")

        print()
        print(f"  💡 Reasoning:")
        # Wrap long reasoning text
        reasoning_lines = insight.reasoning.split('\n')
        for line in reasoning_lines:
            if len(line) <= 72:
                print(f"     {line}")
            else:
                # Word wrap
                words = line.split()
                current_line = "     "
                for word in words:
                    if len(current_line) + len(word) + 1 <= 77:
                        current_line += word + " "
                    else:
                        print(current_line.rstrip())
                        current_line = "     " + word + " "
                if current_line.strip():
                    print(current_line.rstrip())

        print()
        print("  📤 Frontend should display this insight before showing the plan!")

    elif node_name == "planner" and "plan" in state_update:
        plan = state_update["plan"]
        print("📋 PLANNER OUTPUT:")
        print()
        print(f"  Plan created with {len(plan.tasks)} tasks:")
        print()
        for i, task in enumerate(plan.tasks, 1):
            status_icon = "⏳" if task.status == "pending" else "✅"
            print(f"  {i}. {status_icon} [{task.tool}] {task.description[:60]}...")
            print(f"     Status: {task.status}")
            if task.args:
                print(f"     Args: {task.args}")

    elif node_name == "execute_task":
        print("⚙️  EXECUTOR OUTPUT:")
        print()
        if "past_steps" in state_update and state_update["past_steps"]:
            latest_step = state_update["past_steps"][-1]
            task_dict, result = latest_step
            print(f"  Task: {task_dict.get('description', 'N/A')[:60]}...")
            print(f"  Tool: {task_dict.get('tool', 'N/A')}")
            print(f"  Status: {task_dict.get('status', 'N/A')}")
            if result:
                result_preview = result[:100] + "..." if len(result) > 100 else result
                print(f"  Result preview: {result_preview}")

    elif node_name == "replanner":
        print("🔄 REPLANNER OUTPUT:")
        print()
        if "response" in state_update and state_update["response"]:
            response = state_update["response"]
            print(f"  Response generated ({len(response)} chars)")
            print(f"  Preview: {response[:100]}...")
        elif "plan" in state_update and state_update["plan"]:
            plan = state_update["plan"]
            print(f"  Plan updated with {len(plan.tasks)} tasks")

    elif node_name == "reporter":
        print("📝 REPORTER OUTPUT:")
        print()
        if "response" in state_update and state_update["response"]:
            response = state_update["response"]
            print(f"  Final response generated ({len(response)} chars)")
            print()
            print("  Response preview:")
            print("  " + "─" * 76)
            lines = response.split('\n')
            for line in lines[:5]:  # Show first 5 lines
                print(f"  {line}")
            if len(lines) > 5:
                print(f"  ... ({len(lines) - 5} more lines)")
            print("  " + "─" * 76)

    else:
        # Generic output for other nodes
        print(f"  State update keys: {list(state_update.keys())}")
        for key, value in state_update.items():
            if key == "past_steps":
                print(f"  {key}: {len(value)} steps")
            elif isinstance(value, str):
                preview = value[:100] + "..." if len(value) > 100 else value
                print(f"  {key}: {preview}")
            else:
                print(f"  {key}: {type(value).__name__}")

    print()


def print_json_for_frontend(node_name: str, state_update: dict):
    """Print the JSON that frontend would receive."""
    # Convert to JSON-serializable format
    json_data = {
        "node_name": node_name,
        "state_update": {}
    }

    for key, value in state_update.items():
        if hasattr(value, "dict"):  # Pydantic model
            json_data["state_update"][key] = value.dict()
        elif isinstance(value, list):
            json_data["state_update"][key] = f"<list with {len(value)} items>"
        else:
            json_data["state_update"][key] = str(value) if value else None

    print(json.dumps(json_data, indent=2, ensure_ascii=False))


async def debug_query_stream(query_text: str, show_json: bool = False):
    """
    Debug the query stream with query analyzer.

    Args:
        query_text: The query to test
        show_json: If True, also print JSON format for each event
    """
    print_section(f"🔍 Query Analyzer Debug Session")

    print(f"Query: {query_text}")
    print(f"Mode: Plan-and-Execute with Query Analyzer")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Initialize orchestrator
    print()
    print("Initializing orchestrator...")
    orchestrator = AgentOrchestrator()

    if not orchestrator.use_rag:
        print("❌ ERROR: RAG not available. Please index documents first.")
        return

    print("✅ Orchestrator initialized")

    # Create query
    query = Query(text=query_text)

    print_section("📡 Streaming Events (What Frontend Receives)", "-")

    event_count = 0
    query_insight_received = False
    plan_received = False

    try:
        async for node_name, state_update in orchestrator.stream_query(
            query=query,
            use_plan_execute=True,  # Use Plan-and-Execute workflow
            enable_demo_delay=False
        ):
            event_count += 1

            # Print the event in a readable format
            print_node_event(node_name, state_update, event_count)

            # Track what we've received
            if node_name == "query_analyzer":
                query_insight_received = True
            if node_name == "planner":
                plan_received = True

            # Optionally show JSON format
            if show_json:
                print("📤 JSON Format (for frontend):")
                print_json_for_frontend(node_name, state_update)
                print()

    except KeyError as e:
        # Ignore KeyError from standard workflow (we only care about plan-and-execute)
        if event_count > 0:  # If we got some events, that's fine
            print()
            print(f"⚠️  Note: Workflow completed. Ignoring error from other workflow: {e}")
        else:
            print()
            print(f"❌ ERROR during streaming: {e}")
            import traceback
            traceback.print_exc()
            return
    except Exception as e:
        print()
        print(f"❌ ERROR during streaming: {e}")
        import traceback
        traceback.print_exc()
        return

    # Summary
    print_section("📊 Debug Summary")

    print(f"Total events received: {event_count}")
    print(f"Query insight received: {'✅ YES' if query_insight_received else '❌ NO'}")
    print(f"Plan received: {'✅ YES' if plan_received else '❌ NO'}")
    print()

    if query_insight_received and plan_received:
        print("✅ SUCCESS: Query Analyzer is working correctly!")
        print()
        print("Frontend Integration Notes:")
        print("  1. Listen for 'query_analyzer' event first")
        print("  2. Display query insight to user (type, strategy, entities, reasoning)")
        print("  3. Then show the plan when 'planner' event arrives")
        print("  4. Show progress as 'execute_task' events come in")
        print("  5. Display final response from 'reporter' event")
    else:
        print("⚠️  WARNING: Expected events not received")
        print("   Check the event stream above for issues")

    print()


async def run_multiple_tests():
    """Run multiple test queries to verify different query types."""
    test_queries = [
        {
            "query": "2020年玉山銀行洗錢防制裁罰",
            "description": "Factual query with specific date and bank"
        },
        {
            "query": "分析銀行業洗錢防制的主要問題",
            "description": "Analytical query requiring synthesis"
        },
        {
            "query": "比較玉山銀行和台新銀行的裁罰案件",
            "description": "Comparative query with multiple entities"
        }
    ]

    for i, test_case in enumerate(test_queries, 1):
        print()
        print("=" * 80)
        print(f" TEST {i}/{len(test_queries)}: {test_case['description']}")
        print("=" * 80)
        print()

        await debug_query_stream(test_case["query"], show_json=False)

        if i < len(test_queries):
            print()
            print("Press Enter to continue to next test...")
            input()


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        show_json = "--json" in sys.argv
        await debug_query_stream(query, show_json=show_json)
    else:
        # Interactive mode
        print("=" * 80)
        print(" Query Analyzer Debug Tool")
        print("=" * 80)
        print()
        print("Options:")
        print("  1. Test single query")
        print("  2. Run multiple test queries")
        print("  3. Exit")
        print()

        choice = input("Enter choice (1-3): ").strip()

        if choice == "1":
            query = input("\nEnter query: ").strip()
            if query:
                show_json = input("Show JSON format? (y/n): ").strip().lower() == 'y'
                await debug_query_stream(query, show_json=show_json)
        elif choice == "2":
            await run_multiple_tests()
        else:
            print("Exiting...")


if __name__ == "__main__":
    asyncio.run(main())
