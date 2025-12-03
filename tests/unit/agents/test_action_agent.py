import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from finagent.agents.action_agent import ActionAgent
from finagent.document_processing.retriever import DocumentRetriever, RetrievedChunk
from finagent.models.todo_item import TodoItem

class TestActionAgent(unittest.TestCase):
    def setUp(self):
        self.mock_retriever = MagicMock(spec=DocumentRetriever)
        self.mock_ui_callback = AsyncMock()
        
        # Mock HardSearcher
        with patch("finagent.agents.action_agent.HardSearcher") as MockHardSearcher:
            self.mock_hard_searcher = MockHardSearcher.return_value
            self.agent = ActionAgent(
                retriever=self.mock_retriever,
                ui_callback=self.mock_ui_callback
            )

    async def test_execute_vector_search(self):
        # Mock state
        retrieval_todo = TodoItem(id="1", content="search", category="retrieval", status="pending")
        state = {
            "query": MagicMock(text="test query"),
            "plan": {"use_hard_search": False},
            "search_iteration": 0,
            "todos": [retrieval_todo],
            "processing_steps": [],
            "errors": []
        }

        # Mock retriever results
        chunk = RetrievedChunk(
            text="Test content",
            score=0.5, # Below threshold 0.8
            doc_id="doc1",
            id="chunk1",
            metadata={"filename": "test.txt"}
        )
        self.mock_retriever.retrieve.return_value = [chunk]

        result_state = await self.agent.execute(state)

        self.assertIn("retrieved_chunks", result_state)
        self.assertEqual(len(result_state["retrieved_chunks"]), 1)
        self.assertIn("citations", result_state)
        self.assertEqual(len(result_state["citations"]), 1)
        
        # Verify todo status update
        self.assertEqual(result_state["todos"][0].status, "completed")
        
        # Verify callback
        self.mock_ui_callback.on_retrieval_result.assert_called_once()

    async def test_execute_hard_search(self):
        # Mock state
        state = {
            "query": MagicMock(text="test query"),
            "plan": {"use_hard_search": True},
            "plan_analysis": {"must_have_keywords": ["keyword"]},
            "search_iteration": 0,
            "todos": [],
            "processing_steps": [],
            "errors": []
        }

        # Mock retriever results (empty)
        self.mock_retriever.retrieve.return_value = []

        # Mock hard search results
        chunk = RetrievedChunk(
            text="Hard match content",
            score=0.95,
            doc_id="doc2",
            id="chunk2",
            metadata={"filename": "hard.txt"}
        )
        self.mock_hard_searcher.search.return_value = [chunk]

        result_state = await self.agent.execute(state)

        self.assertEqual(len(result_state["retrieved_chunks"]), 1)
        self.assertEqual(result_state["retrieved_chunks"][0].metadata["filename"], "hard.txt")

    async def test_execute_filtering(self):
        # Mock state
        state = {
            "query": MagicMock(text="test query"),
            "plan": {"use_hard_search": False},
            "todos": [],
            "processing_steps": [],
            "errors": []
        }

        # Mock retriever results (one good, one bad)
        good_chunk = RetrievedChunk(
            text="Good content",
            score=0.5,
            doc_id="doc1",
            id="chunk1",
            metadata={"filename": "good.txt"}
        )
        bad_chunk = RetrievedChunk(
            text="Bad content",
            score=0.9, # Above threshold 0.8
            doc_id="doc2",
            id="chunk2",
            metadata={"filename": "bad.txt"}
        )
        self.mock_retriever.retrieve.return_value = [good_chunk, bad_chunk]

        result_state = await self.agent.execute(state)

        self.assertEqual(len(result_state["retrieved_chunks"]), 1)
        self.assertEqual(result_state["retrieved_chunks"][0].metadata["filename"], "good.txt")

    async def test_execute_failure(self):
        state = {
            "query": MagicMock(text="test query"),
            "plan": {},
            "todos": [],
            "processing_steps": [],
            "errors": []
        }
        
        self.mock_retriever.retrieve.side_effect = Exception("Retrieval failed")
        
        result_state = await self.agent.execute(state)
        
        self.assertIn("檢索失敗", result_state["errors"][0])
        self.assertEqual(result_state["retrieved_chunks"], [])

if __name__ == '__main__':
    unittest.main()
