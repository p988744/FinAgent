"""
Tests for LLM metadata extraction functionality.

This module tests the metadata extraction pipeline for Taiwan financial regulatory documents.
"""

import pytest
from pathlib import Path

from finagent.document_processing.metadata_models import DocumentMetadata, MetadataExtractionResult


# Sample document content for testing
SAMPLE_PENALTY_DOCUMENT = """金融監督管理委員會裁罰書

受處分人：玉山商業銀行股份有限公司
裁罰文號：金管銀法字第10900123456號
裁罰日期：民國109年9月15日

主文

玉山商業銀行股份有限公司因違反洗錢防制法第6條及銀行法相關規定，處新臺幣貳億伍仟萬元罰鍰。

事實

一、玉山商業銀行股份有限公司（下稱該行）辦理防制洗錢及打擊資恐作業，經查有下列缺失：
    (一) 客戶審查作業未確實執行
    (二) 交易監控機制未能有效發現異常交易
    (三) 疑似洗錢交易通報作業延遲

二、該行對高風險客戶之持續審查機制不足，未能及時更新客戶資料及風險評估。

理由

該行違反洗錢防制法第6條第1項規定，依同法第7條第2項規定，處新臺幣貳億伍仟萬元罰鍰。
"""

SAMPLE_COURT_JUDGMENT = """臺灣臺北地方法院刑事判決
案號：110年金重訴字第12號
判決日期：民國110年6月20日

被告：張○○
      國泰世華商業銀行股份有限公司理財專員

主文

張○○犯證券交易法第一百七十一條第一項第一款之內線交易罪，處有期徒刑貳年。

事實

一、張○○於民國108年間擔任國泰世華商業銀行理財專員，因職務關係知悉某上市公司重大消息。

二、張○○明知該消息尚未公開，仍於民國108年3月間購入該公司股票，獲利新臺幣伍佰萬元。

理由

被告張○○之行為已構成證券交易法第一百七十一條第一項第一款之內線交易罪。
"""


@pytest.mark.asyncio
class TestDocumentMetadataModel:
    """Test DocumentMetadata Pydantic model validation."""

    def test_valid_metadata_creation(self):
        """Test creating valid metadata."""
        metadata = DocumentMetadata(
            title="金融監督管理委員會裁罰書 - 玉山銀行洗錢防制違規",
            description="金管會對玉山銀行違反洗錢防制法處以罰鍰。",
            document_type="裁罰書",
            issuing_authority="金管會",
            case_number="金管銀法字第10900123456號",
            document_date="2020-09-15",
            related_institutions=["玉山商業銀行股份有限公司"],
            violation_types=["洗錢防制", "內部控制"],
            penalty_amount="NT$250,000,000",
            keywords=["洗錢防制", "玉山銀行", "裁罰", "客戶審查"],
            extraction_confidence=0.95,
        )

        assert metadata.title is not None
        assert metadata.document_type == "裁罰書"
        assert metadata.extraction_confidence == 0.95
        assert len(metadata.violation_types) == 2

    def test_metadata_with_missing_optional_fields(self):
        """Test metadata with None values for optional fields."""
        metadata = DocumentMetadata(
            title="Test Document",
            description="Test description",
            document_type="其他",
            issuing_authority=None,
            case_number=None,
            document_date=None,
            related_institutions=[],
            violation_types=[],
            penalty_amount=None,
            keywords=["test"],
            extraction_confidence=0.5,
        )

        assert metadata.issuing_authority is None
        assert metadata.case_number is None
        assert metadata.penalty_amount is None

    def test_invalid_confidence_score(self):
        """Test that invalid confidence scores are rejected."""
        with pytest.raises(ValueError):
            DocumentMetadata(
                title="Test",
                description="Test",
                document_type="其他",
                keywords=["test"],
                extraction_confidence=1.5,  # Invalid: > 1.0
            )


