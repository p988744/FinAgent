"""LangGraph workflow for multi-agent legal research."""

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from finagent.agents.action_agent import ActionAgent
from finagent.agents.answer_agent import AnswerAgent
from finagent.agents.planning_agent import PlanningAgent
from finagent.agents.state import AgentState
from finagent.agents.validation_agent import ValidationAgent
from finagent.document_processing.retriever import DocumentRetriever

logger = logging.getLogger(__name__)


class LegalResearchWorkflow:
    """
    LangGraph workflow orchestrating multi-agent legal research.

    Workflow:
        START → Planning → Action → Validation → Answer → END

    Agents:
        1. Planning Agent: Decomposes query into research tasks
        2. Action Agent: Executes RAG retrieval
        3. Validation Agent: Validates citations and coverage
        4. Answer Agent: Synthesizes final answer with LLM
    """

    def __init__(self, retriever: DocumentRetriever):
        """
        Initialize workflow with agents.

        Args:
            retriever: Document retriever for RAG
        """
        self.retriever = retriever

        # Initialize agents
        self.planning_agent = PlanningAgent()
        self.action_agent = ActionAgent(retriever=retriever)
        self.validation_agent = ValidationAgent()
        self.answer_agent = AnswerAgent()

        # Build workflow graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph workflow.

        Returns:
            Compiled StateGraph
        """
        # Create graph with AgentState schema
        workflow = StateGraph(AgentState)

        # Add agent nodes
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("action", self._action_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("answer", self._answer_node)

        # Define edges (linear workflow for MVP)
        workflow.add_edge(START, "planning")
        workflow.add_edge("planning", "action")
        workflow.add_edge("action", "validation")
        workflow.add_edge("validation", "answer")
        workflow.add_edge("answer", END)

        # Compile graph
        compiled = workflow.compile()

        logger.info("LangGraph workflow compiled successfully")
        return compiled

    def _planning_node(self, state: AgentState) -> AgentState:
        """
        Planning agent node.

        Args:
            state: Current state

        Returns:
            Updated state with plan
        """
        logger.info("Executing planning node")
        return self.planning_agent.plan(state)

    def _action_node(self, state: AgentState) -> AgentState:
        """
        Action agent node.

        Args:
            state: Current state

        Returns:
            Updated state with retrieved documents
        """
        logger.info("Executing action node")
        return self.action_agent.execute(state)

    def _validation_node(self, state: AgentState) -> AgentState:
        """
        Validation agent node.

        Args:
            state: Current state

        Returns:
            Updated state with validation results
        """
        logger.info("Executing validation node")
        return self.validation_agent.validate(state)

    def _answer_node(self, state: AgentState) -> AgentState:
        """
        Answer agent node.

        Args:
            state: Current state

        Returns:
            Updated state with final answer
        """
        logger.info("Executing answer node")
        return self.answer_agent.synthesize(state)

    def run(self, state: AgentState) -> dict[str, Any]:
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
            final_state = self.graph.invoke(state)

            logger.info("Workflow completed successfully")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise
