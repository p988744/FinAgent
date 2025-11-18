"""
Pydantic models for document metadata extraction.

This module defines the schema for LLM-extracted metadata from legal documents.
All models use Pydantic for validation and serialization.
"""

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """
    Structured metadata extracted from a legal document using LLM.

    This model represents the complete metadata for a financial regulatory document,
    including administrative information, parties involved, violations, and penalties.
    """

    # Required fields
    title: str = Field(
        ...,
        description="Document title (e.g., '金融監督管理委員會裁罰書 - 玉山銀行洗錢防制違規')",
        min_length=1,
    )

    description: str = Field(
        ...,
        description="2-3 sentence summary of the document in Traditional Chinese",
        min_length=10,
    )

    document_type: str = Field(
        ...,
        description="Document type category: 裁罰書, 判決書, 法規, 新聞, 研究報告, 其他",
    )

    # Optional administrative fields
    issuing_authority: str | None = Field(
        None,
        description="Issuing authority: 金管會, 銀行局, 證券期貨局, 保險局, 中央銀行, 公平會, 法院, or None",
    )

    case_number: str | None = Field(
        None,
        description="Official case/document number (e.g., '金管銀法字第10902345678號')",
    )

    document_date: str | None = Field(
        None,
        description="Document date in YYYY-MM-DD format (convert ROC dates to AD)",
    )

    # Entities and violations
    related_institutions: list[str] = Field(
        default_factory=list,
        description="List of financial institutions mentioned (e.g., ['玉山商業銀行', '國泰世華銀行'])",
    )

    violation_types: list[str] = Field(
        default_factory=list,
        description="List of violation types (e.g., ['洗錢防制', '內部控制', '內線交易'])",
    )

    penalty_amount: str | None = Field(
        None,
        description="Penalty amount as string (e.g., 'NT$250,000,000' or '新臺幣貳億伍仟萬元')",
    )

    # Semantic metadata
    keywords: list[str] = Field(
        default_factory=list,
        description="5-10 keywords extracted from the document for search and categorization",
        min_length=0,  # Allow empty lists
        max_length=15,
    )

    # Quality metadata
    extraction_confidence: float = Field(
        ...,
        description="Confidence score for extraction quality (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    extraction_method: str = Field(
        default="llm",
        description="Method used for extraction: 'llm', 'manual', 'hybrid'",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "title": "金融監督管理委員會裁罰書 - 玉山銀行洗錢防制違規",
                "description": "金管會於109年9月15日對玉山商業銀行因違反洗錢防制法第6條及銀行法相關規定，處新臺幣貳億伍仟萬元罰鍰。主要違規事項包括客戶審查不確實、交易監控機制不完善、及疑似洗錢交易通報延遲。",
                "document_type": "裁罰書",
                "issuing_authority": "金管會",
                "case_number": "金管銀法字第10900123456號",
                "document_date": "2020-09-15",
                "related_institutions": ["玉山商業銀行股份有限公司"],
                "violation_types": ["洗錢防制", "內部控制"],
                "penalty_amount": "NT$250,000,000",
                "keywords": [
                    "洗錢防制",
                    "玉山銀行",
                    "裁罰",
                    "客戶審查",
                    "交易監控",
                    "內部控制",
                ],
                "extraction_confidence": 0.95,
                "extraction_method": "llm",
            }
        }


class MetadataExtractionResult(BaseModel):
    """
    Result of metadata extraction operation.

    Contains the extracted metadata along with operational metadata like
    processing time and any errors encountered.
    """

    doc_id: str = Field(..., description="Document identifier")

    metadata: DocumentMetadata | None = Field(
        None, description="Extracted metadata (None if extraction failed)"
    )

    success: bool = Field(..., description="Whether extraction succeeded")

    error: str | None = Field(None, description="Error message if extraction failed")

    processing_time: float = Field(
        ..., description="Time taken for extraction in seconds", ge=0.0
    )

    llm_tokens_used: int | None = Field(
        None, description="Number of tokens used by LLM", ge=0
    )

    llm_cost_usd: float | None = Field(
        None, description="Estimated cost in USD for LLM call", ge=0.0
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "doc_id": "doc_玉山銀行_洗錢防制裁罰_2020_1da27f67",
                "metadata": {
                    "title": "金融監督管理委員會裁罰書 - 玉山銀行洗錢防制違規",
                    "description": "金管會於109年9月15日對玉山商業銀行處罰...",
                    "document_type": "裁罰書",
                    "issuing_authority": "金管會",
                    "case_number": "金管銀法字第10900123456號",
                    "document_date": "2020-09-15",
                    "related_institutions": ["玉山商業銀行股份有限公司"],
                    "violation_types": ["洗錢防制", "內部控制"],
                    "penalty_amount": "NT$250,000,000",
                    "keywords": ["洗錢防制", "玉山銀行", "裁罰"],
                    "extraction_confidence": 0.95,
                    "extraction_method": "llm",
                },
                "success": True,
                "error": None,
                "processing_time": 2.5,
                "llm_tokens_used": 1500,
                "llm_cost_usd": 0.0015,
            }
        }
