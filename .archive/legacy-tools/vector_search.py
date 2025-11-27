"""Vector search tool using Chroma vector database."""

import logging
from typing import Any

from finagent.document_processing.retriever import DocumentRetriever
from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class VectorSearchTool(BaseTool):
    """Semantic vector search using Chroma and OpenAI embeddings."""

    def __init__(self, retriever: DocumentRetriever | None = None):
        """
        Initialize vector search tool.

        Args:
            retriever: DocumentRetriever instance (optional, will create if not provided)
        """
        self.retriever = retriever or DocumentRetriever()

    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        return ToolCapability(
            name="vector_search",
            description="語義向量搜尋，適合一般性問題和關鍵字搜尋。使用 OpenAI embeddings 和 Chroma 向量資料庫進行語義相似度搜尋。",
            supported_intents=[
                "general_search",  # 一般搜尋
                "keyword_search",  # 關鍵字搜尋
                "semantic_search",  # 語義搜尋
            ],
            required_features=["query"],
            execution_time_estimate="fast",  # ~2-5 seconds
            cost_estimate="low",  # Embedding API call only
            limitations=[
                "無法依據日期或元資料篩選",
                "僅返回 top-k 結果（非完整清單）",
                "可能遺漏精確檔名匹配",
                "需要向量資料庫已建立索引",
            ],
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        Execute vector search.

        Args:
            tool_input: Tool input with query and parameters
                - query: str (required) - Search query
                - top_k: int (optional, default=10) - Number of results
                - relevance_threshold: float (optional, default=0.8) - Max distance threshold
                - filter_document_ids: list[str] (optional) - Filter to specific documents

        Returns:
            ToolOutput with retrieved chunks
        """
        try:
            # Validate collection exists
            if not self.retriever.collection_exists():
                return ToolOutput(
                    success=False,
                    results=[],
                    metadata={},
                    error="向量資料庫尚未建立索引。請先執行 /init 命令建立索引。",
                )

            # Get parameters
            top_k = tool_input.parameters.get("top_k", 10)
            relevance_threshold = tool_input.parameters.get("relevance_threshold", 0.8)
            filter_document_ids = tool_input.parameters.get("filter_document_ids")

            # Build filters
            filters = None
            if filter_document_ids:
                # Chroma uses $in operator for filtering
                filters = {"doc_id": {"$in": filter_document_ids}}

            # Execute retrieval
            chunks = self.retriever.retrieve_with_scores(
                query=tool_input.query,
                n_results=top_k,
                score_threshold=relevance_threshold,
                filters=filters,
            )

            # Convert chunks to dictionaries
            results = []
            for chunk in chunks:
                results.append(
                    {
                        "id": chunk.id,
                        "text": chunk.text,
                        "score": chunk.score,
                        "relevance": 1 - chunk.score,  # Convert distance to similarity
                        "metadata": chunk.metadata,
                        "doc_id": chunk.doc_id,
                        "source": chunk.metadata.get("source", "unknown"),
                        "filename": chunk.metadata.get("filename", "unknown"),
                    }
                )

            logger.info(
                f"Vector search returned {len(results)} results (top_k={top_k}, threshold={relevance_threshold})"
            )

            return ToolOutput(
                success=True,
                results=results,
                metadata={
                    "tool": "vector_search",
                    "top_k": top_k,
                    "relevance_threshold": relevance_threshold,
                    "results_count": len(results),
                    "filtered_document_ids": filter_document_ids,
                },
            )

        except ValueError as e:
            logger.error(f"Vector search failed: {e}")
            return ToolOutput(
                success=False, results=[], metadata={}, error=str(e)
            )

        except Exception as e:
            logger.error(f"Unexpected error in vector search: {e}")
            return ToolOutput(
                success=False,
                results=[],
                metadata={},
                error=f"向量搜尋執行失敗: {str(e)}",
            )

    def validate_input(self, tool_input: ToolInput) -> bool:
        """
        Validate input parameters.

        Args:
            tool_input: Tool input to validate

        Returns:
            True if valid, False otherwise
        """
        # Query is required
        if not tool_input.query or not tool_input.query.strip():
            return False

        # Validate top_k if provided
        if "top_k" in tool_input.parameters:
            top_k = tool_input.parameters["top_k"]
            if not isinstance(top_k, int) or top_k <= 0:
                return False

        # Validate relevance_threshold if provided
        if "relevance_threshold" in tool_input.parameters:
            threshold = tool_input.parameters["relevance_threshold"]
            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
                return False

        # Validate filter_document_ids if provided
        if "filter_document_ids" in tool_input.parameters:
            filter_ids = tool_input.parameters["filter_document_ids"]
            if not isinstance(filter_ids, list):
                return False

        return True