@pytest.mark.asyncio
class TestMetadataExtractionResult:
    """Test MetadataExtractionResult model."""

    def test_successful_extraction_result(self):
        """Test creating a successful extraction result."""
        metadata = DocumentMetadata(
            title="Test Document",
            description="Test description",
            document_type="裁罰書",
            keywords=["test"],
            extraction_confidence=0.9,
        )

        result = MetadataExtractionResult(
            doc_id="test_doc_123",
            metadata=metadata,
            success=True,
            error=None,
            processing_time=2.5,
            llm_tokens_used=1500,
            llm_cost_usd=0.0015,
        )

        assert result.success is True
        assert result.metadata is not None
        assert result.error is None
        assert result.processing_time == 2.5

    def test_failed_extraction_result(self):
        """Test creating a failed extraction result."""
        result = MetadataExtractionResult(
            doc_id="test_doc_456",
            metadata=None,
            success=False,
            error="Extraction failed: Invalid JSON response",
            processing_time=1.0,
            llm_tokens_used=None,
            llm_cost_usd=None,
        )

        assert result.success is False
        assert result.metadata is None
        assert result.error is not None


# Integration tests with actual LLM (requires API key)
@pytest.mark.integration
@pytest.mark.asyncio
class TestLLMMetadataExtractor:
    """Integration tests for LLM metadata extraction."""

    @pytest.fixture
    def sample_documents_dir(self):
        """Get path to sample documents."""
        return Path(__file__).parent.parent / "data" / "documents"

    async def test_extract_penalty_document_metadata(self):
        """Test extracting metadata from a penalty document."""
        from finagent.document_processing.metadata_extractor import MetadataExtractor

        extractor = MetadataExtractor(use_new_model=True)
        result = await extractor.extract_new(
            doc_id="test_penalty",
            filename="test_penalty.txt",
            content=SAMPLE_PENALTY_DOCUMENT,
        )

        assert result.success, f"Extraction failed: {result.error}"
        assert result.metadata is not None

        # Validate extracted metadata
        metadata = result.metadata
        assert "玉山" in metadata.title or "玉山銀行" in metadata.related_institutions[0]
        assert metadata.document_type == "裁罰書"
        assert metadata.issuing_authority in ["金管會", "銀行局"]
        assert metadata.extraction_confidence > 0.7
        assert "洗錢防制" in metadata.violation_types

    async def test_extract_court_judgment_metadata(self):
        """Test extracting metadata from a court judgment."""
        from finagent.document_processing.metadata_extractor import MetadataExtractor

        extractor = MetadataExtractor(use_new_model=True)
        result = await extractor.extract_new(
            doc_id="test_judgment",
            filename="test_judgment.txt",
            content=SAMPLE_COURT_JUDGMENT,
        )

        assert result.success, f"Extraction failed: {result.error}"
        assert result.metadata is not None

        metadata = result.metadata
        assert metadata.document_type in ["判決書", "其他"]
        assert "法院" in metadata.issuing_authority or metadata.issuing_authority == "法院"
        assert "國泰世華" in str(metadata.related_institutions) or "國泰" in str(
            metadata.related_institutions
        )

    async def test_batch_extraction(self):
        """Test batch extraction of multiple documents."""
        from finagent.document_processing.metadata_extractor import MetadataExtractor

        extractor = MetadataExtractor(use_new_model=True)
        documents = [
            ("doc_1", "penalty.txt", SAMPLE_PENALTY_DOCUMENT),
            ("doc_2", "judgment.txt", SAMPLE_COURT_JUDGMENT),
        ]

        results = extractor.extract_batch(documents)

        assert len(results) == 2
        assert all(isinstance(r, MetadataExtractionResult) for r in results)

        # At least one should succeed
        successful = sum(1 for r in results if r.success)
        assert successful > 0


@pytest.mark.unit
class TestExistingMetadataExtractor:
    """Tests for the existing MetadataExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create MetadataExtractor instance."""
        try:
            from finagent.document_processing.metadata_extractor import MetadataExtractor
            return MetadataExtractor()
        except Exception as e:
            pytest.skip(f"MetadataExtractor not available: {e}")

    async def test_fallback_extraction(self, extractor):
        """Test fallback extraction from filename."""
        result = extractor._fallback_extract(
            filename="玉山銀行_洗錢防制_2020.txt",
            content=SAMPLE_PENALTY_DOCUMENT,
            file_path="./data/documents/玉山銀行_洗錢防制_2020.txt",
        )

        assert result.entity == "玉山銀行"
        assert result.penalty_type == "洗錢防制"
        assert result.year_ad == 2020
        assert result.year_roc == 109


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-m", "not integration"])
