"""Tools for Deep Agent.

This module provides @tool-decorated functions for use with Deep Agents.
These wrap the existing BaseTool implementations for compatibility.
"""

from typing import List, Optional
from langchain_core.tools import tool

from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher


# Global instances (initialized lazily)
_retriever: Optional[DocumentRetriever] = None
_hard_searcher: Optional[HardSearcher] = None


def _get_retriever() -> DocumentRetriever:
    """Get or create the document retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = DocumentRetriever()
    return _retriever


def _get_hard_searcher() -> HardSearcher:
    """Get or create the hard searcher instance."""
    global _hard_searcher
    if _hard_searcher is None:
        _hard_searcher = HardSearcher()
    return _hard_searcher


@tool
def semantic_search(query: str, n_results: int = 5) -> str:
    """Perform semantic search on the financial legal document database.

    Use this tool to find documents that are semantically similar to the query.
    Best for finding conceptually related documents even without exact keyword matches.

    Args:
        query: The search query describing what you're looking for
        n_results: Number of results to return (default: 5)

    Returns:
        Formatted search results with source filenames and content excerpts
    """
    try:
        retriever = _get_retriever()
        chunks = retriever.retrieve(query=query, n_results=n_results)

        if not chunks:
            return "No relevant documents found for the query."

        results = []
        for i, chunk in enumerate(chunks, 1):
            filename = chunk.metadata.get("filename", "Unknown")
            relevance = chunk.metadata.get("relevance_score", 0)
            results.append(
                f"[{i}] Source: {filename}\n"
                f"Relevance: {relevance:.2f}\n"
                f"Content: {chunk.text[:500]}...\n"
            )

        return "\n---\n".join(results)
    except Exception as e:
        return f"Error performing semantic search: {str(e)}"


@tool
def keyword_search(keywords: str, max_results: int = 5) -> str:
    """Perform exact keyword search on the financial legal document database.

    Use this tool when you need to find documents that MUST contain specific keywords.
    Best for finding documents with exact terms like bank names, case numbers, or legal terms.

    Args:
        keywords: Comma-separated keywords to search for (all must be present)
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Formatted search results with source filenames and content excerpts
    """
    try:
        # Parse comma-separated keywords
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

        if not keyword_list:
            return "Please provide at least one keyword."

        hard_searcher = _get_hard_searcher()
        chunks = hard_searcher.search(keywords=keyword_list, max_results=max_results)

        if not chunks:
            return f"No documents found containing all keywords: {keyword_list}"

        results = []
        for i, chunk in enumerate(chunks, 1):
            filename = chunk.metadata.get("filename", "Unknown")
            results.append(
                f"[{i}] Source: {filename}\n"
                f"Keywords matched: {keyword_list}\n"
                f"Content: {chunk.text[:500]}...\n"
            )

        return "\n---\n".join(results)
    except Exception as e:
        return f"Error performing keyword search: {str(e)}"


@tool
def hybrid_search(query: str, keywords: str = "", n_results: int = 5) -> str:
    """Perform hybrid search combining semantic and keyword matching.

    Use this tool for comprehensive search that leverages both semantic understanding
    and exact keyword matching. Best for complex queries requiring both approaches.

    Args:
        query: The semantic search query
        keywords: Optional comma-separated keywords that must be present
        n_results: Number of results to return (default: 5)

    Returns:
        Formatted search results combining both search methods
    """
    try:
        retriever = _get_retriever()

        # First, do semantic search
        chunks = retriever.retrieve(query=query, n_results=n_results * 2)

        if not chunks:
            return "No relevant documents found."

        # If keywords provided, filter results
        if keywords.strip():
            keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
            filtered_chunks = []
            for chunk in chunks:
                text_lower = chunk.text.lower()
                if all(kw in text_lower for kw in keyword_list):
                    filtered_chunks.append(chunk)
            chunks = filtered_chunks[:n_results]

            if not chunks:
                return f"No documents found matching both the query and keywords: {keyword_list}"
        else:
            chunks = chunks[:n_results]

        results = []
        for i, chunk in enumerate(chunks, 1):
            filename = chunk.metadata.get("filename", "Unknown")
            relevance = chunk.metadata.get("relevance_score", 0)
            results.append(
                f"[{i}] Source: {filename}\n"
                f"Relevance: {relevance:.2f}\n"
                f"Content: {chunk.text[:500]}...\n"
            )

        return "\n---\n".join(results)
    except Exception as e:
        return f"Error performing hybrid search: {str(e)}"


# Export all tools
FINAGENT_TOOLS = [semantic_search, keyword_search, hybrid_search]
