import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from finagent.agents.planning_agent import PlanningAgent
from finagent.models.plan import QueryAnalysis, PlanTask, ResearchPlan

class TestPlanningAgent(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.mock_ui_callback = AsyncMock()
        
        with patch("finagent.agents.planning_agent.ChatOpenAI", return_value=self.mock_llm):
            self.agent = PlanningAgent(ui_callback=self.mock_ui_callback)

    async def test_plan_success(self):
        # Mock state
        state = {
            "query": MagicMock(text="2020年玉山銀行裁罰案"),
            "processing_steps": [],
            "errors": []
        }

        # Mock _analyze_query (since it's complex and uses LLM/regex)
        mock_analysis = QueryAnalysis(
            keywords=["玉山銀行", "裁罰"],
            must_have_keywords=[],
            entity_type="bank",
            jurisdiction="金管會",
            time_period="2020",
            query_type="enforcement_search",
            complexity="medium"
        )
        
        with patch.object(self.agent, "_analyze_query", return_value=mock_analysis):
            result_state = await self.agent.plan(state)

            self.assertIn("plan", result_state)
            self.assertIn("research_tasks", result_state)
            self.assertIn("todos", result_state)
            self.assertEqual(len(result_state["research_tasks"]), 3) # Vector, Validation, Answer
            self.assertEqual(result_state["plan"]["analysis"]["jurisdiction"], "金管會")
            
            # Verify callback
            self.mock_ui_callback.on_plan_created.assert_called_once()
            self.mock_ui_callback.on_todo_list_created.assert_called_once()

    async def test_plan_complex_query(self):
        # Mock state
        state = {
            "query": MagicMock(text="查詢玉山銀行洗錢防制裁罰"),
            "processing_steps": [],
            "errors": []
        }

        # Mock analysis for complex query
        mock_analysis = QueryAnalysis(
            keywords=["玉山銀行", "洗錢防制"],
            must_have_keywords=["洗錢防制"],
            entity_type="bank",
            jurisdiction="金管會",
            time_period=None,
            query_type="enforcement_search",
            complexity="complex"
        )
        
        with patch.object(self.agent, "_analyze_query", return_value=mock_analysis):
            result_state = await self.agent.plan(state)

            # Should include hard search task
            self.assertEqual(len(result_state["research_tasks"]), 4) # Vector, Hard, Validation, Answer
            self.assertTrue(result_state["plan"]["use_hard_search"])

    async def test_plan_failure(self):
        state = {
            "query": MagicMock(text="error query"),
            "processing_steps": [],
            "errors": []
        }
        
        with patch.object(self.agent, "_analyze_query", side_effect=Exception("Analysis failed")):
            result_state = await self.agent.plan(state)
            
            self.assertIn("規劃失敗", result_state["errors"][0])
            # Should have fallback plan
            self.assertIn("plan", result_state)
            self.assertEqual(len(result_state["plan"]["tasks"]), 3)

if __name__ == '__main__':
    unittest.main()
