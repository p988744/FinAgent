#!/usr/bin/env python3
"""
Direct test of Plan-and-Execute workflow without orchestrator.
This bypasses orchestrator bugs and tests the agent directly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from finagent.agents.plan_execute.graph import PlanExecuteWorkflow
from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher


async def test_plan_execute_workflow():
    """Test Plan-and-Execute workflow directly"""
    print("\n" + "="*80)
    print("Direct Plan-and-Execute Workflow Test")
    print("="*80)

    try:
        # Initialize components
        print("\n📦 Initializing components...")
        retriever = DocumentRetriever(collection_name="legal_documents")
        hard_searcher = HardSearcher(db_path="data/finagent.db")
        workflow = PlanExecuteWorkflow(retriever=retriever, hard_searcher=hard_searcher)

        print("✓ Retriever initialized")
        print("✓ HardSearcher initialized")
        print("✓ Workflow graph compiled")

        # Test query
        query_text = "找出2020年金管會對玉山銀行的洗錢防制裁罰"
        print(f"\n🔍 Query: {query_text}")

        # Initialize state
        initial_state = {
            "input": query_text,
            "plan": None,
            "past_steps": [],
            "response": None
        }

        # Stream workflow execution
        print("\n📡 Streaming workflow execution:\n")
        final_state = initial_state.copy()
        node_count = 0

        async for event in workflow.graph.astream(initial_state):
            for node_name, state_update in event.items():
                node_count += 1
                final_state.update(state_update)

                print(f"  [{node_count}] Node: {node_name}")

                # Show plan when created
                if node_name == "planner" and state_update.get("plan"):
                    plan = state_update["plan"]
                    print(f"      📋 Plan created with {len(plan.tasks)} tasks")
                    for i, task in enumerate(plan.tasks, 1):
                        print(f"         {i}. [{task.tool}] {task.description[:60]}...")

                # Show execution results
                if node_name == "execute_task" and state_update.get("past_steps"):
                    latest_step = state_update["past_steps"][-1]
                    task, result = latest_step
                    task_desc = task.get("description", "N/A") if isinstance(task, dict) else getattr(task, "description", "N/A")
                    print(f"      ✓ Task: {task_desc[:50]}...")
                    print(f"      → Result: {result[:80]}...")

                # Show replanner decision
                if node_name == "replanner":
                    if state_update.get("response"):
                        response = state_update["response"]
                        print(f"      ✅ Replanner decided to respond (not replan)")
                        print(f"      → Response preview: {response[:100]}...")
                    elif state_update.get("plan"):
                        print(f"      🔄 Replanner created new plan")

                # Show reporter output
                if node_name == "reporter" and state_update.get("response"):
                    response = state_update["response"]
                    print(f"      📄 Final report generated")
                    print(f"      → Length: {len(response)} characters")

        # Display final response
        print("\n" + "="*80)
        print("FINAL RESPONSE")
        print("="*80)

        response = final_state.get("response")
        if response:
            print(f"\n{response}\n")
            print(f"✅ Workflow completed successfully!")
            print(f"   Total nodes executed: {node_count}")
            print(f"   Response length: {len(response)} characters")
            return True
        else:
            print(f"\n⚠️  No response in final state")
            print(f"   Final state keys: {list(final_state.keys())}")
            return False

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configuration_check():
    """Quick check that retriever has documents"""
    print("\n" + "="*80)
    print("Configuration Check")
    print("="*80)

    try:
        retriever = DocumentRetriever(collection_name="legal_documents")

        if not retriever.collection:
            print("❌ Collection does not exist")
            return False

        count = retriever.collection.count()
        print(f"\n✓ Collection exists: {retriever.collection_name}")
        print(f"✓ Document chunks indexed: {count}")

        if count == 0:
            print("\n⚠️  Collection is empty. Please run: uv run finagent reindex")
            return False

        return True

    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False


async def main():
    """Run tests"""
    print("\n" + "="*80)
    print("FinAgent v1.1 Direct Workflow Test")
    print("="*80)
    print("\nThis test directly invokes the Plan-and-Execute workflow")
    print("without going through the orchestrator layer.\n")

    # Check configuration
    config_ok = await test_configuration_check()
    if not config_ok:
        print("\n❌ Configuration check failed. Cannot proceed.")
        return 1

    # Run workflow test
    success = await test_plan_execute_workflow()

    print("\n" + "="*80)
    if success:
        print("✅ TEST PASSED")
        print("="*80)
        return 0
    else:
        print("❌ TEST FAILED")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
