"""Integration tests for advanced tools (Phase 3)."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from finagent.database.metadata_db import MetadataDB
from finagent.models.document_metadata import ExtendedDocumentMetadata
from finagent.tools.base import ToolInput
from finagent.tools.hybrid_search import HybridSearchTool
from finagent.tools.multi_entity_search import MultiEntitySearchTool


@pytest.fixture
def temp_db_with_data():
    """Create temporary database with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_metadata.db"
        db = MetadataDB(db_path=str(db_path))

        # Create sample documents
        doc1 = ExtendedDocumentMetadata(
            filename="玉山銀行_洗錢防制_2020.txt",
            file_path="./data/documents/玉山銀行_洗錢防制_2020.txt",
            entity="玉山銀行",
            entity_normalized="玉山商業銀行股份有限公司",
            penalty_type="洗錢防制",
            penalty_amount=250000000.0,
            date="2020-09-15",
            year_roc=109,
            year_ad=2020,
            jurisdiction="金管會",
            document_type="裁罰書",
            case_number="金管銀法字第10900123456號",
            content_length=15000,
            chunk_count=35,
            indexed_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        doc2 = ExtendedDocumentMetadata(
            filename="玉山銀行_內控缺失_2021.txt",
            file_path="./data/documents/玉山銀行_內控缺失_2021.txt",
            entity="玉山銀行",
            entity_normalized="玉山商業銀行股份有限公司",
            penalty_type="內控缺失",
            penalty_amount=50000000.0,
            date="2021-03-10",
            year_roc=110,
            year_ad=2021,
            jurisdiction="金管會",
            document_type="裁罰書",
            case_number=None,
            content_length=10000,
            chunk_count=22,
            indexed_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        doc3 = ExtendedDocumentMetadata(
            filename="國泰世華銀行_內線交易_2021.txt",
            file_path="./data/documents/國泰世華銀行_內線交易_2021.txt",
            entity="國泰世華銀行",
            entity_normalized="國泰世華商業銀行股份有限公司",
            penalty_type="內線交易",
            penalty_amount=100000000.0,
            date="2021-05-20",
            year_roc=110,
            year_ad=2021,
            jurisdiction="金管會",
            document_type="裁罰書",
            case_number=None,
            content_length=12000,
            chunk_count=28,
            indexed_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        # Insert async
        import asyncio

        async def insert_data():
            await db.insert(doc1)
            await db.insert(doc2)
            await db.insert(doc3)

        asyncio.run(insert_data())

        yield db


# Hybrid Search Tool Tests


@pytest.mark.asyncio
async def test_hybrid_search_with_entity_filter(temp_db_with_data):
    """Test hybrid search with entity filter."""
    # Note: This test will work if vector DB exists, otherwise will skip gracefully
    tool = HybridSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="洗錢防制裁罰", parameters={"entity": "玉山", "top_k": 5}
    )

    output = await tool.execute(tool_input)

    # Check metadata filters were applied
    assert "metadata_filters" in output.metadata
    assert output.metadata["metadata_filters"]["entity"] == "玉山"
    assert output.metadata["candidate_count"] == 2  # Two 玉山 documents


@pytest.mark.asyncio
async def test_hybrid_search_with_date_filter(temp_db_with_data):
    """Test hybrid search with date range filter."""
    tool = HybridSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="裁罰",
        parameters={"date_from": "2021-01-01", "date_to": "2021-12-31", "top_k": 5},
    )

    output = await tool.execute(tool_input)

    # Check filters
    assert output.metadata["metadata_filters"]["date_from"] == "2021-01-01"
    assert output.metadata["candidate_count"] == 2  # Two 2021 documents


@pytest.mark.asyncio
async def test_hybrid_search_with_penalty_type_filter(temp_db_with_data):
    """Test hybrid search with penalty type filter."""
    tool = HybridSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="銀行違規", parameters={"penalty_type": "洗錢", "top_k": 5}
    )

    output = await tool.execute(tool_input)

    # Check filters
    assert output.metadata["metadata_filters"]["penalty_type"] == "洗錢"
    assert output.metadata["candidate_count"] == 1  # One 洗錢防制 document


@pytest.mark.asyncio
async def test_hybrid_search_no_filters(temp_db_with_data):
    """Test hybrid search without metadata filters (falls back to pure vector search)."""
    tool = HybridSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="銀行裁罰", parameters={"top_k": 5})

    output = await tool.execute(tool_input)

    # No metadata filters
    assert output.metadata["metadata_filters"] == {}
    assert output.metadata["candidate_count"] == "all"


@pytest.mark.asyncio
async def test_hybrid_search_no_candidates(temp_db_with_data):
    """Test hybrid search when metadata filtering returns no candidates."""
    tool = HybridSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="裁罰", parameters={"entity": "不存在的銀行", "top_k": 5}
    )

    output = await tool.execute(tool_input)

    # Should return success but empty results
    assert output.success is True
    assert len(output.results) == 0
    assert output.metadata["candidate_count"] == 0
    assert output.metadata["stage"] == "metadata_filtering_empty"


