"""Tests for tool registry system."""

import pytest

from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput
from finagent.tools.registry import ToolRegistry


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, name: str, supported_intents: list[str], required_features: list[str] | None = None):
        self.name = name
        self.supported_intents = supported_intents
        self.required_features = required_features or []

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name=self.name,
            description=f"Mock tool: {self.name}",
            supported_intents=self.supported_intents,
            required_features=self.required_features,
            execution_time_estimate="fast",
            cost_estimate="low",
            limitations=[]
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        return ToolOutput(
            success=True,
            results=[{"mock": "result"}],
            metadata={"tool": self.name}
        )

    def validate_input(self, tool_input: ToolInput) -> bool:
        return True


def test_registry_register_tool():
    """Test tool registration."""
    registry = ToolRegistry()
    tool = MockTool("test_tool", ["general_search"])

    registry.register(tool)

    assert registry.count() == 1
    assert "test_tool" in registry.list_tools()


def test_registry_get_tool():
    """Test getting tool by name."""
    registry = ToolRegistry()
    tool = MockTool("test_tool", ["general_search"])
    registry.register(tool)

    retrieved_tool = registry.get_tool("test_tool")
    assert retrieved_tool is not None
    assert retrieved_tool.get_capability().name == "test_tool"


def test_registry_get_nonexistent_tool():
    """Test getting non-existent tool returns None."""
    registry = ToolRegistry()
    tool = registry.get_tool("nonexistent")
    assert tool is None


def test_registry_get_all_capabilities():
    """Test getting all tool capabilities."""
    registry = ToolRegistry()
    tool1 = MockTool("tool1", ["general_search"])
    tool2 = MockTool("tool2", ["temporal"])

    registry.register(tool1)
    registry.register(tool2)

    capabilities = registry.get_all_capabilities()
    assert len(capabilities) == 2
    assert "tool1" in capabilities
    assert "tool2" in capabilities


def test_registry_find_tools_for_intent():
    """Test finding tools by intent."""
    registry = ToolRegistry()
    tool1 = MockTool("vector_search", ["general_search", "semantic_search"])
    tool2 = MockTool("metadata_search", ["temporal", "entity_specific"])
    tool3 = MockTool("hybrid_search", ["general_search", "temporal"])

    registry.register(tool1)
    registry.register(tool2)
    registry.register(tool3)

    # Find tools for general_search intent
    general_tools = registry.find_tools_for_intent("general_search")
    assert len(general_tools) == 2
    assert "vector_search" in general_tools
    assert "hybrid_search" in general_tools

    # Find tools for temporal intent
    temporal_tools = registry.find_tools_for_intent("temporal")
    assert len(temporal_tools) == 2
    assert "metadata_search" in temporal_tools
    assert "hybrid_search" in temporal_tools

    # Find tools for non-existent intent
    no_tools = registry.find_tools_for_intent("nonexistent")
    assert len(no_tools) == 0


def test_registry_find_tools_for_query():
    """Test finding tools by query features."""
    registry = ToolRegistry()
    tool1 = MockTool("vector_search", ["general_search"], required_features=["query"])
    tool2 = MockTool("metadata_search", ["temporal"], required_features=["entity", "date_from"])
    tool3 = MockTool("read_file", ["specific_file"], required_features=["filename"])

    registry.register(tool1)
    registry.register(tool2)
    registry.register(tool3)

    # Query with only "query" feature
    query_features_1 = {"query": "test"}
    tools_1 = registry.find_tools_for_query(query_features_1)
    assert len(tools_1) == 1
    assert "vector_search" in tools_1

    # Query with entity and date_from features
    query_features_2 = {"entity": "玉山銀行", "date_from": "2020-01-01"}
    tools_2 = registry.find_tools_for_query(query_features_2)
    assert len(tools_2) == 1
    assert "metadata_search" in tools_2

    # Query with all features
    query_features_3 = {"query": "test", "entity": "玉山銀行", "date_from": "2020-01-01", "filename": "test.txt"}
    tools_3 = registry.find_tools_for_query(query_features_3)
    assert len(tools_3) == 3  # All tools can handle their required features


def test_registry_multiple_registrations():
    """Test registering same tool multiple times (should update, not duplicate)."""
    registry = ToolRegistry()
    tool1 = MockTool("test_tool", ["general_search"])
    tool2 = MockTool("test_tool", ["temporal"])  # Same name, different config

    registry.register(tool1)
    assert registry.count() == 1

    registry.register(tool2)
    assert registry.count() == 1  # Should still be 1, not 2

    # Latest registration should win
    retrieved_tool = registry.get_tool("test_tool")
    capability = retrieved_tool.get_capability()
    assert "temporal" in capability.supported_intents


@pytest.mark.asyncio
async def test_tool_execute():
    """Test tool execution."""
    tool = MockTool("test_tool", ["general_search"])
    tool_input = ToolInput(query="test query", parameters={})

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 1
    assert output.results[0]["mock"] == "result"
    assert output.metadata["tool"] == "test_tool"


def test_tool_validate_input():
    """Test tool input validation."""
    tool = MockTool("test_tool", ["general_search"])
    tool_input = ToolInput(query="test query", parameters={})

    assert tool.validate_input(tool_input) is True
