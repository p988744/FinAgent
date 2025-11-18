"""Demo script to test dynamic planning with WebSocket integration."""

import asyncio
from finagent.agents.query_analyzer import QueryAnalyzer
from finagent.agents.tool_selector import ToolSelector


async def demo_dynamic_planning():
    """
    Demonstrate dynamic planning workflow:
    1. Query Analysis
    2. Tool Selection
    3. Display results that would be sent to frontend
    """

    # Test queries
    test_queries = [
        "玉山銀行最近一次的罰款紀錄",  # temporal/latest
        "玉山銀行過去所有的裁罰紀錄",  # comprehensive
        "「國泰世華銀行_內線交易_2021.txt」這個檔案的摘要",  # specific file
        "玉山銀行與國泰世華銀行的裁罰紀錄比較",  # comparison
    ]

    analyzer = QueryAnalyzer()
    selector = ToolSelector()

    print("=" * 80)
    print("Dynamic Planning Demo")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n【Query {i}】{query}")
        print("-" * 80)

        # Step 1: Analyze query (using fallback for demo)
        analysis = analyzer._fallback_analyze(query)

        print("\n📊 Query Analysis:")
        print(f"  Intent: {analysis.intent}")
        print(f"  Entities: {analysis.entities}")
        print(f"  Temporal: {analysis.has_temporal_constraint} ({analysis.temporal_type})")
        print(f"  Complexity: {analysis.complexity}")
        print(f"  Multi-entity: {analysis.requires_multi_entity}")
        print(f"  Exhaustive: {analysis.requires_exhaustive_search}")

        # Step 2: Select tools (using fallback for demo)
        selected_tools = selector._fallback_select_tools(query, analysis)

        print("\n🔧 Selected Tools:")
        for tool in selected_tools:
            print(f"  - {tool['tool_name']}")
            print(f"    Reason: {tool['reason']}")
            print(f"    Parameters: {tool.get('parameters', {})}")

        # Step 3: Show what would be sent to WebSocket
        print("\n📡 WebSocket Payload (dynamic_plan_analysis):")
        payload = {
            "query_analysis": {
                "intent": analysis.intent.value,
                "entities": analysis.entities,
                "has_temporal_constraint": analysis.has_temporal_constraint,
                "temporal_type": analysis.temporal_type,
                "complexity": analysis.complexity,
                "requires_multi_entity": analysis.requires_multi_entity,
                "requires_exhaustive_search": analysis.requires_exhaustive_search,
            },
            "selected_tools": selected_tools,
        }

        import json
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        print("\n")


if __name__ == "__main__":
    asyncio.run(demo_dynamic_planning())