@pytest.mark.asyncio
async def test_hybrid_search_validate_input(temp_db_with_data):
    """Test hybrid search input validation."""
    tool = HybridSearchTool(metadata_db=temp_db_with_data)

    # Valid input
    valid_input = ToolInput(query="test", parameters={"entity": "玉山"})
    assert tool.validate_input(valid_input) is True

    # Invalid input (no query)
    invalid_input = ToolInput(query="", parameters={"entity": "玉山"})
    assert tool.validate_input(invalid_input) is False

    # Invalid top_k
    invalid_input2 = ToolInput(query="test", parameters={"top_k": -1})
    assert tool.validate_input(invalid_input2) is False

    # Invalid date format
    invalid_input3 = ToolInput(query="test", parameters={"date_from": "2021"})
    assert tool.validate_input(invalid_input3) is False


# Multi-Entity Search Tool Tests


@pytest.mark.asyncio
async def test_multi_entity_search_two_entities(temp_db_with_data):
    """Test multi-entity search with two entities."""
    tool = MultiEntitySearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="裁罰",
        parameters={"entities": ["玉山銀行", "國泰世華銀行"], "top_k_per_entity": 3},
    )

    output = await tool.execute(tool_input)

    # Check structure
    assert output.success is True
    assert len(output.results) == 2  # Two entities

    # Verify each entity has results
    entities_found = [r["entity"] for r in output.results]
    assert "玉山銀行" in entities_found
    assert "國泰世華銀行" in entities_found

    # Check metadata
    assert output.metadata["entity_count"] == 2
    assert output.metadata["entities"] == ["玉山銀行", "國泰世華銀行"]


@pytest.mark.asyncio
async def test_multi_entity_search_parallel_execution(temp_db_with_data):
    """Test that multi-entity search executes in parallel."""
    tool = MultiEntitySearchTool(metadata_db=temp_db_with_data)

    # Search for 3 entities
    tool_input = ToolInput(
        query="銀行違規",
        parameters={
            "entities": ["玉山銀行", "國泰世華銀行", "中國信託銀行"],
            "top_k_per_entity": 2,
        },
    )

    output = await tool.execute(tool_input)

    # All 3 entities should be processed
    assert output.success is True
    assert len(output.results) == 3
    assert output.metadata["entity_count"] == 3


@pytest.mark.asyncio
async def test_multi_entity_search_entity_not_found(temp_db_with_data):
    """Test multi-entity search when one entity has no results."""
    tool = MultiEntitySearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="裁罰",
        parameters={"entities": ["玉山銀行", "不存在的銀行"], "top_k_per_entity": 3},
    )

    output = await tool.execute(tool_input)

    # Should still succeed
    assert output.success is True
    assert len(output.results) == 2

    # Find the non-existent entity
    for entity_result in output.results:
        if entity_result["entity"] == "不存在的銀行":
            assert len(entity_result["results"]) == 0
            assert entity_result["candidate_count"] == 0


@pytest.mark.asyncio
async def test_multi_entity_search_less_than_two_entities(temp_db_with_data):
    """Test multi-entity search fails with less than 2 entities."""
    tool = MultiEntitySearchTool(metadata_db=temp_db_with_data)

    # Only one entity
    tool_input = ToolInput(
        query="裁罰", parameters={"entities": ["玉山銀行"], "top_k_per_entity": 3}
    )

    output = await tool.execute(tool_input)

    # Should fail
    assert output.success is False
    assert "至少2個實體" in output.error


@pytest.mark.asyncio
async def test_multi_entity_search_validate_input(temp_db_with_data):
    """Test multi-entity search input validation."""
    tool = MultiEntitySearchTool(metadata_db=temp_db_with_data)

    # Valid input
    valid_input = ToolInput(
        query="test", parameters={"entities": ["玉山銀行", "國泰世華銀行"]}
    )
    assert tool.validate_input(valid_input) is True

    # Invalid input (no query)
    invalid_input = ToolInput(
        query="", parameters={"entities": ["玉山銀行", "國泰世華銀行"]}
    )
    assert tool.validate_input(invalid_input) is False

    # Invalid input (only one entity)
    invalid_input2 = ToolInput(query="test", parameters={"entities": ["玉山銀行"]})
    assert tool.validate_input(invalid_input2) is False

    # Invalid input (entities not a list)
    invalid_input3 = ToolInput(query="test", parameters={"entities": "玉山銀行"})
    assert tool.validate_input(invalid_input3) is False

    # Invalid input (empty entity name)
    invalid_input4 = ToolInput(
        query="test", parameters={"entities": ["玉山銀行", ""]}
    )
    assert tool.validate_input(invalid_input4) is False


# Tool Capability Tests


def test_hybrid_search_capability():
    """Test hybrid search tool capability."""
    tool = HybridSearchTool()
    capability = tool.get_capability()

    assert capability.name == "hybrid_search"
    assert "filtered_semantic_search" in capability.supported_intents
    assert capability.execution_time_estimate == "medium"
    assert capability.cost_estimate == "medium"


def test_multi_entity_search_capability():
    """Test multi-entity search tool capability."""
    tool = MultiEntitySearchTool()
    capability = tool.get_capability()

    assert capability.name == "multi_entity_search"
    assert "comparison" in capability.supported_intents
    assert "entities" in capability.required_features
    assert capability.execution_time_estimate == "medium"
    assert capability.cost_estimate == "high"
