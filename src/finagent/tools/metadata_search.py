"""Metadata search tool for filtering documents by metadata."""

import logging

from finagent.database.metadata_db import MetadataDB
from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class MetadataSearchTool(BaseTool):
    """Search documents by metadata filters (date, entity, jurisdiction, etc.)."""

    def __init__(self, metadata_db: MetadataDB | None = None):
        """
        Initialize metadata search tool.

        Args:
            metadata_db: MetadataDB instance (optional, will create if not provided)
        """
        self.metadata_db = metadata_db or MetadataDB()

    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        return ToolCapability(
            name="metadata_search",
            description="依據元資料篩選文件（日期、實體、裁罰類型、管轄機關等）。適合時間相關查詢和特定實體搜尋。",
            supported_intents=[
                "temporal",  # 時間相關（最近、過去）
                "entity_specific",  # 特定實體
                "jurisdiction_filter",  # 管轄機關篩選
                "penalty_type_filter",  # 裁罰類型篩選
            ],
            required_features=[],  # Optional filters
            execution_time_estimate="fast",  # Database query ~1-2 seconds
            cost_estimate="low",  # No API calls
            limitations=[
                "需要元資料已建立索引",
                "無法進行語義匹配",
                "僅返回元資料（不含文件內容）",
            ],
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        Execute metadata search.

        Args:
            tool_input: Tool input with query and parameters
                - entity: str (optional) - Entity name (partial match)
                - date_from: str (optional) - Start date (YYYY-MM-DD)
                - date_to: str (optional) - End date (YYYY-MM-DD)
                - penalty_type: str (optional) - Penalty type (partial match)
                - jurisdiction: str (optional) - Jurisdiction (exact match)
                - year_ad: int (optional) - Year in AD

        Returns:
            ToolOutput with matching documents' metadata
        """
        try:
            # Build filter from parameters
            filters = {}

            # Entity filter
            if entity := tool_input.parameters.get("entity"):
                filters["entity"] = entity

            # Date range filter
            if date_from := tool_input.parameters.get("date_from"):
                filters["date_from"] = date_from
            if date_to := tool_input.parameters.get("date_to"):
                filters["date_to"] = date_to

            # Penalty type filter
            if penalty_type := tool_input.parameters.get("penalty_type"):
                filters["penalty_type"] = penalty_type

            # Jurisdiction filter
            if jurisdiction := tool_input.parameters.get("jurisdiction"):
                filters["jurisdiction"] = jurisdiction

            # Year filter
            if year_ad := tool_input.parameters.get("year_ad"):
                filters["year_ad"] = year_ad

            # If no filters provided, return error
            if not filters:
                return ToolOutput(
                    success=False,
                    results=[],
                    metadata={},
                    error="請提供至少一個篩選條件（entity, date_from, date_to, penalty_type, jurisdiction, year_ad）",
                )

            # Query metadata DB
            results = await self.metadata_db.search(filters)

            # For temporal queries (latest), results are already sorted by date DESC
            # Check if this is a "latest" query
            if "最近" in tool_input.query or "latest" in tool_input.query.lower():
                # Already sorted DESC, take first one
                if results:
                    results = [results[0]]

            logger.info(
                f"Metadata search returned {len(results)} results with filters: {filters}"
            )

            return ToolOutput(
                success=True,
                results=results,
                metadata={
                    "tool": "metadata_search",
                    "filters": filters,
                    "results_count": len(results),
                },
            )

        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            return ToolOutput(
                success=False,
                results=[],
                metadata={},
                error=f"元資料搜尋執行失敗: {str(e)}",
            )

    def validate_input(self, tool_input: ToolInput) -> bool:
        """
        Validate input parameters.

        Args:
            tool_input: Tool input to validate

        Returns:
            True if at least one filter is provided
        """
        # At least one filter parameter should be provided
        valid_params = [
            "entity",
            "date_from",
            "date_to",
            "penalty_type",
            "jurisdiction",
            "year_ad",
        ]

        has_filter = any(param in tool_input.parameters for param in valid_params)

        # Validate date format if provided
        if "date_from" in tool_input.parameters or "date_to" in tool_input.parameters:
            date_from = tool_input.parameters.get("date_from", "")
            date_to = tool_input.parameters.get("date_to", "")

            # Simple validation: should be YYYY-MM-DD format (10 chars)
            if date_from and len(date_from) != 10:
                return False
            if date_to and len(date_to) != 10:
                return False

        # Validate year_ad if provided
        if "year_ad" in tool_input.parameters:
            year_ad = tool_input.parameters["year_ad"]
            if not isinstance(year_ad, int) or year_ad < 1900 or year_ad > 2100:
                return False

        return has_filter
