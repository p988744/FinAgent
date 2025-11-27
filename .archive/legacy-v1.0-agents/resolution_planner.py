"""Resolution planner for creating query execution plans and todo lists."""

import logging
from typing import Any

from finagent.models.queries import Query
from finagent.models.resolution_plan import ResolutionPlan
from finagent.models.todo_item import TodoItem

logger = logging.getLogger(__name__)


class ResolutionPlanner:
    """
    Creates execution plans and todo lists for queries.

    Analyzes query complexity and determines the optimal execution strategy.
    """

    def __init__(self):
        """Initialize resolution planner."""
        pass

    def create_plan(
        self, query: Query, analysis: dict[str, Any]
    ) -> ResolutionPlan:
        """
        Create an execution plan based on query analysis.

        Args:
            query: User query
            analysis: Query analysis results

        Returns:
            Resolution plan with strategy and tools
        """
        complexity = analysis.get("complexity", "moderate")
        intent = analysis.get("intent", "")
        entities_count = len(analysis.get("entities", []))

        logger.info(
            f"Creating plan for query: complexity={complexity}, "
            f"intent={intent}, entities={entities_count}"
        )

        # Decision logic for plan selection
        if complexity == "simple" and entities_count <= 2:
            plan = ResolutionPlan.create_simple_plan(
                reasoning=f"Simple query with clear intent: {intent}. "
                "Single vector search sufficient."
            )
        elif complexity == "complex" or entities_count > 3:
            plan = ResolutionPlan.create_deep_search_plan(
                reasoning=f"Complex query requiring multi-entity analysis: {intent}. "
                f"Deep search needed for {entities_count} entities."
            )
        else:
            plan = ResolutionPlan.create_complex_plan(
                reasoning=f"Moderate complexity query: {intent}. "
                "Parallel retrieval with concept and vector search."
            )

        logger.info(
            f"Created {plan.strategy} plan with {len(plan.tools)} tools, "
            f"estimated {plan.estimated_time_seconds}s"
        )

        return plan

    def create_todo_list(
        self, plan: ResolutionPlan, analysis: dict[str, Any]
    ) -> list[TodoItem]:
        """
        Create todo list from execution plan.

        Args:
            plan: Resolution plan
            analysis: Query analysis results

        Returns:
            List of todo items in execution order
        """
        todos = []

        # Always start with analysis (if not already done)
        if not analysis.get("completed", False):
            todos.append(
                TodoItem(
                    id="analysis",
                    content="分析查詢意圖與實體",
                    active_form="正在分析查詢意圖與實體",
                    category="analysis",
                    can_parallel=False,
                    dependencies=[],
                    substeps=["Extract entities", "Identify intent", "Assess complexity"],
                )
            )

        # Add retrieval tasks based on strategy
        if plan.strategy == "simple":
            todos.append(
                TodoItem(
                    id="retrieval_vector",
                    content="執行向量相似度檢索",
                    active_form="正在執行向量相似度檢索",
                    category="retrieval",
                    can_parallel=False,
                    dependencies=["analysis"] if "analysis" in [t.id for t in todos] else [],
                    substeps=["vector"],
                )
            )

        elif plan.strategy == "complex":
            # Parallel concept + vector retrieval
            todos.extend(
                [
                    TodoItem(
                        id="retrieval_concept",
                        content="執行概念語意檢索",
                        active_form="正在執行概念語意檢索",
                        category="retrieval",
                        can_parallel=True,  # Can run in parallel
                        dependencies=["analysis"] if "analysis" in [t.id for t in todos] else [],
                        substeps=["concept"],
                    ),
                    TodoItem(
                        id="retrieval_vector",
                        content="執行向量相似度檢索",
                        active_form="正在執行向量相似度檢索",
                        category="retrieval",
                        can_parallel=True,  # Can run in parallel with concept
                        dependencies=["analysis"] if "analysis" in [t.id for t in todos] else [],
                        substeps=["vector"],
                    ),
                ]
            )

        elif plan.strategy == "deep_search":
            # Parallel retrieval + deep search
            todos.extend(
                [
                    TodoItem(
                        id="retrieval_parallel",
                        content="執行並行檢索（概念+向量）",
                        active_form="正在執行並行檢索",
                        category="retrieval",
                        can_parallel=False,  # Internally parallel
                        dependencies=["analysis"] if "analysis" in [t.id for t in todos] else [],
                        substeps=["parallel"],
                    ),
                    TodoItem(
                        id="deep_search",
                        content="閱讀完整文件進行深度分析",
                        active_form="正在閱讀完整文件",
                        category="retrieval",
                        can_parallel=False,
                        dependencies=["retrieval_parallel"],
                        substeps=["Read full documents", "Extract detailed info"],
                    ),
                ]
            )

        # Add validation if needed
        if "citation_validator" in plan.tools:
            retrieval_deps = [
                t.id for t in todos if t.category == "retrieval"
            ]
            todos.append(
                TodoItem(
                    id="validation",
                    content="驗證引用來源與覆蓋度",
                    active_form="正在驗證引用來源",
                    category="validation",
                    can_parallel=False,
                    dependencies=retrieval_deps,
                    substeps=["Check citation integrity", "Verify coverage"],
                )
            )

        # Always end with synthesis
        synthesis_deps = [t.id for t in todos if t.category in ["retrieval", "validation"]]
        todos.append(
            TodoItem(
                id="synthesis",
                content="合成最終答案",
                active_form="正在合成最終答案",
                category="synthesis",
                can_parallel=False,
                dependencies=synthesis_deps,
                substeps=[
                    "Prepare context",
                    "Generate answer",
                    "Format citations",
                ],
            )
        )

        logger.info(
            f"Created todo list with {len(todos)} tasks: "
            f"{[t.id for t in todos]}"
        )

        return todos

    def should_use_deep_search(
        self, query: Query, analysis: dict[str, Any], initial_chunks_count: int
    ) -> bool:
        """
        Decide if deep search (full document reading) is needed.

        Args:
            query: User query
            analysis: Query analysis results
            initial_chunks_count: Number of chunks from initial retrieval

        Returns:
            True if deep search is recommended
        """
        # Deep search criteria
        complexity = analysis.get("complexity", "moderate")
        entities_count = len(analysis.get("entities", []))

        # Use deep search if:
        # 1. Complex query with multiple entities
        # 2. Low initial chunk count (suggests need for more context)
        # 3. Query explicitly asks for detailed analysis

        if complexity == "complex" and entities_count > 3:
            logger.info("Deep search recommended: complex query with many entities")
            return True

        if initial_chunks_count < 5:
            logger.info(
                f"Deep search recommended: low chunk count ({initial_chunks_count})"
            )
            return True

        # Check for keywords suggesting need for detailed analysis
        detail_keywords = ["詳細", "完整", "所有", "全部", "深入", "分析"]
        if any(kw in query.text for kw in detail_keywords):
            logger.info("Deep search recommended: query requests detailed analysis")
            return True

        logger.info("Deep search not needed for this query")
        return False

    def create_adaptive_plan(
        self, query: Query, analysis: dict[str, Any], initial_results: dict[str, Any]
    ) -> ResolutionPlan:
        """
        Create adaptive plan based on initial retrieval results.

        Args:
            query: User query
            analysis: Query analysis results
            initial_results: Results from initial retrieval

        Returns:
            Adapted resolution plan
        """
        initial_chunks = initial_results.get("chunks", [])
        chunk_count = len(initial_chunks)

        # Upgrade plan if initial results are insufficient
        if chunk_count < 5:
            logger.info(
                f"Upgrading to deep search: only {chunk_count} chunks found"
            )
            return ResolutionPlan.create_deep_search_plan(
                reasoning=f"Initial retrieval found only {chunk_count} chunks. "
                "Deep search needed for comprehensive answer."
            )

        # Otherwise use original plan complexity
        complexity = analysis.get("complexity", "moderate")

        if complexity == "simple":
            return ResolutionPlan.create_simple_plan()
        elif complexity == "complex":
            return ResolutionPlan.create_complex_plan()
        else:
            return ResolutionPlan.create_deep_search_plan()
