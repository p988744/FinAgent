"""Hard search tool for keyword matching."""

import asyncio
from typing import List, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from finagent.document_processing.hard_searcher import HardSearcher


class HardSearchInput(BaseModel):
    """Input for the hard search tool."""

    keywords: List[str] = Field(description="List of keywords to search for")
    max_results: int = Field(default=5, description="Maximum number of results to return")

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Override to handle string input for keywords."""
        if isinstance(obj, dict) and "keywords" in obj:
            kw = obj["keywords"]
            # Convert string to list if necessary
            if isinstance(kw, str):
                # Split by common delimiters (space, comma, Chinese comma)
                import re
                obj = obj.copy()
                obj["keywords"] = [k.strip() for k in re.split(r'[,，\s]+', kw) if k.strip()]
        return super().model_validate(obj, *args, **kwargs)


class HardSearchTool(BaseTool):
    """Tool for finding documents containing specific keywords (exact match)."""

    name: str = "hard_search"
    description: str = "Useful for finding documents that MUST contain specific keywords."
    args_schema: Type[BaseModel] = HardSearchInput
    hard_searcher: HardSearcher = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, keywords: List[str], max_results: int = 5) -> str:
        """Run the hard search tool synchronously."""
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

    async def _arun(self, keywords: List[str], max_results: int = 5) -> str:
        """Run the hard search tool asynchronously."""
        # Since HardSearcher.search is synchronous, we run it in a thread
        return await asyncio.to_thread(self._run, keywords=keywords, max_results=max_results)
