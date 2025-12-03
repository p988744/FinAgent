import unittest
from unittest.mock import MagicMock, AsyncMock
from finagent.agents.validation_agent import ValidationAgent
from finagent.document_processing.retriever import RetrievedChunk
from finagent.models.citations import LegalCitation, CitationType, CitationAuthority

class TestValidationAgent(unittest.TestCase):
    def setUp(self):
        self.mock_ui_callback = AsyncMock()
        self.agent = ValidationAgent(min_citations=1, ui_callback=self.mock_ui_callback)

    async def test_validate_success(self):
        # Mock state
        chunk = RetrievedChunk(
            text="Test content with keyword",
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
            "query": MagicMock(text="keyword"),
            "retrieved_chunks": [chunk],
            "citations": [citation],
            "processing_steps": [],
            "errors": [],
            "todos": []
        }

        result_state = await self.agent.validate(state)

        self.assertTrue(result_state["validation_passed"])
        self.assertEqual(len(result_state["validation_issues"]), 0)
        self.mock_ui_callback.on_validation_complete.assert_called_once_with(passed=True, issues=[])

    async def test_validate_missing_citations(self):
        state = {
            "query": MagicMock(text="keyword"),
            "retrieved_chunks": [],
            "citations": [],
            "processing_steps": [],
            "errors": [],
            "todos": []
        }

        result_state = await self.agent.validate(state)

        self.assertFalse(result_state["validation_passed"])
        self.assertIn("引用來源不足", result_state["validation_issues"][0])

    async def test_validate_missing_metadata(self):
        chunk = RetrievedChunk(
            text="Test content",
            score=0.5,
            doc_id="doc1",
            id="chunk1",
            metadata={} # Missing filename
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
            "query": MagicMock(text="keyword"),
            "retrieved_chunks": [chunk],
            "citations": [citation],
            "processing_steps": [],
            "errors": [],
            "todos": []
        }

        result_state = await self.agent.validate(state)

        self.assertFalse(result_state["validation_passed"])
        self.assertTrue(any("缺少檔名資訊" in issue for issue in result_state["validation_issues"]))

    async def test_validate_missing_keywords(self):
        # Chunk text does not contain "keyword"
        chunk = RetrievedChunk(
            text="Content without target word",
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
        # Query implies "keyword" is must-have (simple query extraction)
        state = {
            "query": MagicMock(text="keyword"),
            "retrieved_chunks": [chunk],
            "citations": [citation],
            "processing_steps": [],
            "errors": [],
            "todos": []
        }

        # Mock extract_must_have_keywords to return ["keyword"]
        with unittest.mock.patch("finagent.agents.validation_agent.extract_must_have_keywords", return_value=["keyword"]):
            result_state = await self.agent.validate(state)

            self.assertFalse(result_state["validation_passed"])
            self.assertTrue(any("關鍵字檢查失敗" in issue for issue in result_state["validation_issues"]))

if __name__ == '__main__':
    unittest.main()
