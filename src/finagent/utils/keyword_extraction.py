"""Keyword extraction utilities for query validation."""

import re
from typing import List, Tuple


def extract_critical_keywords(query: str) -> List[str]:
    """
    Extract critical keywords that MUST appear in cited documents.

    Focuses on domain-specific terms, technical phrases, and key concepts
    that define the query's specific topic.

    Args:
        query: User query text

    Returns:
        List of critical keywords that must be present in citations
    """
    keywords = []

    # Pattern 1: Multi-character technical terms (5+ characters, high priority)
    # These are usually specific topics that MUST match
    technical_terms = [
        "專業投資人資格審核",
        "專業投資人",
        "共同行銷",
        "創投公司",
        "創業投資",
        "警告處分",
        "內線交易",
        "重大訊息",
        "利害關係人",
        "洗錢防制",
        "法規遵循",
        "作業風險",
    ]

    for term in technical_terms:
        if term in query:
            keywords.append(term)

    # Pattern 2: Entity type keywords (must match entity type)
    entity_keywords = {
        "創投": ["創投", "創業投資"],
        "證券商": ["證券商"],
        "銀行": ["銀行"],
        "保險": ["保險", "人壽", "產險"],
        "投信": ["證券投資信託", "投信"],
    }

    for entity_type, variants in entity_keywords.items():
        for variant in variants:
            if variant in query and variant not in keywords:
                keywords.append(variant)
                break  # Only add one variant per type

    # Pattern 3: Legal/regulatory specific terms
    legal_terms = [
        "金控法", "證券交易法", "銀行法", "保險法",
        "裁罰", "處分", "罰鍰", "糾正",
    ]

    for term in legal_terms:
        if term in query and len(term) >= 3:  # Avoid single char matches
            if term not in keywords:
                keywords.append(term)

    return keywords


def extract_must_have_keywords(query: str) -> List[str]:
    """
    Extract keywords that are absolutely required in cited documents.

    More restrictive than critical_keywords - these are non-negotiable.

    Args:
        query: User query text

    Returns:
        List of must-have keywords
    """
    must_have = []

    # Specific technical topics (5+ chars) - these MUST appear
    if "專業投資人" in query:
        must_have.append("專業投資人")

    if "共同行銷" in query:
        must_have.append("共同行銷")

    if "創投" in query or "創業投資" in query:
        must_have.extend(["創投", "創業投資"])  # At least one must match

    if "警告" in query and "處分" in query:
        must_have.append("警告")

    if "內線交易" in query:
        must_have.append("內線交易")

    return must_have


def extract_keywords_with_priority(query: str) -> List[Tuple[str, int]]:
    """
    Extract keywords with priority scores for ranking.

    Higher priority = more important to match

    Args:
        query: User query text

    Returns:
        List of (keyword, priority_score) tuples, sorted by priority
    """
    keywords_with_priority = []

    # Priority 10: Specific technical phrases (5+ chars)
    priority_10_patterns = [
        "專業投資人資格審核",
        "內線交易重大訊息",
        "利害關係人交易",
    ]

    for pattern in priority_10_patterns:
        if pattern in query:
            keywords_with_priority.append((pattern, 10))

    # Priority 9: Technical terms (4-5 chars)
    priority_9_patterns = [
        "專業投資人",
        "共同行銷",
        "警告處分",
        "內線交易",
        "洗錢防制",
    ]

    for pattern in priority_9_patterns:
        if pattern in query and pattern not in [k for k, _ in keywords_with_priority]:
            keywords_with_priority.append((pattern, 9))

    # Priority 8: Entity types
    entity_patterns = [
        "創投公司", "創業投資",
        "證券商", "投信公司",
        "銀行", "保險公司",
    ]

    for pattern in entity_patterns:
        if pattern in query and pattern not in [k for k, _ in keywords_with_priority]:
            keywords_with_priority.append((pattern, 8))

    # Priority 7: Regulatory authorities
    authority_patterns = ["金管會", "中央銀行", "公平會"]
    for pattern in authority_patterns:
        if pattern in query and pattern not in [k for k, _ in keywords_with_priority]:
            keywords_with_priority.append((pattern, 7))

    # Priority 5: Legal terms
    legal_patterns = ["金控法", "證券交易法", "銀行法", "裁罰", "處分"]
    for pattern in legal_patterns:
        if pattern in query and pattern not in [k for k, _ in keywords_with_priority]:
            keywords_with_priority.append((pattern, 5))

    # Priority 3: General terms (2-3 chars)
    general_patterns = ["證券", "金融", "投資"]
    for pattern in general_patterns:
        if pattern in query and pattern not in [k for k, _ in keywords_with_priority]:
            keywords_with_priority.append((pattern, 3))

    # Sort by priority (highest first)
    keywords_with_priority.sort(key=lambda x: x[1], reverse=True)

    return keywords_with_priority


def identify_entity_type(text: str) -> str:
    """
    Identify the entity type mentioned in text.

    Args:
        text: Query or document text

    Returns:
        Entity type string or "unknown"
    """
    # Check in order of specificity
    if "創投" in text or "創業投資" in text:
        return "venture_capital"

    if "證券投資信託" in text or "投信" in text:
        return "securities_investment_trust"

    if "證券商" in text:
        return "securities_firm"

    if "商業銀行" in text or ("銀行" in text and "中央銀行" not in text):
        return "commercial_bank"

    if "保險" in text:
        if "人壽" in text:
            return "life_insurance"
        elif "產險" in text or "產物保險" in text:
            return "property_insurance"
        return "insurance"

    if "金融控股" in text or "金控" in text:
        return "financial_holding"

    return "unknown"


def validate_keyword_presence(keywords: List[str], document_text: str) -> Tuple[bool, List[str]]:
    """
    Check if required keywords are present in document.

    Args:
        keywords: List of required keywords
        document_text: Document content to check

    Returns:
        Tuple of (all_present: bool, missing_keywords: List[str])
    """
    missing = []

    for keyword in keywords:
        if keyword not in document_text:
            missing.append(keyword)

    return len(missing) == 0, missing


def validate_entity_type_match(query: str, document_text: str) -> bool:
    """
    Check if query and document discuss the same entity type.

    Args:
        query: User query
        document_text: Document content

    Returns:
        True if entity types match or if no specific type required
    """
    query_type = identify_entity_type(query)
    doc_type = identify_entity_type(document_text)

    # If query doesn't specify entity type, accept any document
    if query_type == "unknown":
        return True

    # If document doesn't have clear type, be conservative and reject
    if doc_type == "unknown":
        return False

    # Types must match
    return query_type == doc_type
