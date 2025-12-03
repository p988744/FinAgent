"""Executor agent for the Plan-and-Execute agent flow."""

import logging

from langgraph.constants import Send

from finagent.agents.plan_execute.models import PlanExecuteState, PlanTask
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever
from finagent.tools import HardSearchTool, HybridRetrieverTool, RetrieverTool

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """Agent responsible for executing the tasks in the plan."""

    def __init__(self, retriever: DocumentRetriever, hard_searcher: HardSearcher):
        """Initialize the executor agent."""
        self.retriever_tool = RetrieverTool(retriever=retriever)
        self.hard_search_tool = HardSearchTool(hard_searcher=hard_searcher)
        self.hybrid_retriever_tool = HybridRetrieverTool(
            retriever=retriever,
            semantic_weight=0.6,  # 60% semantic
            keyword_weight=0.4    # 40% keyword (BM25)
        )
        self.tools = {
            "retriever": self.retriever_tool,
            "hard_search": self.hard_search_tool,
            "hybrid_search": self.hybrid_retriever_tool,  # New hybrid tool
        }

    def detect_dependencies(self, tasks: list[PlanTask]) -> dict[int, list[int]]:
        """
        Detect dependencies between tasks.

        Simple heuristic: A task depends on another if its description mentions "task X" or "step X".
        """
        dependencies = {}
        for task in tasks:
            depends_on = []
            # Check for explicit references like "task 1", "step 1", etc.
            # This is a simple heuristic and can be improved with LLM analysis if needed
            for other_task in tasks:
                if other_task.id == task.id:
                    continue

                # Check if description references the other task ID
                # e.g., "Use the results from task 1..."
                ref_patterns = [
                    f"task {other_task.id}",
                    f"step {other_task.id}",
                    f"task #{other_task.id}",
                    f"step #{other_task.id}"
                ]

                if any(pattern in task.description.lower() for pattern in ref_patterns):
                    depends_on.append(other_task.id)

            dependencies[task.id] = depends_on
        return dependencies

    def route_tasks(self, state: PlanExecuteState):
        """
        Route independent tasks to parallel execution.
        """
        plan = state["plan"]
        past_steps = state.get("past_steps", [])
        completed_task_ids = {step[0]["id"] for step in past_steps}

        # Detect dependencies
        dependencies = self.detect_dependencies(plan.tasks)

        # Find executable tasks (pending and dependencies met)
        tasks_to_execute = []
        for task in plan.tasks:
            if task.status != "pending":
                continue

            # Check if dependencies are met
            deps = dependencies.get(task.id, [])
            if all(dep_id in completed_task_ids for dep_id in deps):
                tasks_to_execute.append(task)

        if not tasks_to_execute:
            # No executable tasks found (or all done)
            # If there are still pending tasks but no executable ones, it might be a deadlock or waiting for something
            # But for now, we just return empty list which will likely trigger replanner or end
            return []

        # Return Send objects for parallel execution
        return [Send("execute_task", {"task": task}) for task in tasks_to_execute]

    async def execute_task(self, state: dict) -> dict:
        """
        Execute a single task (worker node).

        Can be called in two ways:
        1. Via Send with {"task": PlanTask} - task is provided directly
        2. Via conditional edge - needs to pick next pending task from plan

        Returns: {"past_steps": [(task_dict, result)]}
        """
        # Check if task is provided directly (via Send)
        if "task" in state:
            task = state["task"]
        else:
            # Pick the next pending task from plan
            plan = state.get("plan")
            if not plan or not plan.tasks:
                logger.warning("No plan or tasks found in state")
                return {"past_steps": []}

            past_steps = state.get("past_steps", [])
            completed_task_ids = {step[0]["id"] for step in past_steps}

            pending_tasks = [
                t for t in plan.tasks
                if t.status == "pending" and t.id not in completed_task_ids
            ]

            if not pending_tasks:
                logger.warning("No pending tasks found")
                return {"past_steps": []}

            task = pending_tasks[0]
            logger.info(f"Selected next pending task: {task.id}")

        logger.info(f"Executing task {task.id}: {task.description}")

        tool_name = task.tool
        tool = self.tools.get(tool_name)

        # Enhanced logging: Tool selection
        logger.info(f"Tool selected: {tool_name}")
        logger.debug(f"Tool args: {task.args}")

        if not tool:
            # Enhanced error message with available tools
            available_tools = list(self.tools.keys())
            error_msg = f"Error: Tool '{tool_name}' not found. Available: {available_tools}"
            logger.error(error_msg)
            result = error_msg
            task.status = "failed"
        else:
            try:
                # Log tool invocation
                logger.debug(f"Invoking {tool_name} with args: {task.args}")

                # Use async invoke if available, otherwise sync
                if hasattr(tool, "ainvoke"):
                    result = await tool.ainvoke(task.args)
                else:
                    result = tool.invoke(task.args)
                task.status = "completed"

                # Enhanced logging: Success with result size
                logger.info(f"Tool {tool_name} completed successfully: {len(result)} chars returned")

            except Exception as e:
                error_msg = f"Error executing {tool_name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                result = error_msg
                task.status = "failed"

        task.result = result

        # Return update for past_steps (reducer will append this)
        return {"past_steps": [(task.dict(), result)]}

    # Legacy execute method kept for compatibility or fallback if needed
    # But mostly replaced by route_tasks + execute_task
    async def execute(self, state: PlanExecuteState) -> dict:
        """Execute the next pending task (Sequential Fallback)."""
        # ... (Logic similar to before, but we might not need it if we fully switch to parallel)
        # For now, let's keep it simple and assume the graph will use route_tasks
        return {}
