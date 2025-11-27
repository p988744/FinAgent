"""Query Analyzer agent for understanding user intent before planning."""

import logging
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from finagent.agents.plan_execute.models import PlanExecuteState, QueryInsight
from finagent.config import settings

logger = logging.getLogger(__name__)


class QueryAnalyzerAgent:
    """Agent responsible for analyzing the user's query before planning."""

    def __init__(self):
        """Initialize the query analyzer agent."""
        base_url = settings.effective_llm_base_url
        if base_url:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                base_url=base_url,
                temperature=0,
                timeout=60,  # 60 second timeout for LLM API calls
                max_retries=2,  # Retry failed requests
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                temperature=0,
                timeout=60,  # 60 second timeout for LLM API calls
                max_retries=2,  # Retry failed requests
            )

        self.parser = PydanticOutputParser(pydantic_object=QueryInsight)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a query analysis expert specializing in financial legal research.\n"
                    "Your task is to analyze the user's query and provide insights about:\n"
                    "1. Query type (factual, analytical, comparative, temporal, etc.)\n"
                    "2. Key entities (bank names, dates, amounts, regulations, legal concepts)\n"
                    "3. Recommended search strategy (semantic, keyword, or hybrid)\n"
                    "4. Query complexity (simple, medium, complex)\n"
                    "5. Brief reasoning for your analysis\n\n"
                    "Search Strategy Guidelines:\n"
                    "- semantic: Pure conceptual/analytical queries without specific terms\n"
                    "- keyword: Queries requiring exact matches of ALL specified terms\n"
                    "- hybrid: Queries with BOTH specific terms (dates, amounts, names) AND concepts (recommended for most queries)\n\n"
                    "Examples:\n"
                    "Query: '2020年玉山銀行洗錢防制裁罰'\n"
                    "Analysis:\n"
                    "- Type: factual (seeking specific case information)\n"
                    "- Entities: ['2020年', '玉山銀行', '洗錢防制', '裁罰']\n"
                    "- Strategy: hybrid (has specific year + bank name + legal concept)\n"
                    "- Complexity: simple (single case query)\n"
                    "- Reasoning: Query contains specific temporal marker (2020年), institution name (玉山銀行), "
                    "and legal concept (洗錢防制裁罰). Hybrid search will find documents with both exact terms and related concepts.\n\n"
                    "Query: '分析銀行業洗錢防制的主要問題'\n"
                    "Analysis:\n"
                    "- Type: analytical (requires analysis and synthesis)\n"
                    "- Entities: ['銀行業', '洗錢防制', '主要問題']\n"
                    "- Strategy: semantic (conceptual analysis, no specific terms required)\n"
                    "- Complexity: medium (requires analyzing multiple sources)\n"
                    "- Reasoning: Query asks for analysis of trends/patterns across the banking industry. "
                    "No specific dates, amounts, or institution names. Semantic search will capture conceptual relationships.\n\n"
                    "Query: '找出包含「金管會」和「裁罰」的所有文件'\n"
                    "Analysis:\n"
                    "- Type: search (explicit document retrieval)\n"
                    "- Entities: ['金管會', '裁罰']\n"
                    "- Strategy: keyword (explicit requirement for ALL terms to appear)\n"
                    "- Complexity: simple (straightforward keyword search)\n"
                    "- Reasoning: Query explicitly states \"找出包含...的所有文件\" (find all documents containing...), "
                    "indicating Boolean AND search requirement. All specified terms must appear exactly.\n\n"
                    "{format_instructions}\n",
                ),
                ("user", "{input}"),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())

        self.chain = self.prompt | self.llm | self.parser

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def analyze(self, state: PlanExecuteState) -> dict:
        """
        Analyze the user's query and generate insights.

        Args:
            state: Current workflow state with 'input' field

        Returns:
            dict with 'query_insight' field containing QueryInsight
        """
        logger.info(f"Analyzing query: {state['input']}")

        try:
            insight = await self.chain.ainvoke({"input": state["input"]})

            logger.info(
                f"Query analysis complete - Type: {insight.query_type}, "
                f"Strategy: {insight.search_strategy}, "
                f"Complexity: {insight.complexity}"
            )

            return {"query_insight": insight}

        except Exception as e:
            logger.error(f"Query analysis failed: {e}", exc_info=True)
            # Return a default insight if analysis fails
            fallback_insight = QueryInsight(
                query_type="unknown",
                key_entities=[],
                search_strategy="hybrid",
                complexity="medium",
                reasoning=f"分析失敗，使用預設策略 (Analysis failed, using default strategy): {str(e)}",
            )
            return {"query_insight": fallback_insight}
