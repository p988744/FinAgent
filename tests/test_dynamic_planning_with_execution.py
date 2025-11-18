"""
Demo script showing Dynamic Planning with Tool Execution Tracking.

This demonstrates the complete flow:
1. Query Analysis
2. Tool Selection
3. Tool Execution (with real-time status updates)
4. Results Display
"""

import asyncio
import json
from datetime import datetime


async def demo_dynamic_planning_with_execution():
    """
    Demonstrate dynamic planning with tool execution tracking.

    This simulates what the frontend would see during a query.
    """
    print("=" * 100)
    print("Dynamic Planning with Tool Execution Tracking - Demo")
    print("=" * 100)

    # Test query
    query = "玉山銀行與國泰世華銀行的裁罰紀錄比較"
    print(f"\n📝 Query: {query}\n")

    # Step 1: Query Analysis & Tool Selection (sent immediately after planning)
    print("【Step 1】動態規劃分析")
    print("-" * 100)

    analysis_payload = {
        "query_analysis": {
            "intent": "comparison",
            "entities": ["玉山銀行", "國泰世華銀行"],
            "has_temporal_constraint": False,
            "temporal_type": None,
            "complexity": "medium",
            "requires_multi_entity": True,
            "requires_exhaustive_search": False,
        },
        "selected_tools": [
            {
                "tool_name": "multi_entity_search",
                "reason": "比較查詢需要多實體搜尋",
                "parameters": {
                    "entities": ["玉山銀行", "國泰世華銀行"],
                    "top_k_per_entity": 5,
                },
                "execution_order": 1,
            }
        ],
    }

    print("\n📡 WebSocket Event: dynamic_plan_analysis")
    print(json.dumps(analysis_payload, indent=2, ensure_ascii=False))

    # Step 2: Tool Execution Tracking (sent during action phase)
    print("\n\n【Step 2】工具執行追蹤")
    print("-" * 100)

    # Tool starts executing
    print("\n▶️  Tool Execution Started")
    print("📡 WebSocket Event: tool_execution_update")
    execution_start = {
        "tool_name": "multi_entity_search",
        "status": "executing",
        "parameters": {
            "entities": ["玉山銀行", "國泰世華銀行"],
            "top_k_per_entity": 5,
        },
    }
    print(json.dumps(execution_start, indent=2, ensure_ascii=False))

    # Simulate execution time
    await asyncio.sleep(1)

    # Tool completes successfully
    print("\n✅ Tool Execution Completed")
    print("📡 WebSocket Event: tool_execution_update")
    execution_complete = {
        "tool_name": "multi_entity_search",
        "status": "completed",
        "result_count": 10,
        "execution_time_ms": 850,
    }
    print(json.dumps(execution_complete, indent=2, ensure_ascii=False))

    # Step 3: Visual Representation
    print("\n\n【Step 3】前端顯示效果")
    print("-" * 100)
    print("""
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🔍 動態規劃分析                                                      1 個工具    │
├────────────────────────────────────────────────────────────────────────────────┤
│ ℹ️ 查詢分析                                                                      │
│                                                                                │
│ 🏷️ 意圖: [比較分析]           ⏱️ 複雜度: [medium]                                │
│                                                                                │
│ 🏷️ 實體:                                                                        │
│   [玉山銀行] [國泰世華銀行]                                                       │
│                                                                                │
│ Features: [🏷️ 多實體]                                                           │
├────────────────────────────────────────────────────────────────────────────────┤
│ 🔧 選擇的工具                                                                    │
│                                                                                │
│ ✅ 🔀 多實體搜尋                                                  #1  [已完成]     │
│    比較查詢需要多實體搜尋                                                         │
│    ✓ 10 個結果 (850ms)                                                         │
│    entities: 玉山銀行, 國泰世華銀行  top_k_per_entity: 5                          │
└────────────────────────────────────────────────────────────────────────────────┘
""")

    # Example 2: Failed execution
    print("\n\n【Example 2】工具執行失敗示例")
    print("-" * 100)

    print("\n📡 WebSocket Event: tool_execution_update (failed)")
    execution_failed = {
        "tool_name": "read_file",
        "status": "failed",
        "error": "檔案不存在: 國泰世華銀行_內線交易_2021.txt",
    }
    print(json.dumps(execution_failed, indent=2, ensure_ascii=False))

    print("\n前端顯示:")
    print("""
┌────────────────────────────────────────────────────────────────────────────────┐
│ ❌ 📄 讀取檔案                                                      #1  [失敗]     │
│    直接讀取指定檔案                                                               │
│    ✗ 檔案不存在: 國泰世華銀行_內線交易_2021.txt                                     │
│    filename: 國泰世華銀行_內線交易_2021.txt                                        │
└────────────────────────────────────────────────────────────────────────────────┘
""")

    # Example 3: Multiple tools with different statuses
    print("\n\n【Example 3】多工具執行狀態")
    print("-" * 100)
    print("""
情境：複雜查詢需要執行多個工具

📡 Events:
1. dynamic_plan_analysis → 選擇了 3 個工具
2. tool_execution_update (hybrid_search) → executing
3. tool_execution_update (hybrid_search) → completed
4. tool_execution_update (metadata_search) → executing
5. tool_execution_update (metadata_search) → completed
6. tool_execution_update (vector_search) → executing

前端顯示 (即時更新):
┌────────────────────────────────────────────────────────────────────────────────┐
│ ✅ 🔄 混合搜尋                                                    #1  [已完成]     │
│    兩階段搜尋（元數據過濾 + 向量搜尋）                                              │
│    ✓ 15 個結果 (1200ms)                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ ✅ ⏱ 元數據搜尋                                                   #2  [已完成]     │
│    基於元數據過濾                                                                │
│    ✓ 3 個結果 (450ms)                                                          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 🔵 🔍 向量搜尋                                                    #3  [執行中...]  │
│    語義向量搜尋                                                                  │
│    (執行中...)                                                                  │
└────────────────────────────────────────────────────────────────────────────────┘
""")

    print("\n" + "=" * 100)
    print("Demo Complete!")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(demo_dynamic_planning_with_execution())
