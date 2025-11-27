"""List documents tool for comprehensive document listing."""

import logging

from finagent.database.metadata_db import MetadataDB
from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class ListDocumentsTool(BaseTool):
    """List all documents matching criteria (exhaustive, not top-k)."""

    def __init__(self, metadata_db: MetadataDB | None = None):
        """
        Initialize list documents tool.

        Args:
            metadata_db: MetadataDB instance (optional, will create if not provided)
        """
        self.metadata_db = metadata_db or MetadataDB()

    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        return ToolCapability(
            name="list_documents",
            description="列出所有符合條件的文件（完整清單，非 top-k）。適合「所有」、「全部」等完整性查詢。",
            supported_intents=[
                "comprehensive_list",  # 所有記錄
                "inventory",  # 清單
                "catalog",  # 目錄
            ],
            required_features=["entity"],  # At minimum, need entity or criteria
            execution_time_estimate="fast",  # Database query
            cost_estimate="low",  # No API calls
            limitations=[
                "僅返回元資料（不含完整內容）",
                "需要後續深度讀取以獲取細節",
                "需要元資料已建立索引",
            ],
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        List all matching documents.

        Args:
            tool_input: Tool input with query and parameters
                - entity: str (optional) - Entity name
                - penalty_type: str (optional) - Penalty type

        Returns:
            ToolOutput with list of all matching documents
        """
        try:
            entity = tool_input.parameters.get("entity")
            penalty_type = tool_input.parameters.get("penalty_type")

            # Query document DB for all matching files
            all_docs = await self.metadata_db.list_all(
                entity=entity, penalty_type=penalty_type
            )

            # Format results with essential metadata
            results = []
            for doc in all_docs:
                results.append(
                    {
                        "filename": doc["filename"],
                        "entity": doc["entity"],
                        "entity_normalized": doc["entity_normalized"],
                        "penalty_type": doc["penalty_type"],
                        "penalty_amount": doc["penalty_amount"],
                        "date": doc["date"],
                        "year_roc": doc["year_roc"],
                        "year_ad": doc["year_ad"],
                        "jurisdiction": doc["jurisdiction"],
                        "document_type": doc["document_type"],
                        "case_number": doc["case_number"],
                        "file_path": doc["file_path"],
                    }
                )

            logger.info(
                f"List documents returned {len(results)} results (entity={entity}, penalty_type={penalty_type})"
            )

            return ToolOutput(
                success=True,
                results=results,
                metadata={
                    "tool": "list_documents",
                    "total_count": len(results),
                    "entity": entity,
                    "penalty_type": penalty_type,
                },
            )

        except Exception as e:
            logger.error(f"List documents failed: {e}")
            return ToolOutput(
                success=False,
                results=[],
                metadata={},
                error=f"列出文件失敗: {str(e)}",
            )

    def validate_input(self, tool_input: ToolInput) -> bool:
        """
        Validate input parameters.

        Args:
            tool_input: Tool input to validate

        Returns:
            True if entity is provided
        """
        # At least entity or penalty_type should be provided
        has_entity = "entity" in tool_input.parameters
        has_penalty_type = "penalty_type" in tool_input.parameters

        return has_entity or has_penalty_type
