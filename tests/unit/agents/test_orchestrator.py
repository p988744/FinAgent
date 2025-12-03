import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query
from finagent.models.answers import LegalAnswer, ConfidenceLevel

class TestAgentOrchestrator(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        with patch("finagent.agents.orchestrator.DocumentRetriever") as MockRetriever, \
             patch("finagent.agents.orchestrator.PlanExecuteWorkflow") as MockPlanExecute, \
             patch("finagent.agents.orchestrator.WikiBuilderWorkflow") as MockWikiBuilder, \
             patch("finagent.agents.orchestrator.WikiSearchWorkflow") as MockWikiSearch, \
             patch("finagent.agents.orchestrator.HardSearcher") as MockHardSearcher, \
             patch("finagent.agents.orchestrator.create_finagent_deep_agent") as MockDeepAgent:
            
            self.mock_retriever = MockRetriever.return_value
            self.mock_retriever.collection_exists.return_value = True
            
            self.mock_plan_execute = MockPlanExecute.return_value
            self.mock_wiki_builder = MockWikiBuilder.return_value
            
            self.orchestrator = AgentOrchestrator(enable_query_logging=False)

    async def test_process_query_success(self):
        query = Query(text="test query")
        
        # Mock _process_with_plan_execute
        mock_answer = LegalAnswer(
            executive_summary="Summary",
            key_findings=["Finding 1"],
            detailed_analysis="Analysis",
            citations=[],
            confidence_score=ConfidenceLevel.HIGH,
            confidence_explanation="High confidence",
            limitations=[],
            processing_steps=[]
        )
        
        with patch.object(self.orchestrator, "_process_with_plan_execute", return_value=mock_answer):
            result = await self.orchestrator.process_query(query)
            
            self.assertEqual(result, mock_answer)
            self.assertIsNotNone(result.processing_time_ms)

    async def test_process_with_plan_execute_success(self):
        query = Query(text="test query")
        
        # Mock graph stream
        mock_event = {"node": {"response": "Executive Summary\n\n- Key Finding 1\n\nDetailed Analysis"}}
        
        async def mock_astream(*args, **kwargs):
            yield mock_event
            
        self.orchestrator.plan_execute_workflow.graph.astream = mock_astream
        
        result = await self.orchestrator._process_with_plan_execute(query)
        
        self.assertIsInstance(result, LegalAnswer)
        self.assertIn("Executive Summary", result.executive_summary)
        self.assertIn("Key Finding 1", result.key_findings[0])

    async def test_process_with_plan_execute_failure(self):
        query = Query(text="test query")
        
        # Mock graph stream yielding no response
        async def mock_astream(*args, **kwargs):
            yield {"node": {}}
            
        self.orchestrator.plan_execute_workflow.graph.astream = mock_astream
        
        result = await self.orchestrator._process_with_plan_execute(query)
        
        self.assertIn("v1.1 workflow failed", result.executive_summary)

if __name__ == '__main__':
    unittest.main()
