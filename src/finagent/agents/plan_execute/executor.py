"""Executor agent for the Plan-and-Execute agent flow."""

import logging

from finagent.agents.plan_execute.models import PlanExecuteState
from finagent.agents.plan_execute.tools import HardSearchTool, RetrieverTool
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """Agent responsible for executing the tasks in the plan."""

    def __init__(self, retriever: DocumentRetriever, hard_searcher: HardSearcher):
        """Initialize the executor agent."""
        self.retriever_tool = RetrieverTool(retriever=retriever)
        self.hard_search_tool = HardSearchTool(hard_searcher=hard_searcher)
        self.tools = {
            "retriever": self.retriever_tool,
            "hard_search": self.hard_search_tool,
        }

    async def execute(self, state: PlanExecuteState) -> dict:
        """Execute the next pending task in the plan."""
        plan = state["plan"]
        past_steps = state.get("past_steps", [])
        
        # Find the next pending task
        # In a more complex version, we could execute multiple independent tasks in parallel
        task_to_execute = None
        for task in plan.tasks:
            if task.status == "pending":
                task_to_execute = task
                break
        
        if not task_to_execute:
            # No pending tasks
            return {"past_steps": past_steps}
        
        logger.info(f"Executing task {task_to_execute.id}: {task_to_execute.description}")
        
        # Execute the tool
        tool_name = task_to_execute.tool
        tool = self.tools.get(tool_name)
        
        if not tool:
            result = f"Error: Tool '{tool_name}' not found."
            task_to_execute.status = "failed"
        else:
            try:
                # Run the tool (tools are sync, but we can wrap if needed)
                # For now, we assume they are fast enough or we accept blocking
                result = tool.invoke(task_to_execute.args)
                task_to_execute.status = "completed"
            except Exception as e:
                result = f"Error executing tool: {str(e)}"
                task_to_execute.status = "failed"
        
        task_to_execute.result = result
        
        # Update past steps
        new_step = (task_to_execute.dict(), result)
        past_steps.append(new_step)
        
        return {"plan": plan, "past_steps": past_steps}
