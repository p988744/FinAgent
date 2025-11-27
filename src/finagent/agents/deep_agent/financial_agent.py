"""FinAgent Deep Agent - Financial Legal Research Agent.

This module implements a Deep Agent for financial legal research using the
deepagents library. It provides Claude Code-like capabilities including:
- Task planning with built-in write_todos tool
- Sub-agent delegation for specialized tasks
- Context management via checkpointer
"""

from typing import Any, Dict, List, Optional
import logging

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage, AIMessage

from finagent.agents.deep_agent.tools import (
    semantic_search,
    keyword_search,
    hybrid_search,
    FINAGENT_TOOLS,
)
from finagent.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# System prompt for the main Financial Agent
FINANCIAL_AGENT_PROMPT = """你是 FinAgent，專精於台灣金融法律研究的 AI 助手。

## 專業領域
- 金管會裁罰案例分析
- 銀行監理法規解讀
- 洗錢防制法規研究
- 金融判決書分析
- 保險、證券、期貨相關法規

## 工作原則
1. **規劃先行**：對於複雜查詢，先使用 write_todos 工具規劃研究步驟
2. **引用為本**：所有事實陳述必須附帶來源引用
3. **多次檢索**：如初次檢索不足，應改寫查詢重試
4. **正式書寫**：使用繁體中文正式法律文體
5. **委派專家**：對於特定類型的分析，委派給專業子代理

## 可用工具
- `semantic_search`: 語意搜尋，適合概念性查詢
- `keyword_search`: 關鍵字搜尋，適合精確查詢（機構名稱、案號）
- `hybrid_search`: 混合搜尋，結合語意與關鍵字
- `write_todos`: 規劃任務清單（系統內建）
- `task`: 委派任務給子代理（系統內建）

## 引用格式
- 行內引用：[引用1]、[引用1、2]
- 引用清單格式：
  [1] 來源名稱
      摘要：相關內容摘要

## 回答結構
對於研究型查詢，請依照以下結構回答：

### 執行摘要
（1-2 句總結主要發現）

### 關鍵發現
- 發現 1 [引用1]
- 發現 2 [引用2、3]

### 詳細分析
（完整分析，每項論述附帶引用）

### 信心評分
- 高信心 / 中信心 / 低信心
- 說明：（解釋信心程度的原因）

### 引用來源
[1] 來源 1...
[2] 來源 2...

## 注意事項
- 如果找不到相關文件，請誠實說明並建議替代查詢方式
- 不要編造不存在的資訊
- 對於涉及具體金額或日期的資訊，務必確認引用來源
"""

# Sub-agent definitions (using correct deepagents API format)
# Each subagent is a dictionary with: name, description, prompt, tools, model
RAG_RESEARCHER_SUBAGENT = {
    "name": "rag_researcher",
    "description": "專門執行 RAG 檢索的子代理。使用此子代理進行深度文件搜尋，適合需要多次查詢和彙整的研究任務。",
    "prompt": """你是 RAG 研究員，負責深度搜尋金融法律文件。

工作流程：
1. 分析查詢意圖，識別關鍵概念
2. 使用 semantic_search 進行語意搜尋
3. 使用 keyword_search 補充精確關鍵字搜尋
4. 如果結果不足，改寫查詢重試
5. 彙整相關文件並評估相關性
6. 返回最相關的文件摘要與引用

輸出格式：
- 列出所有找到的相關文件
- 標註每份文件的相關性
- 摘要關鍵內容
""",
    "tools": FINAGENT_TOOLS,
    "model": "gpt-4o-mini",
}

LEGAL_ANALYZER_SUBAGENT = {
    "name": "legal_analyzer",
    "description": "專門分析法律文件的子代理。使用此子代理解讀裁罰書內容、法規條文、或進行法律層面的分析。",
    "prompt": """你是法律分析專家，負責解讀金融法規與裁罰書。

分析重點：
1. 違規事實認定 - 具體違反哪些規定
2. 適用法條與罰則 - 引用的法律依據
3. 裁罰金額計算依據 - 罰款如何決定
4. 前例比較分析 - 與類似案件的比較
5. 實務建議 - 對金融機構的啟示

分析格式：
### 違規事實
（描述違規行為）

### 法律依據
- 法條：...
- 罰則：...

### 裁罰分析
- 金額：...
- 依據：...

### 實務建議
（給金融機構的建議）
""",
    "tools": FINAGENT_TOOLS,
    "model": "gpt-4o-mini",
}

