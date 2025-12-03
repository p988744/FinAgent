import unittest
from unittest.mock import MagicMock
from finagent.tools.search import HardSearchTool
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import RetrievedChunk

class TestHardSearchTool(unittest.TestCase):
    def setUp(self):
        self.mock_searcher = MagicMock(spec=HardSearcher)
        self.tool = HardSearchTool(hard_searcher=self.mock_searcher)

    def test_run_success(self):
        # Mock search results
        chunk = RetrievedChunk(
            text="Test content with keyword",
            score=1.0,
            doc_id="doc1",
            id="chunk1",
            metadata={"filename": "test.txt"}
        )
        self.mock_searcher.search.return_value = [chunk]

        result = self.tool._run(keywords=["keyword"])
        
        self.assertIn("Source: test.txt", result)
        self.assertIn("Content: Test content with keyword", result)
        self.mock_searcher.search.assert_called_with(keywords=["keyword"], max_results=5)

    def test_run_no_results(self):
        self.mock_searcher.search.return_value = []
        
        result = self.tool._run(keywords=["keyword"])
        
        self.assertIn("No documents found", result)

    def test_run_error(self):
        self.mock_searcher.search.side_effect = Exception("Test error")
        
        result = self.tool._run(keywords=["keyword"])
        
        self.assertIn("Error performing hard search: Test error", result)

if __name__ == '__main__':
    unittest.main()
