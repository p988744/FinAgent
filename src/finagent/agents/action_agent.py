"""Action Agent - Executes research tasks using RAG and tools."""

import logging

from finagent.agents.state import AgentState
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

    def __init__(self, retriever: DocumentRetriever, relevance_threshold: float = 0.8):
        """
        Initialize action agent with retriever.

        Args:
            retriever: Document retriever instance
            relevance_threshold: Maximum distance threshold (lower is better, default 0.8)
                                Documents with distance > threshold are filtered out
        """
        self.retriever = retriever
        self.relevance_threshold = relevance_threshold

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

        logger.info("Action agent executing research tasks")

        try:
            # Execute RAG retrieval
            max_results = plan.get("max_results", 5) if plan else 5
            all_chunks = self.retriever.retrieve(query=query.text, n_results=max_results)

            # Filter by relevance threshold
            retrieved_chunks = [
                chunk for chunk in all_chunks if chunk.score <= self.relevance_threshold
            ]

            # Log filtering results
            if len(all_chunks) > len(retrieved_chunks):
                filtered_count = len(all_chunks) - len(retrieved_chunks)
                logger.info(
                    f"Filtered out {filtered_count} low-relevance chunks "
                    f"(threshold: {self.relevance_threshold})"
                )

            if not retrieved_chunks:
                logger.warning("No relevant documents found after filtering")
                state["errors"].append(f"未找到相關文件（相似度門檻：{self.relevance_threshold}）")
                state["retrieved_chunks"] = []
                state["citations"] = []
                return state

            logger.info(
                f"Retrieved {len(retrieved_chunks)} relevant chunks "
                f"(scores: {[f'{c.score:.3f}' for c in retrieved_chunks]})"
            )

            # Extract citations from retrieved documents
            citations = self._extract_citations(retrieved_chunks)

            # Update state
            state["retrieved_chunks"] = retrieved_chunks
            state["citations"] = citations
            state["processing_steps"].append(
                f"行動代理：檢索到 {len(retrieved_chunks)} 筆文件，提取 {len(citations)} 個引用"
            )

        except Exception as e:
            logger.error(f"Action execution failed: {e}", exc_info=True)
            state["errors"].append(f"檢索失敗：{str(e)}")
            state["retrieved_chunks"] = []
            state["citations"] = []

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
