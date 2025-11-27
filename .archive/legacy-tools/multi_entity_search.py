"""Multi-entity search tool for parallel entity comparison."""

import asyncio
import logging

from finagent.database.metadata_db import MetadataDB
from finagent.document_processing.retriever import DocumentRetriever
from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class MultiEntitySearchTool(BaseTool):
    """Search multiple entities in parallel for comparison analysis."""

    def __init__(
        self,
        retriever: DocumentRetriever | None = None,
        metadata_db: MetadataDB | None = None,
    ):
        """
        Initialize multi-entity search tool.

        Args:
            retriever: DocumentRetriever instance (optional)
            metadata_db: MetadataDB instance (optional)
        """
        self.retriever = retriever or DocumentRetriever()
        self.metadata_db = metadata_db or MetadataDB()

    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        return ToolCapability(
            name="multi_entity_search",
            description="並行搜尋多個實體（用於比較分析）。同時搜尋多個銀行或機構，適合「A vs B」或「比較」類查詢。",
            supported_intents=[
                "comparison",  # A vs B
                "multi_entity_analysis",  # 多實體分析
            ],
            required_features=["entities"],  # List of entities
            execution_time_estimate="medium",  # ~5-10 seconds (parallel searches)
            cost_estimate="high",  # Multiple embedding API calls
            limitations=[
                "成本較高（多次搜尋）",
                "需要後續比較邏輯",
                "同時搜尋實體數量建議不超過5個",
            ],
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        Execute multi-entity search.

        Args:
            tool_input: Tool input with query and parameters
                - entities: list[str] (required) - List of entity names (min 2)
                - top_k_per_entity: int (optional, default=5) - Results per entity
                - relevance_threshold: float (optional, default=0.8) - Max distance
                - use_metadata: bool (optional, default=True) - Use metadata filtering

        Returns:
            ToolOutput with results grouped by entity
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

            # Get entities list
            entities = tool_input.parameters.get("entities", [])

            if len(entities) < 2:
                return ToolOutput(
                    success=False,
                    results=[],
                    metadata={},
                    error="多實體搜尋需要至少2個實體。請提供 entities 參數（陣列）。",
                )

            # Get parameters
            top_k_per_entity = tool_input.parameters.get("top_k_per_entity", 5)
            relevance_threshold = tool_input.parameters.get("relevance_threshold", 0.8)
            use_metadata = tool_input.parameters.get("use_metadata", True)

            # Execute searches in parallel
            async def search_entity(entity: str):
                """Search for single entity."""
                try:
                    # Get candidate filenames from metadata if enabled
                    candidate_filenames = None

                    if use_metadata:
                        candidates = await self.metadata_db.search({"entity": entity})
                        candidate_filenames = [c["filename"] for c in candidates]

                        logger.info(
                            f"Entity '{entity}': found {len(candidate_filenames)} candidate documents"
                        )

                        # If no candidates found, return empty for this entity
                        if not candidate_filenames:
                            return {
                                "entity": entity,
                                "results": [],
                                "candidate_count": 0,
                                "error": None,
                            }

                    # Build Chroma filters
                    chroma_filters = None
                    if candidate_filenames:
                        chroma_filters = {"filename": {"$in": candidate_filenames}}

                    # Execute vector search
                    chunks = self.retriever.retrieve_with_scores(
                        query=tool_input.query,
                        n_results=top_k_per_entity,
                        score_threshold=relevance_threshold,
                        filters=chroma_filters,
                    )

                    # Convert to results
                    results = []
                    for chunk in chunks:
                        results.append(
                            {
                                "id": chunk.id,
                                "text": chunk.text,
                                "score": chunk.score,
                                "relevance": 1 - chunk.score,
                                "metadata": chunk.metadata,
                                "doc_id": chunk.doc_id,
                                "source": chunk.metadata.get("source", "unknown"),
                                "filename": chunk.metadata.get("filename", "unknown"),
                            }
                        )

                    return {
                        "entity": entity,
                        "results": results,
                        "candidate_count": len(candidate_filenames)
                        if candidate_filenames
                        else "all",
                        "error": None,
                    }

                except Exception as e:
                    logger.error(f"Search failed for entity '{entity}': {e}")
                    return {
                        "entity": entity,
                        "results": [],
                        "candidate_count": 0,
                        "error": str(e),
                    }

            # Execute all entity searches in parallel
            logger.info(
                f"Starting parallel search for {len(entities)} entities: {entities}"
            )
            entity_results = await asyncio.gather(
                *[search_entity(entity) for entity in entities]
            )

            # Calculate total results
            total_results = sum(len(er["results"]) for er in entity_results)

            logger.info(
                f"Multi-entity search completed: {len(entities)} entities, {total_results} total results"
            )

            return ToolOutput(
                success=True,
                results=entity_results,
                metadata={
                    "tool": "multi_entity_search",
                    "entities": entities,
                    "entity_count": len(entities),
                    "total_results": total_results,
                    "top_k_per_entity": top_k_per_entity,
                    "relevance_threshold": relevance_threshold,
                    "use_metadata": use_metadata,
                },
            )

        except Exception as e:
            logger.error(f"Multi-entity search failed: {e}")
            return ToolOutput(
                success=False,
                results=[],
                metadata={},
                error=f"多實體搜尋執行失敗: {str(e)}",
            )

    def validate_input(self, tool_input: ToolInput) -> bool:
        """
        Validate input parameters.

        Args:
            tool_input: Tool input to validate

        Returns:
            True if valid (at least 2 entities), False otherwise
        """
        # Query is required
        if not tool_input.query or not tool_input.query.strip():
            return False

        # Entities list is required
        entities = tool_input.parameters.get("entities", [])

        if not isinstance(entities, list):
            return False

        if len(entities) < 2:
            return False

        # All entities should be non-empty strings
        if not all(isinstance(e, str) and e.strip() for e in entities):
            return False

        # Validate top_k_per_entity if provided
        if "top_k_per_entity" in tool_input.parameters:
            top_k = tool_input.parameters["top_k_per_entity"]
            if not isinstance(top_k, int) or top_k <= 0:
                return False

        # Validate relevance_threshold if provided
        if "relevance_threshold" in tool_input.parameters:
            threshold = tool_input.parameters["relevance_threshold"]
            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
                return False

        return True
