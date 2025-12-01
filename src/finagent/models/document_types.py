"""
Document Type Classification Schema

Defines the allowed document types for the FinAgent system.
This limits uploads to financial regulatory documents only.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class DocumentCategory(str, Enum):
    """High-level document categories."""

    # Primary categories - Financial regulatory documents
    PENALTY = "penalty"                    # 裁罰書 - Penalty/enforcement documents
    LEGAL_PROVISION = "legal_provision"    # 法條 - Legal provisions/articles
    COURT_JUDGMENT = "court_judgment"      # 判決書 - Court judgments
    REGULATORY_NOTICE = "regulatory_notice"  # 監管公告 - Regulatory announcements
    KNOWLEDGE_BASE = "knowledge_base"      # 知識文件 - Knowledge base documents

    # Secondary categories
    NEWS = "news"                          # 新聞報導 - News articles
    ANALYSIS = "analysis"                  # 分析報告 - Analysis reports
    BANK_STATEMENT = "bank_statement"      # 銀行聲明 - Bank statements

    # Internal use
    OTHER = "other"                        # 其他 - Other


class DocumentType(BaseModel):
    """Document type definition with metadata."""

    category: DocumentCategory
    name_zh: str                           # Chinese name
    name_en: str                           # English name
    description: str                       # Description
    allowed: bool = True                   # Whether this type is allowed for upload
    requires_authority: bool = False       # Whether issuing authority is required
    requires_date: bool = False            # Whether document date is required
    example_filename_pattern: Optional[str] = None  # Example filename pattern


# Allowed document types for upload
ALLOWED_DOCUMENT_TYPES: dict[DocumentCategory, DocumentType] = {
    DocumentCategory.PENALTY: DocumentType(
        category=DocumentCategory.PENALTY,
        name_zh="裁罰書",
        name_en="Penalty Document",
        description="金融監理機關（金管會）發布的裁罰書",
        allowed=True,
        requires_authority=True,
        requires_date=True,
        example_filename_pattern="001_20120112_銀行局_高雄銀行.txt",
    ),
    DocumentCategory.LEGAL_PROVISION: DocumentType(
        category=DocumentCategory.LEGAL_PROVISION,
        name_zh="法條",
        name_en="Legal Provision",
        description="金融相關法規條文（銀行法、洗錢防制法、證券交易法等）",
        allowed=True,
        requires_authority=False,
        requires_date=False,
        example_filename_pattern="法條_銀行法第45條_銀行監理.txt",
    ),
    DocumentCategory.COURT_JUDGMENT: DocumentType(
        category=DocumentCategory.COURT_JUDGMENT,
        name_zh="判決書",
        name_en="Court Judgment",
        description="法院對金融違規案件的判決書",
        allowed=True,
        requires_authority=True,
        requires_date=True,
        example_filename_pattern="判決書_最高法院_109年度台上字第XXX號.txt",
    ),
    DocumentCategory.REGULATORY_NOTICE: DocumentType(
        category=DocumentCategory.REGULATORY_NOTICE,
        name_zh="監管公告",
        name_en="Regulatory Notice",
        description="金融監理機關發布的公告、函釋",
        allowed=True,
        requires_authority=True,
        requires_date=True,
        example_filename_pattern="公告_金管會_20240101_XXXXX.txt",
    ),
    DocumentCategory.KNOWLEDGE_BASE: DocumentType(
        category=DocumentCategory.KNOWLEDGE_BASE,
        name_zh="知識文件",
        name_en="Knowledge Document",
        description="構成要件分析、違規類型對照表等參考文件",
        allowed=True,
        requires_authority=False,
        requires_date=False,
        example_filename_pattern="知識_金融違規類型與構成要件對照表.txt",
    ),
    DocumentCategory.NEWS: DocumentType(
        category=DocumentCategory.NEWS,
        name_zh="新聞報導",
        name_en="News Article",
        description="金融違規相關新聞報導",
        allowed=False,  # Not allowed - secondary source
        requires_authority=False,
        requires_date=True,
    ),
    DocumentCategory.ANALYSIS: DocumentType(
        category=DocumentCategory.ANALYSIS,
        name_zh="分析報告",
        name_en="Analysis Report",
        description="金融違規分析報告",
        allowed=False,  # Not allowed - secondary source
        requires_authority=False,
        requires_date=True,
    ),
    DocumentCategory.BANK_STATEMENT: DocumentType(
        category=DocumentCategory.BANK_STATEMENT,
        name_zh="銀行聲明",
        name_en="Bank Statement",
        description="銀行對裁罰的公開聲明",
        allowed=False,  # Not allowed - biased source
        requires_authority=False,
        requires_date=True,
    ),
    DocumentCategory.OTHER: DocumentType(
        category=DocumentCategory.OTHER,
        name_zh="其他",
        name_en="Other",
        description="其他類型文件（需審核）",
        allowed=False,  # Not allowed by default
        requires_authority=False,
        requires_date=False,
    ),
}


def get_allowed_categories() -> list[DocumentCategory]:
    """Get list of document categories allowed for upload."""
    return [
        cat for cat, doc_type in ALLOWED_DOCUMENT_TYPES.items()
        if doc_type.allowed
    ]


def get_allowed_document_types() -> list[DocumentType]:
    """Get list of document types allowed for upload."""
    return [
        doc_type for doc_type in ALLOWED_DOCUMENT_TYPES.values()
        if doc_type.allowed
    ]


def is_document_type_allowed(category: DocumentCategory | str) -> bool:
    """Check if a document type is allowed for upload."""
    if isinstance(category, str):
        try:
            category = DocumentCategory(category)
        except ValueError:
            return False

    doc_type = ALLOWED_DOCUMENT_TYPES.get(category)
    return doc_type.allowed if doc_type else False


def get_document_type_info(category: DocumentCategory | str) -> Optional[DocumentType]:
    """Get document type information."""
    if isinstance(category, str):
        try:
            category = DocumentCategory(category)
        except ValueError:
            return None

    return ALLOWED_DOCUMENT_TYPES.get(category)


# Validation error messages
DOCUMENT_TYPE_ERRORS = {
    "invalid_type": "無效的文件類型。請選擇：{allowed_types}",
    "not_allowed": "此文件類型（{type_name}）不允許上傳。僅允許上傳以下類型：{allowed_types}",
    "missing_authority": "此文件類型需要指定發布機關",
    "missing_date": "此文件類型需要指定文件日期",
}


class DocumentTypeValidationResult(BaseModel):
    """Result of document type validation."""

    valid: bool
    category: Optional[DocumentCategory] = None
    document_type: Optional[DocumentType] = None
    error_message: Optional[str] = None
    warnings: list[str] = []


def classify_document_by_path(file_path: str) -> DocumentCategory:
    """
    Auto-classify document type based on file path and filename patterns.

    Classification rules (priority order):
    1. Check filename prefix (法條_, 知識_, 判決書_, 公告_, etc.) - HIGHEST PRIORITY
    2. Check penalty document pattern (XXX_YYYYMMDD_機關_機構.txt → 裁罰書)
    3. Check parent directory name (法規, 裁罰歷史資料, FAQ, etc.)
    4. Check regulatory authority keywords in filename

    Args:
        file_path: Full file path or filename

    Returns:
        DocumentCategory based on classification rules
    """
    import re
    from pathlib import Path

    path = Path(file_path)
    filename = path.name
    parent_dir = path.parent.name if path.parent.name != "documents" else ""

    # Rule 1: Check filename prefix (HIGHEST PRIORITY)
    # This ensures specific file naming conventions override directory-based classification
    prefix_mapping = {
        "法條_": DocumentCategory.LEGAL_PROVISION,
        "知識_": DocumentCategory.KNOWLEDGE_BASE,
        "判決書_": DocumentCategory.COURT_JUDGMENT,
        "公告_": DocumentCategory.REGULATORY_NOTICE,
        "裁罰_": DocumentCategory.PENALTY,
    }

    for prefix, category in prefix_mapping.items():
        if filename.startswith(prefix):
            return category

    # Rule 2: Check penalty document pattern (XXX_YYYYMMDD_機關_機構.txt)
    # Examples: 001_20120112_銀行局_高雄銀行股份有限公司.txt
    penalty_pattern = r"^\d{3}_\d{8}_[\u4e00-\u9fff]+_.*\.txt$"
    if re.match(penalty_pattern, filename):
        return DocumentCategory.PENALTY

    # Rule 3: Check parent directory
    dir_mapping = {
        "法規": DocumentCategory.LEGAL_PROVISION,
        "裁罰歷史資料": DocumentCategory.PENALTY,
        "裁罰資料": DocumentCategory.PENALTY,
        "判決書": DocumentCategory.COURT_JUDGMENT,
        "公告": DocumentCategory.REGULATORY_NOTICE,
        "知識": DocumentCategory.KNOWLEDGE_BASE,
        "FAQ": DocumentCategory.KNOWLEDGE_BASE,
    }

    if parent_dir in dir_mapping:
        return dir_mapping[parent_dir]

    # Rule 4: Check if filename contains regulatory authority keywords
    authority_keywords = ["銀行局", "保險局", "證券期貨局", "金管會", "檢查局"]
    for keyword in authority_keywords:
        if keyword in filename:
            return DocumentCategory.PENALTY

    # Default: OTHER (will need manual classification)
    return DocumentCategory.OTHER


def classify_document_by_content(content: str, filename: str = "") -> DocumentCategory:
    """
    Auto-classify document type based on content analysis (rule-based).

    This is a fallback when path-based classification returns OTHER.

    Args:
        content: Document text content
        filename: Optional filename for additional context

    Returns:
        DocumentCategory based on content analysis
    """
    # First try path-based classification
    if filename:
        path_category = classify_document_by_path(filename)
        if path_category != DocumentCategory.OTHER:
            return path_category

    # Content-based classification
    content_lower = content[:2000]  # Check first 2000 chars

    # Legal provision indicators
    legal_keywords = ["第一條", "第二條", "第一項", "依據本法", "違反本法", "條文"]
    if any(kw in content_lower for kw in legal_keywords) and "法" in content_lower:
        return DocumentCategory.LEGAL_PROVISION

    # Penalty document indicators
    penalty_keywords = ["裁罰", "處分", "罰鍰", "新臺幣", "金管銀", "金管證", "金管保"]
    if sum(1 for kw in penalty_keywords if kw in content_lower) >= 2:
        return DocumentCategory.PENALTY

    # Court judgment indicators
    judgment_keywords = ["判決", "上訴人", "被上訴人", "原審", "法院"]
    if sum(1 for kw in judgment_keywords if kw in content_lower) >= 2:
        return DocumentCategory.COURT_JUDGMENT

    # Knowledge base indicators
    knowledge_keywords = ["定義", "類型", "要件", "概念", "說明", "對照表"]
    if any(kw in content_lower for kw in knowledge_keywords):
        return DocumentCategory.KNOWLEDGE_BASE

    return DocumentCategory.OTHER


class LLMClassificationResult(BaseModel):
    """Result of LLM-based document classification."""

    category: DocumentCategory
    confidence: float  # 0.0 - 1.0
    reasoning: str
    suggested_document_type: Optional[str] = None  # e.g., "裁罰書", "法條", "知識文件"


async def classify_document_with_llm(
    content: str,
    filename: str = "",
    use_fallback: bool = True,
) -> LLMClassificationResult:
    """
    Classify document type using LLM (GPT-4o-mini).

    This provides more accurate classification than rule-based methods,
    especially for edge cases and ambiguous documents.

    Args:
        content: Document text content (first 3000 chars will be used)
        filename: Optional filename for additional context
        use_fallback: If True, use rule-based fallback on LLM failure

    Returns:
        LLMClassificationResult with category, confidence, and reasoning
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from finagent.config import settings
    import json
    import logging

    logger = logging.getLogger(__name__)

    # First try path-based classification (fast, no API cost)
    if filename:
        path_category = classify_document_by_path(filename)
        if path_category != DocumentCategory.OTHER:
            return LLMClassificationResult(
                category=path_category,
                confidence=0.95,
                reasoning=f"根據檔案路徑/名稱分類: {filename}",
                suggested_document_type=ALLOWED_DOCUMENT_TYPES[path_category].name_zh,
            )

    # Prepare content snippet
    content_snippet = content[:3000] if len(content) > 3000 else content

    # LLM classification prompt
    prompt = ChatPromptTemplate.from_template("""你是一位金融法律文件分類專家。請分析以下文件內容，判斷其屬於哪種類型。

文件名稱: {filename}

文件內容（節錄）:
{content}

可用的文件類型:
1. penalty - 裁罰書: 金融監理機關（金管會）發布的裁罰處分書，包含違規事實、法律依據、處分內容
2. legal_provision - 法條: 金融相關法規條文（銀行法、洗錢防制法、證券交易法等）
3. court_judgment - 判決書: 法院對金融違規案件的判決書
4. regulatory_notice - 監管公告: 金融監理機關發布的公告、函釋
5. knowledge_base - 知識文件: 構成要件分析、違規類型對照表、解釋說明等參考文件

請用 JSON 格式回覆:
{{
    "category": "penalty|legal_provision|court_judgment|regulatory_notice|knowledge_base",
    "confidence": 0.0-1.0,
    "reasoning": "簡短說明分類理由",
    "suggested_document_type": "中文類型名稱"
}}

只輸出 JSON，不要其他文字。""")

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # Use fast, cheap model for classification
            api_key=settings.effective_llm_api_key,
            base_url=settings.effective_llm_base_url,
            temperature=0,
            timeout=30,
        )

        chain = prompt | llm
        response = await chain.ainvoke({
            "filename": filename or "未知",
            "content": content_snippet,
        })

        # Parse JSON response
        response_text = response.content.strip()
        # Remove markdown code block if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        result = json.loads(response_text)

        # Map category string to enum
        category_str = result.get("category", "other")
        try:
            category = DocumentCategory(category_str)
        except ValueError:
            category = DocumentCategory.OTHER

        return LLMClassificationResult(
            category=category,
            confidence=float(result.get("confidence", 0.8)),
            reasoning=result.get("reasoning", "LLM 分類"),
            suggested_document_type=result.get("suggested_document_type"),
        )

    except Exception as e:
        logger.warning(f"LLM classification failed: {e}, using fallback")

        if use_fallback:
            # Fallback to rule-based classification
            fallback_category = classify_document_by_content(content, filename)
            return LLMClassificationResult(
                category=fallback_category,
                confidence=0.6,
                reasoning=f"規則分類（LLM 失敗: {str(e)[:50]}）",
                suggested_document_type=ALLOWED_DOCUMENT_TYPES.get(
                    fallback_category, ALLOWED_DOCUMENT_TYPES[DocumentCategory.OTHER]
                ).name_zh,
            )
        else:
            raise


