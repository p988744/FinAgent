"""LangGraph workflow for multi-agent legal research."""

import logging
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from finagent.agents.action_agent import ActionAgent
from finagent.agents.answer_agent import AnswerAgent
from finagent.agents.planning_agent import PlanningAgent
from finagent.agents.query_analysis_agent import (
    QueryAnalysisAgent,
    should_request_clarification,
)
from finagent.agents.reference_guard import ReferenceGuard
from finagent.agents.state import AgentState
from finagent.agents.validation_agent import ValidationAgent
from finagent.document_processing.retriever import DocumentRetriever

logger = logging.getLogger(__name__)


class LegalResearchWorkflow:
    """
    LangGraph workflow orchestrating multi-agent legal research.

    Workflow:
        START → Query Analysis → [Clarification?] → Planning → Action → Validation → Reference Guard → [Decision] → Answer → END
                                       ↓                                    ↑                              ↓
                                 Human-in-Loop                             └────────── Re-Search ←────────┘
                                       ↓
                                  [Enrichment] → Planning

    Agents:
        0. Query Analysis Agent: Analyzes query and requests clarification if needed
        1. Planning Agent: Decomposes query into research tasks
        2. Action Agent: Executes RAG retrieval with adaptive strategies
        3. Validation Agent: Validates citations and coverage
        4. Reference Guard: Decides if re-search is needed
        5. Answer Agent: Synthesizes final answer with LLM
    """

    def __init__(
        self,
        retriever: DocumentRetriever,
        max_search_iterations: int = 2,
        clarification_handler=None,
        ui_callback=None,
    ):
        """
        Initialize workflow with agents.

        Args:
            retriever: Document retriever for RAG
            max_search_iterations: Maximum re-search iterations (default: 2)
            clarification_handler: Optional callback for requesting user clarification
                                   Signature: async def handler(clarification_request) -> str
            ui_callback: Optional UICallback for progress updates
        """
        self.retriever = retriever
        self.max_search_iterations = max_search_iterations
        self.clarification_handler = clarification_handler
        self.ui_callback = ui_callback

        # Initialize agents with UI callback
        self.query_analysis_agent = QueryAnalysisAgent(ui_callback=ui_callback)
        self.planning_agent = PlanningAgent(ui_callback=ui_callback)
        self.action_agent = ActionAgent(retriever=retriever, ui_callback=ui_callback)
        self.validation_agent = ValidationAgent(ui_callback=ui_callback)
        self.reference_guard = ReferenceGuard(max_iterations=max_search_iterations)
        self.answer_agent = AnswerAgent(ui_callback=ui_callback)

        # Build workflow graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph workflow with query analysis and re-search capability.

        Returns:
            Compiled StateGraph
        """
        # Create graph with AgentState schema
        workflow = StateGraph(AgentState)

        # Add agent nodes
        workflow.add_node("query_analysis", self._query_analysis_node)
        workflow.add_node("human_clarification", self._human_clarification_node)
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("action", self._action_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("reference_guard", self._reference_guard_node)
        workflow.add_node("answer", self._answer_node)

        # Define edges
        workflow.add_edge(START, "query_analysis")

        # Conditional edge from query analysis
        workflow.add_conditional_edges(
            "query_analysis",
            lambda state: should_request_clarification(state),
            {
                "clarify": "human_clarification",  # Request clarification
                "proceed": "planning",  # Skip clarification
            },
        )

        # From human clarification, always go to planning (enriched or not)
        workflow.add_edge("human_clarification", "planning")

        # Rest of the workflow
        workflow.add_edge("planning", "action")
        workflow.add_edge("action", "validation")
        workflow.add_edge("validation", "reference_guard")

        # Conditional edge from reference guard
        workflow.add_conditional_edges(
            "reference_guard",
            self._decide_next_step,
            {
                "research": "action",  # Loop back to action for re-search
                "answer": "answer",  # Proceed to answer
            },
        )

        workflow.add_edge("answer", END)

        # Compile graph
        compiled = workflow.compile()

        logger.info("LangGraph workflow with query analysis and re-search compiled successfully")
        return compiled

    async def _query_analysis_node(self, state: AgentState) -> AgentState:
        """
        Query analysis agent node.

        Args:
            state: Current state

        Returns:
            Updated state with clarification request (if needed)
        """
        logger.info("Executing query analysis node")
        # QueryAnalysisAgent.analyze_query is likely sync, but we can wrap it if needed
        # or just call it directly if it doesn't block significantly.
        # If it does I/O, it should be async. Checking if it's async...
        # Assuming it's sync for now as I haven't checked it, but it's safe to call sync from async.
        return await self.query_analysis_agent.analyze_query(state)

    async def _human_clarification_node(self, state: AgentState) -> AgentState:
        """
        Human-in-the-loop clarification node.

        This node pauses workflow execution and requests clarification from user.

        Args:
            state: Current state with clarification request

        Returns:
            Updated state with clarification response
        """
        logger.info("Executing human clarification node")

        # Call clarification handler if provided
        if self.clarification_handler:
            try:
                # Handler should be async
                clarification_response = await self.clarification_handler(state.get("clarification_request"))
                state["clarification_response"] = clarification_response

                # Enrich query with clarification
                if clarification_response and clarification_response.strip():
                    state = self.query_analysis_agent.enrich_query_with_clarification(state)
                else:
                    state["processing_steps"].append(
                        "Human Clarification: 使用者略過澄清，繼續原查詢"
                    )

            except Exception as e:
                logger.error(f"Clarification handler failed: {e}")
                state["processing_steps"].append(f"Human Clarification: 失敗 ({str(e)})")
                state["clarification_response"] = None
        else:
            # No handler provided, skip clarification
            logger.warning("No clarification handler provided, skipping")
            state["processing_steps"].append("Human Clarification: 未設定處理器，略過")
            state["clarification_response"] = None

        return state

    async def _planning_node(self, state: AgentState) -> AgentState:
        """
        Planning agent node.

        Args:
            state: Current state

        Returns:
            Updated state with plan
        """
        logger.info("Executing planning node")
        # PlanningAgent.plan is likely sync
        return await self.planning_agent.plan(state)

    async def _action_node(self, state: AgentState) -> AgentState:
        """
        Action agent node.

        Args:
            state: Current state

        Returns:
            Updated state with retrieved documents
        """
        logger.info("Executing action node")
        return await self.action_agent.execute(state)

    async def _validation_node(self, state: AgentState) -> AgentState:
        """
        Validation agent node.

        Args:
            state: Current state

        Returns:
            Updated state with validation results
        """
        logger.info("Executing validation node")
        return await self.validation_agent.validate(state)

    async def _reference_guard_node(self, state: AgentState) -> AgentState:
        """
        Reference guard node.

        Args:
            state: Current state

        Returns:
            Updated state with re-search decision
        """
        logger.info("Executing reference guard node")
        # ReferenceGuard.evaluate is likely sync
        return self.reference_guard.evaluate(state)

    def _decide_next_step(self, state: AgentState) -> Literal["research", "answer"]:
        """
        Decide next node after reference guard.

        Args:
            state: Current state

        Returns:
            "research" to loop back to action, "answer" to proceed to answer
        """
        current_iteration = state.get("search_iteration", 0)
        validation_passed = state.get("validation_passed", True)
        validation_issues = state.get("validation_issues", [])
        has_documents = len(state.get("retrieved_chunks", [])) > 0

        # Use reference guard logic to decide
        should_research = self.reference_guard._should_research(
            current_iteration=current_iteration,
            validation_passed=validation_passed,
            validation_issues=validation_issues,
            has_documents=has_documents,
        )

        if should_research:
            logger.info("Decision: Re-search")
            return "research"
        else:
            logger.info("Decision: Proceed to answer")
            return "answer"

    async def _answer_node(self, state: AgentState) -> AgentState:
        """
        Answer agent node.

        Args:
            state: Current state

        Returns:
            Updated state with final answer
        """
        logger.info("Executing answer node")
        return await self.answer_agent.synthesize(state)

    async def run(self, state: AgentState) -> dict[str, Any]:
        """
        Run the workflow.

        Args:
            state: Initial state with query

        Returns:
            Final state with answer
        """
        logger.info("Starting LangGraph workflow")

        try:
            # Invoke compiled graph
            # ainvoke is the async version
            final_state = await self.graph.ainvoke(state)

            logger.info("Workflow completed successfully")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise

    async def stream(self, state: AgentState, enable_demo_delay: bool = False):
        """
        Stream the workflow execution, yielding events for each node.

        Args:
            state: Initial state with query
            enable_demo_delay: If True, add delays after each node for demo/testing purposes.
                               This makes real-time updates more visually obvious.
                               NOT recommended for production use.

        Yields:
            Tuples of (node_name, state_update) for each step
        """
        logger.info(f"Starting LangGraph workflow with streaming (demo_delay={enable_demo_delay})")

        # Demo delay configuration (seconds) for testing real-time updates
        demo_delays = {
            "query_analysis": 2,
            "planning": 3,
            "action": 2,
            "validation": 1,
            "reference_guard": 1,
            "answer": 5,
            "human_clarification": 2,
        }

        try:
            # Stream graph execution - yields events for each node
            # astream is the async generator version
            async for event in self.graph.astream(state, stream_mode="updates"):
                # event is a dict with node name as key and state update as value
                for node_name, state_update in event.items():
                    logger.info(f"Streaming node completed: {node_name}")
                    yield node_name, state_update

                    # Add demo delay if enabled (for testing/verification)
                    if enable_demo_delay and node_name in demo_delays:
                        delay = demo_delays[node_name]
                        logger.debug(f"Demo delay: sleeping {delay}s after {node_name}")
                        import asyncio
                        await asyncio.sleep(delay)

            logger.info("Workflow streaming completed successfully")

        except Exception as e:
            logger.error(f"Workflow streaming failed: {e}", exc_info=True)
            raise
