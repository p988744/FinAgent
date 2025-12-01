import unittest
from unittest.mock import MagicMock, AsyncMock
from finagent.tools.retriever import RetrieverTool
from finagent.document_processing.retriever import DocumentRetriever, RetrievedChunk

class TestRetrieverTool(unittest.TestCase):
    def setUp(self):
        self.mock_retriever = MagicMock(spec=DocumentRetriever)
        self.tool = RetrieverTool(retriever=self.mock_retriever)

    def test_run_success(self):
        # Mock retrieved chunks
        chunk = RetrievedChunk(
            text="Test content",
            score=0.9,
            doc_id="doc1",
            id="chunk1",
            metadata={"filename": "test.txt"}
        )
        self.mock_retriever.retrieve.return_value = [chunk]

        result = self.tool._run(query="test query")
        
        self.assertIn("Source: test.txt", result)
        self.assertIn("Content: Test content", result)
        self.mock_retriever.retrieve.assert_called_with(query="test query", n_results=5)

    def test_run_no_results(self):
        self.mock_retriever.retrieve.return_value = []
        
        result = self.tool._run(query="test query")
        
        self.assertEqual(result, "No relevant documents found.")

    def test_run_error(self):
        self.mock_retriever.retrieve.side_effect = Exception("Test error")
        
        result = self.tool._run(query="test query")
        
        self.assertIn("Error retrieving documents: Test error", result)

    async def test_arun(self):
        # Mock retrieved chunks
        chunk = RetrievedChunk(
            text="Test content",
            score=0.9,
            doc_id="doc1",
            id="chunk1",
            metadata={"filename": "test.txt"}
        )
        self.mock_retriever.retrieve.return_value = [chunk]

        result = await self.tool._arun(query="test query")
        
        self.assertIn("Source: test.txt", result)
        self.assertIn("Content: Test content", result)

if __name__ == '__main__':
    unittest.main()
