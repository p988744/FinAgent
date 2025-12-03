"""LangGraph workflow for the enhanced Wiki Search agent.

This workflow provides multi-tool retrieval with query analysis and planning:
1. analyze_query - Understand query intent and extract entities
2. plan_retrieval - Create a search plan with multiple tasks
3. execute_searches - Run semantic/keyword searches in parallel
4. merge_results - Deduplicate and rank results
5. synthesize - Generate wiki-style report with citations
"""

import asyncio
import logging
import time

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from finagent.agents.wiki_search.merger import ResultMerger
from finagent.agents.wiki_search.models import (
    SearchResult,
    SearchStrategy,
    WikiSearchState,
)
from finagent.agents.wiki_search.planner import SearchPlanner
from finagent.agents.wiki_search.prompts import SYNTHESIZE_PROMPT
from finagent.config import settings
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever

logger = logging.getLogger(__name__)


class WikiSearchWorkflow:
    """Enhanced workflow for wiki-style search and report generation.

    Features:
    - Query analysis to understand user intent
    - Multi-tool search planning (semantic + keyword)
    - Parallel search execution
    - Result deduplication and ranking
    - Wiki-style report synthesis with citations
    """

    def __init__(
        self,
        retriever: DocumentRetriever | None = None,
        hard_searcher: HardSearcher | None = None,
    ):
        """Initialize the workflow.

        Args:
            retriever: Document retriever for semantic search
            hard_searcher: Hard searcher for keyword search
        """
        self.retriever = retriever
        self.hard_searcher = hard_searcher

        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.effective_llm_api_key,
            base_url=settings.effective_llm_base_url,
            temperature=0,
        )

        self.planner = SearchPlanner()
        self.merger = ResultMerger()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the enhanced LangGraph workflow.

        Flow:
        START → analyze_query → plan_retrieval → execute_searches
              → merge_results → synthesize → END
        """
        workflow = StateGraph(WikiSearchState)

        # Add nodes
        workflow.add_node("analyze_query", self.analyze_query_node)
        workflow.add_node("plan_retrieval", self.plan_retrieval_node)
        workflow.add_node("execute_searches", self.execute_searches_node)
        workflow.add_node("merge_results", self.merge_results_node)
        workflow.add_node("synthesize", self.synthesize_node)

        # Set entry point
        workflow.set_entry_point("analyze_query")

        # Add edges
        workflow.add_edge("analyze_query", "plan_retrieval")
        workflow.add_edge("plan_retrieval", "execute_searches")
        workflow.add_edge("execute_searches", "merge_results")
        workflow.add_edge("merge_results", "synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    async def analyze_query_node(self, state: WikiSearchState) -> dict:
        """Analyze the user query to understand intent and entities.

        Args:
            state: Current workflow state

        Returns:
            State update with query_insight
        """
        logger.info(f"Analyzing query: {state['input'][:50]}...")

        try:
            result = await self.planner.analyze_query(state)
            result["current_stage"] = "analyzing"
            result["progress"] = 20
            return result
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "query_insight": None,
                "current_stage": "analyzing",
                "progress": 20,
                "error": str(e),
            }

    async def plan_retrieval_node(self, state: WikiSearchState) -> dict:
        """Create a search plan based on query analysis.

        Args:
            state: Current workflow state with query_insight

        Returns:
            State update with search_plan
        """
        logger.info("Creating search plan...")

        try:
            result = await self.planner.create_search_plan(state)
            result["current_stage"] = "planning"
            result["progress"] = 35
            return result
        except Exception as e:
            logger.error(f"Search planning failed: {e}")
            # Fallback to simple semantic search
            return {
                "search_plan": {
                    "tasks": [
                        {
                            "id": 1,
                            "description": "語意搜尋",
                            "tool": "retriever",
                            "query": state["input"],
                            "filters": {},
                            "priority": 1,
                        }
                    ],
                    "strategy": SearchStrategy.SEMANTIC.value,
                    "max_results_per_task": 5,
                    "merge_strategy": "relevance",
                },
                "current_stage": "planning",
                "progress": 35,
            }

    async def execute_searches_node(self, state: WikiSearchState) -> dict:
        """Execute search tasks from the plan.

        Args:
            state: Current workflow state with search_plan

        Returns:
            State update with search_results
        """
        plan = state.get("search_plan", {})
        tasks = plan.get("tasks", [])
        max_results = plan.get("max_results_per_task", 5)

        logger.info(f"Executing {len(tasks)} search tasks...")

        search_results = []

        # Execute tasks (can be parallelized for independent tasks)
        for task in tasks:
            task_id = task.get("id", 0)
            tool = task.get("tool", "retriever")
            query = task.get("query", state["input"])

            logger.info(f"Task {task_id}: {tool} - {query[:30]}...")

            start_time = time.time()

            try:
                if tool == "retriever" and self.retriever:
                    docs = await self._execute_semantic_search(query, max_results)
                elif tool == "hard_search" and self.hard_searcher:
                    keywords = task.get("filters", {}).get("keywords", [query])
                    docs = await self._execute_keyword_search(keywords, max_results)
                elif tool == "hybrid_search":
                    # Combine both searches
                    semantic_docs = await self._execute_semantic_search(query, max_results) if self.retriever else []
                    keyword_docs = await self._execute_keyword_search([query], max_results) if self.hard_searcher else []
                    docs = semantic_docs + keyword_docs
                else:
                    # Fallback to semantic if available
                    docs = await self._execute_semantic_search(query, max_results) if self.retriever else []

                execution_time = int((time.time() - start_time) * 1000)

                result = SearchResult(
                    task_id=task_id,
                    tool_used=tool,
                    query=query,
                    documents=[self._doc_to_dict(d) for d in docs],
                    result_count=len(docs),
                    execution_time_ms=execution_time,
                    success=True,
                )

            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                execution_time = int((time.time() - start_time) * 1000)
                result = SearchResult(
                    task_id=task_id,
                    tool_used=tool,
                    query=query,
                    documents=[],
                    result_count=0,
                    execution_time_ms=execution_time,
                    success=False,
                    error=str(e),
                )

            search_results.append(result.model_dump())

        total_docs = sum(r.get("result_count", 0) for r in search_results)
        logger.info(f"Search execution complete: {total_docs} documents found")

        return {
            "search_results": search_results,
            "current_stage": "searching",
            "progress": 55,
        }

    async def _execute_semantic_search(
        self, query: str, n_results: int
    ) -> list[Document]:
        """Execute semantic search using the retriever.

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of retrieved documents
        """
        if not self.retriever:
            return []

        # Run in thread since retriever.retrieve is synchronous
        chunks = await asyncio.to_thread(
            self.retriever.retrieve, query=query, n_results=n_results
        )

        # Convert to Document objects
        return [
            Document(
                page_content=chunk.text,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]

    async def _execute_keyword_search(
        self, keywords: list[str], max_results: int
    ) -> list[Document]:
        """Execute keyword search using the hard searcher.

        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of results

        Returns:
            List of matching documents
        """
        if not self.hard_searcher:
            return []

        # Run in thread since hard_searcher.search is synchronous
        chunks = await asyncio.to_thread(
            self.hard_searcher.search, keywords=keywords, max_results=max_results
        )

        # Convert to Document objects
        return [
            Document(
                page_content=chunk.text,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]

    def _doc_to_dict(self, doc: Document) -> dict:
        """Convert a Document to a dictionary.

        Args:
            doc: LangChain Document

        Returns:
            Dictionary representation
        """
        return {
            "text": doc.page_content,
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "doc_id": doc.metadata.get("doc_id"),
            "score": doc.metadata.get("score"),
        }

    def merge_results_node(self, state: WikiSearchState) -> dict:
        """Merge and deduplicate search results.

        Args:
            state: Current workflow state with search_results

        Returns:
            State update with merged_results
        """
        logger.info("Merging search results...")
        return self.merger.merge_results(state)

    async def synthesize_node(self, state: WikiSearchState) -> dict:
        """Synthesize the merged results into a wiki-style report.

        Args:
            state: Current workflow state with merged_results

        Returns:
            State update with response and citations
        """
        logger.info("Synthesizing wiki report...")

        merged = state.get("merged_results", {})
        documents = merged.get("documents", [])

        if not documents:
            return {
                "response": "找不到相關文件。請嘗試使用不同的搜尋關鍵字。",
                "documents": [],
                "citations": [],
                "current_stage": "complete",
                "progress": 100,
            }

        # Format documents for synthesis
        doc_str = "\n\n".join([
            f"[引用{i+1}] 來源: {d.get('metadata', {}).get('filename', 'Unknown')}\n{d.get('text', d.get('page_content', ''))}"
            for i, d in enumerate(documents[:10])  # Limit to top 10
        ])

        # Generate report
        chain = SYNTHESIZE_PROMPT | self.llm | StrOutputParser()
        response = await chain.ainvoke({
            "input": state["input"],
            "documents": doc_str,
        })

        # Convert documents to LangChain Document objects
        doc_objects = [
            Document(
                page_content=d.get("text", d.get("page_content", "")),
                metadata=d.get("metadata", {}),
            )
            for d in documents
        ]

        # Build citations
        citations = [
            {
                "id": i + 1,
                "source": d.get("metadata", {}).get("filename", "Unknown"),
                "excerpt": d.get("text", d.get("page_content", ""))[:200],
                "relevance": merged.get("relevance_scores", [])[i] if i < len(merged.get("relevance_scores", [])) else 1.0,
            }
            for i, d in enumerate(documents[:10])
        ]

        logger.info(f"Wiki report generated with {len(citations)} citations")

        return {
            "response": response,
            "documents": doc_objects,
            "citations": citations,
            "current_stage": "complete",
            "progress": 100,
        }

    async def search(self, query: str) -> dict:
        """Execute the full search workflow.

        Args:
            query: User's search query

        Returns:
            Final state with response and citations
        """
        initial_state: WikiSearchState = {
            "input": query,
            "query_insight": None,
            "search_plan": None,
            "search_results": None,
            "merged_results": None,
            "documents": [],
            "response": "",
            "citations": None,
            "current_stage": "starting",
            "progress": 0,
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state)
        return result

    async def stream_search(self, query: str):
        """Stream the search workflow with progress updates.

        Args:
            query: User's search query

        Yields:
            Progress updates and final result
        """
        initial_state: WikiSearchState = {
            "input": query,
            "query_insight": None,
            "search_plan": None,
            "search_results": None,
            "merged_results": None,
            "documents": [],
            "response": "",
            "citations": None,
            "current_stage": "starting",
            "progress": 0,
            "error": None,
        }

        async for event in self.graph.astream(initial_state):
            # Extract node name and state update
            for node_name, state_update in event.items():
                yield {
                    "node": node_name,
                    "stage": state_update.get("current_stage", node_name),
                    "progress": state_update.get("progress", 0),
                    "update": state_update,
                }
