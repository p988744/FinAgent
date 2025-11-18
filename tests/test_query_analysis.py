"""Tests for query analyzer and tool selector (Phase 4)."""

import pytest

from finagent.agents.query_analyzer import QueryAnalyzer, QueryAnalysis, QueryIntent
from finagent.agents.tool_selector import ToolSelector


# Query Analyzer Tests


@pytest.mark.asyncio
async def test_query_analyzer_temporal_latest():
    """Test query analyzer for temporal 'latest' queries."""
    analyzer = QueryAnalyzer()

    # Use fallback for testing (no LLM call)
    analysis = analyzer._fallback_analyze("玉山銀行最近一次的罰款紀錄")

    assert analysis.intent == QueryIntent.TEMPORAL
    assert analysis.has_temporal_constraint is True
    assert analysis.temporal_type == "latest"
    assert "玉山銀行" in analysis.entities


@pytest.mark.asyncio
async def test_query_analyzer_comprehensive():
    """Test query analyzer for comprehensive queries."""
    analyzer = QueryAnalyzer()

    analysis = analyzer._fallback_analyze("玉山銀行過去所有的裁罰紀錄")

    assert analysis.intent == QueryIntent.COMPREHENSIVE
    assert analysis.requires_exhaustive_search is True
    assert "玉山銀行" in analysis.entities


@pytest.mark.asyncio
async def test_query_analyzer_specific_file():
    """Test query analyzer for specific file queries."""
    analyzer = QueryAnalyzer()

    analysis = analyzer._fallback_analyze("國泰世華銀行_內線交易_2021.txt 這個檔案的摘要")

    assert analysis.intent == QueryIntent.SPECIFIC_FILE


@pytest.mark.asyncio
async def test_query_analyzer_comparison():
    """Test query analyzer for comparison queries."""
    analyzer = QueryAnalyzer()

    analysis = analyzer._fallback_analyze("玉山銀行與國泰世華銀行的裁罰紀錄比較")

    assert analysis.intent == QueryIntent.COMPARISON
    assert analysis.requires_multi_entity is True
    assert len(analysis.entities) >= 1  # At least one entity detected


@pytest.mark.asyncio
async def test_query_analyzer_general():
    """Test query analyzer for general queries."""
    analyzer = QueryAnalyzer()

    analysis = analyzer._fallback_analyze("洗錢防制裁罰案件")

    assert analysis.intent == QueryIntent.GENERAL_SEARCH


# Tool Selector Tests


@pytest.mark.asyncio
async def test_tool_selector_temporal_latest():
    """Test tool selector for temporal 'latest' queries."""
    selector = ToolSelector()

    analysis = QueryAnalysis(
        intent=QueryIntent.TEMPORAL,
        secondary_intents=[],
        entities=["玉山銀行"],
        has_temporal_constraint=True,
        temporal_type="latest",
        date_range=None,
        has_file_reference=False,
        filename=None,
        complexity="medium",
        requires_exhaustive_search=False,
        requires_multi_entity=False,
        extracted_parameters={},
    )

    # Use fallback for testing
    tools = selector._fallback_select_tools("玉山銀行最近一次的罰款紀錄", analysis)

    assert len(tools) == 1
    assert tools[0]["tool_name"] == "metadata_search"
    assert tools[0]["parameters"]["entity"] == "玉山銀行"


@pytest.mark.asyncio
async def test_tool_selector_comprehensive():
    """Test tool selector for comprehensive queries."""
    selector = ToolSelector()

    analysis = QueryAnalysis(
        intent=QueryIntent.COMPREHENSIVE,
        secondary_intents=[],
        entities=["玉山銀行"],
        has_temporal_constraint=False,
        temporal_type=None,
        date_range=None,
        has_file_reference=False,
        filename=None,
        complexity="medium",
        requires_exhaustive_search=True,
        requires_multi_entity=False,
        extracted_parameters={},
    )

    tools = selector._fallback_select_tools("玉山銀行過去所有的裁罰紀錄", analysis)

    assert len(tools) == 1
    assert tools[0]["tool_name"] == "list_documents"
    assert tools[0]["parameters"]["entity"] == "玉山銀行"


