"""Tool selector for choosing appropriate tools based on query analysis."""

import json
import logging
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.agents.query_analyzer import QueryAnalysis
from finagent.config import settings
from finagent.tools.registry import get_registry

logger = logging.getLogger(__name__)


class ToolSelector:
    """Selects appropriate tools based on query analysis using LLM."""

    SELECTION_PROMPT = """你是一個工具選擇專家。根據查詢分析結果，選擇最適合的工具來執行任務。

可用工具：
{tool_descriptions}

查詢：{query}

查詢分析：
```json
{query_analysis}
```

請選擇最適合的工具組合，並說明原因。以 JSON 格式回答：

```json
{{
  "selected_tools": [
    {{
      "tool_name": "工具名稱",
      "reason": "選擇原因",
      "parameters": {{"參數名": "參數值"}},
      "execution_order": 1
    }}
  ],
  "execution_strategy": "sequential 或 parallel",
  "estimated_total_time": 估計總時間（秒）
}}
```

**工具選擇指引**：

1. **temporal + entity_specific** (最近一次)
   → 使用 metadata_search（entity + 自動取最新）

2. **comprehensive + entity_specific** (所有、全部)
   → 使用 list_documents（完整清單）

3. **specific_file** (特定檔名)
   → 使用 read_file

4. **comparison + multi_entity** (比較分析)
   → 使用 multi_entity_search

5. **temporal + general_search** (時間+關鍵字)
   → 使用 hybrid_search（metadata filtering + vector search）

6. **general_search** (一般搜尋)
   → 使用 vector_search

**重要規則**：
- 優先選擇最精確的工具（避免過度使用 general tools）
- 如果有明確的實體和時間限制，使用 hybrid_search
- 比較查詢必須使用 multi_entity_search
- 「所有」、「全部」必須使用 list_documents（不是 vector_search）
- 可選擇多個工具組合（但要合理）

請選擇工具。
"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.effective_llm_base_url,
            api_key=settings.effective_llm_api_key,
            temperature=0.0,  # Deterministic for tool selection
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是專業的工具選擇專家。"),
                ("user", self.SELECTION_PROMPT),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    async def select_tools(
        self, query: str, analysis: QueryAnalysis
    ) -> list[dict]:
        """
        Select tools based on query analysis.

        Args:
            query: User query string
            analysis: QueryAnalysis object

        Returns:
            List of selected tools with parameters
        """
        try:
            # Get all tool capabilities
            registry = get_registry()
            capabilities = registry.get_all_capabilities()

            # Format tool descriptions for LLM
            tool_descriptions = "\n\n".join(
                [
                    f"**{cap.name}**\n"
                    f"描述：{cap.description}\n"
                    f"支援意圖：{', '.join(cap.supported_intents)}\n"
                    f"必要特徵：{', '.join(cap.required_features) if cap.required_features else '無'}\n"
                    f"執行時間：{cap.execution_time_estimate}\n"
                    f"成本：{cap.cost_estimate}\n"
                    f"限制：{', '.join(cap.limitations) if cap.limitations else '無'}"
                    for cap in capabilities.values()
                ]
            )

            # Use LLM to select tools
            response = await self.chain.ainvoke(
                {
                    "query": query,
                    "tool_descriptions": tool_descriptions,
                    "query_analysis": analysis.model_dump_json(indent=2),
                }
            )

            # Parse response
            selection = self._parse_json_response(response)

            selected_tools = selection.get("selected_tools", [])

            logger.info(
                f"Tool selection: {len(selected_tools)} tools selected - {[t['tool_name'] for t in selected_tools]}"
            )

            return selected_tools

        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            # Fallback to rule-based selection
            return self._fallback_select_tools(query, analysis)

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON object found in response")

            # Parse JSON
            data = json.loads(json_str)

            logger.debug(f"Parsed tool selection: {data.get('selected_tools', [])}")

            return data

        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def _fallback_select_tools(
        self, query: str, analysis: QueryAnalysis
    ) -> list[dict]:
        """
        Fallback tool selection using rule-based logic.

        Args:
            query: User query string
            analysis: QueryAnalysis object

        Returns:
            List of selected tools
        """
        logger.warning("Using fallback tool selection")

        selected_tools = []

        # Rule 1: Comparison queries → multi_entity_search
        if analysis.requires_multi_entity and len(analysis.entities) >= 2:
            selected_tools.append(
                {
                    "tool_name": "multi_entity_search",
                    "reason": "比較查詢需要多實體搜尋",
                    "parameters": {
                        "entities": analysis.entities,
                        "top_k_per_entity": 5,
                    },
                    "execution_order": 1,
                }
            )
            return selected_tools

        # Rule 2: Specific file → read_file
        if analysis.has_file_reference and analysis.filename:
            selected_tools.append(
                {
                    "tool_name": "read_file",
                    "reason": "指定特定檔案",
                    "parameters": {"filename": analysis.filename},
                    "execution_order": 1,
                }
            )
            return selected_tools

        # Rule 3: Comprehensive listing → list_documents
        if analysis.requires_exhaustive_search and analysis.entities:
            selected_tools.append(
                {
                    "tool_name": "list_documents",
                    "reason": "需要完整清單",
                    "parameters": {"entity": analysis.entities[0]},
                    "execution_order": 1,
                }
            )
            return selected_tools

        # Rule 4: Temporal + entity → metadata_search or hybrid_search
        if analysis.has_temporal_constraint and analysis.entities:
            if analysis.temporal_type == "latest":
                # Latest record → metadata_search
                selected_tools.append(
                    {
                        "tool_name": "metadata_search",
                        "reason": "查詢最近一次記錄",
                        "parameters": {"entity": analysis.entities[0]},
                        "execution_order": 1,
                    }
                )
            else:
                # Time range + semantic → hybrid_search
                params = {"entity": analysis.entities[0], "top_k": 10}
                if analysis.date_range:
                    params["date_from"] = analysis.date_range.get("from")
                    params["date_to"] = analysis.date_range.get("to")
                selected_tools.append(
                    {
                        "tool_name": "hybrid_search",
                        "reason": "時間限制+語義搜尋",
                        "parameters": params,
                        "execution_order": 1,
                    }
                )
            return selected_tools

        # Rule 5: Default → vector_search
        selected_tools.append(
            {
                "tool_name": "vector_search",
                "reason": "一般語義搜尋",
                "parameters": {"top_k": 10, "relevance_threshold": 0.8},
                "execution_order": 1,
            }
        )

        return selected_tools
