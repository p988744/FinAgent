"""Read file tool for direct file access."""

import logging
from pathlib import Path

from finagent.database.metadata_db import MetadataDB
from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class ReadFileTool(BaseTool):
    """Read a specific file directly by filename or path."""

    def __init__(self, metadata_db: MetadataDB | None = None):
        """
        Initialize read file tool.

        Args:
            metadata_db: MetadataDB instance (optional, will create if not provided)
        """
        self.metadata_db = metadata_db or MetadataDB()

    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        return ToolCapability(
            name="read_file",
            description="直接讀取特定檔案（依檔名或路徑）。適合指定特定檔案名稱的查詢。",
            supported_intents=[
                "specific_file",  # 指定檔案查詢
                "direct_access",  # 直接存取
            ],
            required_features=["filename"],
            execution_time_estimate="fast",  # File I/O
            cost_estimate="low",  # No API calls
            limitations=[
                "需要精確檔名或路徑",
                "無法進行語義搜尋",
                "檔案必須存在於系統中",
            ],
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """
        Read file directly.

        Args:
            tool_input: Tool input with query and parameters
                - filename: str (required) - Filename or path

        Returns:
            ToolOutput with file content and metadata
        """
        try:
            filename = tool_input.parameters.get("filename")

            if not filename:
                return ToolOutput(
                    success=False,
                    results=[],
                    metadata={},
                    error="請提供檔名（filename 參數）",
                )

            # Find file path from metadata DB
            file_path = await self.metadata_db.get_file_path(filename)

            if not file_path:
                # Try direct path if filename is actually a path
                potential_path = Path(filename)
                if potential_path.exists() and potential_path.is_file():
                    file_path = str(potential_path)
                else:
                    return ToolOutput(
                        success=False,
                        results=[],
                        metadata={},
                        error=f"找不到檔案: {filename}",
                    )

            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try other encodings
                with open(file_path, "r", encoding="big5") as f:
                    content = f.read()

            # Get metadata
            metadata = await self.metadata_db.get_metadata(filename)

            if not metadata:
                # Create basic metadata if not in DB
                metadata = {
                    "filename": filename,
                    "file_path": file_path,
                    "content_length": len(content),
                }

            result = {
                "filename": filename,
                "content": content,
                "metadata": metadata,
                "file_path": file_path,
                "content_length": len(content),
            }

            logger.info(f"Read file: {filename} ({len(content)} chars)")

            return ToolOutput(
                success=True,
                results=[result],
                metadata={
                    "tool": "read_file",
                    "file_path": file_path,
                    "content_length": len(content),
                },
            )

        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
            return ToolOutput(
                success=False,
                results=[],
                metadata={},
                error=f"檔案不存在: {filename}",
            )

        except Exception as e:
            logger.error(f"Read file failed: {e}")
            return ToolOutput(
                success=False,
                results=[],
                metadata={},
                error=f"讀取檔案失敗: {str(e)}",
            )

    def validate_input(self, tool_input: ToolInput) -> bool:
        """
        Validate input parameters.

        Args:
            tool_input: Tool input to validate

        Returns:
            True if filename is provided
        """
        # Filename is required
        filename = tool_input.parameters.get("filename")
        return bool(filename and isinstance(filename, str) and filename.strip())
