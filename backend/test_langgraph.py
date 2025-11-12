"""Test script for LangGraph workflow."""

import asyncio
import logging
from finagent.models.queries import Query
from finagent.agents.orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_langgraph_workflow():
    """Test the LangGraph multi-agent workflow."""
    print("=" * 80)
    print("Testing LangGraph Multi-Agent Workflow")
    print("=" * 80)

    # Initialize orchestrator
    print("\n1. Initializing orchestrator...")
    orchestrator = AgentOrchestrator()

    # Create test query
    print("\n2. Creating test query...")
    query = Query(
        text="玉山銀行洗錢防制裁罰",
        max_results=3
    )
    print(f"   Query: {query.text}")
    print(f"   Max results: {query.max_results}")

    # Process query
    print("\n3. Processing query through LangGraph workflow...")
    try:
        answer = await orchestrator.process_query(query)

        # Display results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)

        print(f"\n執行摘要:\n{answer.executive_summary}\n")

        print(f"關鍵發現:")
        for i, finding in enumerate(answer.key_findings, 1):
            print(f"  {i}. {finding}")

        print(f"\n引用數量: {len(answer.citations)}")
        for citation in answer.citations[:3]:  # Show first 3
            print(f"  [{citation.id}] {citation.title}")

        print(f"\n信心分數: {answer.confidence_score.value}")
        print(f"信心說明: {answer.confidence_explanation}")

        print(f"\n處理時間: {answer.processing_time_ms}ms")

        print(f"\n詳細分析:\n{answer.detailed_analysis[:500]}...")

        print("\n" + "=" * 80)
        print("Test completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_langgraph_workflow())
