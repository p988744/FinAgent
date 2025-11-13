"""Legal citation models."""

from enum import Enum

from pydantic import BaseModel, Field


class CitationAuthority(str, Enum):
    """Source authority level for citations."""

    PRIMARY = "primary"  # Official documents (裁罰書, 判決書)
    SECONDARY = "secondary"  # News, regulatory announcements
    TERTIARY = "tertiary"  # Legal commentary, analysis


class CitationType(str, Enum):
    """Type of legal citation."""

    ENFORCEMENT_DOCUMENT = "enforcement_document"  # 裁罰書
    COURT_JUDGMENT = "judgment"  # 判決書
    STATUTE = "statute"  # 法規
    REGULATION = "regulation"  # 行政規則
    NEWS = "news"  # 新聞
    ANNOUNCEMENT = "announcement"  # 公告


class LegalCitation(BaseModel):
    """
    Legal citation with formal Taiwan citation format.

    Represents a source document cited in legal research answers.
    """

    id: int = Field(..., description="Citation number (e.g., 1, 2, 3)")
    type: CitationType = Field(..., description="Type of citation")
    authority: CitationAuthority = Field(..., description="Source authority level")

    # Core citation info
    title: str = Field(..., description="Document title or case name")
    formatted_citation: str = Field(
        ...,
        description="Formatted citation in Taiwan legal style",
        examples=["金融監督管理委員會，金管銀法字第10800123456號裁罰書（民國108年9月15日）"],
    )

    # Optional metadata
    date: str | None = Field(None, description="Document date (YYYY-MM-DD)")
    url: str | None = Field(None, description="Document URL")
    page_number: str | None = Field(None, description="Page number if applicable")
    section: str | None = Field(None, description="Section reference (e.g., '第三章A節')")

    # Source details
    issuing_authority: str | None = Field(
        None, description="Issuing authority (e.g., '金管會', '最高法院')"
    )
    case_number: str | None = Field(None, description="Case number (e.g., '110年台上字第1234號')")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "type": "enforcement_document",
                "authority": "primary",
                "title": "玉山銀行洗錢防制缺失裁罰案",
                "formatted_citation": "金融監督管理委員會，金管銀法字第10800123456號裁罰書，受處分者：玉山商業銀行股份有限公司（民國108年9月15日）",
                "date": "2019-09-15",
                "url": "https://www.fsc.gov.tw/...",
                "issuing_authority": "金管會",
                "case_number": "金管銀法字第10800123456號",
            }
        }
