"""Test cases for CLI Retrieval script.

This module tests the cli_retrieval.py script with both expected and boundary cases.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, create_autospec

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.agents.plan_execute.models import QueryInsight
from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher


def create_mock_retriever():
    """Create a mock DocumentRetriever that passes Pydantic validation."""
    mock = create_autospec(DocumentRetriever, instance=True)
    mock.collection_exists.return_value = True
    return mock


def create_mock_searcher():
    """Create a mock HardSearcher that passes Pydantic validation."""
    mock = create_autospec(HardSearcher, instance=True)
    return mock


class TestCLIRetrievalExpectedCases:
    """Test expected/happy path cases for CLI Retrieval."""

    @pytest.mark.asyncio
    async def test_auto_mode_factual_query(self):
        """Test auto mode with factual query selecting hybrid search."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "2020年玉山銀行洗錢防制裁罰"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.QueryAnalyzerAgent") as mock_analyzer_class:

            # Mock retriever
            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            # Mock hard searcher
            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            # Mock query analyzer
            mock_analyzer = MagicMock()
            query_insight = QueryInsight(
                query_type="factual",
                key_entities=["2020年", "玉山銀行", "洗錢防制", "裁罰"],
                search_strategy="hybrid",
                complexity="simple",
                reasoning="Query has specific terms and concepts.",
            )

            async def mock_analyze(state):
                return {"query_insight": query_insight}

            mock_analyzer.analyze = mock_analyze
            mock_analyzer_class.return_value = mock_analyzer

            # Mock hybrid tool
            with patch("scripts.cli_retrieval.HybridRetrieverTool") as mock_hybrid_tool:
                mock_tool_instance = MagicMock()
                mock_tool_instance._run.return_value = "Found 2 relevant documents:\n\n1. Document A\n2. Document B"
                mock_hybrid_tool.return_value = mock_tool_instance

                await retrieval_search(query_text, tool_choice="auto", num_results=5)

                # Verify analyzer was used
                mock_analyzer_class.assert_called_once()
                # Verify tool was executed
                mock_tool_instance._run.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_semantic_search(self):
        """Test manual semantic search selection."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "分析銀行業洗錢防制的主要問題"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.RetrieverTool") as mock_retriever_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found 5 relevant documents:\n\n1. Doc 1\n2. Doc 2\n3. Doc 3\n4. Doc 4\n5. Doc 5"
            mock_retriever_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="semantic", num_results=10)

            # Verify semantic tool was used
            mock_retriever_tool.assert_called_once_with(retriever=mock_retriever)
            mock_tool_instance._run.assert_called_once_with(query=query_text, n_results=10)

    @pytest.mark.asyncio
    async def test_manual_keyword_search(self):
        """Test manual keyword search selection."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "金管會 裁罰 玉山銀行"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.HardSearchTool") as mock_keyword_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found 3 documents with ALL keywords:\n\n1. Doc A\n2. Doc B\n3. Doc C"
            mock_keyword_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="keyword", num_results=5)

            # Verify keyword tool was used
            mock_keyword_tool.assert_called_once_with(hard_searcher=mock_searcher)
            # Keywords should be extracted from query
            call_args = mock_tool_instance._run.call_args
            assert "keywords" in call_args[1]

    @pytest.mark.asyncio
    async def test_manual_hybrid_search(self):
        """Test manual hybrid search selection."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "2020年銀行洗錢防制"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.HybridRetrieverTool") as mock_hybrid_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found 4 documents (hybrid search):\n\n1. Doc 1\n2. Doc 2\n3. Doc 3\n4. Doc 4"
            mock_hybrid_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="hybrid", num_results=7)

            # Verify hybrid tool was used with correct weights
            mock_hybrid_tool.assert_called_once_with(retriever=mock_retriever, semantic_weight=0.6, keyword_weight=0.4)
            mock_tool_instance._run.assert_called_once_with(query=query_text, k=7)


class TestCLIRetrievalBoundaryCases:
    """Test boundary and edge cases for CLI Retrieval."""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test handling of empty query string."""
        from scripts.cli_retrieval import retrieval_search

        query_text = ""

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.HybridRetrieverTool") as mock_hybrid_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "No documents found."
            mock_hybrid_tool.return_value = mock_tool_instance

            # Should handle empty query gracefully
            await retrieval_search(query_text, tool_choice="hybrid", num_results=5)

            mock_tool_instance._run.assert_called_once()

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """Test handling of very long query (>1000 characters)."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "玉山銀行洗錢防制裁罰案件" * 100  # ~1000+ characters

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.HybridRetrieverTool") as mock_hybrid_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found documents..."
            mock_hybrid_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="hybrid", num_results=5)

            # Should handle long query
            mock_tool_instance._run.assert_called_once()

    @pytest.mark.asyncio
    async def test_single_character_query(self):
        """Test handling of single character query."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "銀"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.RetrieverTool") as mock_retriever_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found many documents..."
            mock_retriever_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="semantic", num_results=5)

            mock_tool_instance._run.assert_called_once()

    @pytest.mark.asyncio
    async def test_collection_not_exists(self):
        """Test when vector database collection doesn't exist."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "玉山銀行裁罰"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class:

            mock_retriever = MagicMock()
            mock_retriever.collection_exists.return_value = False  # No collection
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            # Should detect and report error gracefully
            await retrieval_search(query_text, tool_choice="auto", num_results=5)

            # Should not attempt to search
            mock_retriever.collection_exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_tool_choice(self):
        """Test invalid tool choice parameter."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "玉山銀行裁罰"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            # Should handle invalid tool choice gracefully
            await retrieval_search(query_text, tool_choice="invalid_tool", num_results=5)

    @pytest.mark.asyncio
    async def test_num_results_edge_cases(self):
        """Test edge cases for num_results parameter."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "玉山銀行裁罰"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.RetrieverTool") as mock_retriever_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found 1 document"
            mock_retriever_tool.return_value = mock_tool_instance

            # Test num_results = 1
            await retrieval_search(query_text, tool_choice="semantic", num_results=1)
            mock_tool_instance._run.assert_called_with(query=query_text, n_results=1)

            # Test num_results = 100 (large number)
            await retrieval_search(query_text, tool_choice="semantic", num_results=100)
            mock_tool_instance._run.assert_called_with(query=query_text, n_results=100)

    @pytest.mark.asyncio
    async def test_search_tool_exception(self):
        """Test handling of exceptions during search."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "玉山銀行裁罰"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.RetrieverTool") as mock_retriever_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.side_effect = Exception("Search failed")
            mock_retriever_tool.return_value = mock_tool_instance

            # Should handle exception gracefully
            await retrieval_search(query_text, tool_choice="semantic", num_results=5)

    @pytest.mark.asyncio
    async def test_query_with_only_stopwords(self):
        """Test query containing only common stopwords."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "的 是 在 有 和"  # Common Chinese stopwords

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.RetrieverTool") as mock_retriever_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "No meaningful results."
            mock_retriever_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="semantic", num_results=5)

            mock_tool_instance._run.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_mixed_languages(self):
        """Test query with mixed Chinese and English."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "玉山銀行 anti-money laundering penalties 2020"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.HybridRetrieverTool") as mock_hybrid_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found bilingual documents..."
            mock_hybrid_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="hybrid", num_results=5)

            mock_tool_instance._run.assert_called_once()


