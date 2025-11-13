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
**信心評分:** {answer.confidence_score}

---

## 執行摘要

{answer.executive_summary}

---

## 關鍵發現

"""
    for finding in answer.key_findings:
        content += f"- {finding}\n"

    content += f"""
---

## 詳細分析

{answer.detailed_analysis}

"""

    if answer.final_answer:
        content += f"""---

## 最終答案

{answer.final_answer}

"""

    content += "---\n\n"

    # Add citations if available
    if answer.citations:
        content += """## 引用來源

"""
        for citation in answer.citations:
            content += f"""### [{citation.id}] {citation.title}

{citation.formatted_citation}

- **類型:** {citation.type.value}
- **權威:** {citation.authority.value}
"""
            if citation.date:
                content += f"- **日期:** {citation.date}\n"
            if citation.url:
                content += f"- **網址:** {citation.url}\n"

            content += "\n"

    # Add confidence explanation
    if answer.confidence_explanation:
        content += f"""---

## 信心評估說明

{answer.confidence_explanation}

"""

    # Add limitations
    if answer.limitations:
        content += """---

## 限制與注意事項

"""
        for limitation in answer.limitations:
            content += f"- {limitation}\n"

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
            "executive_summary": answer.executive_summary,
            "key_findings": answer.key_findings,
            "detailed_analysis": answer.detailed_analysis,
            "final_answer": answer.final_answer,
            "confidence_score": answer.confidence_score,
            "confidence_explanation": answer.confidence_explanation,
        },
        "citations": [],
        "limitations": answer.limitations,
        "processing_time_ms": answer.processing_time_ms,
    }

    # Add citations
    if answer.citations:
        for citation in answer.citations:
            data["citations"].append(
                {
                    "id": citation.id,
                    "title": citation.title,
                    "formatted_citation": citation.formatted_citation,
                    "type": citation.type.value,
                    "authority": citation.authority.value,
                    "date": citation.date,
                    "url": citation.url,
                    "page_number": citation.page_number,
                    "section": citation.section,
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
信心評分: {answer.confidence_score}

{"=" * 60}

執行摘要
{"-" * 60}

{answer.executive_summary}

{"=" * 60}

關鍵發現
{"-" * 60}

"""
    for finding in answer.key_findings:
        content += f"• {finding}\n"

    content += f"""
{"=" * 60}

詳細分析
{"-" * 60}

{answer.detailed_analysis}

"""

    if answer.final_answer:
        content += f"""{"=" * 60}

最終答案
{"-" * 60}

{answer.final_answer}

"""

    content += f"""{"=" * 60}

"""

    # Add citations
    if answer.citations:
        content += f"""引用來源
{"-" * 60}

"""
        for citation in answer.citations:
            content += f"""[{citation.id}] {citation.title}
    {citation.formatted_citation}
    類型: {citation.type.value}
    權威: {citation.authority.value}
"""
            if citation.date:
                content += f"    日期: {citation.date}\n"
            if citation.url:
                content += f"    網址: {citation.url}\n"

            content += "\n"

    # Add confidence explanation
    if answer.confidence_explanation:
        content += f"""信心評估說明
{"-" * 60}

{answer.confidence_explanation}

"""

    # Add limitations
    if answer.limitations:
        content += f"""限制與注意事項
{"-" * 60}

"""
        for limitation in answer.limitations:
            content += f"• {limitation}\n"
        content += "\n"

    content += f"""{"-" * 60}

此文件由 FinAgent 自動生成於 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    # Write to file
    filepath.write_text(content, encoding="utf-8")

    return filepath
