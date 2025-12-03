"""Plan-and-Execute workflow module.

Enhanced LangGraph workflow with human-in-the-loop confirmation.
Flow:
1. Query Analyzer - Analyze user query
2. Planner - Create research plan
3. Plan Confirmation - Wait for user approval (optional)
4. Execute Tasks - Execute plan tasks
5. Replanner - Review and replan if needed
6. Reporter - Generate final report
"""

from finagent.agents.plan_execute.confirmation import (
    ConfirmationHandler,
    PlanConfirmationRequest,
    PlanConfirmationResponse,
    PlanModification,
)
from finagent.agents.plan_execute.executor import ExecutorAgent
from finagent.agents.plan_execute.graph import PlanExecuteWorkflow
from finagent.agents.plan_execute.models import (
    Plan,
    PlanExecuteState,
    PlanTask,
    QueryInsight,
)
from finagent.agents.plan_execute.planner import PlannerAgent
from finagent.agents.plan_execute.query_analyzer import QueryAnalyzerAgent
from finagent.agents.plan_execute.replanner import ReplannerAgent
from finagent.agents.plan_execute.reporter import ReporterAgent

__all__ = [
    # Main workflow
    "PlanExecuteWorkflow",
    # State and models
    "PlanExecuteState",
    "Plan",
    "PlanTask",
    "QueryInsight",
    # Confirmation
    "ConfirmationHandler",
    "PlanConfirmationRequest",
    "PlanConfirmationResponse",
    "PlanModification",
    # Agents
    "PlannerAgent",
    "ExecutorAgent",
    "ReplannerAgent",
    "ReporterAgent",
    "QueryAnalyzerAgent",
]
