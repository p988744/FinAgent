"""Extended document metadata for filtering and querying."""

from datetime import datetime

from pydantic import BaseModel, Field


class ExtendedDocumentMetadata(BaseModel):
    """
    Extended document metadata for filtering and temporal queries.

    This model is used for the metadata database layer to enable
    metadata-based search and filtering.
    """

    # File information
    filename: str = Field(..., description="Document filename")
    file_path: str = Field(..., description="Full file path")

    # Entity information
    entity: str = Field(..., description="Bank or institution name")
    entity_normalized: str = Field(
        ...,
        description="Normalized entity name (e.g., '玉山銀行' → '玉山商業銀行股份有限公司')",
    )

    # Penalty information
    penalty_type: str = Field(
        ..., description="Penalty type (洗錢防制, 內線交易, etc.)"
    )
    penalty_amount: float | None = Field(None, description="Penalty amount in NTD")

    # Date information
    date: str = Field(..., description="Document date (ISO format YYYY-MM-DD)")
    year_roc: int | None = Field(None, description="ROC year (民國)")
    year_ad: int | None = Field(None, description="AD year")

    # Jurisdiction
    jurisdiction: str = Field(
        ..., description="Regulatory body (金管會, 中央銀行, etc.)"
    )

    # Document characteristics
    document_type: str = Field(
        ..., description="Document type (裁罰書, 判決書, etc.)"
    )
    case_number: str | None = Field(None, description="Case number (案號)")

    # Content metadata
    content_length: int = Field(..., description="Content length in characters")
    chunk_count: int = Field(..., description="Number of chunks indexed")

    # Timestamps
    indexed_at: str = Field(..., description="Indexing timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "玉山銀行_洗錢防制_2020.txt",
                "file_path": "./data/documents/玉山銀行_洗錢防制_2020.txt",
                "entity": "玉山銀行",
                "entity_normalized": "玉山商業銀行股份有限公司",
                "penalty_type": "洗錢防制",
                "penalty_amount": 250000000.0,
                "date": "2020-09-15",
                "year_roc": 109,
                "year_ad": 2020,
                "jurisdiction": "金管會",
                "document_type": "裁罰書",
                "case_number": "金管銀法字第10900123456號",
                "content_length": 15000,
                "chunk_count": 35,
                "indexed_at": "2025-01-18T10:30:00",
                "updated_at": "2025-01-18T10:30:00",
            }
        }