PENALTY_COMPARATOR_SUBAGENT = {
    "name": "penalty_comparator",
    "description": "專門比較裁罰案例的子代理。使用此子代理進行不同案例間的比較分析，找出裁罰趨勢和規律。",
    "prompt": """你是裁罰案例比較專家，負責分析和比較不同金融機構的裁罰案例。

工作重點：
1. 搜尋相關裁罰案例
2. 整理案例基本資訊（機構、日期、金額、違規類型）
3. 比較不同案例的異同
4. 分析裁罰趨勢
5. 提供統計摘要

輸出格式：
### 案例清單
| 機構 | 日期 | 金額 | 違規類型 |
|------|------|------|---------|

### 比較分析
（案例間的異同）

### 趨勢觀察
（裁罰趨勢分析）
""",
    "tools": FINAGENT_TOOLS,
    "model": "gpt-4o-mini",
}


class FinAgentDeepAgent:
    """Wrapper class for FinAgent Deep Agent.

    This class manages the Deep Agent lifecycle and provides a consistent
    interface for the orchestrator.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        enable_subagents: bool = True,
        enable_filesystem: bool = False,
    ):
        """Initialize the FinAgent Deep Agent.

        Args:
            model: LLM model to use (default: from config)
            enable_subagents: Enable sub-agent delegation for specialized tasks
            enable_filesystem: Enable filesystem tools (disabled by default for security)
        """
        self.config_manager = ConfigManager()

        # Get model from config if not specified
        if model is None:
            model = self.config_manager.get_setting("llm_model") or "gpt-4o-mini"

        self.model = model
        self.enable_subagents = enable_subagents
        self.enable_filesystem = enable_filesystem
        self._agent = None

    def _create_agent(self):
        """Create the Deep Agent with configured settings."""
        # Define subagents if enabled
        subagents = None
        if self.enable_subagents:
            subagents = [
                RAG_RESEARCHER_SUBAGENT,
                LEGAL_ANALYZER_SUBAGENT,
                PENALTY_COMPARATOR_SUBAGENT,
            ]

        # Create the Deep Agent
        # Note: create_deep_agent automatically includes:
        # - write_todos tool for task planning
        # - task tool for subagent delegation (when subagents provided)
        # - filesystem tools (when enable_filesystem=True)
        agent = create_deep_agent(
            model=self.model,
            system_prompt=FINANCIAL_AGENT_PROMPT,
            tools=FINAGENT_TOOLS,
            subagents=subagents,
            # Disable filesystem tools for security (we use our own RAG tools)
            backend=None if not self.enable_filesystem else "native",
        )

        return agent

    @property
    def agent(self):
        """Get or create the Deep Agent instance."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    async def ainvoke(
        self,
        query: str,
        thread_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Invoke the Deep Agent asynchronously.

        Args:
            query: The user's research query
            thread_id: Optional thread ID for conversation continuity
            **kwargs: Additional arguments passed to the agent

        Returns:
            Dict containing the agent's response and metadata
        """
        config = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        try:
            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config if config else None,
            )

            # Extract the response
            messages = result.get("messages", [])
            response_text = ""
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    response_text = msg.content
                    break

            return {
                "response": response_text,
                "messages": messages,
                "thread_id": thread_id,
            }

        except Exception as e:
            logger.error(f"Deep Agent invocation failed: {e}")
            raise

    def invoke(
        self,
        query: str,
        thread_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Invoke the Deep Agent synchronously.

        Args:
            query: The user's research query
            thread_id: Optional thread ID for conversation continuity
            **kwargs: Additional arguments passed to the agent

        Returns:
            Dict containing the agent's response and metadata
        """
        config = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        try:
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=query)]},
                config if config else None,
            )

            # Extract the response
            messages = result.get("messages", [])
            response_text = ""
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    response_text = msg.content
                    break

            return {
                "response": response_text,
                "messages": messages,
                "thread_id": thread_id,
            }

        except Exception as e:
            logger.error(f"Deep Agent invocation failed: {e}")
            raise

    async def astream(
        self,
        query: str,
        thread_id: Optional[str] = None,
        **kwargs,
    ):
        """Stream the Deep Agent response asynchronously.

        Args:
            query: The user's research query
            thread_id: Optional thread ID for conversation continuity
            **kwargs: Additional arguments passed to the agent

        Yields:
            Streaming chunks from the agent
        """
        config = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        try:
            async for chunk in self.agent.astream(
                {"messages": [HumanMessage(content=query)]},
                config if config else None,
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Deep Agent streaming failed: {e}")
            raise


def create_finagent_deep_agent(
    model: Optional[str] = None,
    enable_subagents: bool = True,
    enable_filesystem: bool = False,
) -> FinAgentDeepAgent:
    """Create a FinAgent Deep Agent instance.

    This is the main factory function for creating Deep Agents.

    Args:
        model: LLM model to use (default: from config)
        enable_subagents: Enable sub-agent delegation
        enable_filesystem: Enable filesystem tools (disabled by default)

    Returns:
        Configured FinAgentDeepAgent instance
    """
    return FinAgentDeepAgent(
        model=model,
        enable_subagents=enable_subagents,
        enable_filesystem=enable_filesystem,
    )
