"""Concept extraction from document metadata and TABLE_OF_CONTENTS.md."""

from pathlib import Path

from finagent.document_processing.metadata_store import DocumentMetadata


def extract_document_concepts(metadata: DocumentMetadata) -> list[str]:
    """
    Extract concepts from document metadata.

    Args:
        metadata: Document metadata

    Returns:
        List of concept names extracted from metadata
    """
    concepts = []

    # From violation_types
    if metadata.violation_types:
        concepts.extend(metadata.violation_types)

    # From issuing_authority
    if metadata.issuing_authority:
        concepts.append(metadata.issuing_authority)

    # From related_institutions
    if metadata.related_institutions:
        concepts.extend(metadata.related_institutions)

    # From keywords (top 5 only to avoid noise)
    if metadata.keywords:
        concepts.extend(metadata.keywords[:5])

    # Deduplicate
    return list(set(concepts))


def infer_concept_type(name: str, metadata: DocumentMetadata | None = None) -> str:
    """
    Infer concept type from name and metadata context.

    Args:
        name: Concept name
        metadata: Optional document metadata for context

    Returns:
        Concept type: violation_type, authority, institution, or topic
    """
    # Authority keywords
    authority_keywords = ["金管會", "中央銀行", "公平會", "證期局", "銀行局", "保險局"]
    if any(keyword in name for keyword in authority_keywords):
        return "authority"

    # Institution keywords (bank names, etc.)
    institution_keywords = ["銀行", "保險", "證券", "金控", "Bank", "Insurance"]
    if any(keyword in name for keyword in institution_keywords):
        return "institution"

    # Violation type keywords
    violation_keywords = ["洗錢", "內線", "詐欺", "違規", "裁罰", "防制", "交易", "揭露"]
    if any(keyword in name for keyword in violation_keywords):
        return "violation_type"

    # Check metadata context if provided
    if metadata:
        if name in metadata.violation_types:
            return "violation_type"
        if name == metadata.issuing_authority:
            return "authority"
        if name in metadata.related_institutions:
            return "institution"

    # Default to topic
    return "topic"


def analyze_toc_for_concepts(
    toc_path: Path, llm_generator=None, max_concepts: int = 50
) -> list[dict]:
    """
    Analyze TABLE_OF_CONTENTS.md to extract global concepts using LLM.

    Args:
        toc_path: Path to TABLE_OF_CONTENTS.md
        llm_generator: LLM generator instance (MetadataGenerator or similar)
        max_concepts: Maximum number of concepts to extract

    Returns:
        List of concept dictionaries with name, type, description, keywords
    """
    if not toc_path.exists():
        return []

    # Read TOC content
    toc_content = toc_path.read_text(encoding="utf-8")

    # If no LLM generator provided, do basic extraction
    if llm_generator is None:
        return extract_concepts_basic(toc_content, max_concepts)

    # Use LLM to analyze TOC
    prompt = f"""
分析以下法律文件目錄，提取關鍵概念和主題。

{toc_content[:10000]}  # Limit to first 10000 chars to avoid token limits

請提取前{max_concepts}個最重要的概念/主題，並分類。

輸出格式（JSON array）：
[
  {{
    "concept_name": "洗錢防制",
    "concept_type": "violation_type",
    "description": "銀行未能建立完善的洗錢防制機制",
    "keywords": ["AML", "反洗錢", "可疑交易", "洗錢防制法"]
  }},
  {{
    "concept_name": "金管會",
    "concept_type": "authority",
    "description": "金融監督管理委員會，台灣金融業主管機關",
    "keywords": ["FSC", "金融監管", "監理機關"]
  }},
  {{
    "concept_name": "玉山銀行",
    "concept_type": "institution",
    "description": "玉山商業銀行股份有限公司",
    "keywords": ["E.SUN Bank", "玉山商銀"]
  }}
]

concept_type 必須是以下之一：
- violation_type: 違規類型（洗錢防制、內線交易、資訊揭露等）
- authority: 監管機構（金管會、中央銀行、公平會等）
- institution: 金融機構（銀行、保險公司、證券商等）
- topic: 一般主題

只輸出 JSON array，不要其他文字。
"""

    try:
        # Call LLM
        response = llm_generator.llm.generate(prompt)

        # Parse JSON response
        import json

        concepts = json.loads(response)

        # Validate format
        validated_concepts = []
        for concept in concepts:
            if (
                "concept_name" in concept
                and "concept_type" in concept
                and concept["concept_type"]
                in ["violation_type", "authority", "institution", "topic"]
            ):
                validated_concepts.append(
                    {
                        "name": concept["concept_name"],
                        "concept_type": concept["concept_type"],
                        "description": concept.get("description", ""),
                        "keywords": concept.get("keywords", []),
                    }
                )

        return validated_concepts[:max_concepts]

    except Exception as e:
        print(f"Error analyzing TOC with LLM: {e}")
        # Fallback to basic extraction
        return extract_concepts_basic(toc_content, max_concepts)


def extract_concepts_basic(toc_content: str, max_concepts: int = 50) -> list[dict]:
    """
    Basic concept extraction without LLM (fallback).

    Extracts concepts by counting frequency in TOC.

    Args:
        toc_content: TABLE_OF_CONTENTS.md content
        max_concepts: Maximum number of concepts

    Returns:
        List of concept dictionaries
    """
    from collections import Counter

    # Extract all unique terms from TYPE, AUTHORITY, INSTITUTIONS columns
    concepts_counter = Counter()

    for line in toc_content.split("\n"):
        if "|" in line and "未分類" not in line:
            parts = line.split("|")
            if len(parts) >= 8:
                # TYPE (index 1), AUTHORITY (index 3), INSTITUTIONS (index 4)
                doc_type = parts[1].strip()
                authority = parts[3].strip()
                institutions = parts[4].strip()

                if doc_type and doc_type != "-":
                    concepts_counter[doc_type] += 1
                if authority and authority != "-":
                    concepts_counter[authority] += 1
                if institutions and institutions != "-":
                    for inst in institutions.split(","):
                        inst = inst.strip()
                        if inst:
                            concepts_counter[inst] += 1

    # Get top concepts
    top_concepts = concepts_counter.most_common(max_concepts)

    # Convert to concept format
    concepts = []
    for name, count in top_concepts:
        concepts.append(
            {
                "name": name,
                "concept_type": infer_concept_type(name),
                "description": f"出現在 {count} 份文件中",
                "keywords": [],
            }
        )

    return concepts
