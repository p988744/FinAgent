import unittest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from finagent.tools.hybrid_retriever import HybridRetrieverTool
from finagent.document_processing.retriever import DocumentRetriever, RetrievedChunk

class TestHybridRetrieverTool(unittest.TestCase):
    def setUp(self):
        self.mock_retriever = MagicMock(spec=DocumentRetriever)
        # Mock collection
        self.mock_collection = MagicMock()
        self.mock_retriever.collection = self.mock_collection
        
        self.tool = HybridRetrieverTool(
            retriever=self.mock_retriever,
            semantic_weight=0.5,
            keyword_weight=0.5
        )

    def test_run_success(self):
        # Mock collection data
        self.mock_collection.get.return_value = {
            "documents": ["doc1 content", "doc2 content"],
            "metadatas": [{"filename": "doc1.txt"}, {"filename": "doc2.txt"}]
        }

        # Mock vector results
        vector_chunk = RetrievedChunk(
            text="doc1 content",
            score=0.9,
            doc_id="doc1",
            id="chunk1",
            metadata={"filename": "doc1.txt"}
        )
        self.mock_retriever.retrieve.return_value = [vector_chunk]

        # Mock BM25 results
        bm25_doc = Document(page_content="doc2 content", metadata={"filename": "doc2.txt"})
        
        with patch("finagent.tools.hybrid_retriever.BM25Retriever") as MockBM25:
            mock_bm25_instance = MockBM25.from_documents.return_value
            mock_bm25_instance.invoke.return_value = [bm25_doc]

            result = self.tool._run(query="test query", k=2)

            self.assertIn("🔍 混合檢索結果", result)
            self.assertIn("doc1.txt", result)
            self.assertIn("doc2.txt", result)

    def test_run_empty_kb(self):
        self.mock_collection.get.return_value = {"documents": []}
        
        result = self.tool._run(query="test query")
        
        self.assertIn("知識庫為空", result)

    def test_run_no_results(self):
        self.mock_collection.get.return_value = {
            "documents": ["doc1"],
            "metadatas": [{"filename": "doc1.txt"}]
        }
        self.mock_retriever.retrieve.return_value = []
        
        with patch("finagent.tools.hybrid_retriever.BM25Retriever") as MockBM25:
            mock_bm25_instance = MockBM25.from_documents.return_value
            mock_bm25_instance.invoke.return_value = []

            result = self.tool._run(query="test query")
            
            self.assertIn("未找到相關文件", result)

    def test_run_error(self):
        self.mock_collection.get.side_effect = Exception("Test error")
        
        result = self.tool._run(query="test query")
        
        self.assertIn("混合檢索失敗: Test error", result)

if __name__ == '__main__':
    unittest.main()
