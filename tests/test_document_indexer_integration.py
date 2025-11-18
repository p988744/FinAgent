"""
Integration test for DocumentIndexer with SQLite and Chroma.

Tests the complete flow:
1. Document indexing to both Chroma and SQLite
2. Document deletion from both databases
3. Data consistency between Chroma and SQLite
"""

import tempfile
from datetime import datetime
from pathlib import Path

import chromadb
import pytest
from chromadb.config import Settings

from finagent.database.document_db import DocumentDatabase
from finagent.document_processing.embeddings import EmbeddingGenerator
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.loader import Document


@pytest.fixture
def temp_directories():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as chroma_dir, tempfile.TemporaryDirectory() as db_dir:
        yield {
            "chroma_dir": chroma_dir,
            "db_path": str(Path(db_dir) / "test.db"),
        }


@pytest.fixture
def mock_embedding_generator():
    """Mock embedding generator for testing."""

    class MockEmbeddingGenerator:
        def generate_embeddings_batch(self, texts):
            # Return fake embeddings (1536 dimensions for text-embedding-3-small)
            return [[0.1] * 1536 for _ in texts]

    return MockEmbeddingGenerator()


@pytest.fixture
def document_db(temp_directories):
    """Create DocumentDatabase instance with temporary database."""
    db = DocumentDatabase(db_path=temp_directories["db_path"])

    # Initialize schema
    import sqlite3
    from pathlib import Path

    # First run base schema
    base_schema_file = Path(__file__).parent.parent / "src" / "finagent" / "database" / "schema.sql"
    migration_file = Path(__file__).parent.parent / "src" / "finagent" / "database" / "migrations" / "001_wiki_tables.sql"

    conn = sqlite3.connect(temp_directories["db_path"])
    cursor = conn.cursor()

    # Load and run base schema
    with open(base_schema_file, "r", encoding="utf-8") as f:
        base_sql = f.read()
    cursor.executescript(base_sql)

    # Load and run migration (only the new column additions will take effect)
    with open(migration_file, "r", encoding="utf-8") as f:
        migration_sql = f.read()
    cursor.executescript(migration_sql)

    conn.commit()
    conn.close()

    return db


@pytest.fixture
def indexer(temp_directories, mock_embedding_generator, document_db):
    """Create DocumentIndexer with temporary storage."""
    return DocumentIndexer(
        collection_name="test_collection",
        persist_directory=temp_directories["chroma_dir"],
        embedding_generator=mock_embedding_generator,
        document_db=document_db,
    )


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        id="test_doc_123",
        content="這是一個測試文件。\n\n它包含多個段落。\n\n這是第三段。",
        source="/tmp/test_document.txt",
        metadata={
            "filename": "test_document.txt",
            "file_extension": ".txt",
            "file_size": 100,
        },
        loaded_at=datetime.now(),
    )


def test_index_document_creates_entries_in_both_databases(
    indexer, document_db, sample_document
):
    """Test that indexing creates entries in both Chroma and SQLite."""
    # Index document
    chunk_count = indexer.index_document(sample_document)

    assert chunk_count > 0, "Should create at least one chunk"

    # Verify Chroma
    chroma_results = indexer.collection.get(where={"doc_id": sample_document.id})
    assert len(chroma_results["ids"]) == chunk_count, "Chroma should have all chunks"

    # Verify SQLite
    doc = document_db.get_document(sample_document.id)
    assert doc is not None, "Document should exist in SQLite"
    assert doc["doc_id"] == sample_document.id
    assert doc["filename"] == "test_document.txt"
    assert doc["file_path"] == "/tmp/test_document.txt"
    assert doc["indexed"] == 1, "Document should be marked as indexed"
    assert doc["chunk_count"] == chunk_count, "Chunk count should match"


def test_delete_document_removes_from_both_databases(
    indexer, document_db, sample_document
):
    """Test that deletion removes from both Chroma and SQLite."""
    # Index document first
    chunk_count = indexer.index_document(sample_document)
    assert chunk_count > 0

    # Verify it exists
    assert indexer.document_exists(sample_document.id)
    assert document_db.get_document(sample_document.id) is not None

    # Delete document
    deleted_count = indexer.delete_document(sample_document.id)
    assert deleted_count == chunk_count

    # Verify deletion from Chroma
    chroma_results = indexer.collection.get(where={"doc_id": sample_document.id})
    assert len(chroma_results["ids"]) == 0, "Chroma should have no chunks"

    # Verify deletion from SQLite
    doc = document_db.get_document(sample_document.id)
    assert doc is None, "Document should not exist in SQLite"


