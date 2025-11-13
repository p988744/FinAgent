"""Export formatters for query results."""

import json
from datetime import datetime
from pathlib import Path

from finagent.models.answers import LegalAnswer


def export_to_markdown(answer: LegalAnswer, query: str, filename: str | None = None) -> Path:
    """
    Export answer to Markdown format.

    Args:
        answer: LegalAnswer object
        query: Original query text
        filename: Optional filename (auto-generated if None)

    Returns:
        Path to exported file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"finagent_result_{timestamp}.md"

    filepath = Path(filename)

    # Build markdown content
    content = f"""# FinAgent 查詢結果

**查詢:** {query}
**時間:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**信心評分:** {answer.confidence_level}

---

## 執行摘要

{answer.summary if answer.summary else answer.answer[:200] + "..."}

---

## 完整回答

{answer.answer}

---

"""

    # Add citations if available
    if answer.citations:
        content += """## 引用來源

"""
        for idx, citation in enumerate(answer.citations, 1):
            content += f"""### [{idx}] {citation.title}

- **類型:** {citation.type.value}
- **權威:** {citation.authority.value}
"""
            if citation.date:
                content += f"- **日期:** {citation.date}\n"
            if citation.url:
                content += f"- **網址:** {citation.url}\n"
            if citation.description:
                content += f"- **說明:** {citation.description}\n"

            content += "\n"

    # Add metadata
    content += """---

## 元數據

"""
    if answer.metadata:
        for key, value in answer.metadata.items():
            content += f"- **{key}:** {value}\n"

    content += f"""
---

*此文件由 FinAgent 自動生成於 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Write to file
    filepath.write_text(content, encoding="utf-8")

    return filepath


def export_to_json(answer: LegalAnswer, query: str, filename: str | None = None) -> Path:
    """
    Export answer to JSON format.

    Args:
        answer: LegalAnswer object
        query: Original query text
        filename: Optional filename (auto-generated if None)

    Returns:
        Path to exported file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"finagent_result_{timestamp}.json"

    filepath = Path(filename)

    # Build JSON structure
    data = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "answer": {
            "text": answer.answer,
            "summary": answer.summary,
            "confidence_level": answer.confidence_level,
            "confidence_score": answer.confidence_score,
        },
        "citations": [],
        "metadata": answer.metadata if answer.metadata else {},
    }

    # Add citations
    if answer.citations:
        for citation in answer.citations:
            data["citations"].append(
                {
                    "title": citation.title,
                    "type": citation.type.value,
                    "authority": citation.authority.value,
                    "date": citation.date,
                    "url": citation.url,
                    "description": citation.description,
                    "page_numbers": citation.page_numbers,
                }
            )

    # Write to file
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return filepath


def export_to_text(answer: LegalAnswer, query: str, filename: str | None = None) -> Path:
    """
    Export answer to plain text format.

    Args:
        answer: LegalAnswer object
        query: Original query text
        filename: Optional filename (auto-generated if None)

    Returns:
        Path to exported file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"finagent_result_{timestamp}.txt"

    filepath = Path(filename)

    # Build text content
    content = f"""FinAgent 查詢結果
{"=" * 60}

查詢: {query}
時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
信心評分: {answer.confidence_level}

{"=" * 60}

執行摘要
{"-" * 60}

{answer.summary if answer.summary else answer.answer[:200] + "..."}

{"=" * 60}

完整回答
{"-" * 60}

{answer.answer}

{"=" * 60}

"""

    # Add citations
    if answer.citations:
        content += """引用來源
{"-" * 60}

"""
        for idx, citation in enumerate(answer.citations, 1):
            content += f"""[{idx}] {citation.title}
    類型: {citation.type.value}
    權威: {citation.authority.value}
"""
            if citation.date:
                content += f"    日期: {citation.date}\n"
            if citation.url:
                content += f"    網址: {citation.url}\n"

            content += "\n"

    content += f"""{"-" * 60}

此文件由 FinAgent 自動生成於 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    # Write to file
    filepath.write_text(content, encoding="utf-8")

    return filepath
