"""Planner agent for the Plan-and-Execute agent flow."""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.agents.plan_execute.models import Plan, PlanExecuteState
from finagent.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class PlannerAgent:
    """Agent responsible for creating the initial research plan."""

    def __init__(self):
        """Initialize the planner agent."""
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

        self.parser = PydanticOutputParser(pydantic_object=Plan)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert researcher. Your task is to plan a research strategy for a given user query.\n"
                    "Break down the query into step-by-step tasks.\n\n"
                    "Available tools:\n"
                    "1. retriever: Semantic vector search. Best for:\n"
                    "   - Conceptual/analytical queries\n"
                    "   - Understanding relationships and meanings\n"
                    "   - When exact terms don't matter\n"
                    "   Args: {{\"query\": str}}\n\n"
                    "2. hard_search: Exact keyword matching (grep-style). Best for:\n"
                    "   - Finding documents with specific exact terms\n"
                    "   - Boolean AND searches across keywords\n"
                    "   - When ALL keywords MUST appear exactly\n"
                    "   Args: {{\"keywords\": List[str]}}\n\n"
                    "3. hybrid_search: Combined BM25 + Vector search (60% semantic, 40% keyword). Best for:\n"
                    "   - Queries with BOTH specific terms AND concepts\n"
                    "   - Dates, numbers, names + context (e.g., '2020年玉山銀行洗錢防制裁罰500萬')\n"
                    "   - When you need both precision and understanding\n"
                    "   - Most real-world queries benefit from this\n"
                    "   Args: {{\"query\": str, \"k\": int}}\n\n"
                    "Tool Selection Guidelines:\n"
                    "- Use hybrid_search as DEFAULT for most queries (combines best of both)\n"
                    "- Use retriever for pure conceptual/analytical queries (no specific terms needed)\n"
                    "- Use hard_search only when ALL keywords MUST appear exactly\n\n"
                    "Examples:\n"
                    "- '2020年玉山銀行洗錢防制裁罰' → hybrid_search (has year, bank name, concept)\n"
                    "- '分析銀行業洗錢防制的主要問題' → retriever (analytical, no specific terms)\n"
                    "- '找出包含「金管會」和「裁罰」的文件' → hard_search (explicit AND requirement)\n\n"
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
        reraise=True
    )
    async def plan(self, state: PlanExecuteState) -> dict:
        """Generate a plan based on the input."""
        plan = await self.chain.ainvoke({"input": state["input"]})
        return {"plan": plan}
