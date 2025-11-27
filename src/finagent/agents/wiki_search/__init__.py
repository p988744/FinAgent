"""Wiki Search Agent module.

Enhanced workflow for wiki-style search and report generation.
Features:
- Query analysis to understand user intent
- Multi-tool search planning (semantic + keyword)
- Parallel search execution
- Result deduplication and ranking
- Wiki-style report synthesis with citations
"""

from finagent.agents.wiki_search.graph import WikiSearchWorkflow
from finagent.agents.wiki_search.models import (
    WikiSearchState,
    SearchStrategy,
    QueryType,
    QueryInsight,
    SearchTask,
    SearchPlan,
    SearchResult,
    MergedResult,
    WikiCitation,
)
from finagent.agents.wiki_search.planner import SearchPlanner
from finagent.agents.wiki_search.merger import ResultMerger

__all__ = [
    # Main workflow
    "WikiSearchWorkflow",
    # State and models
    "WikiSearchState",
    "SearchStrategy",
    "QueryType",
    "QueryInsight",
    "SearchTask",
    "SearchPlan",
    "SearchResult",
    "MergedResult",
    "WikiCitation",
    # Components
    "SearchPlanner",
    "ResultMerger",
]
