"""Retriever tool for semantic search."""

import asyncio
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

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
        """Run the retriever tool synchronously."""
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

    async def _arun(self, query: str, n_results: int = 5) -> str:
        """Run the retriever tool asynchronously."""
        # Since DocumentRetriever.retrieve is synchronous, we run it in a thread
        return await asyncio.to_thread(self._run, query=query, n_results=n_results)
