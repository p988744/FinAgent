"""Answer models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from finagent.models.citations import LegalCitation


class ConfidenceLevel(str, Enum):
    """Confidence level for answer."""

    HIGH = "高"  # High confidence
    MEDIUM = "中"  # Medium confidence
    LOW = "低"  # Low confidence


class LegalAnswer(BaseModel):
    """
    Structured answer with formal Taiwan legal citations.

    Represents the final synthesized answer to a legal research query.
    """

    # Core answer components
    executive_summary: str = Field(
        ...,
        max_length=1000,
        description="Executive summary (執行摘要)"
    )
    key_findings: List[str] = Field(
        ...,
        description="Key findings with embedded citations (關鍵發現)"
    )
    detailed_analysis: str = Field(
        ...,
        description="Detailed analysis with comprehensive citations (詳細分析)"
    )

    # Optional components
    precedent_comparison: Optional[str] = Field(
        None,
        description="Comparison with similar cases (判例比較)"
    )

    # Citations
    citations: List[LegalCitation] = Field(
        ...,
        description="All source citations in formal Taiwan legal format"
    )

    # Confidence assessment
    confidence_score: ConfidenceLevel = Field(
        ...,
        description="Confidence level (高/中/低)"
    )
    confidence_explanation: str = Field(
        ...,
        description="Explanation for confidence rating"
    )

    # Limitations
    limitations: List[str] = Field(
        default_factory=list,
        description="Known limitations or caveats"
    )

    # Metadata
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "executive_summary": "玉山商業銀行股份有限公司因其洗錢防制作業缺失，遭金融監督管理委員會裁處新台幣2.5億元罰鍰 [引用1]。",
                "key_findings": [
                    "罰款金額：新台幣2.5億元罰鍰 [引用1，第四章]",
                    "監管機構：金融監督管理委員會（金管會）",
                    "違規類型：洗錢防制法相關規定；違反銀行法第45條之2 [引用1，第三章]"
                ],
                "detailed_analysis": "根據金管會裁罰書...",
                "citations": [
                    {
                        "id": 1,
                        "type": "enforcement_document",
                        "authority": "primary",
                        "title": "玉山銀行洗錢防制缺失裁罰案",
                        "formatted_citation": "金融監督管理委員會，金管銀法字第10800123456號裁罰書（民國108年9月15日）"
                    }
                ],
                "confidence_score": "高",
                "confidence_explanation": "基於官方裁罰書主要來源，所有關鍵事實已驗證",
                "limitations": []
            }
        }
