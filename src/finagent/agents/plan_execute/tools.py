"""Tools for the Plan-and-Execute agent flow."""

from typing import List, Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever


class RetrieverInput(BaseModel):
    """Input for the retriever tool."""

    query: str = Field(description="The query string to search for")
    n_results: int = Field(default=5, description="Number of results to return")


class RetrieverTool(BaseTool):
    """Tool for retrieving documents using semantic search."""

    name: str = "retriever"
    description: str = "Useful for finding relevant documents based on semantic similarity."
    args_schema: Type[BaseModel] = RetrieverInput
    retriever: DocumentRetriever = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str, n_results: int = 5) -> str:
        """Run the retriever tool."""
        try:
            chunks = self.retriever.retrieve(query=query, n_results=n_results)
            if not chunks:
                return "No relevant documents found."
            
            results = []
            for i, chunk in enumerate(chunks, 1):
                filename = chunk.metadata.get("filename", "Unknown")
                results.append(f"[{i}] Source: {filename}\nContent: {chunk.text}\n")
            
            return "\n---\n".join(results)
        except Exception as e:
            return f"Error retrieving documents: {str(e)}"


class HardSearchInput(BaseModel):
    """Input for the hard search tool."""

    keywords: List[str] = Field(description="List of keywords to search for")
    max_results: int = Field(default=5, description="Maximum number of results to return")


class HardSearchTool(BaseTool):
    """Tool for finding documents containing specific keywords (exact match)."""

    name: str = "hard_search"
    description: str = "Useful for finding documents that MUST contain specific keywords."
    args_schema: Type[BaseModel] = HardSearchInput
    hard_searcher: HardSearcher = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, keywords: List[str], max_results: int = 5) -> str:
        """Run the hard search tool."""
        try:
            chunks = self.hard_searcher.search(keywords=keywords, max_results=max_results)
            if not chunks:
                return f"No documents found containing all keywords: {keywords}"
            
            results = []
            for i, chunk in enumerate(chunks, 1):
                filename = chunk.metadata.get("filename", "Unknown")
                results.append(f"[{i}] Source: {filename}\nContent: {chunk.text}\n")
            
            return "\n---\n".join(results)
        except Exception as e:
            return f"Error performing hard search: {str(e)}"
