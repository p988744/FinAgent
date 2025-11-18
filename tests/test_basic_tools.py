"""Integration tests for basic tools (Phase 2)."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from finagent.database.metadata_db import MetadataDB
from finagent.models.document_metadata import ExtendedDocumentMetadata
from finagent.tools.base import ToolInput
from finagent.tools.list_documents import ListDocumentsTool
from finagent.tools.metadata_search import MetadataSearchTool
from finagent.tools.read_file import ReadFileTool


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


# Metadata Search Tool Tests


@pytest.mark.asyncio
async def test_metadata_search_by_entity(temp_db_with_data):
    """Test metadata search by entity."""
    tool = MetadataSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="玉山銀行裁罰", parameters={"entity": "玉山"})

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 2  # Two 玉山 documents
    assert all("玉山" in r["entity"] for r in output.results)


@pytest.mark.asyncio
async def test_metadata_search_latest(temp_db_with_data):
    """Test metadata search for latest record."""
    tool = MetadataSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="玉山銀行最近一次的罰款紀錄", parameters={"entity": "玉山"}
    )

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 1  # Only latest
    assert output.results[0]["date"] == "2021-03-10"  # Most recent


@pytest.mark.asyncio
async def test_metadata_search_by_date_range(temp_db_with_data):
    """Test metadata search by date range."""
    tool = MetadataSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="2021年裁罰",
        parameters={"date_from": "2021-01-01", "date_to": "2021-12-31"},
    )

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 2  # Two 2021 documents
    assert all(r["year_ad"] == 2021 for r in output.results)


@pytest.mark.asyncio
async def test_metadata_search_by_penalty_type(temp_db_with_data):
    """Test metadata search by penalty type."""
    tool = MetadataSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="洗錢防制裁罰", parameters={"penalty_type": "洗錢"})

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 1
    assert "洗錢防制" in output.results[0]["penalty_type"]


@pytest.mark.asyncio
async def test_metadata_search_no_filters(temp_db_with_data):
    """Test metadata search fails without filters."""
    tool = MetadataSearchTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="查詢", parameters={})

    output = await tool.execute(tool_input)

    assert output.success is False
    assert "至少一個篩選條件" in output.error


@pytest.mark.asyncio
async def test_metadata_search_validate_input(temp_db_with_data):
    """Test metadata search input validation."""
    tool = MetadataSearchTool(metadata_db=temp_db_with_data)

    # Valid input
    valid_input = ToolInput(query="test", parameters={"entity": "玉山"})
    assert tool.validate_input(valid_input) is True

    # Invalid input (no filters)
    invalid_input = ToolInput(query="test", parameters={})
    assert tool.validate_input(invalid_input) is False

    # Invalid date format
    invalid_date_input = ToolInput(
        query="test", parameters={"date_from": "2021"}
    )  # Too short
    assert tool.validate_input(invalid_date_input) is False


# List Documents Tool Tests


@pytest.mark.asyncio
async def test_list_documents_by_entity(temp_db_with_data):
    """Test list all documents by entity."""
    tool = ListDocumentsTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="玉山銀行所有裁罰", parameters={"entity": "玉山"})

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 2  # All 玉山 documents
    assert output.metadata["total_count"] == 2


@pytest.mark.asyncio
async def test_list_documents_by_penalty_type(temp_db_with_data):
    """Test list all documents by penalty type."""
    tool = ListDocumentsTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="內控缺失", parameters={"penalty_type": "內控"})

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 1
    assert "內控" in output.results[0]["penalty_type"]


@pytest.mark.asyncio
async def test_list_documents_comprehensive(temp_db_with_data):
    """Test list all documents (comprehensive)."""
    tool = ListDocumentsTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="玉山銀行所有文件", parameters={"entity": "玉山"})

    output = await tool.execute(tool_input)

    assert output.success is True
    assert len(output.results) == 2  # Exhaustive, not top-k

    # Verify all results have required fields
    for result in output.results:
        assert "filename" in result
        assert "entity" in result
        assert "penalty_type" in result
        assert "date" in result


@pytest.mark.asyncio
async def test_list_documents_validate_input(temp_db_with_data):
    """Test list documents input validation."""
    tool = ListDocumentsTool(metadata_db=temp_db_with_data)

    # Valid input with entity
    valid_input = ToolInput(query="test", parameters={"entity": "玉山"})
    assert tool.validate_input(valid_input) is True

    # Valid input with penalty_type
    valid_input2 = ToolInput(query="test", parameters={"penalty_type": "洗錢"})
    assert tool.validate_input(valid_input2) is True

    # Invalid input (no entity or penalty_type)
    invalid_input = ToolInput(query="test", parameters={})
    assert tool.validate_input(invalid_input) is False


# Read File Tool Tests


@pytest.mark.asyncio
async def test_read_file_success(temp_db_with_data):
    """Test reading a file successfully."""
    # Create a temporary test file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_content = "這是測試文件內容。"
        test_file.write_text(test_content, encoding="utf-8")

        # Add to metadata DB
        metadata = ExtendedDocumentMetadata(
            filename="test.txt",
            file_path=str(test_file),
            entity="測試銀行",
            entity_normalized="測試銀行股份有限公司",
            penalty_type="測試",
            penalty_amount=None,
            date="2021-01-01",
            year_roc=110,
            year_ad=2021,
            jurisdiction="金管會",
            document_type="測試",
            case_number=None,
            content_length=len(test_content),
            chunk_count=1,
            indexed_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        await temp_db_with_data.insert(metadata)

        # Test read file tool
        tool = ReadFileTool(metadata_db=temp_db_with_data)

        tool_input = ToolInput(query="讀取檔案", parameters={"filename": "test.txt"})

        output = await tool.execute(tool_input)

        assert output.success is True
        assert len(output.results) == 1
        assert output.results[0]["content"] == test_content
        assert output.results[0]["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_read_file_not_found(temp_db_with_data):
    """Test reading a non-existent file."""
    tool = ReadFileTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(
        query="讀取檔案", parameters={"filename": "nonexistent.txt"}
    )

    output = await tool.execute(tool_input)

    assert output.success is False
    assert "找不到檔案" in output.error


@pytest.mark.asyncio
async def test_read_file_no_filename(temp_db_with_data):
    """Test read file without filename."""
    tool = ReadFileTool(metadata_db=temp_db_with_data)

    tool_input = ToolInput(query="讀取檔案", parameters={})

    output = await tool.execute(tool_input)

    assert output.success is False
    assert "請提供檔名" in output.error


@pytest.mark.asyncio
async def test_read_file_validate_input(temp_db_with_data):
    """Test read file input validation."""
    tool = ReadFileTool(metadata_db=temp_db_with_data)

    # Valid input
    valid_input = ToolInput(query="test", parameters={"filename": "test.txt"})
    assert tool.validate_input(valid_input) is True

    # Invalid input (no filename)
    invalid_input = ToolInput(query="test", parameters={})
    assert tool.validate_input(invalid_input) is False

    # Invalid input (empty filename)
    invalid_input2 = ToolInput(query="test", parameters={"filename": ""})
    assert tool.validate_input(invalid_input2) is False


# Tool Capability Tests


def test_metadata_search_capability():
    """Test metadata search tool capability."""
    tool = MetadataSearchTool()
    capability = tool.get_capability()

    assert capability.name == "metadata_search"
    assert "temporal" in capability.supported_intents
    assert capability.execution_time_estimate == "fast"
    assert capability.cost_estimate == "low"


def test_list_documents_capability():
    """Test list documents tool capability."""
    tool = ListDocumentsTool()
    capability = tool.get_capability()

    assert capability.name == "list_documents"
    assert "comprehensive_list" in capability.supported_intents
    assert "entity" in capability.required_features


def test_read_file_capability():
    """Test read file tool capability."""
    tool = ReadFileTool()
    capability = tool.get_capability()

    assert capability.name == "read_file"
    assert "specific_file" in capability.supported_intents
    assert "filename" in capability.required_features
