"""Human-in-the-loop plan confirmation handler.

Handles user confirmation of research plans before execution,
allowing users to approve, reject, or modify plans.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from finagent.agents.plan_execute.models import Plan, PlanExecuteState, PlanTask

logger = logging.getLogger(__name__)


class PlanModification(BaseModel):
    """User modification to a plan."""

    add_tasks: list[dict] = Field(
        default_factory=list,
        description="Tasks to add to the plan",
    )
    remove_task_ids: list[int] = Field(
        default_factory=list,
        description="IDs of tasks to remove",
    )
    modify_tasks: list[dict] = Field(
        default_factory=list,
        description="Tasks to modify (with id and new fields)",
    )


class PlanConfirmationRequest(BaseModel):
    """Request sent to user for plan confirmation."""

    plan: Plan
    query: str
    query_insight: dict | None = None
    task_count: int
    estimated_time_seconds: int = Field(default=30)
    requested_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class PlanConfirmationResponse(BaseModel):
    """User's response to plan confirmation request."""

    approved: bool
    modifications: PlanModification | None = None
    user_feedback: str | None = None
    responded_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ConfirmationHandler:
    """Handles plan confirmation flow with human-in-the-loop.

    This handler:
    1. Prepares plan confirmation requests
    2. Processes user responses (approve/reject/modify)
    3. Applies modifications to plans
    """

    def __init__(self):
        """Initialize the confirmation handler."""
        self.pending_confirmations: dict[str, PlanConfirmationRequest] = {}

    def prepare_confirmation_request(
        self, state: PlanExecuteState
    ) -> PlanConfirmationRequest:
        """Prepare a plan confirmation request from the current state.

        Args:
            state: Current workflow state with plan

        Returns:
            Confirmation request to send to user
        """
        plan = state.get("plan")
        if not plan:
            plan = Plan(tasks=[])

        # Ensure plan is a Plan object
        if isinstance(plan, dict):
            plan = Plan(**plan)

        # Calculate estimated time (rough estimate)
        task_count = len(plan.tasks)
        estimated_time = task_count * 15  # ~15 seconds per task

        request = PlanConfirmationRequest(
            plan=plan,
            query=state["input"],
            query_insight=(
                state.get("query_insight").model_dump()
                if hasattr(state.get("query_insight"), "model_dump")
                else state.get("query_insight")
            ),
            task_count=task_count,
            estimated_time_seconds=estimated_time,
        )

        logger.info(
            f"Prepared confirmation request: {task_count} tasks, "
            f"estimated {estimated_time}s"
        )

        return request

    def process_confirmation_response(
        self, state: PlanExecuteState, response: PlanConfirmationResponse
    ) -> dict:
        """Process user's confirmation response.

        Args:
            state: Current workflow state
            response: User's confirmation response

        Returns:
            State update with confirmation result
        """
        logger.info(f"Processing confirmation: approved={response.approved}")

        if response.approved:
            # Plan approved, proceed with execution
            return {
                "plan_approved": True,
                "user_modifications": None,
                "confirmation_requested_at": None,
                "confirmation_received_at": response.responded_at,
            }

        # Plan rejected or modified
        if response.modifications:
            # Apply modifications to the plan
            modified_plan = self._apply_modifications(
                state.get("plan"), response.modifications
            )
            return {
                "plan_approved": False,
                "plan": modified_plan,
                "user_modifications": response.modifications.model_dump(),
                "confirmation_requested_at": None,
                "confirmation_received_at": response.responded_at,
            }

        # Plan rejected without modifications
        return {
            "plan_approved": False,
            "user_modifications": None,
            "user_feedback": response.user_feedback,
            "confirmation_requested_at": None,
            "confirmation_received_at": response.responded_at,
        }

    def _apply_modifications(
        self, plan: Any, modifications: PlanModification
    ) -> Plan:
        """Apply user modifications to a plan.

        Args:
            plan: Original plan
            modifications: User's modifications

        Returns:
            Modified plan
        """
        # Ensure plan is a Plan object
        if isinstance(plan, dict):
            plan = Plan(**plan)
        elif plan is None:
            plan = Plan(tasks=[])

        tasks = list(plan.tasks)

        # Remove tasks
        if modifications.remove_task_ids:
            tasks = [t for t in tasks if t.id not in modifications.remove_task_ids]
            logger.info(f"Removed tasks: {modifications.remove_task_ids}")

        # Modify existing tasks
        for mod in modifications.modify_tasks:
            task_id = mod.get("id")
            if task_id is not None:
                for i, task in enumerate(tasks):
                    if task.id == task_id:
                        # Update task fields
                        for key, value in mod.items():
                            if key != "id" and hasattr(task, key):
                                setattr(task, key, value)
                        tasks[i] = task
                        logger.info(f"Modified task {task_id}")
                        break

        # Add new tasks
        next_id = max((t.id for t in tasks), default=0) + 1
        for task_data in modifications.add_tasks:
            new_task = PlanTask(
                id=task_data.get("id", next_id),
                description=task_data.get("description", ""),
                tool=task_data.get("tool", "retriever"),
                args=task_data.get("args", {}),
                status="pending",
            )
            tasks.append(new_task)
            logger.info(f"Added task {new_task.id}: {new_task.description[:30]}...")
            next_id += 1

        # Renumber tasks if needed
        for i, task in enumerate(tasks, 1):
            task.id = i

        return Plan(tasks=tasks)

    def create_confirmation_node(self, state: PlanExecuteState) -> dict:
        """Node function for plan confirmation (before interrupt).

        This node prepares the confirmation request and marks the state
        as awaiting confirmation. The actual interrupt is handled by
        LangGraph's interrupt_before mechanism.

        Args:
            state: Current workflow state

        Returns:
            State update with confirmation request info
        """
        request = self.prepare_confirmation_request(state)

        return {
            "confirmation_request": request.model_dump(),
            "confirmation_requested_at": request.requested_at,
            "plan_approved": None,  # Awaiting response
        }

    def route_after_confirmation(self, state: PlanExecuteState) -> str:
        """Determine next node after confirmation response.

        Args:
            state: Current workflow state with confirmation response

        Returns:
            Next node name: "execute_task" or "planner"
        """
        plan_approved = state.get("plan_approved")

        if plan_approved is None:
            # Still awaiting confirmation (should not happen after interrupt)
            logger.warning("Route called but plan_approved is None")
            return "plan_confirmation"

        if plan_approved:
            # Plan approved, proceed to execution
            logger.info("Plan approved, routing to execute_task")
            return "execute_task"
        else:
            # Plan rejected or modified, go back to planner
            logger.info("Plan modified/rejected, routing to planner")
            return "planner"
