import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from finagent.agents.query_analysis_agent import QueryAnalysisAgent, ClarificationRequest

class TestQueryAnalysisAgent(unittest.TestCase):
    def setUp(self):
        self.mock_ui_callback = AsyncMock()
        with patch("finagent.agents.query_analysis_agent.ChatOpenAI") as MockLLM:
            self.mock_llm = MockLLM.return_value
            self.agent = QueryAnalysisAgent(ui_callback=self.mock_ui_callback)

    async def test_analyze_query_needs_clarification(self):
        # Mock state
        state = {
            "query": MagicMock(text="模糊查詢"),
            "processing_steps": []
        }

        # Mock LLM response
        mock_result = ClarificationRequest(
            needs_clarification=True,
            reason="Ambiguous",
            questions=["Question 1"],
            understood_intent="Intent",
            confidence="low"
        )
        
        # Mock structured output chain
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_result)
        self.agent.llm.with_structured_output.return_value = mock_chain

        result_state = await self.agent.analyze_query(state)

        self.assertTrue(result_state["clarification_request"]["needs_clarification"])
        self.assertEqual(result_state["clarification_request"]["questions"], ["Question 1"])
        self.mock_ui_callback.on_clarification_requested.assert_called_once()

    async def test_analyze_query_clear(self):
        # Mock state
        state = {
            "query": MagicMock(text="明確查詢"),
            "processing_steps": []
        }

        # Mock LLM response
        mock_result = ClarificationRequest(
            needs_clarification=False,
            reason="",
            questions=[],
            understood_intent="Intent",
            confidence="high"
        )
        
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_result)
        self.agent.llm.with_structured_output.return_value = mock_chain

        result_state = await self.agent.analyze_query(state)

        self.assertFalse(result_state["clarification_request"]["needs_clarification"])

    def test_enrich_query(self):
        state = {
            "query": MagicMock(text="Original"),
            "clarification_response": "Clarification",
            "processing_steps": []
        }

        result_state = self.agent.enrich_query_with_clarification(state)

        self.assertIn("Original", result_state["query"].text)
        self.assertIn("Clarification", result_state["query"].text)

if __name__ == '__main__':
    unittest.main()
