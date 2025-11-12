"""Planning Agent - Decomposes queries and creates research plans."""

import logging
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.config import settings
from finagent.agents.state import AgentState

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

    def __init__(self, model: Optional[str] = None):
        """Initialize planning agent with LLM."""
        effective_model = model or settings.llm_model
        base_url = settings.effective_llm_base_url

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

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "{query}")
        ])

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

    def plan(self, state: AgentState) -> AgentState:
        """
        Create research plan from query.

        Args:
            state: Current agent state with query

        Returns:
            Updated state with plan and research tasks
        """
        query = state["query"]
        logger.info(f"Planning research for query: {query.text[:100]}")

        try:
            # Invoke LLM to create plan
            response = self.chain.invoke({"query": query.text})

            # Parse response (for now, use raw content)
            plan_text = response.content

            # Extract structured plan (simplified for MVP)
            plan = {
                "raw_plan": plan_text,
                "query_text": query.text,
                "max_results": query.max_results or 5,
            }

            # Generate simple research tasks
            research_tasks = [
                f"檢索與「{query.text}」相關的法律文件",
                "提取關鍵事實與引用來源",
                "驗證引用完整性",
                "綜合分析並生成答案"
            ]

            # Update state
            state["plan"] = plan
            state["research_tasks"] = research_tasks
            state["processing_steps"].append("規劃代理：已制定研究計劃")

            logger.info(f"Created plan with {len(research_tasks)} tasks")

        except Exception as e:
            logger.error(f"Planning failed: {e}", exc_info=True)
            state["errors"].append(f"規劃失敗：{str(e)}")

        return state