def test_index_multiple_documents(indexer, document_db):
    """Test indexing multiple documents."""
    docs = [
        Document(
            id=f"doc_{i}",
            content=f"文件 {i} 的內容。\n\n這是第二段。",
            source=f"/tmp/doc_{i}.txt",
            metadata={"filename": f"doc_{i}.txt"},
            loaded_at=datetime.now(),
        )
        for i in range(3)
    ]

    # Index all documents
    total_chunks = indexer.index_documents(docs)
    assert total_chunks > 0

    # Verify all in SQLite
    all_docs = document_db.list_documents()
    assert len(all_docs) == 3

    for doc in docs:
        db_doc = document_db.get_document(doc.id)
        assert db_doc is not None
        assert db_doc["indexed"] == 1


def test_statistics_consistency(indexer, document_db):
    """Test that statistics are consistent between Chroma and SQLite."""
    docs = [
        Document(
            id=f"stat_doc_{i}",
            content=f"統計測試文件 {i}。" * 50,  # Make it long enough for multiple chunks
            source=f"/tmp/stat_{i}.txt",
            metadata={"filename": f"stat_{i}.txt"},
            loaded_at=datetime.now(),
        )
        for i in range(5)
    ]

    # Index documents
    indexer.index_documents(docs)

    # Get statistics
    db_stats = document_db.get_statistics()
    chroma_count = indexer.collection.count()

    assert db_stats["total_documents"] == 5
    assert db_stats["indexed_documents"] == 5
    assert db_stats["total_chunks"] == chroma_count


def test_content_preview_is_stored(indexer, document_db):
    """Test that content preview is stored in SQLite."""
    long_content = "這是一個很長的文件。" * 100

    doc = Document(
        id="preview_test",
        content=long_content,
        source="/tmp/preview.txt",
        metadata={"filename": "preview.txt"},
        loaded_at=datetime.now(),
    )

    indexer.index_document(doc)

    # Check content preview
    db_doc = document_db.get_document("preview_test")
    assert db_doc["content_preview"] is not None
    assert len(db_doc["content_preview"]) == 500  # First 500 chars
    assert db_doc["content_preview"].startswith("這是一個很長的文件。")


def test_metadata_is_preserved(indexer, document_db):
    """Test that custom metadata is preserved."""
    doc = Document(
        id="metadata_test",
        content="測試元數據保存",
        source="/tmp/metadata.txt",
        metadata={
            "filename": "metadata.txt",
            "custom_field": "custom_value",
            "year": 2024,
            "tags": ["test", "metadata"],
        },
        loaded_at=datetime.now(),
    )

    indexer.index_document(doc)

    db_doc = document_db.get_document("metadata_test")
    assert db_doc["custom_fields"] is not None

    # Metadata should be a dict (stored in custom_fields)
    metadata = db_doc["custom_fields"]
    assert isinstance(metadata, dict)
    assert metadata["custom_field"] == "custom_value"
    assert metadata["year"] == 2024
    assert metadata["tags"] == ["test", "metadata"]


def test_reindex_same_document(indexer, document_db, sample_document):
    """Test that reindexing the same document updates both databases."""
    # Index first time
    chunk_count_1 = indexer.index_document(sample_document)

    # Modify content and reindex
    sample_document.content = "這是更新後的內容。\n\n新的段落。\n\n更多內容。\n\n還有更多。"
    chunk_count_2 = indexer.index_document(sample_document)

    # Chunk count might be different
    assert chunk_count_2 > 0

    # Verify Chroma has new chunks
    chroma_results = indexer.collection.get(where={"doc_id": sample_document.id})
    # Note: Chroma might have both old and new chunks without explicit deletion
    # In production, we'd want to delete old chunks first

    # Verify SQLite is updated
    doc = document_db.get_document(sample_document.id)
    assert doc is not None
    # The last index operation should update chunk_count
    assert doc["chunk_count"] == chunk_count_2


def test_document_exists_check(indexer, sample_document):
    """Test document existence check."""
    assert not indexer.document_exists(sample_document.id)

    indexer.index_document(sample_document)

    assert indexer.document_exists(sample_document.id)


def test_get_document_chunks(indexer, sample_document):
    """Test retrieving document chunks."""
    chunk_count = indexer.index_document(sample_document)

    chunks = indexer.get_document_chunks(sample_document.id)

    assert len(chunks) == chunk_count
    assert all("id" in chunk for chunk in chunks)
    assert all("text" in chunk for chunk in chunks)
    assert all("metadata" in chunk for chunk in chunks)
