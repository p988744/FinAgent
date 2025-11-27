"""Result merging for WikiSearch workflow.

Merges, deduplicates, and ranks results from multiple search tasks.
"""

import logging
from typing import List, Optional

from finagent.agents.wiki_search.models import (
    MergedResult,
    SearchResult,
    WikiSearchState,
)

logger = logging.getLogger(__name__)


class ResultMerger:
    """Merges and deduplicates search results from multiple tasks."""

    def __init__(self, dedup_threshold: float = 0.8):
        """Initialize the result merger.

        Args:
            dedup_threshold: Similarity threshold for deduplication (0-1)
        """
        self.dedup_threshold = dedup_threshold

    def merge_results(self, state: WikiSearchState) -> dict:
        """Merge results from multiple search tasks.

        Args:
            state: Current workflow state with search_results

        Returns:
            State update with merged_results
        """
        search_results = state.get("search_results", [])
        plan = state.get("search_plan", {})
        merge_strategy = plan.get("merge_strategy", "relevance")

        logger.info(f"Merging {len(search_results)} search results with strategy: {merge_strategy}")

        try:
            # Collect all documents
            all_documents = []
            sources = []

            for result in search_results:
                task_id = result.get("task_id", 0)
                documents = result.get("documents", [])
                tool_used = result.get("tool_used", "unknown")

                for doc in documents:
                    # Add source information
                    doc["_source_task"] = task_id
                    doc["_tool_used"] = tool_used
                    all_documents.append(doc)

                if documents:
                    sources.append(f"Task {task_id} ({tool_used})")

            # Deduplicate by document ID or content similarity
            unique_documents = self._deduplicate(all_documents)

            # Rank by relevance
            if merge_strategy == "relevance":
                ranked_documents = self._rank_by_relevance(unique_documents)
            elif merge_strategy == "chronological":
                ranked_documents = self._rank_by_date(unique_documents)
            else:
                ranked_documents = unique_documents

            # Calculate relevance scores
            relevance_scores = self._calculate_relevance_scores(ranked_documents)

            # Create merged result
            merged = MergedResult(
                documents=ranked_documents,
                total_unique=len(ranked_documents),
                sources=sources,
                relevance_scores=relevance_scores,
            )

            logger.info(f"Merged to {len(ranked_documents)} unique documents from {len(sources)} sources")

            return {
                "merged_results": merged.model_dump(),
                "current_stage": "merging",
                "progress": 70,
            }

        except Exception as e:
            logger.error(f"Result merging failed: {e}")
            return {
                "merged_results": MergedResult(
                    documents=[],
                    total_unique=0,
                    sources=[],
                    relevance_scores=[],
                ).model_dump(),
                "current_stage": "merging",
                "progress": 70,
                "error": str(e),
            }

    def _deduplicate(self, documents: List[dict]) -> List[dict]:
        """Deduplicate documents by ID or content.

        Args:
            documents: List of documents to deduplicate

        Returns:
            Deduplicated list of documents
        """
        seen_ids = set()
        seen_content_hashes = set()
        unique_docs = []

        for doc in documents:
            # Get document ID
            doc_id = doc.get("doc_id") or doc.get("id") or doc.get("metadata", {}).get("doc_id")

            # Check by ID first
            if doc_id and doc_id in seen_ids:
                continue

            # Check by content hash
            content = doc.get("text") or doc.get("page_content") or ""
            content_hash = hash(content[:500])  # Use first 500 chars for hash

            if content_hash in seen_content_hashes:
                continue

            # Mark as seen
            if doc_id:
                seen_ids.add(doc_id)
            seen_content_hashes.add(content_hash)

            unique_docs.append(doc)

        return unique_docs

    def _rank_by_relevance(self, documents: List[dict]) -> List[dict]:
        """Rank documents by relevance score.

        Args:
            documents: List of documents to rank

        Returns:
            Sorted list of documents
        """
        def get_score(doc: dict) -> float:
            # Try different score fields
            score = doc.get("score") or doc.get("relevance") or doc.get("_score")
            if score is not None:
                return float(score)
            # Default score based on position
            return 0.5

        return sorted(documents, key=get_score, reverse=True)

    def _rank_by_date(self, documents: List[dict]) -> List[dict]:
        """Rank documents by date (newest first).

        Args:
            documents: List of documents to rank

        Returns:
            Sorted list of documents
        """
        def get_date(doc: dict) -> str:
            metadata = doc.get("metadata", {})
            return metadata.get("document_date") or metadata.get("date") or "0000-00-00"

        return sorted(documents, key=get_date, reverse=True)

    def _calculate_relevance_scores(self, documents: List[dict]) -> List[float]:
        """Calculate relevance scores for ranked documents.

        Args:
            documents: Ranked list of documents

        Returns:
            List of relevance scores
        """
        scores = []
        total = len(documents)

        for i, doc in enumerate(documents):
            # Try to use existing score
            existing_score = doc.get("score") or doc.get("relevance")
            if existing_score is not None:
                scores.append(float(existing_score))
            else:
                # Calculate based on rank position
                # Top document gets 1.0, scores decrease linearly
                score = 1.0 - (i / total) if total > 0 else 1.0
                scores.append(round(score, 3))

        return scores
