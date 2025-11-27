"""
Workflow Simulation Test - Investigate why tools cause timeouts in actual workflow.

Purpose: Simulate the v1.1 Plan-and-Execute workflow step-by-step to identify
where LLM timeouts occur.

Test Flow:
1. QueryAnalyzer (LLM call)
2. Planner (LLM call)
3. Executor (Tool calls - NO LLM)
4. Replanner (LLM call)
5. Reporter (LLM call)

Expected: Steps 1, 2, 4, 5 use LLM. Step 3 uses tools only.
"""

import asyncio
import time
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from finagent.config_manager import ConfigManager
from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.tools import RetrieverTool, HardSearchTool, HybridRetrieverTool


class Task(BaseModel):
    """Simplified task model."""
    id: int
    description: str
    tool: str
    args: dict
    status: str = "pending"


class SimplePlan(BaseModel):
    """Simplified plan model."""
    tasks: List[Task]


async def test_step_1_query_analyzer():
    """
    Step 1: QueryAnalyzer (LLM call).

    Purpose: Analyze query to determine type, strategy, complexity.
    """
    print("\n" + "=" * 80)
    print("STEP 1: QueryAnalyzer (LLM Call)")
    print("=" * 80)

    config = ConfigManager()
    settings = config.get_all_settings()

    llm = ChatOpenAI(
        model=settings.get("llm_model", "gpt-4o-mini"),
        api_key=settings.get("llm_api_key"),
        base_url=settings.get("llm_base_url"),
        temperature=0.0,
        timeout=60.0,
        max_retries=2
    )

    messages = [
        SystemMessage(content="你是一個查詢分析專家。分析用戶查詢並判斷類型。"),
        HumanMessage(content="Query: 玉山銀行洗錢防制裁罰")
    ]

    try:
        start_time = time.time()
        response = await llm.ainvoke(messages)
        execution_time = time.time() - start_time

        print(f"✅ QueryAnalyzer completed in {execution_time:.2f}s")
        print(f"Response: {response.content[:150]}...")
        print("=" * 80)

        return True, execution_time

    except Exception as e:
        print(f"❌ QueryAnalyzer failed: {str(e)}")
        print("=" * 80)
        return False, 0.0


async def test_step_2_planner():
    """
    Step 2: Planner (LLM call).

    Purpose: Create research plan with tasks and tool assignments.
    """
    print("\n" + "=" * 80)
    print("STEP 2: Planner (LLM Call)")
    print("=" * 80)

    config = ConfigManager()
    settings = config.get_all_settings()

    llm = ChatOpenAI(
        model=settings.get("llm_model", "gpt-4o-mini"),
        api_key=settings.get("llm_api_key"),
        base_url=settings.get("llm_base_url"),
        temperature=0.0,
        timeout=60.0,
        max_retries=2
    )

    # Simplified plan generation prompt
    messages = [
        SystemMessage(content="""你是研究規劃專家。根據查詢創建研究計劃。

Available tools:
1. retriever: Semantic search
2. hard_search: Keyword search
3. hybrid_search: Combined search

Return a JSON plan with tasks."""),
        HumanMessage(content="Create a plan for: 玉山銀行洗錢防制裁罰")
    ]

    try:
        start_time = time.time()
        response = await llm.ainvoke(messages)
        execution_time = time.time() - start_time

        print(f"✅ Planner completed in {execution_time:.2f}s")
        print(f"Response: {response.content[:150]}...")
        print("=" * 80)

        return True, execution_time

    except Exception as e:
        print(f"❌ Planner failed: {str(e)}")
        print("=" * 80)
        return False, 0.0


