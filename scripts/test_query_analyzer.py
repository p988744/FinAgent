"""Test script for Query Analyzer agent."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.agents.plan_execute.query_analyzer import QueryAnalyzerAgent
from finagent.agents.plan_execute.models import PlanExecuteState


async def test_query_analyzer():
    """Test the QueryAnalyzerAgent with various query types."""

    print("="*80)
    print("Query Analyzer Test Suite")
    print("="*80)
    print()

    # Initialize query analyzer
    analyzer = QueryAnalyzerAgent()

    # Test queries
    test_queries = [
        {
            "query": "2020年玉山銀行洗錢防制裁罰500萬的案件詳情",
            "description": "Factual query with specific date, bank, amount"
        },
        {
            "query": "分析銀行業洗錢防制的主要問題",
            "description": "Analytical query requiring synthesis"
        },
        {
            "query": "找出文件中包含「金管會」和「裁罰」的所有案件",
            "description": "Explicit keyword search requirement"
        },
        {
            "query": "比較玉山銀行和台新銀行在內部控制方面的裁罰案件",
            "description": "Comparative query with multiple entities"
        },
        {
            "query": "2020-2023年間所有銀行的洗錢防制裁罰案件趨勢",
            "description": "Temporal query with range"
        }
    ]

    for i, test_case in enumerate(test_queries, 1):
        print(f"─"*80)
        print(f"Test Case {i}/{len(test_queries)}")
        print(f"─"*80)
        print(f"Query: {test_case['query']}")
        print(f"Description: {test_case['description']}")
        print()

        # Create state
        state: PlanExecuteState = {
            "input": test_case["query"],
            "query_insight": None,
            "plan": None,
            "past_steps": [],
            "response": None
        }

        try:
            # Analyze query
            result = await analyzer.analyze(state)
            insight = result["query_insight"]

            # Display results
            print(f"📊 Analysis Results:")
            print(f"   Query Type: {insight.query_type}")
            print(f"   Search Strategy: {insight.search_strategy}")
            print(f"   Complexity: {insight.complexity}")
            print(f"   Key Entities: {', '.join(insight.key_entities) if insight.key_entities else 'None'}")
            print()
            print(f"💡 Reasoning:")
            print(f"   {insight.reasoning}")
            print()
            print(f"✅ Analysis completed successfully")

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("="*80)
    print("Test suite completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_query_analyzer())
