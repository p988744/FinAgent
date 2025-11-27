"""Test cases for CLI Research script.

This module tests the cli_research.py script with both expected and boundary cases.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.agents.plan_execute.models import Plan, PlanTask, QueryInsight
from finagent.models.queries import Query


class TestCLIResearchExpectedCases:
    """Test expected/happy path cases for CLI Research."""

    @pytest.mark.asyncio
    async def test_factual_query(self):
        """Test factual query with specific entities and dates."""
        from scripts.cli_research import research_query

        query_text = "2020年玉山銀行洗錢防制裁罰"

        # Mock the orchestrator
        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            # Create expected query insight
            query_insight = QueryInsight(
                query_type="factual",
                key_entities=["2020年", "玉山銀行", "洗錢防制", "裁罰"],
                search_strategy="hybrid",
                complexity="simple",
                reasoning="Query seeks specific information about a 2020 case involving 玉山銀行.",
            )

            # Create expected plan
            plan = Plan(
                tasks=[
                    PlanTask(id=1, 
                        description="Search for 2020 玉山銀行 洗錢防制 裁罰",
                        tool="hybrid_search",
                        args={"query": "2020年玉山銀行洗錢防制裁罰", "k": 5},
                        status="pending",
                    ),
                    PlanTask(id=2, 
                        description="Filter results by relevance",
                        tool="retriever",
                        args={"query": "玉山銀行洗錢防制", "n_results": 3},
                        status="pending",
                    ),
                ]
            )

            # Mock stream_query to return events
            async def mock_stream():
                yield "query_analyzer", {"query_insight": query_insight}
                yield "planner", {"plan": plan}
                yield "execute_task", {
                    "past_steps": [
                        (
                            {"description": "Search", "tool": "hybrid_search", "status": "completed"},
                            "Found 2 documents...",
                        )
                    ]
                }
                yield "reporter", {"response": "根據查詢結果，2020年玉山銀行因洗錢防制缺失被金管會裁罰500萬元..."}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            # Execute the query
            await research_query(query_text, verbose=False)

            # Verify orchestrator was initialized
            mock_orchestrator.assert_called_once()
            # Verify stream_query was called with correct parameters
            mock_instance.stream_query.assert_called_once()
            call_kwargs = mock_instance.stream_query.call_args[1]
            assert call_kwargs["use_plan_execute"] is True
            assert call_kwargs["query"].text == query_text

    @pytest.mark.asyncio
    async def test_analytical_query(self):
        """Test analytical query requiring synthesis."""
        from scripts.cli_research import research_query

        query_text = "分析銀行業洗錢防制的主要問題"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            query_insight = QueryInsight(
                query_type="analytical",
                key_entities=["銀行業", "洗錢防制", "主要問題"],
                search_strategy="semantic",
                complexity="medium",
                reasoning="Query requires analysis and synthesis of multiple sources.",
            )

            plan = Plan(
                tasks=[
                    PlanTask(id=3, 
                        description="Search for bank AML issues",
                        tool="retriever",
                        args={"query": "銀行業洗錢防制問題", "n_results": 10},
                        status="pending",
                    )
                ]
            )

            async def mock_stream():
                yield "query_analyzer", {"query_insight": query_insight}
                yield "planner", {"plan": plan}
                yield "execute_task", {
                    "past_steps": [({"description": "Search", "tool": "retriever", "status": "completed"}, "Found 5 documents...")]
                }
                yield "reporter", {"response": "銀行業洗錢防制主要問題包括：1. 內部控制不足..."}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            await research_query(query_text, verbose=True)

            mock_orchestrator.assert_called_once()
            mock_instance.stream_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_comparative_query(self):
        """Test comparative query with multiple entities."""
        from scripts.cli_research import research_query

        query_text = "比較玉山銀行和台新銀行的裁罰案件"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            query_insight = QueryInsight(
                query_type="comparative",
                key_entities=["玉山銀行", "台新銀行", "裁罰案件"],
                search_strategy="hybrid",
                complexity="medium",
                reasoning="Query requires comparison of two banks' penalty cases.",
            )

            plan = Plan(
                tasks=[
                    PlanTask(id=4, 
                        description="Search for 玉山銀行 penalties",
                        tool="hybrid_search",
                        args={"query": "玉山銀行裁罰", "k": 5},
                        status="pending",
                    ),
                    PlanTask(id=5, 
                        description="Search for 台新銀行 penalties",
                        tool="hybrid_search",
                        args={"query": "台新銀行裁罰", "k": 5},
                        status="pending",
                    ),
                ]
            )

            async def mock_stream():
                yield "query_analyzer", {"query_insight": query_insight}
                yield "planner", {"plan": plan}
                yield "execute_task", {"past_steps": [({"description": "Search 1", "tool": "hybrid_search", "status": "completed"}, "Found 3 documents...")]}
                yield "execute_task", {"past_steps": [({"description": "Search 2", "tool": "hybrid_search", "status": "completed"}, "Found 2 documents...")]}
                yield "reporter", {"response": "比較分析：玉山銀行共有3件裁罰案件...台新銀行共有2件..."}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            await research_query(query_text, verbose=False)

            mock_orchestrator.assert_called_once()


class TestCLIResearchBoundaryCases:
    """Test boundary and edge cases for CLI Research."""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test handling of empty query string."""
        from scripts.cli_research import research_query
        from pydantic import ValidationError

        query_text = ""

        # Empty query should raise ValidationError from Query model (min length 1)
        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            # Expect ValidationError to be raised
            with pytest.raises(ValidationError) as excinfo:
                await research_query(query_text, verbose=False)

            # Verify error is about string length
            assert "String should have at least 1 character" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """Test handling of very long query (>500 characters)."""
        from scripts.cli_research import research_query

        query_text = "我想要查詢關於" + "玉山銀行洗錢防制裁罰案件" * 30  # ~300+ characters

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            query_insight = QueryInsight(
                query_type="factual",
                key_entities=["玉山銀行", "洗錢防制", "裁罰案件"],
                search_strategy="hybrid",
                complexity="simple",
                reasoning="Query is long but intent is clear.",
            )

            async def mock_stream():
                yield "query_analyzer", {"query_insight": query_insight}
                yield "planner", {"plan": Plan(tasks=[PlanTask(id=6, description="Search", tool="hybrid_search", args={"query": query_text[:200], "k": 5}, status="pending")])}
                yield "execute_task", {"past_steps": [({"description": "Search", "tool": "hybrid_search", "status": "completed"}, "Found documents...")]}
                yield "reporter", {"response": "查詢結果..."}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            await research_query(query_text, verbose=False)

            mock_orchestrator.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_special_characters(self):
        """Test query with special characters and symbols."""
        from scripts.cli_research import research_query

        query_text = "玉山銀行@#$%裁罰！？（2020年）"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            query_insight = QueryInsight(
                query_type="factual",
                key_entities=["玉山銀行", "裁罰", "2020年"],
                search_strategy="hybrid",
                complexity="simple",
                reasoning="Query has special characters but intent is clear.",
            )

            async def mock_stream():
                yield "query_analyzer", {"query_insight": query_insight}
                yield "planner", {"plan": Plan(tasks=[PlanTask(id=7, description="Search", tool="hybrid_search", args={"query": "玉山銀行 裁罰 2020年", "k": 5}, status="pending")])}
                yield "execute_task", {"past_steps": [({"description": "Search", "tool": "hybrid_search", "status": "completed"}, "Found documents...")]}
                yield "reporter", {"response": "查詢結果..."}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            await research_query(query_text, verbose=False)

            mock_orchestrator.assert_called_once()

    @pytest.mark.asyncio
    async def test_rag_not_available(self):
        """Test when RAG system is not available."""
        from scripts.cli_research import research_query

        query_text = "玉山銀行裁罰"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()
            mock_instance.use_rag = False  # RAG not available
            mock_orchestrator.return_value = mock_instance

            # Should handle gracefully
            await research_query(query_text, verbose=False)

            mock_orchestrator.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_error_during_execution(self):
        """Test handling of errors during workflow execution."""
        from scripts.cli_research import research_query

        query_text = "玉山銀行裁罰"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            async def mock_stream():
                yield "query_analyzer", {
                    "query_insight": QueryInsight(
                        query_type="factual",
                        key_entities=["玉山銀行", "裁罰"],
                        search_strategy="hybrid",
                        complexity="simple",
                        reasoning="Test",
                    )
                }
                yield "planner", {"plan": Plan(tasks=[PlanTask(id=8, description="Search", tool="hybrid_search", args={}, status="pending")])}
                # Simulate error
                raise Exception("Workflow execution error")

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            # Should not crash, but handle error gracefully
            await research_query(query_text, verbose=False)

            mock_orchestrator.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_response_generated(self):
        """Test when workflow completes but no response is generated."""
        from scripts.cli_research import research_query

        query_text = "玉山銀行裁罰"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            async def mock_stream():
                yield "query_analyzer", {
                    "query_insight": QueryInsight(
                        query_type="factual",
                        key_entities=["玉山銀行", "裁罰"],
                        search_strategy="hybrid",
                        complexity="simple",
                        reasoning="Test",
                    )
                }
                yield "planner", {"plan": Plan(tasks=[])}
                # No reporter response
                yield "reporter", {"response": None}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            await research_query(query_text, verbose=False)

            mock_orchestrator.assert_called_once()

    @pytest.mark.asyncio
    async def test_unicode_and_emoji_in_query(self):
        """Test query with unicode characters and emojis."""
        from scripts.cli_research import research_query

        query_text = "🏦 玉山銀行 💰 裁罰 📅 2020年"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            query_insight = QueryInsight(
                query_type="factual",
                key_entities=["玉山銀行", "裁罰", "2020年"],
                search_strategy="hybrid",
                complexity="simple",
                reasoning="Query has emojis but intent is clear.",
            )

            async def mock_stream():
                yield "query_analyzer", {"query_insight": query_insight}
                yield "planner", {"plan": Plan(tasks=[PlanTask(id=9, description="Search", tool="hybrid_search", args={"query": "玉山銀行 裁罰 2020年", "k": 5}, status="pending")])}
                yield "execute_task", {"past_steps": [({"description": "Search", "tool": "hybrid_search", "status": "completed"}, "Found documents...")]}
                yield "reporter", {"response": "查詢結果..."}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            await research_query(query_text, verbose=False)

            mock_orchestrator.assert_called_once()