class TestCLIRetrievalAutoModeSelection:
    """Test auto mode tool selection logic."""

    @pytest.mark.asyncio
    async def test_auto_mode_selects_semantic_for_analytical_query(self):
        """Test that auto mode selects semantic search for analytical queries."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "分析金融業法規遵循的挑戰"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.QueryAnalyzerAgent") as mock_analyzer_class, patch(
            "scripts.cli_retrieval.RetrieverTool"
        ) as mock_retriever_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            # Analyzer recommends semantic
            mock_analyzer = MagicMock()
            query_insight = QueryInsight(
                query_type="analytical",
                key_entities=["金融業", "法規遵循", "挑戰"],
                search_strategy="semantic",
                complexity="medium",
                reasoning="Analytical query requires conceptual search.",
            )

            async def mock_analyze(state):
                return {"query_insight": query_insight}

            mock_analyzer.analyze = mock_analyze
            mock_analyzer_class.return_value = mock_analyzer

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found semantic results..."
            mock_retriever_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="auto", num_results=5)

            # Verify semantic tool was selected
            mock_retriever_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_mode_selects_keyword_for_explicit_keyword_query(self):
        """Test that auto mode selects keyword search when query explicitly requests it."""
        from scripts.cli_retrieval import retrieval_search

        query_text = "找出包含「金管會」和「裁罰」的所有文件"

        with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class, patch(
            "scripts.cli_retrieval.HardSearcher"
        ) as mock_searcher_class, patch("scripts.cli_retrieval.QueryAnalyzerAgent") as mock_analyzer_class, patch(
            "scripts.cli_retrieval.HardSearchTool"
        ) as mock_keyword_tool:

            mock_retriever = create_mock_retriever()
            mock_retriever_class.return_value = mock_retriever

            mock_searcher = create_mock_searcher()
            mock_searcher_class.return_value = mock_searcher

            # Analyzer recommends keyword
            mock_analyzer = MagicMock()
            query_insight = QueryInsight(
                query_type="keyword_search",
                key_entities=["金管會", "裁罰"],
                search_strategy="keyword",
                complexity="simple",
                reasoning="Query explicitly requests exact keyword matching.",
            )

            async def mock_analyze(state):
                return {"query_insight": query_insight}

            mock_analyzer.analyze = mock_analyze
            mock_analyzer_class.return_value = mock_analyzer

            mock_tool_instance = MagicMock()
            mock_tool_instance._run.return_value = "Found keyword results..."
            mock_keyword_tool.return_value = mock_tool_instance

            await retrieval_search(query_text, tool_choice="auto", num_results=5)

            # Verify keyword tool was selected
            mock_keyword_tool.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
