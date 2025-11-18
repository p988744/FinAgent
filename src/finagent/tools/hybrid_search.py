"""Hybrid search tool combining vector search with metadata filtering."""

import logging

from finagent.database.metadata_db import MetadataDB
from finagent.document_processing.retriever import DocumentRetriever
from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class HybridSearchTool(BaseTool):
    """Hybrid search combining semantic vector search with metadata filtering."""

    def __init__(
        self,
        retriever: DocumentRetriever | None = None,
        metadata_db: MetadataDB | None = None,
    ):
        """
        Initialize hybrid search tool.

        Args:
            retriever: DocumentRetriever instance (optional)
            metadata_db: MetadataDB instance (optional)
        """
        self.retriever = retriever or DocumentRetriever()
        self.metadata_db = metadata_db or MetadataDB()

    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        return ToolCapability(
            name="hybrid_search",
            description="混合搜尋（語義向量 + 元資料篩選）。結合語義相似度與元資料篩選，適合需要時間限制或實體篩選的語義查詢。",
            supported_intents=[
                "filtered_semantic_search",  # 篩選後的語義搜尋
                "temporal_with_keywords",  # 時間 + 關鍵字
                "entity_with_semantic",  # 實體 + 語義
            ],
            required_features=["query"],  # Query + optional filters
            execution_time_estimate="medium",  # ~3-7 seconds (metadata + vector)
            cost_estimate="medium",  # Embedding API call + database query
            limitations=[
                "比純向量或元資料搜尋慢",
                "需要向量索引和元資料資料庫",
                "候選文件數量會影響效能",
            ],
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        Execute hybrid search.

        Two-stage process:
        1. Metadata filtering: Get candidate documents
        2. Vector search: Semantic search within candidates

        Args:
            tool_input: Tool input with query and parameters
                - query: str (required) - Search query
                - entity: str (optional) - Entity filter
                - date_from: str (optional) - Start date (YYYY-MM-DD)
                - date_to: str (optional) - End date (YYYY-MM-DD)
                - penalty_type: str (optional) - Penalty type filter
                - jurisdiction: str (optional) - Jurisdiction filter
                - year_ad: int (optional) - Year filter
                - top_k: int (optional, default=10) - Number of results
                - relevance_threshold: float (optional, default=0.8) - Max distance

        Returns:
            ToolOutput with filtered semantic search results
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

            # Step 1: Metadata filtering to get candidate documents
            metadata_filters = {}

            if entity := tool_input.parameters.get("entity"):
                metadata_filters["entity"] = entity
            if date_from := tool_input.parameters.get("date_from"):
                metadata_filters["date_from"] = date_from
            if date_to := tool_input.parameters.get("date_to"):
                metadata_filters["date_to"] = date_to
            if penalty_type := tool_input.parameters.get("penalty_type"):
                metadata_filters["penalty_type"] = penalty_type
            if jurisdiction := tool_input.parameters.get("jurisdiction"):
                metadata_filters["jurisdiction"] = jurisdiction
            if year_ad := tool_input.parameters.get("year_ad"):
                metadata_filters["year_ad"] = year_ad

            candidate_filenames = None
            candidate_count = "all"

            if metadata_filters:
                # Get candidate documents from metadata
                candidates = await self.metadata_db.search(metadata_filters)
                candidate_filenames = [c["filename"] for c in candidates]
                candidate_count = len(candidate_filenames)

                logger.info(
                    f"Metadata filtering found {candidate_count} candidates with filters: {metadata_filters}"
                )

                # If no candidates found, return empty results
                if candidate_count == 0:
                    return ToolOutput(
                        success=True,
                        results=[],
                        metadata={
                            "tool": "hybrid_search",
                            "metadata_filters": metadata_filters,
                            "candidate_count": 0,
                            "results_count": 0,
                            "stage": "metadata_filtering_empty",
                        },
                    )

            # Step 2: Vector search within candidates
            top_k = tool_input.parameters.get("top_k", 10)
            relevance_threshold = tool_input.parameters.get("relevance_threshold", 0.8)

            # Build Chroma filters for vector search
            chroma_filters = None
            if candidate_filenames:
                # Chroma uses $in operator for filtering
                chroma_filters = {"filename": {"$in": candidate_filenames}}

            # Execute vector search
            chunks = self.retriever.retrieve_with_scores(
                query=tool_input.query,
                n_results=top_k,
                score_threshold=relevance_threshold,
                filters=chroma_filters,
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
                f"Hybrid search returned {len(results)} results (candidates={candidate_count}, top_k={top_k})"
            )

            return ToolOutput(
                success=True,
                results=results,
                metadata={
                    "tool": "hybrid_search",
                    "metadata_filters": metadata_filters,
                    "candidate_count": candidate_count,
                    "top_k": top_k,
                    "relevance_threshold": relevance_threshold,
                    "results_count": len(results),
                    "stage": "completed",
                },
            )

        except ValueError as e:
            logger.error(f"Hybrid search failed: {e}")
            return ToolOutput(success=False, results=[], metadata={}, error=str(e))

        except Exception as e:
            logger.error(f"Unexpected error in hybrid search: {e}")
            return ToolOutput(
                success=False,
                results=[],
                metadata={},
                error=f"混合搜尋執行失敗: {str(e)}",
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

        # Validate date format if provided
        if "date_from" in tool_input.parameters or "date_to" in tool_input.parameters:
            date_from = tool_input.parameters.get("date_from", "")
            date_to = tool_input.parameters.get("date_to", "")

            if date_from and len(date_from) != 10:
                return False
            if date_to and len(date_to) != 10:
                return False

        # Validate year_ad if provided
        if "year_ad" in tool_input.parameters:
            year_ad = tool_input.parameters["year_ad"]
            if not isinstance(year_ad, int) or year_ad < 1900 or year_ad > 2100:
                return False

        return True
