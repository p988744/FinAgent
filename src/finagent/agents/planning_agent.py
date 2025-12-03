"""Planning Agent - Decomposes queries and creates research plans."""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.agents.state import AgentState
from finagent.config import settings
from finagent.models.plan import PlanTask, QueryAnalysis, ResearchPlan
from finagent.utils.keyword_extraction import (
    extract_critical_keywords,
    extract_must_have_keywords,
    identify_entity_type,
)

logger = logging.getLogger(__name__)


class PlanningAgent:
    """
    Planning Agent decomposes complex legal queries into research tasks.

    Responsibilities:
    - Analyze query intent (penalty search, precedent analysis, etc.)
    - Identify relevant jurisdictions (金管會, 中央銀行, etc.)
    - Decompose into sequential research tasks
    - Determine required data sources
    """

    def __init__(self, model: str | None = None, ui_callback=None):
        """Initialize planning agent with LLM.

        Args:
            model: Optional model name override
            ui_callback: Optional UICallback for progress updates
        """
        effective_model = model or settings.llm_model
        base_url = settings.effective_llm_base_url
        self.ui_callback = ui_callback

        if base_url:
            # Custom endpoint
            self.llm = ChatOpenAI(
                model=effective_model,
                api_key=settings.effective_llm_api_key,
                base_url=base_url,
                temperature=settings.llm_temperature,
            )
        else:
            # OpenAI default
            self.llm = ChatOpenAI(
                model=effective_model,
                api_key=settings.effective_llm_api_key,
                temperature=settings.llm_temperature,
            )

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", self._get_system_prompt()), ("user", "{query}")]
        )

        self.chain = self.prompt | self.llm

    def _get_system_prompt(self) -> str:
        """Get system prompt for planning agent."""
        return """你是台灣法律研究系統的規劃代理（Planning Agent）。

你的任務是分析使用者的法律查詢，並制定結構化的研究計劃。

## 分析重點

1. **查詢類型識別**
   - 裁罰查詢（罰鍰、裁罰書）
   - 判例查詢（判決書、案號）
   - 法規查詢（銀行法、金融法規）
   - 趨勢分析（多年度、跨機關）

2. **主管機關識別**
   - 金管會（銀行局、證期局、保險局）
   - 中央銀行
   - 公平會
   - 法院（最高法院、高等法院）

3. **關鍵實體識別**
   - 金融機構名稱（例：玉山銀行、國泰世華）
   - 違規類型（例：洗錢防制、內線交易）
   - 時間範圍（例：2020年、民國109年）

4. **研究任務分解**
   - 任務1：檢索相關裁罰文件
   - 任務2：提取關鍵事實與數據
   - 任務3：比對歷史案例
   - 任務4：綜合分析與引用

## 輸出格式

以JSON格式輸出研究計劃：

```json
{{
  "query_type": "裁罰查詢",
  "jurisdiction": ["金管會-銀行局"],
  "entities": {{
    "institution": "玉山銀行",
    "violation_type": "洗錢防制",
    "time_range": "2020"
  }},
  "research_tasks": [
    "檢索玉山銀行2020年洗錢防制相關裁罰文件",
    "提取裁罰金額、違規事實、法律依據",
    "尋找類似案例進行比較分析"
  ],
  "expected_sources": ["裁罰書", "金管會公告"],
  "complexity": "medium"
}}
```

請務必以繁體中文回應，並確保計劃具體可執行。"""

    async def plan(self, state: AgentState) -> AgentState:
        """
        Create research plan from query with detailed analysis.

        Args:
            state: Current agent state with query

        Returns:
            Updated state with plan, analysis, and research tasks
        """
        query = state["query"]
        logger.info(f"Planning research for query: {query.text[:100]}")

        try:
            # Step 1: Analyze query
            # This is sync, but fast enough
            analysis = self._analyze_query(query.text)

            # Step 2: Generate research tasks
            tasks = self._generate_tasks(analysis)

            # Step 3: Create research plan
            plan = ResearchPlan(
                analysis=analysis,
                tasks=tasks,
                max_results=self._determine_max_results(analysis),
                use_hard_search=self._should_use_hard_search(analysis),
                estimated_total_time=sum(t.estimated_time for t in tasks if t.estimated_time),
            )

            # Step 4: Display plan to user
            self._display_plan(plan)

            # Emit plan created callback
            if self.ui_callback:
                try:
                    # Convert ResearchPlan to dict for callback
                    await self.ui_callback.on_plan_created(plan)
                except Exception:
                    pass

            # Step 5: Update state
            state["plan"] = plan.dict()
            state["research_tasks"] = [t.task for t in tasks]
            state["plan_analysis"] = analysis.dict()

            # Convert tasks to todo items and store in state (Phase 5)
            from finagent.models.todo_item import TodoItem
            todos = []
            for t in tasks:
                # Determine category based on task content
                if "搜" in t.task or "檢索" in t.task or "深度搜索" in t.task:
                    category = "retrieval"
                elif "驗證" in t.task:
                    category = "validation"
                elif "生成" in t.task or "答案" in t.task:
                    category = "synthesis"
                else:
                    category = "analysis"

                todo = TodoItem(
                    id=f"task_{t.id}",
                    content=t.task,
                    active_form=f"正在執行 {t.task}",
                    status="pending",
                    category=category,
                )
                todos.append(todo)

            # Store todos in state for cross-agent access
            state["todos"] = todos

            # Emit todo list created callback
            if self.ui_callback:
                try:
                    await self.ui_callback.on_todo_list_created(todos)
                except Exception as e:
                    logger.warning(f"Failed to emit todo list callback: {e}")

            # Add detailed analysis to processing steps (user-visible)
            analysis_header = (
                f"📋 查詢分析 | 關鍵字: {', '.join(analysis.keywords[:3])} | "
                f"實體: {analysis.entity_type} | 複雜度: {analysis.complexity}"
            )
            if analysis.jurisdiction:
                analysis_header += f" | 管轄: {analysis.jurisdiction}"
            if analysis.time_period:
                analysis_header += f" | 時間: {analysis.time_period}"

            state["processing_steps"].append(analysis_header)

            # Add task list to processing steps
            state["processing_steps"].append(
                f"📝 研究任務（{len(tasks)}項，預估{plan.estimated_total_time}秒）："
            )
            for task in tasks:
                symbol = "⏱" if task.search_method == "hard_search" else "🔍"
                state["processing_steps"].append(f"  {symbol} {task.task} (~{task.estimated_time}s)")

            if plan.use_hard_search:
                state["processing_steps"].append("⚠️  將使用深度搜索（grep）以確保完整覆蓋")

            logger.info(f"Created plan with {len(tasks)} tasks, complexity: {analysis.complexity}")

        except Exception as e:
            logger.error(f"Planning failed: {e}", exc_info=True)
            state["errors"].append(f"規劃失敗：{str(e)}")

            # Fallback to simple plan with complete structure
            fallback_analysis = {
                "keywords": query.query.split()[:5],
                "must_have_keywords": [],
                "entity_type": "unknown",
                "jurisdiction": None,
                "time_period": None,
                "query_type": "general_search",
                "complexity": "simple"
            }
            fallback_tasks = [
                {"id": 1, "task": "檢索相關文件", "status": "pending", "search_method": "vector_search", "estimated_time": 10},
                {"id": 2, "task": "驗證引用", "status": "pending", "search_method": "vector_search", "estimated_time": 5},
                {"id": 3, "task": "生成答案", "status": "pending", "search_method": "vector_search", "estimated_time": 5}
            ]
            state["plan"] = {
                "analysis": fallback_analysis,
                "tasks": fallback_tasks,
                "max_results": query.max_results or 5,
                "use_hard_search": False,
                "estimated_total_time": 20
            }

        return state

    def _analyze_query(self, query_text: str) -> QueryAnalysis:
        """
        Analyze query and extract key information.

        Args:
            query_text: Query text in Chinese

        Returns:
            QueryAnalysis object with extracted information
        """
        # Try semantic query expansion (if concept_synonyms table exists)
        try:
            from finagent.document_processing.semantic_mapper import expand_query_with_concepts

            query_expansion = expand_query_with_concepts(query_text)
        except Exception as e:
            # Fallback if concept expansion fails (e.g., missing table)
            logger.debug(f"Query expansion failed: {e}")
            query_expansion = {"expanded_terms": []}

        # Extract keywords (combine original + expanded from concepts)
        keywords = extract_critical_keywords(query_text)
        must_have = extract_must_have_keywords(query_text)

        # Add expanded terms from semantic concepts
        if query_expansion["expanded_terms"]:
            # Use expanded terms as additional keywords for better recall
            keywords.extend(query_expansion["expanded_terms"][:10])  # Limit to top 10
            # Deduplicate while preserving order
            seen = set()
            keywords = [k for k in keywords if not (k in seen or seen.add(k))]

        # Identify entity type
        entity_type = identify_entity_type(query_text)

        # Identify jurisdiction
        jurisdiction = None
        if "金管會" in query_text or "金融監督管理委員會" in query_text:
            jurisdiction = "金管會"
            if "銀行局" in query_text:
                jurisdiction = "金管會-銀行局"
            elif "證期局" in query_text or "證券期貨局" in query_text:
                jurisdiction = "金管會-證券期貨局"
            elif "保險局" in query_text:
                jurisdiction = "金管會-保險局"
        elif "中央銀行" in query_text:
            jurisdiction = "中央銀行"
        elif "公平會" in query_text or "公平交易委員會" in query_text:
            jurisdiction = "公平會"

        # Identify time period (basic extraction)
        time_period = None
        import re

        year_match = re.search(r"(\d{4})年|民國(\d{2,3})年", query_text)
        if year_match:
            time_period = year_match.group(0)

        # Identify query type
        query_type = "enforcement_search"
        if "判決" in query_text or "案號" in query_text:
            query_type = "court_judgment"
        elif "解釋" in query_text or "規定" in query_text or "法令" in query_text:
            query_type = "legal_interpretation"
        elif "趨勢" in query_text or "統計" in query_text:
            query_type = "trend_analysis"

        # Determine complexity
        complexity = "medium"
        if len(must_have) > 2 or entity_type not in ["unknown", "bank"]:
            complexity = "complex"
        elif len(keywords) <= 2 and not must_have:
            complexity = "simple"

        return QueryAnalysis(
            keywords=keywords,
            must_have_keywords=must_have,
            entity_type=entity_type,
            jurisdiction=jurisdiction,
            time_period=time_period,
            query_type=query_type,
            complexity=complexity,
        )

    def _generate_tasks(self, analysis: QueryAnalysis) -> list[PlanTask]:
        """
        Generate research tasks based on analysis.

        Args:
            analysis: Query analysis results

        Returns:
            List of research tasks
        """
        tasks = []
        task_id = 1

        # Task 1: Vector search (always)
        keywords_str = ", ".join(analysis.keywords[:3])  # First 3 keywords
        tasks.append(
            PlanTask(
                id=task_id,
                task=f"向量搜索：{keywords_str}",
                status="pending",
                search_method="vector_search",
                estimated_time=10,
            )
        )
        task_id += 1

        # Task 2: Hard search (if complex and has must-have keywords)
        if analysis.complexity == "complex" and analysis.must_have_keywords:
            must_have_str = ", ".join(analysis.must_have_keywords)
            tasks.append(
                PlanTask(
                    id=task_id,
                    task=f"深度搜索：grep 關鍵字「{must_have_str}」",
                    status="pending",
                    search_method="hard_search",
                    estimated_time=30,
                )
            )
            task_id += 1

        # Task 3: Validation (always)
        tasks.append(
            PlanTask(
                id=task_id,
                task="驗證引用完整性和關鍵字匹配",
                status="pending",
                search_method="vector_search",  # N/A
                estimated_time=5,
            )
        )
        task_id += 1

        # Task 4: Answer synthesis (always)
        tasks.append(
            PlanTask(
                id=task_id,
                task="生成答案並格式化引用",
                status="pending",
                search_method="vector_search",  # N/A
                estimated_time=15,
            )
        )

        return tasks

    def _determine_max_results(self, analysis: QueryAnalysis) -> int:
        """
        Determine maximum results based on query complexity.

        Args:
            analysis: Query analysis

        Returns:
            Maximum number of results to retrieve
        """
        if analysis.complexity == "complex":
            return 10
        elif analysis.complexity == "simple":
            return 5
        else:
            return 7

    def _should_use_hard_search(self, analysis: QueryAnalysis) -> bool:
        """
        Decide if hard search should be used.

        Args:
            analysis: Query analysis

        Returns:
            True if hard search should be used
        """
        # Use hard search for complex queries with must-have keywords
        return analysis.complexity == "complex" and len(analysis.must_have_keywords) > 0

    def _display_plan(self, plan: ResearchPlan):
        """
        Display research plan to user via logging.

        Args:
            plan: Research plan to display
        """
        logger.info("=" * 80)
        logger.info("📋 查詢分析結果")
        logger.info("=" * 80)
        logger.info(f"關鍵字: {', '.join(plan.analysis.keywords)}")
        if plan.analysis.must_have_keywords:
            logger.info(f"必要關鍵字: {', '.join(plan.analysis.must_have_keywords)}")
        logger.info(f"實體類型: {plan.analysis.entity_type}")
        logger.info(f"管轄機關: {plan.analysis.jurisdiction or '未指定'}")
        if plan.analysis.time_period:
            logger.info(f"時間範圍: {plan.analysis.time_period}")
        logger.info(f"查詢類型: {plan.analysis.query_type}")
        logger.info(f"複雜度: {plan.analysis.complexity}")
        logger.info("")
        logger.info("📝 研究任務清單")
        logger.info("-" * 80)
        for task in plan.tasks:
            # Select symbol based on search method
            if task.search_method == "hard_search":
                symbol = "⏱"  # Hard search takes time
            elif task.search_method == "hybrid":
                symbol = "🔄"  # Hybrid
            else:
                symbol = "🔍"  # Vector search

            logger.info(f"  [ ] {task.id}. {symbol} {task.task} (~{task.estimated_time}s)")
        logger.info("")
        logger.info(f"預估總時間: {plan.estimated_total_time}秒")
        logger.info(f"使用深度搜索: {'是' if plan.use_hard_search else '否'}")
        logger.info("=" * 80)
