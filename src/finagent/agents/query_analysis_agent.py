"""Query Analysis Agent - Analyzes user queries and requests clarification when needed.

This agent runs BEFORE the planning agent to understand user intent and identify
ambiguous queries that need clarification.
"""

from typing import Optional

from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

from finagent.agents.state import AgentState


class ClarificationRequest(BaseModel):
    """Request for user clarification."""

    needs_clarification: bool = Field(
        description="Whether the query needs clarification from user"
    )
    reason: str = Field(description="Why clarification is needed (if applicable)")
    questions: list[str] = Field(
        default_factory=list, description="Specific questions to ask the user"
    )
    understood_intent: str = Field(
        description="What we understand so far about the user's intent"
    )
    confidence: str = Field(
        description="Confidence level: high/medium/low in understanding the query"
    )


class QueryAnalysisAgent:
    """Analyzes user queries and requests clarification when needed.

    This agent:
    1. Analyzes the user's query to understand intent
    2. Identifies ambiguities or missing information
    3. Requests clarification via human-in-the-loop if needed
    4. Enriches the query with understood context
    """

    def __init__(self, ui_callback=None):
        """Initialize query analysis agent.

        Args:
            ui_callback: Optional UICallback for progress updates
        """
        from finagent.config import settings
        from langchain_openai import ChatOpenAI

        self.ui_callback = ui_callback

        # Initialize LLM using settings (same pattern as other agents)
        base_url = settings.effective_llm_base_url
        if base_url:
            # Custom endpoint (e.g., Ollama)
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                base_url=base_url,
                temperature=0.0,  # Deterministic for analysis
            )
        else:
            # OpenAI default
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                temperature=0.0,  # Deterministic for analysis
            )

        # System prompt for query analysis
        self.system_prompt = """你是一個金融法律研究系統的查詢分析專家。

你的任務是分析使用者的查詢意圖，判斷是否需要進一步澄清。

# 需要澄清的情況

1. **模糊的時間範圍**
   - 例：「最近的裁罰」（最近多久？）
   - 例：「去年」（民國幾年？西元幾年？）

2. **模糊的實體**
   - 例：「銀行」（哪家銀行？所有銀行？）
   - 例：「保險公司」（特定公司？產險？壽險？）

3. **多重可能的意圖**
   - 例：「玉山銀行洗錢」可能是：
     a) 查詢玉山銀行的洗錢裁罰案件
     b) 查詢洗錢防制相關法規
     c) 查詢洗錢防制的一般資訊

4. **缺少關鍵資訊**
   - 例：「裁罰案件有哪些」（什麼類型的裁罰？）
   - 例：「法規遵循」（哪方面的法規？）

5. **過於寬泛的查詢**
   - 例：「金融違規」（太廣泛，難以聚焦）
   - 例：「金管會裁罰」（所有裁罰？特定年份？）

# 不需要澄清的情況

1. **具體明確的查詢**
   - 例：「玉山銀行2020年洗錢防制裁罰」
   - 例：「內線交易案件2019-2021」

2. **常見的查詢模式**
   - 例：「洗錢防制案件有哪些」（清楚的探索性查詢）
   - 例：「金管會對保險公司的裁罰」（明確的查詢範圍）

# 分析步驟

1. 識別查詢中的實體（機構、違規類型、時間等）
2. 判斷意圖是否清晰（探索、統計、案例、法規）
3. 評估是否有足夠資訊執行查詢
4. 如需澄清，提出1-3個具體問題

# 輸出格式

返回 JSON 格式：
```json
{
  "needs_clarification": true/false,
  "reason": "為什麼需要澄清",
  "questions": ["問題1", "問題2", "問題3"],
  "understood_intent": "目前理解的使用者意圖",
  "confidence": "high/medium/low"
}
```

# 原則

- 只有在**真正必要**時才要求澄清
- 不要過度謹慎，影響使用者體驗
- 對常見查詢模式有信心，直接執行
- 澄清問題要具體、簡潔
- 一次最多問3個問題
"""

    def analyze_query(self, state: AgentState) -> AgentState:
        """Analyze query and determine if clarification is needed.

        Args:
            state: Current agent state with user query

        Returns:
            Updated state with clarification request (if needed)
        """
        query = state["query"]
        query_text = query.text

        # Emit analysis start callback
        if self.ui_callback:
            import asyncio
            try:
                asyncio.create_task(self.ui_callback.on_analysis_start(query))
            except RuntimeError:
                # If no event loop is running, skip callback
                pass

        # Create structured output chain
        analysis_chain = self.llm.with_structured_output(ClarificationRequest)

        # Analyze query
        user_message = f"""請分析以下使用者查詢：

查詢：{query_text}

請判斷是否需要向使用者澄清，並說明理由。"""

        try:
            result = analysis_chain.invoke(
                [SystemMessage(content=self.system_prompt), {"role": "user", "content": user_message}]
            )

            # Add to processing steps
            step = f"Query Analysis: {'需要澄清' if result.needs_clarification else '理解清晰'}"
            state["processing_steps"].append(step)

            # Store clarification request
            if result.needs_clarification:
                state["clarification_request"] = {
                    "needs_clarification": True,
                    "reason": result.reason,
                    "questions": result.questions,
                    "understood_intent": result.understood_intent,
                    "confidence": result.confidence,
                }
            else:
                state["clarification_request"] = {
                    "needs_clarification": False,
                    "understood_intent": result.understood_intent,
                    "confidence": result.confidence,
                }

            # Store understood intent for later use
            state["query_intent"] = result.understood_intent

            # Emit analysis complete callback
            if self.ui_callback:
                analysis_summary = {
                    "intent": result.understood_intent,
                    "confidence": result.confidence,
                    "needs_clarification": result.needs_clarification,
                }
                import asyncio
                try:
                    asyncio.create_task(self.ui_callback.on_analysis_complete(analysis_summary))
                except RuntimeError:
                    pass

            # Emit clarification request callback if needed
            if result.needs_clarification and self.ui_callback:
                try:
                    asyncio.create_task(self.ui_callback.on_clarification_requested(result.questions))
                except RuntimeError:
                    pass

        except Exception as e:
            # If analysis fails, proceed without clarification
            state["processing_steps"].append(f"Query Analysis: 分析失敗 ({str(e)})")
            state["clarification_request"] = {
                "needs_clarification": False,
                "understood_intent": query_text,
                "confidence": "low",
            }

        return state

    def enrich_query_with_clarification(self, state: AgentState) -> AgentState:
        """Enrich query with user's clarification response.

        Args:
            state: State with original query and clarification response

        Returns:
            Updated state with enriched query
        """
        if not state.get("clarification_response"):
            return state

        original_query = state["query"].text
        clarification = state["clarification_response"]

        # Create enriched query by combining original + clarification
        enriched_query = f"{original_query}\n\n補充說明：{clarification}"

        # Update query text
        state["query"].text = enriched_query

        # Add to processing steps
        state["processing_steps"].append("Query Enrichment: 已整合使用者補充說明")

        return state


def should_request_clarification(state: AgentState) -> str:
    """Determine if we should request clarification from user.

    This is a routing function for LangGraph conditional edges.

    Args:
        state: Current agent state

    Returns:
        "clarify" if clarification needed, "proceed" otherwise
    """
    clarification_request = state.get("clarification_request", {})

    if clarification_request.get("needs_clarification", False):
        return "clarify"
    else:
        return "proceed"


def has_clarification_response(state: AgentState) -> str:
    """Check if user provided clarification response.

    This is a routing function for LangGraph conditional edges.

    Args:
        state: Current agent state

    Returns:
        "enriched" if response provided, "skip" if user skipped
    """
    clarification_response = state.get("clarification_response")

    if clarification_response and clarification_response.strip():
        return "enriched"
    else:
        # User skipped clarification, proceed with original query
        return "skip"
