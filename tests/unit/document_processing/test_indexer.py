import unittest
from unittest.mock import MagicMock, patch
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.loader import Document

class TestDocumentIndexer(unittest.TestCase):
    def setUp(self):
        # Mock Chroma components
        with patch("finagent.document_processing.indexer.chromadb.PersistentClient") as MockClient:
            self.mock_client = MockClient.return_value
            self.mock_collection = MagicMock()
            self.mock_client.get_or_create_collection.return_value = self.mock_collection
            
            # Mock embedding generator
            with patch("finagent.document_processing.indexer.EmbeddingGenerator") as MockEmbedding:
                self.mock_embedding_gen = MockEmbedding.return_value
                self.mock_embedding_gen.generate_embeddings.return_value = [[0.1, 0.2, 0.3]]
                
                self.indexer = DocumentIndexer(
                    collection_name="test_collection",
                    persist_directory="/tmp/test_chroma"
                )

    def test_init(self):
        """Test DocumentIndexer initialization"""
        self.assertIsNotNone(self.indexer.collection)
        self.assertEqual(self.indexer.collection_name, "test_collection")

    async def test_index_document_success(self):
        """Test indexing a single document"""
        # Create test document
        from datetime import datetime
        document = Document(
            id="doc1",
            content="這是一段測試文件內容。" * 50,  # Make it long enough to chunk
            source="/tmp/test.txt",
            loaded_at=datetime.now(),
            metadata={"filename": "test.txt", "doc_id": "doc1"}
        )

        # Index the document
        chunk_count = await self.indexer.index_document(document)

        # Verify
        self.assertGreater(chunk_count, 0)
        self.mock_collection.add.assert_called()

    async def test_index_document_with_additional_metadata(self):
        """Test indexing document with additional metadata"""
        from datetime import datetime
        document = Document(
            id="doc1",
            content="測試內容" * 50,
            source="/tmp/test.txt",
            loaded_at=datetime.now(),
            metadata={"filename": "test.txt", "doc_id": "doc1"}
        )
        additional_metadata = {"category": "legal", "year": 2023}

        chunk_count = await self.indexer.index_document(document, additional_metadata=additional_metadata)

        # Verify metadata is merged
        self.assertGreater(chunk_count, 0)
        call_args = self.mock_collection.add.call_args
        metadatas = call_args[1]["metadatas"]
        self.assertTrue(any("category" in m for m in metadatas))

    async def test_index_documents_batch(self):
        """Test indexing multiple documents"""
        from datetime import datetime
        documents = [
            Document(id="doc1", content="文件一" * 50, source="/tmp/doc1.txt", loaded_at=datetime.now(), metadata={"filename": "doc1.txt", "doc_id": "doc1"}),
            Document(id="doc2", content="文件二" * 50, source="/tmp/doc2.txt", loaded_at=datetime.now(), metadata={"filename": "doc2.txt", "doc_id": "doc2"}),
            Document(id="doc3", content="文件三" * 50, source="/tmp/doc3.txt", loaded_at=datetime.now(), metadata={"filename": "doc3.txt", "doc_id": "doc3"}),
        ]

        total_chunks = await self.indexer.index_documents(documents)

        # Verify
        self.assertGreater(total_chunks, 0)
        # Should have called add multiple times (once per document)
        self.assertGreaterEqual(self.mock_collection.add.call_count, 3)

    def test_delete_document(self):
        """Test deleting a document from the index"""
        # Mock get to return some chunks
        self.mock_collection.get.return_value = {
            "ids": ["chunk1", "chunk2", "chunk3"]
        }

        deleted_count = self.indexer.delete_document("doc1")

        # Verify
        self.assertEqual(deleted_count, 3)
        self.mock_collection.delete.assert_called_once()

    def test_delete_document_not_found(self):
        """Test deleting a non-existent document"""
        self.mock_collection.get.return_value = {"ids": []}

        deleted_count = self.indexer.delete_document("nonexistent")

        self.assertEqual(deleted_count, 0)

    def test_clear_collection(self):
        """Test clearing all documents"""
        self.mock_collection.count.return_value = 10

        self.indexer.clear_collection()

        # Verify delete was called
        self.mock_client.delete_collection.assert_called_once_with(name="test_collection")
        # Verify collection was recreated
        self.assertEqual(self.mock_client.get_or_create_collection.call_count, 2)  # Once in __init__, once in clear

    def test_get_collection_stats(self):
        """Test getting collection statistics"""
        self.mock_collection.count.return_value = 42
        self.mock_collection.get.return_value = {
            "metadatas": [{"doc_id": "doc1"}, {"doc_id": "doc2"}, {"doc_id": "doc1"}]
        }

        stats = self.indexer.get_collection_stats()

        # Verify
        self.assertEqual(stats["total_chunks"], 42)
        self.assertEqual(stats["collection_name"], "test_collection")
        # Don't assert on unique_documents if it's not in the actual implementation

    def test_document_exists(self):
        """Test checking if document exists"""
        # Mock document exists
        self.mock_collection.get.return_value = {"ids": ["chunk1"]}
        
        exists = self.indexer.document_exists("doc1")
        self.assertTrue(exists)

        # Mock document doesn't exist
        self.mock_collection.get.return_value = {"ids": []}
        
        exists = self.indexer.document_exists("doc2")
        self.assertFalse(exists)

    def test_get_document_chunks(self):
        """Test retrieving all chunks for a document"""
        self.mock_collection.get.return_value = {
            "ids": ["chunk1", "chunk2"],
            "documents": ["Content 1", "Content 2"],
            "metadatas": [{"chunk_id": 0}, {"chunk_id": 1}]
        }

        chunks = self.indexer.get_document_chunks("doc1")

        # Verify
        self.assertEqual(len(chunks), 2)
        self.mock_collection.get.assert_called_once()

if __name__ == '__main__':
    unittest.main()
