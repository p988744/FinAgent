import unittest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from finagent.agents.answer_agent import AnswerAgent, StructuredAnswerOutput
from finagent.document_processing.retriever import RetrievedChunk
from finagent.models.citations import LegalCitation, CitationType, CitationAuthority

class TestAnswerAgent(unittest.TestCase):
    def setUp(self):
        self.mock_ui_callback = AsyncMock()
        with patch("finagent.agents.answer_agent.ChatOpenAI") as MockLLM:
            self.mock_llm = MockLLM.return_value
            self.agent = AnswerAgent(ui_callback=self.mock_ui_callback)
            # Mock the chain
            self.agent.chain = MagicMock()

    async def test_synthesize_success(self):
        # Mock state
        chunk = RetrievedChunk(
            text="Test content",
            score=0.5,
            doc_id="doc1",
            id="chunk1",
            metadata={"filename": "test.txt"}
        )
        citation = LegalCitation(
            id=1,
            type=CitationType.ENFORCEMENT_DOCUMENT,
            authority=CitationAuthority.PRIMARY,
            title="test.txt",
            formatted_citation="test.txt",
            issuing_authority="金管會"
        )
        state = {
            "query": MagicMock(text="test query"),
            "retrieved_chunks": [chunk],
            "citations": [citation],
            "processing_steps": [],
            "errors": [],
            "todos": []
        }

        # Mock LLM response
        mock_response = json.dumps({
            "executive_summary": "Summary",
            "key_findings": ["Finding 1 [引用1](#cite-1)", "Finding 2 [引用1](#cite-1)", "Finding 3 [引用1](#cite-1)"],
            "detailed_analysis": "Analysis",
            "final_answer": "Answer"
        })
        
        # Mock ainvoke (async)
        self.agent.chain.ainvoke = AsyncMock(return_value=mock_response)

        result_state = await self.agent.synthesize(state)

        self.assertIn("answer", result_state)
        self.assertEqual(result_state["answer"].executive_summary, "Summary")
        self.assertEqual(len(result_state["answer"].key_findings), 3)
        self.mock_ui_callback.on_answer_generation_complete.assert_called_once()

    async def test_synthesize_fallback_parsing(self):
        # Mock state
        state = {
            "query": MagicMock(text="test query"),
            "retrieved_chunks": [MagicMock()],
            "citations": [],
            "processing_steps": [],
            "errors": [],
            "todos": []
        }

        # Mock malformed LLM response
        mock_response = "Not JSON\n\nExecutive Summary\n\n- Finding 1\n- Finding 2\n- Finding 3\n\nFinal Answer"
        
        self.agent.chain.ainvoke = AsyncMock(return_value=mock_response)

        result_state = await self.agent.synthesize(state)

        self.assertIn("answer", result_state)
        # Should use fallback parser
        self.assertTrue(len(result_state["answer"].key_findings) >= 3)

    async def test_synthesize_no_chunks(self):
        state = {
            "query": MagicMock(text="test query"),
            "retrieved_chunks": [],
            "citations": [],
            "processing_steps": [],
            "errors": [],
            "todos": []
        }

        result_state = await self.agent.synthesize(state)

        self.assertIn("answer", result_state)
        self.assertIn("未找到相關文件", result_state["answer"].executive_summary)

if __name__ == '__main__':
    unittest.main()
