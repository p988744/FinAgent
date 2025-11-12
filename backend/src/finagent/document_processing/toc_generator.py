"""Compact, grep-friendly Table of Contents generator."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from finagent.document_processing.metadata_store import DocumentMetadataStore, DocumentMetadata


class CompactTableOfContents:
    """
    Generates compact, grep-friendly table of contents.

    Format designed for:
    - Easy grepping (one line per document)
    - Compact display
    - Machine-readable structure
    """

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
        Generate compact table of contents.

        Format:
        - Header with stats
        - One-line-per-document index (grep-friendly)
        - Compact details section
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

        # Header
        lines.append("# 文件目錄")
        lines.append("")
        lines.append(f"更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"總數: {len(all_metadata)} 份")
        lines.append("")

        # Statistics (compact table)
        lines.append("## 📊 統計")
        lines.append("")
        stats_line = " | ".join([f"{dt}: {len(docs)}" for dt, docs in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True)])
        lines.append(stats_line)
        lines.append("")

        # Grep-friendly index (one line per document)
        lines.append("## 📋 文件索引 (Grep-Friendly)")
        lines.append("")
        lines.append("```")
        lines.append("# Format: FILENAME | TYPE | DATE | AUTHORITY | INSTITUTIONS | PENALTY | VIOLATIONS | KEYWORDS")
        lines.append("#")

        for meta in sorted(all_metadata, key=lambda m: m.date if m.date else "0000-00-00", reverse=True):
            # Create compact one-line entry
            parts = [
                meta.filename,
                meta.document_type,
                meta.date or "-",
                meta.issuing_authority or "-",
                ";".join(meta.related_institutions) or "-",
                meta.penalty_amount or "-",
                ";".join(meta.violation_types) or "-",
                ";".join(meta.keywords[:5]) if meta.keywords else "-",  # Limit to 5 keywords
            ]

            line = " | ".join(parts)
            lines.append(line)

        lines.append("```")
        lines.append("")

        # Compact details by type
        lines.append("## 📚 分類明細")
        lines.append("")

        # Define preferred order
        type_order = [
            "裁罰書", "判決書", "法規條文", "監管公告",
            "新聞報導", "銀行聲明", "分析報告", "其他"
        ]

        # Process types in preferred order
        for doc_type in type_order:
            if doc_type not in by_type:
                continue

            docs = by_type[doc_type]
            lines.append(f"### {doc_type} ({len(docs)})")
            lines.append("")

            for meta in docs:
                # Compact one-line summary
                summary_parts = [
                    f"**{meta.filename}**",
                    f"`{meta.date or '無日期'}`",
                ]

                if meta.issuing_authority:
                    summary_parts.append(f"{meta.issuing_authority}")

                if meta.related_institutions:
                    summary_parts.append(f"[{', '.join(meta.related_institutions[:2])}]")

                if meta.penalty_amount:
                    summary_parts.append(f"💰{meta.penalty_amount}")

                if meta.violation_types:
                    summary_parts.append(f"⚠️{', '.join(meta.violation_types[:2])}")

                line = " · ".join(summary_parts)
                lines.append(f"- {line}")

                # Description (if not too long)
                if len(meta.description) <= 100:
                    lines.append(f"  > {meta.description}")
                else:
                    lines.append(f"  > {meta.description[:97]}...")

                lines.append("")

            lines.append("")

        # Process remaining types
        remaining_types = set(by_type.keys()) - set(type_order)
        for doc_type in sorted(remaining_types):
            docs = by_type[doc_type]
            lines.append(f"### {doc_type} ({len(docs)})")
            lines.append("")

            for meta in docs:
                summary_parts = [
                    f"**{meta.filename}**",
                    f"`{meta.date or '無日期'}`",
                ]

                if meta.related_institutions:
                    summary_parts.append(f"[{', '.join(meta.related_institutions[:2])}]")

                line = " · ".join(summary_parts)
                lines.append(f"- {line}")

                if len(meta.description) <= 100:
                    lines.append(f"  > {meta.description}")
                else:
                    lines.append(f"  > {meta.description[:97]}...")

                lines.append("")

            lines.append("")

        # Grep guide
        lines.append("---")
        lines.append("")
        lines.append("## 🔍 使用 Grep 搜尋")
        lines.append("")
        lines.append("```bash")
        lines.append("# 搜尋特定機構")
        lines.append("grep '玉山' TABLE_OF_CONTENTS.md")
        lines.append("")
        lines.append("# 搜尋特定日期")
        lines.append("grep '2020-' TABLE_OF_CONTENTS.md")
        lines.append("")
        lines.append("# 搜尋特定類型")
        lines.append("grep '裁罰書' TABLE_OF_CONTENTS.md")
        lines.append("")
        lines.append("# 搜尋裁罰金額")
        lines.append("grep '億元' TABLE_OF_CONTENTS.md")
        lines.append("")
        lines.append("# 搜尋違規類型")
        lines.append("grep '洗錢防制' TABLE_OF_CONTENTS.md")
        lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def _generate_empty_toc(self) -> str:
        """Generate TOC for empty collection."""
        lines = []
        lines.append("# 文件目錄")
        lines.append("")
        lines.append(f"更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"總數: 0 份")
        lines.append("")
        lines.append("## 📋 目前無文件")
        lines.append("")
        lines.append("請執行以下步驟新增文件：")
        lines.append("")
        lines.append("1. 將文件放置到 `data/documents/` 目錄")
        lines.append("2. 執行 `/reindex` 自動初始化並建立索引")
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


# Alias for backward compatibility
TableOfContents = CompactTableOfContents
