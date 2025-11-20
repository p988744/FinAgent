"""LangGraph workflow for the Plan-and-Execute agent flow."""

from langgraph.graph import END, StateGraph

from finagent.agents.plan_execute.executor import ExecutorAgent
from finagent.agents.plan_execute.models import PlanExecuteState
from finagent.agents.plan_execute.planner import PlannerAgent
from finagent.agents.plan_execute.replanner import ReplannerAgent
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever


class PlanExecuteWorkflow:
    """Workflow for the Plan-and-Execute agent."""

    def __init__(self, retriever: DocumentRetriever, hard_searcher: HardSearcher):
        """Initialize the workflow."""
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(retriever=retriever, hard_searcher=hard_searcher)
        self.replanner = ReplannerAgent()
        
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(PlanExecuteState)
        
        # Add nodes
        workflow.add_node("planner", self.planner.plan)
        workflow.add_node("executor", self.executor.execute)
        workflow.add_node("replanner", self.replanner.replan)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add edges
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "replanner")
        
        # Conditional edge from replanner
        def should_end(state: PlanExecuteState):
            if state.get("response"):
                return END
            else:
                return "executor"
        
        workflow.add_conditional_edges(
            "replanner",
            should_end,
            {
                END: END,
                "executor": "executor",
            },
        )
        
        return workflow.compile()
