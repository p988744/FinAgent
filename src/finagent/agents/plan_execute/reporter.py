"""Reporter agent for formatting the final response."""

import logging
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from finagent.agents.plan_execute.models import PlanExecuteState
from finagent.config import settings

logger = logging.getLogger(__name__)

REPORT_PROMPT = """You are a professional financial legal researcher.
Your task is to compile a final report based on the executed research plan and results.

Query: {input}

Research Steps & Results:
{past_steps}

Instructions:
1. Synthesize the information into a clear, structured report.
2. Use the following structure:
   - **Executive Summary**: A brief overview of the findings.
   - **Key Findings**: Detailed points with evidence.
   - **Analysis**: Connection to relevant laws and regulations.
   - **Conclusion**: Final answer to the user's query.
3. Cite your sources explicitly using the [Source Name] format.
4. If the results are insufficient, state what is missing.
5. Use Traditional Chinese (繁體中文).

Report:"""

class ReporterAgent:
    """Agent responsible for generating the final report."""

    def __init__(self):
        """Initialize the reporter agent."""
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.effective_llm_api_key,
            base_url=settings.effective_llm_base_url,
            temperature=0,
            timeout=60,  # 60 second timeout for LLM API calls
            max_retries=2,  # Retry failed requests
        )
        self.prompt = ChatPromptTemplate.from_template(REPORT_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _format_steps(self, past_steps: List[tuple]) -> str:
        """Format past steps for the prompt."""
        formatted = []
        for i, (task, result) in enumerate(past_steps, 1):
            task_desc = task.get("description", "Unknown Task")
            formatted.append(f"Step {i}: {task_desc}\nResult: {result}\n")
        return "\n---\n".join(formatted)

    async def report(self, state: PlanExecuteState) -> dict:
        """Generate the final report."""
        logger.info("Generating final report...")
        
        input_query = state["input"]
        past_steps = state.get("past_steps", [])
        
        formatted_steps = self._format_steps(past_steps)
        
        response = await self.chain.ainvoke({
            "input": input_query,
            "past_steps": formatted_steps
        })
        
        return {"response": response}
