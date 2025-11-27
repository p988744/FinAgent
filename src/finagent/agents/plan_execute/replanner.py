"""Replanner agent for the Plan-and-Execute agent flow."""

from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.agents.plan_execute.models import Plan, PlanExecuteState, PlanTask
from finagent.config import settings


class ReplannerOutput(BaseModel):
    """Output for the replanner agent."""

    response: Optional[str] = Field(
        description="The final answer to the user's question, if enough information has been gathered. If not, leave empty."
    )
    new_plan: Optional[Plan] = Field(
        description="The updated plan if more information is needed. If response is provided, this is ignored."
    )


from langchain_core.output_parsers import PydanticOutputParser

from langchain_core.output_parsers import StrOutputParser
import json
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ReplannerAgent:
    """Agent responsible for updating the plan based on execution results."""

    def __init__(self):
        """Initialize the replanner agent."""
        base_url = settings.effective_llm_base_url
        if base_url:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                base_url=base_url,
                temperature=0,
                timeout=60,  # 60 second timeout for LLM API calls
                max_retries=2,  # Retry failed requests
                model_kwargs={"response_format": {"type": "json_object"}},
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                temperature=0,
                timeout=60,  # 60 second timeout for LLM API calls
                max_retries=2,  # Retry failed requests
                model_kwargs={"response_format": {"type": "json_object"}},
            )

        # Use the Pydantic model just for generating instructions, not for parsing
        self.parser = PydanticOutputParser(pydantic_object=ReplannerOutput)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert researcher. Your task is to review the progress of a research plan and decide the next steps.\n"
                    "You have the original query, the current plan, and the results of executed tasks.\n"
                    "1. If you have enough information to answer the user's query, provide the 'response'.\n"
                    "2. If you need more information, provide a 'new_plan' with updated tasks. You can keep pending tasks or add new ones.\n"
                    "   - Do NOT include completed tasks in the new plan.\n"
                    "   - Available tools: retriever (args: query), hard_search (args: keywords)\n"
                    "IMPORTANT: Your response MUST be a valid JSON object matching the schema.\n"
                    "{format_instructions}\n",
                ),
                (
                    "user",
                    "Query: {input}\n\n"
                    "Original Plan: {plan}\n\n"
                    "Past Steps:\n{past_steps}",
                ),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())
        
        # Use StrOutputParser to get raw string, then parse manually
        self.chain = self.prompt | self.llm | StrOutputParser()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def replan(self, state: PlanExecuteState) -> dict:
        """Replan based on the current state."""
        # Format past steps for the prompt
        past_steps_str = ""
        for task_dict, result in state["past_steps"]:
            # Truncate result to avoid context overflow
            truncated_result = str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
            past_steps_str += f"Task: {task_dict['description']}\nResult: {truncated_result}\n---\n"
            
        raw_output = await self.chain.ainvoke(
            {
                "input": state["input"],
                "plan": state["plan"],
                "past_steps": past_steps_str,
            }
        )
        
        # Clean up the output (remove markdown code blocks if present)
        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
        if cleaned_output.startswith("```"):
            cleaned_output = cleaned_output[3:]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]
        
        cleaned_output = cleaned_output.strip()
        
        try:
            parsed_json = json.loads(cleaned_output)
            output = ReplannerOutput(**parsed_json)
            
            if output.response:
                return {"response": output.response}
            else:
                return {"plan": output.new_plan}
                
        except Exception as e:
            # Fallback: If parsing fails, return a default response or error
            # For now, let's try to return a generic response if we have past steps, 
            # assuming the model tried to answer but failed JSON formatting.
            if state["past_steps"]:
                 return {"response": "I have gathered some information but encountered an error generating the final structured response. Please check the activity log for details."}
            return {"response": f"Error parsing replanner output: {str(e)}"}
