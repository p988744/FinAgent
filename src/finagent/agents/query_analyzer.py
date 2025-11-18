"""Query analyzer for intent classification and feature extraction."""

import json
import logging
import re
from enum import Enum

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from finagent.config import settings

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Query intent types."""

    GENERAL_SEARCH = "general_search"  # 一般搜尋
    TEMPORAL = "temporal"  # 時間相關（最近、過去）
    COMPREHENSIVE = "comprehensive"  # 完整清單（所有）
    SPECIFIC_FILE = "specific_file"  # 特定檔案
    COMPARISON = "comparison"  # 比較分析
    ENTITY_SPECIFIC = "entity_specific"  # 特定實體


class QueryAnalysis(BaseModel):
    """Structured query analysis result."""

    # Intent
    intent: QueryIntent = Field(..., description="Primary query intent")
    secondary_intents: list[QueryIntent] = Field(
        default_factory=list, description="Secondary intents"
    )

    # Entity extraction
    entities: list[str] = Field(
        default_factory=list,
        description="Extracted entity names (banks, institutions)",
    )

    # Temporal features
    has_temporal_constraint: bool = Field(False, description="Has time constraint")
    temporal_type: str | None = Field(
        None,
        description="Type of temporal constraint (latest, past, specific_date, year_range)",
    )
    date_range: dict | None = Field(None, description="Extracted date range")

    # File reference
    has_file_reference: bool = Field(False, description="References specific file")
    filename: str | None = Field(None, description="Extracted filename")

    # Query characteristics
    complexity: str = Field(..., description="simple | medium | complex")
    requires_exhaustive_search: bool = Field(
        False, description="Requires all results (not top-k)"
    )
    requires_multi_entity: bool = Field(
        False, description="Requires multi-entity orchestration"
    )

    # Extracted parameters
    extracted_parameters: dict = Field(
        default_factory=dict, description="Additional extracted parameters"
    )


class QueryAnalyzer:
    """Analyzes user query to determine intent and features using LLM."""

    ANALYSIS_PROMPT = """你是一個專業的查詢分析助手。分析使用者的查詢，辨識意圖和特徵。

查詢意圖類型：
- general_search: 一般關鍵字搜尋
- temporal: 時間相關（最近、過去、特定日期、年份）
- comprehensive: 要求完整清單（所有、全部、過去所有）
- specific_file: 指定特定檔案名稱（包含 .txt 等副檔名）
- comparison: 比較分析（A vs B、比較、與...相比）
- entity_specific: 特定實體的資訊

使用者查詢：{query}

請以 JSON 格式回答，包含以下欄位：

```json
{{
  "intent": "主要意圖（選一個）",
  "secondary_intents": ["次要意圖陣列"],
  "entities": ["提及的實體名稱陣列"],
  "has_temporal_constraint": true/false,
  "temporal_type": "latest/past/specific_date/year_range/null",
  "date_range": {{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}} 或 null,
  "has_file_reference": true/false,
  "filename": "檔案名稱或null",
  "complexity": "simple/medium/complex",
  "requires_exhaustive_search": true/false,
  "requires_multi_entity": true/false,
  "extracted_parameters": {{
    "penalty_type": "裁罰類型",
    "jurisdiction": "監管機構",
    "year_ad": 年份數字,
    其他參數...
  }}
}}
```

**重要規則**：
1. entities: 提取所有提及的銀行或機構名稱（如「玉山銀行」、「國泰世華銀行」）
2. temporal_type: latest（最近一次）、past（過去）、specific_date（特定日期）、year_range（年份範圍）
3. requires_exhaustive_search: 如果查詢包含「所有」、「全部」、「過去所有」等，設為 true
4. requires_multi_entity: 如果查詢包含多個實體且需要比較，設為 true
5. complexity: simple（單一實體+單一條件）、medium（多條件或時間限制）、complex（多實體或比較）
6. extracted_parameters: 提取裁罰類型、年份、監管機構等具體參數

