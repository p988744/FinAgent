"""Action Agent - Executes research tasks using RAG and tools."""

import logging

from finagent.agents.reference_guard import get_search_params
from finagent.agents.state import AgentState
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever, RetrievedChunk
from finagent.models.citations import CitationAuthority, CitationType, LegalCitation

logger = logging.getLogger(__name__)


class ActionAgent:
    """
    Action Agent executes research tasks using available tools.

    Current capabilities:
    - RAG document retrieval (semantic search)

    Future capabilities:
    - Web search for recent cases
    - Database queries for structured data
    - API calls to regulatory bodies
    """

    def __init__(
        self,
        retriever: DocumentRetriever,
        relevance_threshold: float = 0.8,
        db_path: str = "data/finagent.db",
        ui_callback=None,
    ):
        """
        Initialize action agent with retriever.

        Args:
            retriever: Document retriever instance
            relevance_threshold: Maximum distance threshold (lower is better, default 0.8)
                                Documents with distance > threshold are filtered out
            db_path: Path to database for hard search
            ui_callback: Optional UICallback for progress updates
        """
        self.retriever = retriever
        self.relevance_threshold = relevance_threshold
        self.hard_searcher = HardSearcher(db_path=db_path)
        self.ui_callback = ui_callback

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute research tasks from plan.

        Args:
            state: Current agent state with plan

        Returns:
            Updated state with retrieved chunks and citations
        """
        query = state["query"]
        plan = state["plan"]

        # Get search parameters based on current iteration
        search_iteration = state.get("search_iteration", 0)
        search_params = get_search_params(search_iteration)

        strategy = search_params["strategy"]
        threshold = search_params["threshold"]
        max_results = search_params["max_results"]

        logger.info(
            f"Action agent executing research tasks: iteration={search_iteration}, "
            f"strategy={strategy}, threshold={threshold}, max_results={max_results}"
        )

        try:
            # Phase 5: Find and mark retrieval todo as in_progress
            todos = state.get("todos", [])
            retrieval_todo = next((t for t in todos if t.category == "retrieval"), None)

            if retrieval_todo and retrieval_todo.status == "pending":
                retrieval_todo.mark_started()
                if self.ui_callback:
                    import asyncio
                    try:
                        asyncio.create_task(self.ui_callback.on_todo_started(retrieval_todo))
                    except RuntimeError:
                        pass

            # Emit retrieval start callback
            if self.ui_callback:
                import asyncio
                try:
                    asyncio.create_task(
                        self.ui_callback.on_retrieval_start(
                            query=query.text,
                            strategy=strategy,
                            max_results=max_results
                        )
                    )
                except RuntimeError:
                    pass

            # Execute RAG retrieval with iteration-specific params
            all_chunks = self.retriever.retrieve(query=query.text, n_results=max_results)

            # Filter by threshold (from search strategy)
            retrieved_chunks = [chunk for chunk in all_chunks if chunk.score <= threshold]

            # Log filtering results
            if len(all_chunks) > len(retrieved_chunks):
                filtered_count = len(all_chunks) - len(retrieved_chunks)
                logger.info(
                    f"Filtered out {filtered_count} low-relevance chunks (threshold: {threshold})"
                )

            if not retrieved_chunks:
                logger.warning("No relevant documents found after filtering")
                state["errors"].append(f"未找到相關文件（相似度門檻：{threshold}）")
                state["retrieved_chunks"] = []
                state["citations"] = []
                return state

            logger.info(
                f"Retrieved {len(retrieved_chunks)} relevant chunks with {strategy} strategy "
                f"(scores: {[f'{c.score:.3f}' for c in retrieved_chunks]})"
            )

            # Emit retrieval result callback
            if self.ui_callback:
                import asyncio
                try:
                    asyncio.create_task(
                        self.ui_callback.on_retrieval_result(
                            strategy=strategy,
                            count=len(retrieved_chunks),
                            total=len(all_chunks)
                        )
                    )
                except RuntimeError:
                    pass

            # Hard search if enabled in plan
            hard_chunks = []
            if plan and plan.get("use_hard_search"):
                plan_analysis = state.get("plan_analysis", {})
                must_have_keywords = plan_analysis.get("must_have_keywords", [])

                if must_have_keywords:
                    logger.info(f"Executing hard search for keywords: {must_have_keywords}")
                    state["processing_steps"].append(
                        f"行動代理：執行深度搜索，搜尋關鍵字「{', '.join(must_have_keywords)}」"
                    )

                    try:
                        hard_chunks = self.hard_searcher.search(
                            keywords=must_have_keywords,
                            max_results=max_results,
                        )
                        logger.info(f"Hard search found {len(hard_chunks)} matches")
                        state["processing_steps"].append(
                            f"行動代理：深度搜索找到 {len(hard_chunks)} 筆精確匹配"
                        )
                    except Exception as e:
                        logger.error(f"Hard search failed: {e}", exc_info=True)
                        state["processing_steps"].append(
                            f"行動代理：深度搜索失敗（{str(e)}）"
                        )

            # Merge vector and hard search results
            all_chunks = self._merge_chunks(retrieved_chunks, hard_chunks)

            logger.info(f"Total chunks after merge: {len(all_chunks)}")

            # Extract citations from all retrieved documents
            citations = self._extract_citations(all_chunks)

            # Update state
            state["retrieved_chunks"] = all_chunks
            state["citations"] = citations

            # Add final summary to processing steps
            if hard_chunks:
                state["processing_steps"].append(
                    f"行動代理（{strategy}策略）：向量搜索 {len(retrieved_chunks)} 筆 + "
                    f"深度搜索 {len(hard_chunks)} 筆 = 總計 {len(all_chunks)} 筆文件，"
                    f"提取 {len(citations)} 個引用"
                )
            else:
                state["processing_steps"].append(
                    f"行動代理（{strategy}策略）：檢索到 {len(all_chunks)} 筆文件，"
                    f"提取 {len(citations)} 個引用"
                )

            # Phase 5: Mark retrieval todo as completed
            if retrieval_todo:
                retrieval_todo.mark_completed(result={"count": len(all_chunks)})
                if self.ui_callback:
                    import asyncio
                    try:
                        asyncio.create_task(self.ui_callback.on_todo_completed(retrieval_todo))
                    except RuntimeError:
                        pass

            # Update state with todos
            state["todos"] = todos

        except Exception as e:
            logger.error(f"Action execution failed: {e}", exc_info=True)
            state["errors"].append(f"檢索失敗：{str(e)}")
            state["retrieved_chunks"] = []
            state["citations"] = []

            # Phase 5: Mark retrieval todo as failed
            todos = state.get("todos", [])
            retrieval_todo = next((t for t in todos if t.category == "retrieval"), None)
            if retrieval_todo:
                retrieval_todo.mark_failed(error=str(e))
                if self.ui_callback:
                    import asyncio
                    try:
                        asyncio.create_task(self.ui_callback.on_todo_failed(retrieval_todo, str(e)))
                    except RuntimeError:
                        pass
            state["todos"] = todos

        return state

    def _extract_citations(self, chunks: list[RetrievedChunk]) -> list[LegalCitation]:
        """
        Extract citations from retrieved document chunks.

        Args:
            chunks: List of retrieved chunks

        Returns:
            List of legal citations
        """
        citations = []
        seen_docs = set()

        for idx, chunk in enumerate(chunks, 1):
            doc_id = chunk.doc_id

            # Avoid duplicate citations from same document
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)

            # Extract metadata
            filename = chunk.metadata.get("filename", "未知文件")
            source = chunk.metadata.get("source", "")

            # Create citation
            citation = LegalCitation(
                id=idx,
                type=CitationType.ENFORCEMENT_DOCUMENT,
                authority=CitationAuthority.PRIMARY,
                title=filename,
                formatted_citation=f"{filename}",
                issuing_authority="金管會",
                source_url=source if source.startswith("http") else None,
            )

            citations.append(citation)

        return citations

    def _merge_chunks(
        self,
        vector_chunks: list[RetrievedChunk],
        hard_chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Merge vector and hard search chunks, deduplicating by file+position.

        Strategy:
        1. Keep all hard search chunks (high priority)
        2. Add vector chunks that don't overlap with hard chunks
        3. Sort by relevance score (descending)
        4. Return merged list

        Args:
            vector_chunks: Chunks from vector search
            hard_chunks: Chunks from hard search

        Returns:
            Merged and deduplicated list of chunks
        """
        if not hard_chunks:
            return vector_chunks

        if not vector_chunks:
            return hard_chunks

        # Track seen chunks by (filename, text_hash)
        seen = set()
        merged = []

        # Add all hard search chunks first (higher priority)
        for chunk in hard_chunks:
            key = (chunk.metadata.get("filename"), hash(chunk.text[:100]))
            if key not in seen:
                seen.add(key)
                merged.append(chunk)

        # Add vector chunks that don't overlap
        for chunk in vector_chunks:
            key = (chunk.metadata.get("filename"), hash(chunk.text[:100]))
            if key not in seen:
                seen.add(key)
                merged.append(chunk)

        # Sort by score (lower is better for distance, higher is better for hard search)
        # Hard search chunks have score ~0.95, vector chunks have score 0.0-0.8
        # So reverse sort will put hard search first
        merged.sort(key=lambda c: c.score, reverse=True)

        logger.info(
            f"Merged {len(vector_chunks)} vector + {len(hard_chunks)} hard = "
            f"{len(merged)} unique chunks"
        )

        return merged
