"""
Demo script showing Task Tool Usage Tracking in Research Plan.

This demonstrates how tool usage information (request parameters and results)
can be displayed in the Research Plan panel for user verification.
"""

import asyncio
import json
from datetime import datetime


async def demo_task_tool_usage():
    """
    Demonstrate task tool usage tracking with expandable details.

    This simulates what the frontend would see during RAG retrieval.
    """
    print("=" * 100)
    print("Task Tool Usage Tracking - Demo")
    print("=" * 100)

    # Test query
    query = "玉山銀行洗錢防制裁罰"
    print(f"\n📝 Query: {query}\n")

    # Step 1: Research Plan Created
    print("【Step 1】研究計畫建立")
    print("-" * 100)

    plan_payload = {
        "analysis": {
            "keywords": ["玉山銀行", "洗錢防制", "裁罰"],
            "must_have_keywords": ["玉山銀行"],
            "entity_type": "bank",
            "jurisdiction": "金管會",
            "time_period": None,
            "query_type": "penalty_search",
            "complexity": "medium",
        },
        "tasks": [
            {
                "id": 1,
                "task": "搜尋玉山銀行相關裁罰文件",
                "status": "pending",
                "search_method": "vector_search",
                "estimated_time": 5,
            },
            {
                "id": 2,
                "task": "過濾洗錢防制相關案件",
                "status": "pending",
                "search_method": "hybrid",
                "estimated_time": 3,
            },
        ],
        "max_results": 10,
        "use_hard_search": False,
        "estimated_total_time": 8,
    }

    print("\n📡 WebSocket Event: plan_created")
    print(json.dumps(plan_payload, indent=2, ensure_ascii=False))

    # Step 2: Task 1 Execution with Tool Usage
    print("\n\n【Step 2】任務 1 執行 - 向量搜尋")
    print("-" * 100)

    print("\n📡 WebSocket Event: task_tool_usage (task_id: 1)")
    task1_tool_usage = {
        "task_id": 1,
        "tool_usage": {
            "tool_name": "vector_search",
            "request_params": {
                "query": "玉山銀行洗錢防制裁罰",
                "n_results": 10,
                "relevance_threshold": 0.8,
            },
            "result_count": 8,
            "execution_time_ms": 1250,
            "sample_results": [
                {
                    "source": "玉山銀行_洗錢防制裁罰_2020.txt",
                    "relevance": 0.92,
                    "snippet": "金管會於2020年9月15日以金管銀法字第10902345678號函，對玉山商業銀行股份有限公司處以新臺幣1,000萬元罰鍰...",
                },
                {
                    "source": "玉山銀行_內部控制缺失_2019.txt",
                    "relevance": 0.85,
                    "snippet": "玉山銀行於辦理防制洗錢及打擊資恐作業，未能確實遵循相關法令規定...",
                },
                {
                    "source": "玉山銀行_客戶審查缺失_2020.txt",
                    "relevance": 0.81,
                    "snippet": "該行對於客戶身分審查及持續審查作業存有缺失，未能有效辨識高風險客戶...",
                },
            ],
        },
    }
    print(json.dumps(task1_tool_usage, indent=2, ensure_ascii=False))

    await asyncio.sleep(1)

    # Step 3: Task 2 Execution with Hybrid Search
    print("\n\n【Step 3】任務 2 執行 - 混合搜尋")
    print("-" * 100)

    print("\n📡 WebSocket Event: task_tool_usage (task_id: 2)")
    task2_tool_usage = {
        "task_id": 2,
        "tool_usage": {
            "tool_name": "hybrid_search",
            "request_params": {
                "metadata_filter": {"keywords": ["洗錢防制"]},
                "vector_query": "裁罰案件",
                "n_results": 5,
            },
            "result_count": 5,
            "execution_time_ms": 850,
            "sample_results": [
                {
                    "source": "玉山銀行_洗錢防制裁罰_2020.txt",
                    "relevance": 0.95,
                    "snippet": "因違反洗錢防制法第6條、第7條及第8條規定，經金管會裁罰...",
                },
                {
                    "source": "玉山銀行_防制洗錢缺失_2019.txt",
                    "relevance": 0.88,
                    "snippet": "該行防制洗錢內部控制制度存有缺失，包括客戶盡職調查不完整...",
                },
            ],
        },
    }
    print(json.dumps(task2_tool_usage, indent=2, ensure_ascii=False))

    # Step 4: Visual Representation
    print("\n\n【Step 4】前端顯示效果 - 展開任務詳情")
    print("-" * 100)
    print(
        """
┌────────────────────────────────────────────────────────────────────────────────┐
│ 📋 研究計畫                                               2 項任務・8 秒         │
├────────────────────────────────────────────────────────────────────────────────┤
│ 📊 查詢分析                                                                      │
│                                                                                │
│ 🏷️ 關鍵字: [玉山銀行] [洗錢防制] [裁罰]                                           │
│ 🏢 管轄機關: 金管會                                                              │
│ 📝 查詢類型: penalty_search                                                     │
│ ⏱️ 複雜度: [medium]                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ 📝 研究任務                                                                      │
│                                                                                │
│ ▼ ✅ 🔍 1. 搜尋玉山銀行相關裁罰文件                              ~5s [已完成]    │
│   ┌──────────────────────────────────────────────────────────────────────┐    │
│   │ 🔧 vector_search                                        ✓ 8 個結果    │    │
│   │ ⏱️ 執行時間: 1250ms                                                    │    │
│   │                                                                        │    │
│   │ 📋 請求參數                                                             │    │
│   │ {                                                                      │    │
│   │   "query": "玉山銀行洗錢防制裁罰",                                       │    │
│   │   "n_results": 10,                                                     │    │
│   │   "relevance_threshold": 0.8                                           │    │
│   │ }                                                                      │    │
│   │                                                                        │    │
│   │ 📄 檢索結果範例 (前 3 筆)                                                │    │
│   │ ┌────────────────────────────────────────────────────────────────┐    │    │
│   │ │ 玉山銀行_洗錢防制裁罰_2020.txt                              92%  │    │    │
│   │ │ 金管會於2020年9月15日以金管銀法字第10902345678號函，對玉...   │    │    │
│   │ └────────────────────────────────────────────────────────────────┘    │    │
│   │ ┌────────────────────────────────────────────────────────────────┐    │    │
│   │ │ 玉山銀行_內部控制缺失_2019.txt                              85%  │    │    │
│   │ │ 玉山銀行於辦理防制洗錢及打擊資恐作業，未能確實遵循相關法...   │    │    │
│   │ └────────────────────────────────────────────────────────────────┘    │    │
│   │ ┌────────────────────────────────────────────────────────────────┐    │    │
│   │ │ 玉山銀行_客戶審查缺失_2020.txt                              81%  │    │    │
│   │ │ 該行對於客戶身分審查及持續審查作業存有缺失，未能有效辨識...   │    │    │
│   │ └────────────────────────────────────────────────────────────────┘    │    │
│   │                                                                        │    │
│   │ 💡 驗證提示：                                                           │    │
│   │ 您可以檢查上述請求參數和結果，確認系統是否正確理解您的查詢並       │    │
│   │ 檢索到相關文件。                                                        │    │
│   └──────────────────────────────────────────────────────────────────────┘    │
│                                                                                │
│ ▼ ✅ 🔄 2. 過濾洗錢防制相關案件                                  ~3s [已完成]    │
│   ┌──────────────────────────────────────────────────────────────────────┐    │
│   │ 🔧 hybrid_search                                        ✓ 5 個結果     │    │
│   │ ⏱️ 執行時間: 850ms                                                     │    │
│   │                                                                        │    │
│   │ 📋 請求參數                                                             │    │
│   │ {                                                                      │    │
│   │   "metadata_filter": {"keywords": ["洗錢防制"]},                       │    │
│   │   "vector_query": "裁罰案件",                                          │    │
│   │   "n_results": 5                                                       │    │
│   │ }                                                                      │    │
│   │                                                                        │    │
│   │ 📄 檢索結果範例 (前 2 筆)                                                │    │
│   │ ┌────────────────────────────────────────────────────────────────┐    │    │
│   │ │ 玉山銀行_洗錢防制裁罰_2020.txt                              95%  │    │    │
│   │ │ 因違反洗錢防制法第6條、第7條及第8條規定，經金管會裁罰...     │    │    │
│   │ └────────────────────────────────────────────────────────────────┘    │    │
│   │ ┌────────────────────────────────────────────────────────────────┐    │    │
│   │ │ 玉山銀行_防制洗錢缺失_2019.txt                              88%  │    │    │
│   │ │ 該行防制洗錢內部控制制度存有缺失，包括客戶盡職調查不完整...   │    │    │
│   │ └────────────────────────────────────────────────────────────────┘    │    │
│   │                                                                        │    │
│   │ 💡 驗證提示：                                                           │    │
│   │ 您可以檢查上述請求參數和結果，確認系統是否正確理解您的查詢並       │    │
│   │ 檢索到相關文件。                                                        │    │
│   └──────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────────┘
"""
    )

    # Example 2: Failed Tool Execution
    print("\n\n【Example 2】工具執行失敗示例")
    print("-" * 100)

    print("\n📡 WebSocket Event: task_tool_usage (failed)")
    failed_tool_usage = {
        "task_id": 1,
        "tool_usage": {
            "tool_name": "vector_search",
            "request_params": {
                "query": "不存在的銀行",
                "n_results": 10,
            },
            "error": "檢索結果為空：未找到符合條件的文件",
        },
    }
    print(json.dumps(failed_tool_usage, indent=2, ensure_ascii=False))

    print("\n前端顯示:")
    print(
        """
┌────────────────────────────────────────────────────────────────────────────────┐
│ ▼ ❌ 🔍 1. 搜尋相關文件                                          ~5s [失敗]       │
│   ┌──────────────────────────────────────────────────────────────────────┐    │
│   │ 🔧 vector_search                                        ✗ 執行失敗     │    │
│   │                                                                        │    │
│   │ 📋 請求參數                                                             │    │
│   │ {                                                                      │    │
│   │   "query": "不存在的銀行",                                              │    │
│   │   "n_results": 10                                                      │    │
│   │ }                                                                      │    │
│   │                                                                        │    │
│   │ ❌ 錯誤訊息                                                             │    │
│   │ 檢索結果為空：未找到符合條件的文件                                        │    │
│   └──────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────────┘
"""
    )

    print("\n" + "=" * 100)
    print("Demo Complete!")
    print("=" * 100)
    print("\n💡 Key Features:")
    print("  1. ✅ Click task to expand/collapse tool usage details")
    print("  2. ✅ View exact request parameters sent to retrieval tools")
    print("  3. ✅ See sample results with relevance scores")
    print("  4. ✅ Verify system correctly understood the query")
    print("  5. ✅ Check for errors or unexpected behavior")
    print("\n📖 User Benefit:")
    print("  Users can verify the system's retrieval process is working correctly")
    print("  and producing relevant results before reading the final answer.")


if __name__ == "__main__":
    asyncio.run(demo_task_tool_usage())