**範例1**：
查詢：「玉山銀行最近一次的罰款紀錄」
回答：
```json
{{
  "intent": "temporal",
  "secondary_intents": ["entity_specific"],
  "entities": ["玉山銀行"],
  "has_temporal_constraint": true,
  "temporal_type": "latest",
  "date_range": null,
  "has_file_reference": false,
  "filename": null,
  "complexity": "medium",
  "requires_exhaustive_search": false,
  "requires_multi_entity": false,
  "extracted_parameters": {{"penalty_type": "罰款"}}
}}
```

**範例2**：
查詢：「玉山銀行與國泰世華銀行的裁罰紀錄比較」
回答：
```json
{{
  "intent": "comparison",
  "secondary_intents": ["entity_specific"],
  "entities": ["玉山銀行", "國泰世華銀行"],
  "has_temporal_constraint": false,
  "temporal_type": null,
  "date_range": null,
  "has_file_reference": false,
  "filename": null,
  "complexity": "complex",
  "requires_exhaustive_search": false,
  "requires_multi_entity": true,
  "extracted_parameters": {{"penalty_type": "裁罰"}}
}}
```

請分析上述查詢。
"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.effective_llm_base_url,
            api_key=settings.effective_llm_api_key,
            temperature=0.0,  # Deterministic for analysis
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是專業的查詢分析助手。"),
                ("user", self.ANALYSIS_PROMPT),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    async def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze query and return structured analysis.

        Args:
            query: User query string

        Returns:
            QueryAnalysis object
        """
        try:
            # Invoke LLM to analyze query
            response = await self.chain.ainvoke({"query": query})

            # Parse JSON response
            analysis_dict = self._parse_json_response(response)

            # Create QueryAnalysis object
            analysis = QueryAnalysis(**analysis_dict)

            logger.info(f"Query analysis: intent={analysis.intent}, entities={analysis.entities}, complexity={analysis.complexity}")

            return analysis

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            # Fallback to simple analysis
            return self._fallback_analyze(query)

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

            logger.debug(f"Parsed query analysis: {list(data.keys())}")

            return data

        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    def _fallback_analyze(self, query: str) -> QueryAnalysis:
        """
        Fallback analysis using simple heuristics.

        Args:
            query: User query string

        Returns:
            QueryAnalysis with basic intent detection
        """
        logger.warning(f"Using fallback analysis for: {query}")

        # Detect intent using keywords
        intent = QueryIntent.GENERAL_SEARCH
        secondary_intents = []
        entities = []
        has_temporal = False
        temporal_type = None
        requires_exhaustive = False
        requires_multi_entity = False

        # Temporal detection
        if any(keyword in query for keyword in ["最近", "latest"]):
            intent = QueryIntent.TEMPORAL
            has_temporal = True
            temporal_type = "latest"
        elif any(keyword in query for keyword in ["過去", "所有", "全部", "所有的"]):
            intent = QueryIntent.COMPREHENSIVE
            requires_exhaustive = True

        # File reference detection
        if ".txt" in query or "檔案" in query:
            intent = QueryIntent.SPECIFIC_FILE

        # Comparison detection
        if any(keyword in query for keyword in ["比較", "vs", "與", "和"]):
            intent = QueryIntent.COMPARISON
            requires_multi_entity = True

        # Simple entity extraction (look for common bank names)
        bank_names = [
            "玉山銀行", "國泰世華銀行", "中國信託銀行", "台新銀行",
            "富邦銀行", "第一銀行", "華南銀行", "彰化銀行"
        ]
        for bank in bank_names:
            if bank in query:
                entities.append(bank)

        return QueryAnalysis(
            intent=intent,
            secondary_intents=secondary_intents,
            entities=entities,
            has_temporal_constraint=has_temporal,
            temporal_type=temporal_type,
            date_range=None,
            has_file_reference=False,
            filename=None,
            complexity="medium",
            requires_exhaustive_search=requires_exhaustive,
            requires_multi_entity=requires_multi_entity,
            extracted_parameters={},
        )
