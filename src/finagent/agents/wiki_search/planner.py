"""Search planning agent for WikiSearch workflow.

Analyzes user queries and creates optimal search plans with
multiple retrieval strategies.
"""

import logging
from typing import Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from finagent.agents.wiki_search.models import (
    QueryInsight,
    QueryType,
    SearchPlan,
    SearchStrategy,
    SearchTask,
    WikiSearchState,
)
from finagent.config import settings

logger = logging.getLogger(__name__)


class SearchPlanner:
    """Analyzes queries and creates search plans for WikiSearch workflow."""

    ANALYSIS_PROMPT = """你是台灣金融法律查詢分析專家。分析以下查詢並提供結構化的分析結果。

**用戶查詢**：{query}

請以 JSON 格式回答：

{{
    "query_type": "查詢類型（factual/analytical/comparative/temporal/exploratory）",
    "key_entities": ["關鍵實體（銀行名、機構名、人名）"],
    "key_topics": ["關鍵主題（洗錢防制、內部控制、裁罰等）"],
    "search_strategy": "建議搜尋策略（semantic/keyword/hybrid/category）",
    "date_range": "日期範圍（如 2020-2023，無則為 null）",
    "complexity": "查詢複雜度（simple/medium/complex）",
    "reasoning": "分析說明（1-2句）"
}}

**查詢類型說明**：
- factual: 尋找特定事實（如：玉山銀行2020年裁罰金額）
- analytical: 需要分析（如：洗錢防制違規的常見原因）
- comparative: 比較查詢（如：各銀行裁罰金額比較）
- temporal: 時間相關（如：2020年裁罰案件）
- exploratory: 探索瀏覽（如：銀行違規類型）

**搜尋策略說明**：
- semantic: 概念性查詢，使用向量搜尋
- keyword: 精確關鍵字，使用關鍵字搜尋
- hybrid: 混合策略（推薦大多數情況）
- category: 按分類瀏覽"""

    PLANNING_PROMPT = """你是搜尋規劃專家。根據查詢分析結果，創建搜尋任務計畫。

**用戶查詢**：{query}

**查詢分析**：
- 查詢類型：{query_type}
- 關鍵實體：{key_entities}
- 關鍵主題：{key_topics}
- 建議策略：{search_strategy}
- 複雜度：{complexity}

請創建搜尋任務計畫，以 JSON 格式回答：

{{
    "tasks": [
        {{
            "id": 1,
            "description": "任務描述",
            "tool": "工具名稱（retriever/hard_search/hybrid_search）",
            "query": "搜尋查詢",
            "filters": {{}},
            "priority": 1
        }}
    ],
    "strategy": "整體策略（semantic/keyword/hybrid/category）",
    "max_results_per_task": 5,
    "merge_strategy": "合併策略（relevance/chronological/source）"
}}

**工具選擇指南**：
- retriever: 概念性搜尋，找相似內容（推薦用於 analytical/exploratory）
- hard_search: 精確關鍵字，必須包含所有關鍵字（推薦用於 factual）
- hybrid_search: 混合搜尋（推薦用於 comparative/temporal）

**任務設計原則**：
1. 簡單查詢：1-2 個任務
2. 中等複雜度：2-3 個任務
3. 複雜查詢：3-5 個任務
4. 優先使用 hybrid_search 除非有特定需求
5. 每個任務應有明確目標"""

    def __init__(self):
        """Initialize the WikiSearch planner."""
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.effective_llm_api_key,
            base_url=settings.effective_llm_base_url,
            temperature=0,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
    )
    async def analyze_query(self, state: WikiSearchState) -> dict:
        """Analyze the user query to understand intent and entities.

        Args:
            state: Current workflow state

        Returns:
            State update with query_insight
        """
        query = state["input"]
        logger.info(f"Analyzing query: {query[:50]}...")

        try:
            # Create analysis chain
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是查詢分析專家。只輸出 JSON，不要添加其他文字。"),
                ("user", self.ANALYSIS_PROMPT),
            ])

            chain = prompt | self.llm | JsonOutputParser()

            # Run analysis
            result = await chain.ainvoke({"query": query})

            # Map string values to enums
            query_type_str = result.get("query_type", "exploratory")
            search_strategy_str = result.get("search_strategy", "hybrid")

            query_type = QueryType(query_type_str) if query_type_str in [e.value for e in QueryType] else QueryType.EXPLORATORY
            search_strategy = SearchStrategy(search_strategy_str) if search_strategy_str in [e.value for e in SearchStrategy] else SearchStrategy.HYBRID

            # Create QueryInsight
            insight = QueryInsight(
                query_type=query_type,
                key_entities=result.get("key_entities", []),
                key_topics=result.get("key_topics", []),
                search_strategy=search_strategy,
                date_range=result.get("date_range"),
                complexity=result.get("complexity", "medium"),
                reasoning=result.get("reasoning", ""),
            )

            logger.info(f"Query analysis complete: type={query_type.value}, strategy={search_strategy.value}")

            return {
                "query_insight": insight.model_dump(),
                "current_stage": "analyzing",
                "progress": 20,
            }

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            # Return default analysis
            return {
                "query_insight": QueryInsight(
                    query_type=QueryType.EXPLORATORY,
                    key_entities=[],
                    key_topics=[],
                    search_strategy=SearchStrategy.HYBRID,
                    complexity="medium",
                    reasoning="自動分析失敗，使用預設策略",
                ).model_dump(),
                "current_stage": "analyzing",
                "progress": 20,
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
    )
    async def create_search_plan(self, state: WikiSearchState) -> dict:
        """Create a search plan based on query analysis.

        Args:
            state: Current workflow state with query_insight

        Returns:
            State update with search_plan
        """
        query = state["input"]
        insight = state.get("query_insight", {})

        logger.info(f"Creating search plan for: {query[:50]}...")

        try:
            # Create planning chain
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是搜尋規劃專家。只輸出 JSON，不要添加其他文字。"),
                ("user", self.PLANNING_PROMPT),
            ])

            chain = prompt | self.llm | JsonOutputParser()

            # Run planning
            result = await chain.ainvoke({
                "query": query,
                "query_type": insight.get("query_type", "exploratory"),
                "key_entities": ", ".join(insight.get("key_entities", [])),
                "key_topics": ", ".join(insight.get("key_topics", [])),
                "search_strategy": insight.get("search_strategy", "hybrid"),
                "complexity": insight.get("complexity", "medium"),
            })

            # Parse tasks
            tasks = []
            for task_data in result.get("tasks", []):
                task = SearchTask(
                    id=task_data.get("id", len(tasks) + 1),
                    description=task_data.get("description", "搜尋相關文件"),
                    tool=task_data.get("tool", "hybrid_search"),
                    query=task_data.get("query", query),
                    filters=task_data.get("filters", {}),
                    priority=task_data.get("priority", 1),
                )
                tasks.append(task)

            # If no tasks, create default
            if not tasks:
                tasks = [
                    SearchTask(
                        id=1,
                        description="搜尋相關文件",
                        tool="hybrid_search",
                        query=query,
                        filters={},
                        priority=1,
                    )
                ]

            # Map strategy string to enum
            strategy_str = result.get("strategy", "hybrid")
            strategy = SearchStrategy(strategy_str) if strategy_str in [e.value for e in SearchStrategy] else SearchStrategy.HYBRID

            # Create SearchPlan
            plan = SearchPlan(
                tasks=tasks,
                strategy=strategy,
                max_results_per_task=result.get("max_results_per_task", 5),
                merge_strategy=result.get("merge_strategy", "relevance"),
            )

            logger.info(f"Search plan created: {len(tasks)} tasks, strategy={strategy.value}")

            return {
                "search_plan": plan.model_dump(),
                "current_stage": "planning",
                "progress": 40,
            }

        except Exception as e:
            logger.error(f"Search planning failed: {e}")
            # Return default plan
            default_plan = SearchPlan(
                tasks=[
                    SearchTask(
                        id=1,
                        description="搜尋相關文件",
                        tool="hybrid_search",
                        query=query,
                        filters={},
                        priority=1,
                    )
                ],
                strategy=SearchStrategy.HYBRID,
                max_results_per_task=5,
                merge_strategy="relevance",
            )

            return {
                "search_plan": default_plan.model_dump(),
                "current_stage": "planning",
                "progress": 40,
            }
