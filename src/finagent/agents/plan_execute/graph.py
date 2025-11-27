"""LangGraph workflow for the Plan-and-Execute agent flow.

Enhanced with human-in-the-loop confirmation before plan execution.
Flow:
1. Query Analyzer - Analyze user query
2. Planner - Create research plan
3. Plan Confirmation - Wait for user approval (optional INTERRUPT)
4. Execute Tasks - Execute plan tasks
5. Replanner - Review and replan if needed
6. Reporter - Generate final report
"""

import logging
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from finagent.agents.plan_execute.confirmation import ConfirmationHandler
from finagent.agents.plan_execute.executor import ExecutorAgent
from finagent.agents.plan_execute.models import PlanExecuteState
from finagent.agents.plan_execute.planner import PlannerAgent
from finagent.agents.plan_execute.query_analyzer import QueryAnalyzerAgent
from finagent.agents.plan_execute.replanner import ReplannerAgent
from finagent.agents.plan_execute.reporter import ReporterAgent
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever

logger = logging.getLogger(__name__)


class PlanExecuteWorkflow:
    """Workflow for the Plan-and-Execute agent with human-in-the-loop.

    Features:
    - Query analysis before planning
    - Plan creation with task breakdown
    - Human-in-the-loop confirmation (optional)
    - Task execution with multiple tools
    - Dynamic replanning based on results
    - Final report generation
    """

    def __init__(
        self,
        retriever: DocumentRetriever,
        hard_searcher: HardSearcher,
        enable_confirmation: bool = False,
    ):
        """Initialize the workflow.

        Args:
            retriever: Document retriever for semantic search
            hard_searcher: Hard searcher for keyword search
            enable_confirmation: Whether to require user confirmation before execution
        """
        self.enable_confirmation = enable_confirmation

        # Initialize agents
        self.query_analyzer = QueryAnalyzerAgent()
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(retriever=retriever, hard_searcher=hard_searcher)
        self.replanner = ReplannerAgent()
        self.reporter = ReporterAgent()
        self.confirmation_handler = ConfirmationHandler()

        # Validate tools are available
        self._validate_tools()

        # Build graph (with or without confirmation)
        self.graph = self._build_graph()

    def _validate_tools(self):
        """Validate that all required tools are registered."""
        required_tools = {"retriever", "hard_search", "hybrid_search"}
        available_tools = set(self.executor.tools.keys())

        missing_tools = required_tools - available_tools
        if missing_tools:
            raise RuntimeError(
                f"Missing required tools: {missing_tools}. "
                f"Available: {available_tools}"
            )

        logger.info(f"Tool validation passed. Available tools: {available_tools}")

    def _build_graph(self):
        """Build the LangGraph workflow.

        If confirmation is enabled, adds a plan_confirmation node with interrupt.
        """
        workflow = StateGraph(PlanExecuteState)

        # Add nodes
        workflow.add_node("query_analyzer", self.query_analyzer.analyze)
        workflow.add_node("planner", self.planner.plan)
        workflow.add_node("execute_task", self.executor.execute_task)
        workflow.add_node("replanner", self.replanner.replan)
        workflow.add_node("reporter", self.reporter.report)

        if self.enable_confirmation:
            # Add confirmation node
            workflow.add_node(
                "plan_confirmation",
                self.confirmation_handler.create_confirmation_node,
            )

        # Set entry point
        workflow.set_entry_point("query_analyzer")

        # From query analyzer to planner
        workflow.add_edge("query_analyzer", "planner")

        if self.enable_confirmation:
            # Flow with confirmation:
            # Planner -> Plan Confirmation -> (approved?) -> Execute or Planner
            workflow.add_edge("planner", "plan_confirmation")

            # Conditional edge after confirmation
            workflow.add_conditional_edges(
                "plan_confirmation",
                self._route_after_confirmation,
                {
                    "execute_task": "execute_task",
                    "planner": "planner",
                },
            )
        else:
            # Direct flow without confirmation
            workflow.add_conditional_edges(
                "planner",
                self.executor.route_tasks,
                ["execute_task"],
            )

        # From execute_task to replanner
        workflow.add_edge("execute_task", "replanner")

        # Conditional edge from replanner
        def replanner_router(state: PlanExecuteState):
            if state.get("response"):
                logger.info("Replanner has response, routing to reporter")
                return "reporter"

            # Check if there are pending tasks to execute
            plan = state.get("plan")
            if not plan or not plan.tasks:
                logger.info("No plan or tasks, routing to reporter")
                return "reporter"

            past_steps = state.get("past_steps", [])
            completed_task_ids = {step[0]["id"] for step in past_steps}
            pending_tasks = [t for t in plan.tasks if t.status == "pending" and t.id not in completed_task_ids]

            if pending_tasks:
                logger.info(f"Found {len(pending_tasks)} pending tasks, routing to execute_task")
                return "execute_task"
            else:
                logger.info("No pending tasks, routing to reporter")
                return "reporter"

        workflow.add_conditional_edges(
            "replanner",
            replanner_router,
            {"execute_task": "execute_task", "reporter": "reporter"},
        )

        # Edge from reporter to END
        workflow.add_edge("reporter", END)

        # Compile with checkpointer if confirmation is enabled
        if self.enable_confirmation:
            memory = MemorySaver()
            return workflow.compile(
                checkpointer=memory,
                interrupt_before=["plan_confirmation"],
            )
        else:
            return workflow.compile()

    def _route_after_confirmation(self, state: PlanExecuteState) -> str:
        """Route after plan confirmation.

        Args:
            state: Current workflow state

        Returns:
            Next node name
        """
        plan_approved = state.get("plan_approved")

        if plan_approved is True:
            logger.info("Plan approved, proceeding to execution")
            return "execute_task"
        elif plan_approved is False:
            logger.info("Plan modified/rejected, returning to planner")
            return "planner"
        else:
            # This shouldn't happen after resuming from interrupt
            # But handle it gracefully by proceeding
            logger.warning("plan_approved is None after confirmation, proceeding anyway")
            return "execute_task"

    async def run(
        self,
        query: str,
        thread_id: Optional[str] = None,
    ) -> dict:
        """Run the workflow.

        Args:
            query: User's research query
            thread_id: Optional thread ID for confirmation flow

        Returns:
            Final state with response
        """
        initial_state: PlanExecuteState = {
            "input": query,
            "query_insight": None,
            "plan": None,
            "past_steps": [],
            "response": None,
            "scratchpad": [],
            # Confirmation fields
            "confirmation_request": None,
            "plan_approved": None,
            "user_modifications": None,
            "user_feedback": None,
            "confirmation_requested_at": None,
            "confirmation_received_at": None,
        }

        if self.enable_confirmation and thread_id:
            # Use thread config for resumable execution
            config = {"configurable": {"thread_id": thread_id}}
            result = await self.graph.ainvoke(initial_state, config)
        else:
            result = await self.graph.ainvoke(initial_state)

        return result

    async def resume_with_confirmation(
        self,
        thread_id: str,
        approved: bool,
        modifications: Optional[dict] = None,
        feedback: Optional[str] = None,
    ) -> dict:
        """Resume workflow after user confirmation.

        Args:
            thread_id: Thread ID from initial run
            approved: Whether user approved the plan
            modifications: Optional plan modifications
            feedback: Optional user feedback

        Returns:
            Final state with response
        """
        if not self.enable_confirmation:
            raise RuntimeError("Confirmation is not enabled for this workflow")

        from finagent.agents.plan_execute.confirmation import (
            PlanConfirmationResponse,
            PlanModification,
        )

        # Create response
        response = PlanConfirmationResponse(
            approved=approved,
            modifications=(
                PlanModification(**modifications) if modifications else None
            ),
            user_feedback=feedback,
        )

        # Process response to get state update
        config = {"configurable": {"thread_id": thread_id}}

        # Get current state
        current_state = await self.graph.aget_state(config)

        # Update state with confirmation response
        state_update = self.confirmation_handler.process_confirmation_response(
            current_state.values, response
        )

        # Update the state
        await self.graph.aupdate_state(config, state_update)

        # Resume execution
        result = await self.graph.ainvoke(None, config)

        return result

    async def stream(self, query: str, thread_id: Optional[str] = None):
        """Stream the workflow execution.

        Args:
            query: User's research query
            thread_id: Optional thread ID for confirmation flow

        Yields:
            Progress updates and final result
        """
        initial_state: PlanExecuteState = {
            "input": query,
            "query_insight": None,
            "plan": None,
            "past_steps": [],
            "response": None,
            "scratchpad": [],
            # Confirmation fields
            "confirmation_request": None,
            "plan_approved": None,
            "user_modifications": None,
            "user_feedback": None,
            "confirmation_requested_at": None,
            "confirmation_received_at": None,
        }

        if self.enable_confirmation and thread_id:
            config = {"configurable": {"thread_id": thread_id}}
            async for event in self.graph.astream(initial_state, config):
                for node_name, state_update in event.items():
                    yield {
                        "node": node_name,
                        "update": state_update,
                        "is_interrupt": node_name == "plan_confirmation",
                    }
        else:
            async for event in self.graph.astream(initial_state):
                for node_name, state_update in event.items():
                    yield {
                        "node": node_name,
                        "update": state_update,
                        "is_interrupt": False,
                    }

    def get_confirmation_request(self, state: dict) -> Optional[dict]:
        """Get the confirmation request from state.

        Args:
            state: Current workflow state

        Returns:
            Confirmation request dict or None
        """
        return state.get("confirmation_request")