@pytest.mark.asyncio
async def test_tool_selector_specific_file():
    """Test tool selector for specific file queries."""
    selector = ToolSelector()

    analysis = QueryAnalysis(
        intent=QueryIntent.SPECIFIC_FILE,
        secondary_intents=[],
        entities=[],
        has_temporal_constraint=False,
        temporal_type=None,
        date_range=None,
        has_file_reference=True,
        filename="國泰世華銀行_內線交易_2021.txt",
        complexity="simple",
        requires_exhaustive_search=False,
        requires_multi_entity=False,
        extracted_parameters={},
    )

    tools = selector._fallback_select_tools("檔案的摘要", analysis)

    assert len(tools) == 1
    assert tools[0]["tool_name"] == "read_file"
    assert tools[0]["parameters"]["filename"] == "國泰世華銀行_內線交易_2021.txt"


@pytest.mark.asyncio
async def test_tool_selector_comparison():
    """Test tool selector for comparison queries."""
    selector = ToolSelector()

    analysis = QueryAnalysis(
        intent=QueryIntent.COMPARISON,
        secondary_intents=[],
        entities=["玉山銀行", "國泰世華銀行"],
        has_temporal_constraint=False,
        temporal_type=None,
        date_range=None,
        has_file_reference=False,
        filename=None,
        complexity="complex",
        requires_exhaustive_search=False,
        requires_multi_entity=True,
        extracted_parameters={},
    )

    tools = selector._fallback_select_tools("比較", analysis)

    assert len(tools) == 1
    assert tools[0]["tool_name"] == "multi_entity_search"
    assert tools[0]["parameters"]["entities"] == ["玉山銀行", "國泰世華銀行"]


@pytest.mark.asyncio
async def test_tool_selector_hybrid_search():
    """Test tool selector for time range + semantic queries."""
    selector = ToolSelector()

    analysis = QueryAnalysis(
        intent=QueryIntent.TEMPORAL,
        secondary_intents=[],
        entities=["玉山銀行"],
        has_temporal_constraint=True,
        temporal_type="year_range",
        date_range={"from": "2020-01-01", "to": "2020-12-31"},
        has_file_reference=False,
        filename=None,
        complexity="medium",
        requires_exhaustive_search=False,
        requires_multi_entity=False,
        extracted_parameters={},
    )

    tools = selector._fallback_select_tools("2020年洗錢案件", analysis)

    assert len(tools) == 1
    assert tools[0]["tool_name"] == "hybrid_search"
    assert tools[0]["parameters"]["entity"] == "玉山銀行"
    assert "date_from" in tools[0]["parameters"]


@pytest.mark.asyncio
async def test_tool_selector_general_fallback():
    """Test tool selector falls back to vector_search for general queries."""
    selector = ToolSelector()

    analysis = QueryAnalysis(
        intent=QueryIntent.GENERAL_SEARCH,
        secondary_intents=[],
        entities=[],
        has_temporal_constraint=False,
        temporal_type=None,
        date_range=None,
        has_file_reference=False,
        filename=None,
        complexity="simple",
        requires_exhaustive_search=False,
        requires_multi_entity=False,
        extracted_parameters={},
    )

    tools = selector._fallback_select_tools("洗錢防制", analysis)

    assert len(tools) == 1
    assert tools[0]["tool_name"] == "vector_search"


# Integration Tests


@pytest.mark.asyncio
async def test_analyzer_selector_integration_temporal():
    """Test integration of analyzer and selector for temporal query."""
    analyzer = QueryAnalyzer()
    selector = ToolSelector()

    # Analyze query
    analysis = analyzer._fallback_analyze("玉山銀行最近一次的罰款紀錄")

    # Select tools
    tools = selector._fallback_select_tools("玉山銀行最近一次的罰款紀錄", analysis)

    # Verify correct tool selected
    assert tools[0]["tool_name"] == "metadata_search"


@pytest.mark.asyncio
async def test_analyzer_selector_integration_comparison():
    """Test integration of analyzer and selector for comparison query."""
    analyzer = QueryAnalyzer()
    selector = ToolSelector()

    # Analyze query
    analysis = analyzer._fallback_analyze("玉山銀行與國泰世華銀行的裁罰紀錄比較")

    # Select tools
    tools = selector._fallback_select_tools("玉山銀行與國泰世華銀行的裁罰紀錄比較", analysis)

    # Verify correct tool selected
    assert tools[0]["tool_name"] == "multi_entity_search"
