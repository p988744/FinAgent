"""Tests for metadata database."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from finagent.database.metadata_db import MetadataDB
from finagent.models.document_metadata import ExtendedDocumentMetadata


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_metadata.db"
        db = MetadataDB(db_path=str(db_path))
        yield db


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return ExtendedDocumentMetadata(
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


@pytest.mark.asyncio
async def test_insert_metadata(temp_db, sample_metadata):
    """Test inserting metadata."""
    await temp_db.insert(sample_metadata)

    # Verify insertion
    metadata = await temp_db.get_metadata(sample_metadata.filename)
    assert metadata is not None
    assert metadata["entity"] == "玉山銀行"
    assert metadata["penalty_amount"] == 250000000.0


@pytest.mark.asyncio
async def test_search_by_entity(temp_db, sample_metadata):
    """Test searching by entity."""
    await temp_db.insert(sample_metadata)

    # Search by entity
    results = await temp_db.search({"entity": "玉山"})
    assert len(results) == 1
    assert results[0]["filename"] == sample_metadata.filename


@pytest.mark.asyncio
async def test_search_by_date_range(temp_db, sample_metadata):
    """Test searching by date range."""
    await temp_db.insert(sample_metadata)

    # Search within date range
    results = await temp_db.search({"date_from": "2020-01-01", "date_to": "2020-12-31"})
    assert len(results) == 1

    # Search outside date range
    results = await temp_db.search({"date_from": "2021-01-01", "date_to": "2021-12-31"})
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_by_penalty_type(temp_db, sample_metadata):
    """Test searching by penalty type."""
    await temp_db.insert(sample_metadata)

    # Search by penalty type
    results = await temp_db.search({"penalty_type": "洗錢"})
    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_by_jurisdiction(temp_db, sample_metadata):
    """Test searching by jurisdiction."""
    await temp_db.insert(sample_metadata)

    # Search by jurisdiction
    results = await temp_db.search({"jurisdiction": "金管會"})
    assert len(results) == 1

    # Search by wrong jurisdiction
    results = await temp_db.search({"jurisdiction": "中央銀行"})
    assert len(results) == 0


@pytest.mark.asyncio
async def test_list_all(temp_db, sample_metadata):
    """Test listing all documents."""
    await temp_db.insert(sample_metadata)

    # List all
    results = await temp_db.list_all()
    assert len(results) == 1

    # List by entity
    results = await temp_db.list_all(entity="玉山")
    assert len(results) == 1

    # List by penalty type
    results = await temp_db.list_all(penalty_type="洗錢防制")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_get_file_path(temp_db, sample_metadata):
    """Test getting file path by filename."""
    await temp_db.insert(sample_metadata)

    # Get file path
    file_path = await temp_db.get_file_path(sample_metadata.filename)
    assert file_path == sample_metadata.file_path

    # Get non-existent file path
    file_path = await temp_db.get_file_path("nonexistent.txt")
    assert file_path is None


@pytest.mark.asyncio
async def test_count_documents(temp_db, sample_metadata):
    """Test counting documents."""
    assert await temp_db.count_documents() == 0

    await temp_db.insert(sample_metadata)
    assert await temp_db.count_documents() == 1


@pytest.mark.asyncio
async def test_delete_by_filename(temp_db, sample_metadata):
    """Test deleting metadata by filename."""
    await temp_db.insert(sample_metadata)

    # Delete existing
    deleted = await temp_db.delete_by_filename(sample_metadata.filename)
    assert deleted is True

    # Verify deletion
    metadata = await temp_db.get_metadata(sample_metadata.filename)
    assert metadata is None

    # Delete non-existent
    deleted = await temp_db.delete_by_filename("nonexistent.txt")
    assert deleted is False


@pytest.mark.asyncio
async def test_multiple_documents(temp_db):
    """Test with multiple documents."""
    # Create multiple metadata entries
    metadata1 = ExtendedDocumentMetadata(
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

    metadata2 = ExtendedDocumentMetadata(
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

    await temp_db.insert(metadata1)
    await temp_db.insert(metadata2)

    # Test search returns both
    results = await temp_db.search({"jurisdiction": "金管會"})
    assert len(results) == 2

    # Test search returns only one (by entity)
    results = await temp_db.search({"entity": "玉山"})
    assert len(results) == 1

    # Test search returns latest first (date DESC)
    results = await temp_db.search({})
    assert len(results) == 2
    assert results[0]["date"] > results[1]["date"]  # 2021 before 2020


@pytest.mark.asyncio
async def test_combined_filters(temp_db):
    """Test combined filter conditions."""
    metadata1 = ExtendedDocumentMetadata(
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
        case_number=None,
        content_length=15000,
        chunk_count=35,
        indexed_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    metadata2 = ExtendedDocumentMetadata(
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

    await temp_db.insert(metadata1)
    await temp_db.insert(metadata2)

    # Combined filter: entity + date range
    results = await temp_db.search({
        "entity": "玉山",
        "date_from": "2021-01-01",
        "date_to": "2021-12-31"
    })
    assert len(results) == 1
    assert results[0]["penalty_type"] == "內控缺失"

    # Combined filter: entity + penalty type
    results = await temp_db.search({
        "entity": "玉山",
        "penalty_type": "洗錢"
    })
    assert len(results) == 1
    assert results[0]["date"] == "2020-09-15"
