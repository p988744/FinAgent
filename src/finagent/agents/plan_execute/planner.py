"""Planner agent for the Plan-and-Execute agent flow."""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.agents.plan_execute.models import Plan, PlanExecuteState
from finagent.config import settings

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
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                temperature=0,
            )

        self.parser = PydanticOutputParser(pydantic_object=Plan)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert researcher. Your task is to plan a research strategy for a given user query.\n"
                    "Break down the query into step-by-step tasks.\n"
                    "Available tools:\n"
                    "1. retriever: Semantic search. Use this for general questions or finding relevant context. Args: query (str)\n"
                    "2. hard_search: Keyword search. Use this when specific terms MUST be present. Args: keywords (List[str])\n\n"
                    "{format_instructions}\n",
                ),
                ("user", "{input}"),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())
        
        self.chain = self.prompt | self.llm | self.parser

    async def plan(self, state: PlanExecuteState) -> dict:
        """Generate a plan based on the input."""
        plan = await self.chain.ainvoke({"input": state["input"]})
        return {"plan": plan}
