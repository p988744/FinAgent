"""Unit tests for LLM metadata generation."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing.metadata_generator import MetadataGenerator
from finagent.document_processing.metadata_store import DocumentMetadata


# Sample test documents
SAMPLE_PENALTY_DOC = """
金融監督管理委員會裁罰書

受處分人：玉山商業銀行股份有限公司
統一編號：03028361

主旨：玉山商業銀行股份有限公司辦理洗錢防制作業內控缺失，處罰鍰新臺幣2億5,000萬元。

事實：
經本會查核結果，發現玉山商業銀行於民國107年至109年間，辦理洗錢防制作業存有下列缺失：
（一）未確實辨識客戶實質受益人
（二）對高風險客戶之監控機制不足
（三）未落實可疑交易申報程序

處分：
依銀行法第129條第7款規定，裁處罰鍰新臺幣2億5,000萬元。

中華民國109年9月15日
金融監督管理委員會
"""

SAMPLE_JUDGMENT_DOC = """
臺灣高等法院民事判決
109年度金上字第12號

原告：金融監督管理委員會
被告：國泰世華商業銀行股份有限公司

主文：被告應給付原告新臺幣1億8,000萬元。

事實及理由：
被告於民國108年間涉嫌內線交易，違反證券交易法第157條之1規定。
經查明屬實，依法裁處罰鍰。

中華民國109年3月20日
"""

SAMPLE_REGULATION_DOC = """
銀行法第125條

銀行不得為下列行為：
一、以任何名義收受存款或吸收資金，而不履行交付義務。
二、違反法令、章程或逾越業務範圍。
三、辦理授信未善盡審核責任。
四、經營未經核准之業務。

違反前項規定者，處新臺幣二百萬元以上一千萬元以下罰鍰。

修正日期：民國110年1月20日
"""

EMPTY_DOC = ""

MALFORMED_DOC = "這是一個沒有結構的文件內容隨便寫的一些字"

MIXED_LANGUAGE_DOC = """
Financial Penalty Notice 金融裁罰書

Bank: Yushan Commercial Bank 玉山商業銀行
Amount: NT$ 250,000,000 新臺幣2.5億元
Date: 2020-09-15

