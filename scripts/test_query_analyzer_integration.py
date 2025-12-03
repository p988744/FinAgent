"""Test script to verify Query Analyzer integration with Plan-and-Execute workflow."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.agents.plan_execute.graph import PlanExecuteWorkflow


async def test_query_analyzer_integration():
    """Test the full workflow with query analyzer."""

    print("="*80)
    print("Query Analyzer Integration Test")
    print("="*80)
    print()

    # Initialize components
    print("Initializing components...")
    retriever = DocumentRetriever(collection_name="legal_documents")
    hard_searcher = HardSearcher(db_path="data/finagent.db")
    workflow = PlanExecuteWorkflow(retriever=retriever, hard_searcher=hard_searcher)
    print("✅ Components initialized")
    print()

    # Test query
    test_query = "2020年玉山銀行洗錢防制裁罰"

    print(f"Testing with query: {test_query}")
    print()

    # Create initial state
    initial_state = {
        "input": test_query,
        "query_insight": None,
        "plan": None,
        "past_steps": [],
        "response": None
    }

    print("Workflow execution:")
    print("─"*80)

    node_count = 0
    query_insight_found = False
    plan_found = False

    try:
        # Stream workflow
        async for event in workflow.graph.astream(initial_state):
            for node_name, state_update in event.items():
                node_count += 1
                print(f"✓ Node {node_count}: {node_name}")

                # Check for query_insight
                if "query_insight" in state_update and state_update["query_insight"]:
                    query_insight_found = True
                    insight = state_update["query_insight"]
                    print(f"  📊 Query Insight:")
                    print(f"     Type: {insight.query_type}")
                    print(f"     Strategy: {insight.search_strategy}")
                    print(f"     Complexity: {insight.complexity}")
                    print(f"     Entities: {', '.join(insight.key_entities)}")

                # Check for plan
                if "plan" in state_update and state_update["plan"]:
                    plan_found = True
                    plan = state_update["plan"]
                    print(f"  📋 Plan created with {len(plan.tasks)} tasks:")
                    for i, task in enumerate(plan.tasks[:3], 1):  # Show first 3 tasks
                        task_desc = task.description[:50] + "..." if len(task.description) > 50 else task.description
                        print(f"     {i}. [{task.tool}] {task_desc}")
                    if len(plan.tasks) > 3:
                        print(f"     ... and {len(plan.tasks) - 3} more tasks")

                # Check for response
                if "response" in state_update and state_update["response"]:
                    response = state_update["response"]
                    print(f"  📝 Response generated ({len(response)} chars)")

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("─"*80)
    print()

    # Validation
    print("Validation:")
    print(f"  ✓ Total nodes executed: {node_count}")
    print(f"  {'✅' if query_insight_found else '❌'} Query insight generated")
    print(f"  {'✅' if plan_found else '❌'} Plan created")
    print()

    if query_insight_found and plan_found:
        print("="*80)
        print("✅ Integration test PASSED!")
        print("="*80)
        print()
        print("Summary:")
        print("  ✓ Query Analyzer successfully analyzed the query")
        print("  ✓ Planner created a plan based on the query")
        print("  ✓ Workflow executed without errors")
    else:
        print("="*80)
        print("⚠️  Integration test INCOMPLETE")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(test_query_analyzer_integration())