async def test_step_3_executor():
    """
    Step 3: Executor (Tool calls - NO LLM).

    Purpose: Execute tasks using tools. This should NOT call LLM.
    """
    print("\n" + "=" * 80)
    print("STEP 3: Executor (Tool Calls - NO LLM)")
    print("=" * 80)

    # Initialize tools
    retriever = DocumentRetriever()
    hard_searcher = HardSearcher()

    retriever_tool = RetrieverTool(retriever=retriever)
    hard_search_tool = HardSearchTool(hard_searcher=hard_searcher)
    hybrid_tool = HybridRetrieverTool(retriever=retriever)

    # Simulate tasks from planner
    tasks = [
        {
            "tool": "hybrid_search",
            "args": {"query": "玉山銀行洗錢防制裁罰", "k": 5}
        }
    ]

    try:
        for i, task in enumerate(tasks):
            tool_name = task["tool"]
            args = task["args"]

            print(f"Executing task {i+1}: {tool_name}")
            print(f"Args: {args}")

            start_time = time.time()

            if tool_name == "retriever":
                result = await retriever_tool.ainvoke(args)
            elif tool_name == "hard_search":
                result = await hard_search_tool.ainvoke(args)
            elif tool_name == "hybrid_search":
                result = await hybrid_tool.ainvoke(args)
            else:
                result = f"Unknown tool: {tool_name}"

            execution_time = time.time() - start_time

            print(f"✅ Task {i+1} completed in {execution_time:.2f}s")
            print(f"Result length: {len(result)} chars")
            print(f"Preview: {result[:150]}...")
            print("-" * 80)

        print("=" * 80)
        return True, execution_time

    except Exception as e:
        print(f"❌ Executor failed: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return False, 0.0


async def test_step_4_replanner():
    """
    Step 4: Replanner (LLM call).

    Purpose: Review progress and decide to continue or respond.
    """
    print("\n" + "=" * 80)
    print("STEP 4: Replanner (LLM Call)")
    print("=" * 80)

    config = ConfigManager()
    settings = config.get_all_settings()

    llm = ChatOpenAI(
        model=settings.get("llm_model", "gpt-4o-mini"),
        api_key=settings.get("llm_api_key"),
        base_url=settings.get("llm_base_url"),
        temperature=0.0,
        timeout=60.0,
        max_retries=2
    )

    messages = [
        SystemMessage(content="你是研究進度評估專家。根據任務結果決定是否完成或需要更多任務。"),
        HumanMessage(content="Task completed. Results obtained. Should we proceed to answer?")
    ]

    try:
        start_time = time.time()
        response = await llm.ainvoke(messages)
        execution_time = time.time() - start_time

        print(f"✅ Replanner completed in {execution_time:.2f}s")
        print(f"Response: {response.content[:150]}...")
        print("=" * 80)

        return True, execution_time

    except Exception as e:
        print(f"❌ Replanner failed: {str(e)}")
        print("=" * 80)
        return False, 0.0


async def test_step_5_reporter():
    """
    Step 5: Reporter (LLM call).

    Purpose: Synthesize final answer from task results.
    """
    print("\n" + "=" * 80)
    print("STEP 5: Reporter (LLM Call)")
    print("=" * 80)

    config = ConfigManager()
    settings = config.get_all_settings()

    llm = ChatOpenAI(
        model=settings.get("llm_model", "gpt-4o-mini"),
        api_key=settings.get("llm_api_key"),
        base_url=settings.get("llm_base_url"),
        temperature=0.0,
        timeout=60.0,
        max_retries=2
    )

    messages = [
        SystemMessage(content="你是研究報告專家。根據檢索結果撰寫完整研究報告。"),
        HumanMessage(content="Synthesize final answer based on: [retrieved documents about 玉山銀行洗錢防制裁罰]")
    ]

    try:
        start_time = time.time()
        response = await llm.ainvoke(messages)
        execution_time = time.time() - start_time

        print(f"✅ Reporter completed in {execution_time:.2f}s")
        print(f"Response: {response.content[:150]}...")
        print("=" * 80)

        return True, execution_time

    except Exception as e:
        print(f"❌ Reporter failed: {str(e)}")
        print("=" * 80)
        return False, 0.0


async def test_full_workflow_simulation():
    """
    Test the full workflow end-to-end.

    Purpose: Identify which step causes timeouts.
    """
    print("\n" + "=" * 80)
    print("FULL WORKFLOW SIMULATION")
    print("=" * 80)
    print("Query: 玉山銀行洗錢防制裁罰")
    print("=" * 80)

    total_start = time.time()
    results = {}

    # Step 1: QueryAnalyzer (LLM)
    success1, time1 = await test_step_1_query_analyzer()
    results["query_analyzer"] = (success1, time1)

    if not success1:
        print("\n❌ WORKFLOW STOPPED: QueryAnalyzer failed")
        return results

    # Step 2: Planner (LLM)
    success2, time2 = await test_step_2_planner()
    results["planner"] = (success2, time2)

    if not success2:
        print("\n❌ WORKFLOW STOPPED: Planner failed")
        return results

    # Step 3: Executor (Tools - NO LLM)
    success3, time3 = await test_step_3_executor()
    results["executor"] = (success3, time3)

    if not success3:
        print("\n❌ WORKFLOW STOPPED: Executor failed")
        return results

    # Step 4: Replanner (LLM)
    success4, time4 = await test_step_4_replanner()
    results["replanner"] = (success4, time4)

    if not success4:
        print("\n❌ WORKFLOW STOPPED: Replanner failed")
        return results

    # Step 5: Reporter (LLM)
    success5, time5 = await test_step_5_reporter()
    results["reporter"] = (success5, time5)

    total_time = time.time() - total_start

    # Summary
    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)

    total_llm_time = 0
    total_tool_time = 0

    for step_name, (success, step_time) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        is_llm = step_name in ["query_analyzer", "planner", "replanner", "reporter"]
        step_type = "(LLM)" if is_llm else "(TOOL)"

        print(f"{step_name:20s} {step_type:8s} {status:8s} {step_time:6.2f}s")

        if success:
            if is_llm:
                total_llm_time += step_time
            else:
                total_tool_time += step_time

    print("-" * 80)
    print(f"{'Total LLM Time':32s} {total_llm_time:6.2f}s")
    print(f"{'Total Tool Time':32s} {total_tool_time:6.2f}s")
    print(f"{'Total Workflow Time':32s} {total_time:6.2f}s")
    print("=" * 80)

    all_passed = all(success for success, _ in results.values())

    if all_passed:
        print("🎉 FULL WORKFLOW COMPLETED SUCCESSFULLY")
        print("\nConclusion:")
        print("- All steps executed without timeouts")
        print(f"- LLM calls: {len([s for s in results if s in ['query_analyzer', 'planner', 'replanner', 'reporter']])} total")
        print(f"- Tool calls: {len([s for s in results if s not in ['query_analyzer', 'planner', 'replanner', 'reporter']])} total")
        print(f"- LLM overhead: {total_llm_time:.2f}s")
        print(f"- Tool overhead: {total_tool_time:.2f}s")
    else:
        print("⚠️  WORKFLOW FAILED")
        failed_steps = [name for name, (success, _) in results.items() if not success]
        print(f"\nFailed steps: {', '.join(failed_steps)}")

    print("=" * 80)

    return results


async def main():
    """Run workflow simulation tests."""
    print("\n" + "=" * 80)
    print("WORKFLOW SIMULATION TEST SUITE")
    print("=" * 80)
    print("Purpose: Identify where LLM timeouts occur in v1.1 workflow")
    print("=" * 80)

    # Run full workflow simulation
    results = await test_full_workflow_simulation()

    print("\n✅ Workflow simulation complete!")
    print("\nKey Findings:")
    print("- Identify which steps timeout under load")
    print("- Measure LLM vs Tool execution time")
    print("- Understand where sustained load affects gateway")


if __name__ == "__main__":
    asyncio.run(main())
