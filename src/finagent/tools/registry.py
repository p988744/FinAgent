"""Central registry for all available tools."""

import logging
from typing import Any

from finagent.tools.base import BaseTool, ToolCapability

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._capabilities: dict[str, ToolCapability] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool."""
        capability = tool.get_capability()
        self._tools[capability.name] = tool
        self._capabilities[capability.name] = capability
        logger.info(f"Registered tool: {capability.name}")

    def get_tool(self, name: str) -> BaseTool | None:
        """Get tool by name."""
        return self._tools.get(name)

    def get_all_capabilities(self) -> dict[str, ToolCapability]:
        """Get all tool capabilities for planning."""
        return self._capabilities.copy()

    def find_tools_for_intent(self, intent: str) -> list[str]:
        """Find tools that support a given intent."""
        matching_tools = []
        for name, capability in self._capabilities.items():
            if intent in capability.supported_intents:
                matching_tools.append(name)
        return matching_tools

    def find_tools_for_query(self, query_features: dict[str, Any]) -> list[str]:
        """Find tools that can handle query with given features."""
        matching_tools = []
        for name, capability in self._capabilities.items():
            # Check if all required features are present
            if all(
                feature in query_features for feature in capability.required_features
            ):
                matching_tools.append(name)
        return matching_tools

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def count(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)


# Global registry instance
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry
