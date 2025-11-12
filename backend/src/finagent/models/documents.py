"""Document-related models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EnforcementAction(BaseModel):
    """
    Regulatory enforcement action metadata.

    Represents metadata for a penalty or enforcement action from a regulatory body.
    """

    id: str = Field(..., description="Unique identifier")
    case_number: str = Field(..., description="Official case number (案號)")
    entity_name: str = Field(..., description="Entity name (e.g., '玉山商業銀行股份有限公司')")
    regulator: str = Field(..., description="Regulatory body (e.g., '金管會', '央行')")
    sub_agency: Optional[str] = Field(None, description="Sub-agency (e.g., '銀行局')")

    # Dates
    action_date: str = Field(..., description="Date of enforcement action (YYYY-MM-DD)")
    violation_start_date: Optional[str] = Field(None, description="Start of violation period (YYYY-MM-DD)")
    violation_end_date: Optional[str] = Field(None, description="End of violation period (YYYY-MM-DD)")

    # Violation details
    violation_types: List[str] = Field(
        default_factory=list,
        description="Types of violations (e.g., ['洗錢防制', '內線交易'])"
    )
    statutes_cited: List[str] = Field(
        default_factory=list,
        description="Cited statutes (e.g., ['銀行法第125條'])"
    )

    # Penalty
    penalty_amount: Optional[int] = Field(None, description="Penalty amount in NTD")
    penalty_description: Optional[str] = Field(None, description="Penalty description")
    status: str = Field(default="已結案", description="Case status")

    # Document
    document_url: Optional[str] = Field(None, description="URL to official document")
    summary: str = Field(..., max_length=2000, description="Brief summary of the action")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "fsc-2019-001",
                "case_number": "金管銀法字第10800123456號",
                "entity_name": "玉山商業銀行股份有限公司",
                "regulator": "金管會",
                "sub_agency": "銀行局",
                "action_date": "2019-09-15",
                "violation_types": ["洗錢防制"],
                "statutes_cited": ["銀行法第45條之2"],
                "penalty_amount": 250000000,
                "summary": "因洗錢防制作業缺失，裁處罰鍰新台幣2.5億元"
            }
        }


class DocumentMetadata(BaseModel):
    """Metadata extracted from legal documents."""

    document_id: str = Field(..., description="Document identifier")
    document_type: str = Field(..., description="Document type (enforcement, judgment, etc.)")
    title: str = Field(..., description="Document title")
    page_count: int = Field(..., description="Number of pages")

    # Parties
    parties: List[str] = Field(default_factory=list, description="All parties in the document")

    # Case information
    case_number: Optional[str] = Field(None, description="Case number")
    filing_date: Optional[str] = Field(None, description="Filing date (YYYY-MM-DD)")

    # Key dates and amounts
    key_dates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Important dates with labels"
    )
    penalties: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Penalty amounts and descriptions"
    )

    # Content
    violation_summary: List[str] = Field(
        default_factory=list,
        description="Summary of violations"
    )
    statutes_cited: List[str] = Field(default_factory=list, description="Cited statutes")
    remediation_required: List[str] = Field(
        default_factory=list,
        description="Required remediation measures"
    )


class CourtJudgment(BaseModel):
    """Court judgment metadata."""

    case_number: str = Field(..., description="Case number (e.g., '110年金上字第15號')")
    court_name: str = Field(..., description="Court name (e.g., '最高法院')")
    judgment_date: str = Field(..., description="Judgment date (YYYY-MM-DD)")
    case_type: str = Field(..., description="Case type (e.g., '金', '上訴')")

    # Parties
    parties_plaintiff: List[str] = Field(default_factory=list, description="Plaintiffs")
    parties_defendant: List[str] = Field(default_factory=list, description="Defendants")

    # Content
    main_text: str = Field(..., description="Main text (主文)")
    case_summary: str = Field(..., description="Case summary (案由)")
    judgment_url: Optional[str] = Field(None, description="URL to judgment")


class PrecedentCase(BaseModel):
    """Precedent case for comparison."""

    case_id: str = Field(..., description="Case identifier")
    case_name: str = Field(..., description="Case name")
    date: str = Field(..., description="Case date (YYYY-MM-DD)")
    jurisdiction: str = Field(..., description="Jurisdiction/court")

    # Details
    violation_types: List[str] = Field(default_factory=list, description="Violation types")
    penalty_amount: Optional[int] = Field(None, description="Penalty amount in NTD")
    outcome: str = Field(..., description="Case outcome")

    # Similarity
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Semantic similarity score to query"
    )
    key_similarities: List[str] = Field(
        default_factory=list,
        description="Why this precedent is relevant"
    )
    key_differences: List[str] = Field(
        default_factory=list,
        description="Key differences from query case"
    )