class TestCLIResearchProgressTracking:
    """Test progress tracking and display functionality."""

    @pytest.mark.asyncio
    async def test_progress_with_multiple_tasks(self):
        """Test progress tracking with multiple parallel tasks."""
        from scripts.cli_research import research_query

        query_text = "銀行業裁罰案件"

        with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
            mock_instance = MagicMock()

            plan = Plan(
                tasks=[
                    PlanTask(id=10, description="Task 1", tool="retriever", args={}, status="pending"),
                    PlanTask(id=11, description="Task 2", tool="hard_search", args={}, status="pending"),
                    PlanTask(id=12, description="Task 3", tool="hybrid_search", args={}, status="pending"),
                ]
            )

            async def mock_stream():
                yield "query_analyzer", {
                    "query_insight": QueryInsight(
                        query_type="factual",
                        key_entities=["銀行業", "裁罰案件"],
                        search_strategy="hybrid",
                        complexity="medium",
                        reasoning="Test",
                    )
                }
                yield "planner", {"plan": plan}
                yield "execute_task", {"past_steps": [({"description": "Task 1", "tool": "retriever", "status": "completed"}, "Result 1")]}
                yield "execute_task", {"past_steps": [({"description": "Task 2", "tool": "hard_search", "status": "completed"}, "Result 2")]}
                yield "execute_task", {"past_steps": [({"description": "Task 3", "tool": "hybrid_search", "status": "completed"}, "Result 3")]}
                yield "reporter", {"response": "Final report..."}

            mock_instance.stream_query.return_value = mock_stream()
            mock_instance.use_rag = True
            mock_orchestrator.return_value = mock_instance

            await research_query(query_text, verbose=True)

            mock_orchestrator.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
