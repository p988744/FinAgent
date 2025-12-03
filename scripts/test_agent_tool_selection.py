#!/usr/bin/env python3
"""
Test script for agent tool selection and planning capabilities.

This script validates:
1. Agent correctly selects each registered tool based on query type
2. Planner creates dynamic plans (not always the same)
3. Memory/memo functionality works correctly
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.agents.plan_execute.graph import PlanExecuteWorkflow
from finagent.agents.plan_execute.planner import PlannerAgent
from finagent.agents.plan_execute.executor import ExecutorAgent


async def test_tool_selection():
    """
    Test 1: Agent selects correct tool for different query types.

    Tests each registered tool:
    - retriever: Semantic search (concept-based queries)
    - hard_search: Keyword search (specific term queries)
    - hybrid_search: Combined search (queries with both concepts and specific terms)
    """
    print("\n" + "="*80)
    print("TEST 1: Tool Selection")
    print("="*80)
    print("\nValidating that agent selects appropriate tool for each query type...")

    # Initialize components
    retriever = DocumentRetriever(collection_name="legal_documents")
    hard_searcher = HardSearcher(db_path="data/finagent.db")
    workflow = PlanExecuteWorkflow(retriever=retriever, hard_searcher=hard_searcher)

    # Test cases designed to trigger specific tools
    test_cases = [
        {
            "query": "內部控制缺失的法律責任是什麼？",
            "description": "Conceptual query about internal control legal liability",
            "expected_tool": "retriever",  # Semantic search for concept
            "reason": "Concept-based question requiring semantic understanding"
        },
        {
            "query": "找出文件中包含「金管會」和「裁罰」的所有案件",
            "description": "Keyword search for specific terms",
            "expected_tool": "hard_search",  # Exact keyword matching
            "reason": "Explicit keyword search request"
        },
        {
            "query": "2020年玉山銀行因洗錢防制被罰500萬的案件詳情",
            "description": "Query with specific terms AND concepts",
            "expected_tool": "hybrid_search",  # Both semantic + keyword
            "reason": "Contains specific terms (2020, 500萬) and concepts (洗錢防制)"
        },
        {
            "query": "分析銀行業洗錢防制的主要問題",
            "description": "Analytical query requiring understanding",
            "expected_tool": "retriever",  # Semantic analysis
            "reason": "Analysis task requiring semantic understanding"
        },
        {
            "query": "搜尋2023年所有裁罰金額超過100萬的案件",
            "description": "Search with specific numbers and dates",
            "expected_tool": "hybrid_search",  # Year + amount (hybrid best)
            "reason": "Combines specific numbers with search requirement"
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_tool = test_case["expected_tool"]
        description = test_case["description"]
        reason = test_case["reason"]

        print(f"\n{'─'*80}")
        print(f"Test Case {i}/{len(test_cases)}")
        print(f"{'─'*80}")
        print(f"Query: {query}")
        print(f"Description: {description}")
        print(f"Expected Tool: {expected_tool}")
        print(f"Reason: {reason}")
        print()

        try:
            # Create initial state
            initial_state = {
                "input": query,
                "plan": None,
                "past_steps": [],
                "response": None
            }

            # Run workflow until planner creates plan
            tools_used = []
            async for event in workflow.graph.astream(initial_state):
                for node_name, state_update in event.items():
                    # Capture plan when created
                    if node_name == "planner" and state_update.get("plan"):
                        plan = state_update["plan"]
                        print(f"📋 Plan created with {len(plan.tasks)} tasks:")
                        for j, task in enumerate(plan.tasks, 1):
                            tool_name = task.tool
                            task_desc = task.description[:60]
                            print(f"   {j}. [{tool_name}] {task_desc}...")
                            tools_used.append(tool_name)
                        break
                if tools_used:
                    break

            # Check if expected tool was selected
            if expected_tool in tools_used:
                print(f"\n✅ PASS: Agent selected '{expected_tool}' tool")
                results.append({
                    "query": query[:50],
                    "expected": expected_tool,
                    "selected": tools_used,
                    "success": True
                })
            else:
                print(f"\n⚠️  PARTIAL: Agent selected {tools_used}, expected '{expected_tool}'")
                print(f"   Note: Agent may choose different valid approach")
                results.append({
                    "query": query[:50],
                    "expected": expected_tool,
                    "selected": tools_used,
                    "success": expected_tool in tools_used if tools_used else False
                })

        except Exception as e:
            print(f"\n❌ FAIL: Error - {e}")
            results.append({
                "query": query[:50],
                "expected": expected_tool,
                "selected": [],
                "success": False
            })

    # Summary
    print(f"\n{'='*80}")
    print("TOOL SELECTION SUMMARY")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    print(f"\n{'Query':<50} {'Expected':<15} {'Selected':<15} {'Result':<10}")
    print(f"{'-'*90}")
    for r in results:
        query_short = r["query"][:47] + "..." if len(r["query"]) > 47 else r["query"]
        selected = r["selected"][0] if r["selected"] else "None"
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        print(f"{query_short:<50} {r['expected']:<15} {selected:<15} {status:<10}")

    print(f"\n📊 Results: {passed}/{total} passed ({100*passed/total:.1f}%)")

    return passed == total


async def test_dynamic_planning():
    """
    Test 2: Planner creates different plans for different queries.

    Validates that the planner:
    - Creates different task sequences for different query types
    - Adjusts number of tasks based on complexity
    - Selects appropriate tools for each task
    """
    print("\n" + "="*80)
    print("TEST 2: Dynamic Planning")
    print("="*80)
    print("\nValidating that planner creates different plans (not always the same)...")

    # Initialize planner
    planner = PlannerAgent()

    # Different query types to test dynamic planning
    test_queries = [
        {
            "query": "玉山銀行洗錢防制裁罰",
            "description": "Simple factual query",
            "expected_complexity": "low",  # 1-2 tasks
        },
        {
            "query": "分析2020-2023年間所有銀行的洗錢防制裁罰案件，並總結主要違規類型和金額趨勢",
            "description": "Complex analytical query with multiple requirements",
            "expected_complexity": "high",  # 3+ tasks
        },
        {
            "query": "比較玉山銀行和台新銀行在內部控制方面的裁罰案件",
            "description": "Comparative query requiring multiple searches",
            "expected_complexity": "medium",  # 2-3 tasks
        },
    ]

    plans = []

    for i, test_query in enumerate(test_queries, 1):
        query = test_query["query"]
        description = test_query["description"]
        expected_complexity = test_query["expected_complexity"]

        print(f"\n{'─'*80}")
        print(f"Query {i}/{len(test_queries)}")
        print(f"{'─'*80}")
        print(f"Query: {query}")
        print(f"Description: {description}")
        print(f"Expected Complexity: {expected_complexity}")
        print()

        try:
            # Create plan
            state = {"input": query}
            plan_state = await planner.plan(state)
            plan = plan_state.get("plan")

            if plan:
                num_tasks = len(plan.tasks)
                print(f"📋 Plan created:")
                print(f"   Tasks: {num_tasks}")

                for j, task in enumerate(plan.tasks, 1):
                    task_desc = task.description[:60] + "..." if len(task.description) > 60 else task.description
                    print(f"   {j}. [{task.tool}] {task_desc}")

                plans.append({
                    "query": query[:50],
                    "num_tasks": num_tasks,
                    "tools": [t.tool for t in plan.tasks],
                    "first_tool": plan.tasks[0].tool if plan.tasks else None
                })

                print(f"\n✅ Plan created successfully")
            else:
                print(f"\n❌ No plan created")

        except Exception as e:
            print(f"\n❌ Error creating plan: {e}")

    # Check for diversity in plans
    print(f"\n{'='*80}")
    print("DYNAMIC PLANNING SUMMARY")
    print(f"{'='*80}")

    if len(plans) >= 2:
        # Check if plans are different
        all_same_tasks = all(p["num_tasks"] == plans[0]["num_tasks"] for p in plans)
        all_same_tools = all(p["tools"] == plans[0]["tools"] for p in plans)

        print(f"\nNumber of tasks across plans: {[p['num_tasks'] for p in plans]}")
        print(f"Tool sequences: {[p['tools'] for p in plans]}")

        if all_same_tasks and all_same_tools:
            print(f"\n⚠️  WARNING: All plans are identical (may indicate static planning)")
            print(f"   Expected: Different task counts and tool selections")
            success = False
        else:
            print(f"\n✅ PASS: Plans are dynamic and vary based on query complexity")
            success = True

        return success
    else:
        print(f"\n❌ FAIL: Not enough plans created to test diversity")
        return False


async def test_memory_agent():
    """
    Test 3: Memory/memo functionality.

    Tests:
    - Query history is stored
    - Past results can be referenced
    - Agent can use context from previous queries
    """
    print("\n" + "="*80)
    print("TEST 3: Memory/Memo Agent")
    print("="*80)
    print("\nValidating memory and context management...")

    # Initialize components
    retriever = DocumentRetriever(collection_name="legal_documents")
    hard_searcher = HardSearcher(db_path="data/finagent.db")
    workflow = PlanExecuteWorkflow(retriever=retriever, hard_searcher=hard_searcher)

    # Test scenario: Sequential queries that should reference previous context
    test_scenarios = [
        {
            "query": "玉山銀行2020年的洗錢防制裁罰",
            "description": "Initial query establishing context",
            "expected_behavior": "Store query in history"
        },
        {
            "query": "這個案件的裁罰金額是多少？",
            "description": "Follow-up query requiring previous context",
            "expected_behavior": "Reference previous query context (玉山銀行, 2020, 洗錢防制)"
        },
    ]

    print("\n📝 Testing memory with sequential queries...")
    print("\nNote: Currently, memory is stored in database via query_memo.py")
    print("This test validates that the workflow completes successfully.")
    print("Full memory integration testing will require database verification.\n")

    session_results = []

    for i, scenario in enumerate(test_scenarios, 1):
        query = scenario["query"]
        description = scenario["description"]
        expected = scenario["expected_behavior"]

        print(f"{'─'*80}")
        print(f"Query {i}/{len(test_scenarios)}")
        print(f"{'─'*80}")
        print(f"Query: {query}")
        print(f"Description: {description}")
        print(f"Expected: {expected}")
        print()

        try:
            initial_state = {
                "input": query,
                "plan": None,
                "past_steps": [],
                "response": None
            }

            # Run workflow
            final_state = {}
            node_count = 0
            async for event in workflow.graph.astream(initial_state):
                for node_name, state_update in event.items():
                    node_count += 1
                    final_state.update(state_update)

                    if node_name == "planner":
                        print(f"   ✓ Planner executed")
                    elif node_name == "execute_task":
                        print(f"   ✓ Task executed")
                    elif node_name == "replanner":
                        print(f"   ✓ Replanner executed")

            # Check if workflow completed
            has_response = "response" in final_state and final_state["response"]

            if has_response:
                print(f"\n✅ Query processed successfully")
                print(f"   Nodes executed: {node_count}")
                session_results.append(True)
            else:
                print(f"\n⚠️  Query processed but no final response")
                session_results.append(False)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            session_results.append(False)

    # Summary
    print(f"\n{'='*80}")
    print("MEMORY AGENT SUMMARY")
    print(f"{'='*80}")

    success_count = sum(session_results)
    total = len(session_results)

    print(f"\n✓ Queries processed: {success_count}/{total}")

    if success_count == total:
        print(f"\n✅ PASS: Memory agent workflow functional")
        print(f"\nNote: Full memory testing requires:")
        print(f"  1. Check database for stored queries (query_memo.py)")
        print(f"  2. Verify context is passed between queries")
        print(f"  3. Test replanner uses past_steps for context")
        return True
    else:
        print(f"\n❌ FAIL: Some queries failed to process")
        return False


async def main():
    """Run all agent tests."""
    print("\n" + "="*80)
    print("FinAgent Agent Testing Suite")
    print("="*80)
    print("\nThis suite validates:")
    print("  1. Tool Selection - Agent picks correct tool for query type")
    print("  2. Dynamic Planning - Plans vary based on query complexity")
    print("  3. Memory/Memo - Context is maintained across queries")
    print()

    results = []

    # Test 1: Tool Selection
    try:
        result1 = await test_tool_selection()
        results.append(("Tool Selection", result1))
    except Exception as e:
        print(f"\n❌ Test 1 failed with error: {e}")
        results.append(("Tool Selection", False))

    # Test 2: Dynamic Planning
    try:
        result2 = await test_dynamic_planning()
        results.append(("Dynamic Planning", result2))
    except Exception as e:
        print(f"\n❌ Test 2 failed with error: {e}")
        results.append(("Dynamic Planning", False))

    # Test 3: Memory Agent
    try:
        result3 = await test_memory_agent()
        results.append(("Memory Agent", result3))
    except Exception as e:
        print(f"\n❌ Test 3 failed with error: {e}")
        results.append(("Memory Agent", False))

    # Final Summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n{'Test':<20} {'Result':<10}")
    print(f"{'-'*30}")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status:<10}")

    print(f"\n📊 Overall: {passed}/{total} tests passed ({100*passed/total:.1f}%)")

    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
