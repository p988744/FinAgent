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