def validate_document_type(
    category: str | DocumentCategory,
    issuing_authority: Optional[str] = None,
    document_date: Optional[str] = None,
) -> DocumentTypeValidationResult:
    """
    Validate document type for upload.

    Args:
        category: Document category to validate
        issuing_authority: Optional issuing authority (required for some types)
        document_date: Optional document date (required for some types)

    Returns:
        DocumentTypeValidationResult with validation status and any errors
    """
    warnings = []

    # Convert string to enum
    if isinstance(category, str):
        try:
            category = DocumentCategory(category)
        except ValueError:
            allowed_types = ", ".join([t.name_zh for t in get_allowed_document_types()])
            return DocumentTypeValidationResult(
                valid=False,
                error_message=DOCUMENT_TYPE_ERRORS["invalid_type"].format(
                    allowed_types=allowed_types
                ),
            )

    # Get document type info
    doc_type = ALLOWED_DOCUMENT_TYPES.get(category)
    if not doc_type:
        return DocumentTypeValidationResult(
            valid=False,
            error_message=f"Unknown document category: {category}",
        )

    # Check if type is allowed
    if not doc_type.allowed:
        allowed_types = ", ".join([t.name_zh for t in get_allowed_document_types()])
        return DocumentTypeValidationResult(
            valid=False,
            category=category,
            document_type=doc_type,
            error_message=DOCUMENT_TYPE_ERRORS["not_allowed"].format(
                type_name=doc_type.name_zh,
                allowed_types=allowed_types,
            ),
        )

    # Check required fields (warnings, not errors)
    if doc_type.requires_authority and not issuing_authority:
        warnings.append(DOCUMENT_TYPE_ERRORS["missing_authority"])

    if doc_type.requires_date and not document_date:
        warnings.append(DOCUMENT_TYPE_ERRORS["missing_date"])

    return DocumentTypeValidationResult(
        valid=True,
        category=category,
        document_type=doc_type,
        warnings=warnings,
    )
