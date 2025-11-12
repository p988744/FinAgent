"""Table of Contents generator for document collection."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from finagent.document_processing.metadata_store import DocumentMetadataStore, DocumentMetadata


class TableOfContents:
    """Generates and maintains a table of contents for the document collection."""

    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize TOC generator.

        Args:
            output_path: Path to save TOC file (default: ./data/TABLE_OF_CONTENTS.md)
        """
        self.output_path = Path(output_path or "./data/TABLE_OF_CONTENTS.md")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_store = DocumentMetadataStore()

    def generate(self) -> str:
        """
        Generate complete table of contents.

        Returns:
            Table of contents as markdown string
        """
        all_metadata = self.metadata_store.get_all_metadata()

        if not all_metadata:
            return self._generate_empty_toc()

        # Group by document type
        by_type: Dict[str, List[DocumentMetadata]] = {}
        for meta in all_metadata:
            doc_type = meta.document_type
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(meta)

        # Sort each group by date (newest first)
        for doc_type in by_type:
            by_type[doc_type].sort(
                key=lambda m: m.date if m.date else "0000-00-00",
                reverse=True
            )

        # Generate markdown
        lines = []
        lines.append("# 文件目錄 (Table of Contents)")
        lines.append("")
        lines.append(f"**最後更新:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**總文件數:** {len(all_metadata)}")
        lines.append("")

        # Statistics
        lines.append("## 📊 統計資訊")
        lines.append("")
        lines.append("| 文件類型 | 數量 |")
        lines.append("|---------|------|")
        for doc_type, docs in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            lines.append(f"| {doc_type} | {len(docs)} |")
        lines.append("")

        # Quick Reference Table (compact overview)
        lines.append("## 📋 快速索引")
        lines.append("")
        lines.append("| 檔名 | 類型 | 日期 | 關鍵摘要 |")
        lines.append("|------|------|------|----------|")

        for meta in sorted(all_metadata, key=lambda m: m.date if m.date else "0000-00-00", reverse=True):
            filename = meta.filename[:30] + "..." if len(meta.filename) > 33 else meta.filename
            doc_type = meta.document_type[:8] + "..." if len(meta.document_type) > 10 else meta.document_type
            date = meta.date if meta.date else "未設定"

            # Create compact summary
            summary_parts = []
            if meta.related_institutions:
                summary_parts.append(meta.related_institutions[0])
            if meta.penalty_amount:
                summary_parts.append(f"罰{meta.penalty_amount}")
            if meta.violation_types:
                summary_parts.append(meta.violation_types[0])

            summary = ", ".join(summary_parts[:2]) if summary_parts else "-"
            summary = summary[:25] + "..." if len(summary) > 28 else summary

            lines.append(f"| {filename} | {doc_type} | {date} | {summary} |")

        lines.append("")

        # Detailed sections by document type
        lines.append("## 📚 詳細目錄")
        lines.append("")

        # Define preferred order
        type_order = [
            "裁罰書",
            "判決書",
            "法規條文",
            "監管公告",
            "新聞報導",
            "銀行聲明",
            "分析報告",
            "其他"
        ]

        # Process types in preferred order
        for doc_type in type_order:
            if doc_type not in by_type:
                continue

            docs = by_type[doc_type]
            lines.append(f"### {doc_type} ({len(docs)} 份)")
            lines.append("")

            for idx, meta in enumerate(docs, 1):
                lines.append(f"#### {idx}. {meta.filename}")
                lines.append("")
                lines.append(f"**描述:** {meta.description}")
                lines.append("")

                # Document details
                details = []
                if meta.date:
                    details.append(f"- **日期:** {meta.date}")
                if meta.issuing_authority:
                    details.append(f"- **發布機關:** {meta.issuing_authority}")
                if meta.related_institutions:
                    details.append(f"- **相關機構:** {', '.join(meta.related_institutions)}")
                if meta.penalty_amount:
                    details.append(f"- **裁罰金額:** {meta.penalty_amount}")
                if meta.violation_types:
                    details.append(f"- **違規類型:** {', '.join(meta.violation_types)}")
                if meta.keywords:
                    details.append(f"- **關鍵字:** {', '.join(meta.keywords)}")

                if details:
                    lines.extend(details)
                    lines.append("")

                lines.append(f"**文件ID:** `{meta.doc_id}`")
                lines.append("")
                lines.append("---")
                lines.append("")

        # Process remaining types not in preferred order
        remaining_types = set(by_type.keys()) - set(type_order)
        for doc_type in sorted(remaining_types):
            docs = by_type[doc_type]
            lines.append(f"### {doc_type} ({len(docs)} 份)")
            lines.append("")

            for idx, meta in enumerate(docs, 1):
                lines.append(f"#### {idx}. {meta.filename}")
                lines.append("")
                lines.append(f"**描述:** {meta.description}")
                lines.append("")

                # Document details
                details = []
                if meta.date:
                    details.append(f"- **日期:** {meta.date}")
                if meta.issuing_authority:
                    details.append(f"- **發布機關:** {meta.issuing_authority}")
                if meta.related_institutions:
                    details.append(f"- **相關機構:** {', '.join(meta.related_institutions)}")
                if meta.keywords:
                    details.append(f"- **關鍵字:** {', '.join(meta.keywords)}")

                if details:
                    lines.extend(details)
                    lines.append("")

                lines.append(f"**文件ID:** `{meta.doc_id}`")
                lines.append("")
                lines.append("---")
                lines.append("")

        # Usage notes
        lines.append("## 💡 使用說明")
        lines.append("")
        lines.append("此目錄由系統自動生成，提供文件集合的概覽。")
        lines.append("")
        lines.append("**查詢文件:**")
        lines.append("- 使用 **快速索引** 快速瀏覽所有文件")
        lines.append("- 使用 **詳細目錄** 查看完整文件資訊")
        lines.append("- 使用文件ID可直接定位文件")
        lines.append("")
        lines.append("**工作流程代理:**")
        lines.append("- 可先讀取此目錄了解可用文件")
        lines.append("- 根據需求選擇相關文件進行詳細分析")
        lines.append("- 使用文件ID和檔名定位具體文件")
        lines.append("")
        lines.append("**更新時機:**")
        lines.append("- 執行 `/init` 初始化文件後自動更新")
        lines.append("- 執行 `/reindex` 索引文件時自動更新")
        lines.append("")

        return "\n".join(lines)

    def _generate_empty_toc(self) -> str:
        """Generate TOC for empty collection."""
        lines = []
        lines.append("# 文件目錄 (Table of Contents)")
        lines.append("")
        lines.append(f"**最後更新:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**總文件數:** 0")
        lines.append("")
        lines.append("## 📋 目前無文件")
        lines.append("")
        lines.append("請使用以下步驟新增文件：")
        lines.append("")
        lines.append("1. 將文件放置到 `data/documents/` 目錄")
        lines.append("2. 執行 `/init` 初始化文件描述")
        lines.append("3. 執行 `/reindex` 建立索引")
        lines.append("")
        return "\n".join(lines)

    def save(self) -> Path:
        """
        Generate and save TOC to file.

        Returns:
            Path to saved TOC file
        """
        content = self.generate()
        self.output_path.write_text(content, encoding="utf-8")
        return self.output_path

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Dictionary with statistics
        """
        all_metadata = self.metadata_store.get_all_metadata()

        if not all_metadata:
            return {
                "total": 0,
                "by_type": {},
                "by_authority": {},
                "date_range": None,
            }

        # Count by type
        by_type: Dict[str, int] = {}
        for meta in all_metadata:
            doc_type = meta.document_type
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

        # Count by authority
        by_authority: Dict[str, int] = {}
        for meta in all_metadata:
            if meta.issuing_authority:
                authority = meta.issuing_authority
                by_authority[authority] = by_authority.get(authority, 0) + 1

        # Date range
        dates = [meta.date for meta in all_metadata if meta.date]
        date_range = None
        if dates:
            dates.sort()
            date_range = {"earliest": dates[0], "latest": dates[-1]}

        return {
            "total": len(all_metadata),
            "by_type": by_type,
            "by_authority": by_authority,
            "date_range": date_range,
        }
