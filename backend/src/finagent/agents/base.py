"""Base agent class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.

    All specialized agents (Planning, Action, Answer, Validation) inherit from this.
    """

    def __init__(self, name: str, model: Optional[str] = None):
        """
        Initialize base agent.

        Args:
            name: Agent name
            model: LLM model name (optional, uses config default if not provided)
        """
        self.name = name
        self.model = model
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary function.

        Args:
            input_data: Input data for the agent

        Returns:
            Output data from the agent
        """
        pass

    def log_execution(self, action: str, details: Optional[str] = None):
        """Log agent execution details."""
        log_msg = f"[{self.name}] {action}"
        if details:
            log_msg += f": {details}"
        self.logger.info(log_msg)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
