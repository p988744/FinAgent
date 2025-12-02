"""UI callback interface for sending progress updates during query execution."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from finagent.models.answers import LegalAnswer
from finagent.models.citations import LegalCitation
from finagent.models.queries import Query
from finagent.models.resolution_plan import ResolutionPlan
from finagent.models.todo_item import TodoItem

logger = logging.getLogger(__name__)


class UICallback(ABC):
    """
    Abstract base class for UI callback handlers.

    Implementations can provide CLI, web UI, or API progress updates.
    """

    @abstractmethod
    async def on_analysis_start(self, query: Query):
        """
        Called when query analysis starts.

        Args:
            query: The user's query
        """
        pass

    @abstractmethod
    async def on_analysis_complete(self, analysis: dict[str, Any]):
        """
        Called when query analysis completes.

        Args:
            analysis: Analysis results containing intent, entities, complexity, etc.
        """
        pass

    @abstractmethod
    async def on_clarification_request(self, questions: list[str]) -> str | None:
        """
        Request clarification from the user.

        Args:
            questions: List of clarification questions

        Returns:
            User's clarification response or None if skipped
        """
        pass

    @abstractmethod
    async def on_plan_created(self, plan: ResolutionPlan):
        """
        Called when resolution plan is created.

        Args:
            plan: The execution plan
        """
        pass

    @abstractmethod
    async def on_todo_list_created(self, todos: list[TodoItem]):
        """
        Called when todo list is created.

        Args:
            todos: List of todo items
        """
        pass

    @abstractmethod
    async def on_todo_started(self, todo: TodoItem):
        """
        Called when a todo item starts execution.

        Args:
            todo: The todo item that started
        """
        pass

    @abstractmethod
    async def on_todo_progress(self, todo: TodoItem, percentage: int, message: str = ""):
        """
        Called when a todo item's progress updates.

        Args:
            todo: The todo item
            percentage: Progress percentage (0-100)
            message: Optional progress message
        """
        pass

    @abstractmethod
    async def on_todo_completed(self, todo: TodoItem):
        """
        Called when a todo item completes.

        Args:
            todo: The completed todo item
        """
        pass

    @abstractmethod
    async def on_todo_failed(self, todo: TodoItem, error: str):
        """
        Called when a todo item fails.

        Args:
            todo: The failed todo item
            error: Error message
        """
        pass

    @abstractmethod
    async def on_retrieval_result(self, strategy: str, count: int, total_chunks: int):
        """
        Called when retrieval completes for a strategy.

        Args:
            strategy: Retrieval strategy used (vector, concept, etc.)
            count: Number of documents found
            total_chunks: Total number of chunks retrieved
        """
        pass

    @abstractmethod
    async def on_answer_generation_start(self):
        """Called when answer synthesis starts."""
        pass

    @abstractmethod
    async def on_citations_formatted(self, citations: list[LegalCitation]):
        """
        Called when citations are formatted.

        Args:
            citations: List of formatted citations
        """
        pass

    @abstractmethod
    async def on_answer_complete(self, answer: LegalAnswer):
        """
        Called when final answer is ready.

        Args:
            answer: The generated legal answer
        """
        pass

    @abstractmethod
    async def on_error(self, error: str, context: dict[str, Any] | None = None):
        """
        Called when an error occurs.

        Args:
            error: Error message
            context: Optional context information
        """
        pass


class NoOpCallback(UICallback):
    """
    No-op callback that does nothing.

    Useful for testing or when UI updates are not needed.
    """

    async def on_analysis_start(self, query: Query):
        """No-op."""
        pass

    async def on_analysis_complete(self, analysis: dict[str, Any]):
        """No-op."""
        pass

    async def on_clarification_request(self, questions: list[str]) -> str | None:
        """No-op."""
        return None

    async def on_plan_created(self, plan: ResolutionPlan):
        """No-op."""
        pass

    async def on_todo_list_created(self, todos: list[TodoItem]):
        """No-op."""
        pass

    async def on_todo_started(self, todo: TodoItem):
        """No-op."""
        pass

    async def on_todo_progress(self, todo: TodoItem, percentage: int, message: str = ""):
        """No-op."""
        pass

    async def on_todo_completed(self, todo: TodoItem):
        """No-op."""
        pass

    async def on_todo_failed(self, todo: TodoItem, error: str):
        """No-op."""
        pass

    async def on_retrieval_result(self, strategy: str, count: int, total_chunks: int):
        """No-op."""
        pass

    async def on_answer_generation_start(self):
        """No-op."""
        pass

    async def on_citations_formatted(self, citations: list[LegalCitation]):
        """No-op."""
        pass

    async def on_answer_complete(self, answer: LegalAnswer):
        """No-op."""
        pass

    async def on_error(self, error: str, context: dict[str, Any] | None = None):
        """No-op."""
        pass


class LoggingCallback(UICallback):
    """
    Logging callback that outputs to Python logger.

    Useful for debugging and server-side logging.
    """

    def __init__(self, logger_instance: logging.Logger | None = None):
        """Initialize with optional logger instance."""
        self.logger = logger_instance or logger

    async def on_analysis_start(self, query: Query):
        """Log analysis start."""
        self.logger.info(f"🔍 Analyzing query: {query.text[:100]}...")

    async def on_analysis_complete(self, analysis: dict[str, Any]):
        """Log analysis completion."""
        intent = analysis.get("intent", "unknown")
        complexity = analysis.get("complexity", "unknown")
        self.logger.info(f"✓ Analysis complete - Intent: {intent}, Complexity: {complexity}")

    async def on_clarification_request(self, questions: list[str]) -> str | None:
        """Log clarification request."""
        self.logger.info(f"❓ Clarification needed: {len(questions)} questions")
        return None

    async def on_plan_created(self, plan: ResolutionPlan):
        """Log plan creation."""
        self.logger.info(f"📋 Plan created: {plan.strategy} (~{plan.estimated_time_seconds}s)")

    async def on_todo_list_created(self, todos: list[TodoItem]):
        """Log todo list creation."""
        self.logger.info(f"📝 Todo list created: {len(todos)} tasks")

    async def on_todo_started(self, todo: TodoItem):
        """Log todo start."""
        self.logger.info(f"▶️  Started: {todo.content}")

    async def on_todo_progress(self, todo: TodoItem, percentage: int, message: str = ""):
        """Log todo progress."""
        self.logger.debug(f"⏳ Progress: {todo.content} ({percentage}%) {message}")

    async def on_todo_completed(self, todo: TodoItem):
        """Log todo completion."""
        self.logger.info(f"✓ Completed: {todo.content}")

    async def on_todo_failed(self, todo: TodoItem, error: str):
        """Log todo failure."""
        self.logger.error(f"✗ Failed: {todo.content} - {error}")

    async def on_retrieval_result(self, strategy: str, count: int, total_chunks: int):
        """Log retrieval result."""
        self.logger.info(f"📚 Retrieved: {count} docs ({total_chunks} chunks) via {strategy}")

    async def on_answer_generation_start(self):
        """Log answer generation start."""
        self.logger.info("🤖 Generating answer...")

    async def on_citations_formatted(self, citations: list[LegalCitation]):
        """Log citations."""
        self.logger.info(f"📖 Formatted {len(citations)} citations")

    async def on_answer_complete(self, answer: LegalAnswer):
        """Log answer completion."""
        confidence = answer.confidence_level.value if answer.confidence_level else "unknown"
        self.logger.info(f"✨ Answer complete - Confidence: {confidence}")

    async def on_error(self, error: str, context: dict[str, Any] | None = None):
        """Log error."""
        self.logger.error(f"❌ Error: {error}")
        if context:
            self.logger.debug(f"Context: {context}")