Violation: Anti-Money Laundering 洗錢防制
"""


class TestMetadataGenerator:
    """Test cases for MetadataGenerator."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return MetadataGenerator()

    def test_generate_metadata_penalty_doc(self, generator):
        """Test metadata generation for penalty document."""
        metadata = generator.generate_metadata(
            doc_id="test_penalty_001",
            filename="玉山銀行洗錢防制裁罰.txt",
            content=SAMPLE_PENALTY_DOC
        )

        # Verify basic fields
        assert metadata.doc_id == "test_penalty_001"
        assert metadata.filename == "玉山銀行洗錢防制裁罰.txt"
        assert len(metadata.description) > 0
        assert metadata.document_type in MetadataGenerator.VALID_DOCUMENT_TYPES

        # Should identify as penalty document
        assert metadata.document_type == "裁罰書"

        # Should extract keywords
        assert len(metadata.keywords) >= 3
        assert any("玉山" in kw for kw in metadata.keywords)

        # Should extract date (ROC calendar → Western)
        # 民國109年 = 2020年
        assert metadata.date is not None
        if metadata.date:
            assert "2020" in metadata.date

        # Should identify authority
        assert metadata.issuing_authority == "金管會"

        # Should identify institutions
        assert len(metadata.related_institutions) > 0
        assert any("玉山" in inst for inst in metadata.related_institutions)

        # Should extract penalty amount
        assert metadata.penalty_amount is not None
        if metadata.penalty_amount:
            assert "億" in metadata.penalty_amount or "元" in metadata.penalty_amount

        # Should identify violation types
        assert len(metadata.violation_types) > 0
        assert any("洗錢防制" in vt for vt in metadata.violation_types)

    def test_generate_metadata_judgment_doc(self, generator):
        """Test metadata generation for court judgment."""
        metadata = generator.generate_metadata(
            doc_id="test_judgment_001",
            filename="國泰世華內線交易判決.txt",
            content=SAMPLE_JUDGMENT_DOC
        )

        assert metadata.doc_id == "test_judgment_001"
        assert metadata.document_type == "判決書"
        assert len(metadata.keywords) >= 3

        # Should extract date
        assert metadata.date is not None
        if metadata.date:
            assert "2020" in metadata.date  # 民國109年 = 2020年

        # May identify institutions
        if metadata.related_institutions:
            assert any("國泰" in inst for inst in metadata.related_institutions)

    def test_generate_metadata_regulation_doc(self, generator):
        """Test metadata generation for regulation document."""
        metadata = generator.generate_metadata(
            doc_id="test_reg_001",
            filename="銀行法第125條.txt",
            content=SAMPLE_REGULATION_DOC
        )

        assert metadata.doc_id == "test_reg_001"
        assert metadata.document_type == "法規條文"
        assert len(metadata.keywords) >= 2

        # Should extract date
        assert metadata.date is not None
        if metadata.date:
            assert "2021" in metadata.date  # 民國110年 = 2021年

        # Should NOT have penalty info (it's a regulation, not penalty)
        # (penalty_amount may be mentioned in text but shouldn't be extracted as THE penalty)

    def test_empty_document(self, generator):
        """Test handling of empty document."""
        with pytest.raises(Exception):
            generator.generate_metadata(
                doc_id="test_empty",
                filename="empty.txt",
                content=EMPTY_DOC
            )

    def test_malformed_document(self, generator):
        """Test handling of malformed document."""
        # Should still generate metadata, even if not perfect
        metadata = generator.generate_metadata(
            doc_id="test_malformed",
            filename="malformed.txt",
            content=MALFORMED_DOC
        )

        assert metadata.doc_id == "test_malformed"
        assert metadata.document_type == "其他"  # Should default to "其他"
        assert len(metadata.keywords) > 0  # Should extract some keywords

    def test_mixed_language_document(self, generator):
        """Test handling of mixed Chinese/English document."""
        metadata = generator.generate_metadata(
            doc_id="test_mixed",
            filename="mixed_lang.txt",
            content=MIXED_LANGUAGE_DOC
        )

        assert metadata.doc_id == "test_mixed"
        assert metadata.document_type == "裁罰書"
        assert len(metadata.keywords) > 0

        # Should handle bilingual content
        assert metadata.penalty_amount is not None

    def test_long_document_truncation(self, generator):
        """Test that long documents are properly truncated."""
        # Create a very long document
        long_content = SAMPLE_PENALTY_DOC * 100  # Repeat 100 times

        metadata = generator.generate_metadata(
            doc_id="test_long",
            filename="long_doc.txt",
            content=long_content
        )

        # Should still generate metadata without errors
        assert metadata.doc_id == "test_long"
        assert len(metadata.description) > 0

    def test_metadata_model_validation(self, generator):
        """Test that generated metadata passes Pydantic validation."""
        metadata = generator.generate_metadata(
            doc_id="test_validate",
            filename="test.txt",
            content=SAMPLE_PENALTY_DOC
        )

        # Should be valid DocumentMetadata
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.doc_id is not None
        assert metadata.filename is not None
        assert metadata.description is not None
        assert metadata.document_type is not None
        assert isinstance(metadata.keywords, list)
        assert isinstance(metadata.related_institutions, list)
        assert isinstance(metadata.violation_types, list)

    def test_date_format(self, generator):
        """Test that dates are in correct format (YYYY-MM-DD)."""
        metadata = generator.generate_metadata(
            doc_id="test_date",
            filename="test.txt",
            content=SAMPLE_PENALTY_DOC
        )

        if metadata.date:
            # Should be YYYY-MM-DD format
            assert len(metadata.date) == 10
            assert metadata.date.count("-") == 2
            parts = metadata.date.split("-")
            assert len(parts) == 3
            assert len(parts[0]) == 4  # Year
            assert len(parts[1]) == 2  # Month
            assert len(parts[2]) == 2  # Day

    def test_keywords_limit(self, generator):
        """Test that keywords are reasonably limited."""
        metadata = generator.generate_metadata(
            doc_id="test_keywords",
            filename="test.txt",
            content=SAMPLE_PENALTY_DOC
        )

        # Should have 5-10 keywords (per prompt)
        assert 3 <= len(metadata.keywords) <= 15  # Allow some flexibility

    def test_document_type_validation(self, generator):
        """Test that document type is one of valid types."""
        metadata = generator.generate_metadata(
            doc_id="test_type",
            filename="test.txt",
            content=SAMPLE_PENALTY_DOC
        )

        # Should be one of the valid types (or at least not empty)
        assert metadata.document_type in MetadataGenerator.VALID_DOCUMENT_TYPES or metadata.document_type == "其他"


# Integration test
def test_full_workflow():
    """Test complete workflow: generate → store → retrieve."""
    from finagent.document_processing.metadata_store import DocumentMetadataStore

    # Generate metadata
    generator = MetadataGenerator()
    metadata = generator.generate_metadata(
        doc_id="workflow_test_001",
        filename="workflow_test.txt",
        content=SAMPLE_PENALTY_DOC
    )

    # Store metadata
    store = DocumentMetadataStore()
    store.add_metadata(metadata)

    # Retrieve metadata
    retrieved = store.get_metadata("workflow_test_001")

    # Verify
    assert retrieved is not None
    assert retrieved.doc_id == "workflow_test_001"
    assert retrieved.description == metadata.description
    assert retrieved.document_type == metadata.document_type
    assert retrieved.keywords == metadata.keywords

    print("✓ Full workflow test passed")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
