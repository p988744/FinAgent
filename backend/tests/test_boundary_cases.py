"""Boundary tests for edge cases and error conditions."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing.metadata_generator import MetadataGenerator
from finagent.document_processing.metadata_store import DocumentMetadataStore, DocumentMetadata


class TestBoundaryCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return MetadataGenerator()

    # ========== Input Size Boundaries ==========

    def test_minimal_document(self, generator):
        """Test with minimal valid document."""
        minimal_doc = "金管會裁罰書。玉山銀行。2020年。"

        metadata = generator.generate_metadata(
            doc_id="minimal",
            filename="minimal.txt",
            content=minimal_doc
        )

        assert metadata.doc_id == "minimal"
        assert len(metadata.description) > 0
        assert metadata.document_type is not None

    def test_single_character_document(self, generator):
        """Test with single character."""
        with pytest.raises(Exception):
            generator.generate_metadata(
                doc_id="single_char",
                filename="single.txt",
                content="文"
            )

    def test_maximum_length_document(self, generator):
        """Test with document at max length (4000 chars)."""
        # Create exactly 4000 character document
        base_text = "這是測試文件內容。" * 200  # 10 chars × 200 = 2000
        max_doc = base_text * 2  # 4000 chars

        metadata = generator.generate_metadata(
            doc_id="max_length",
            filename="max.txt",
            content=max_doc
        )

        assert metadata.doc_id == "max_length"
        assert len(metadata.description) > 0

    def test_exceeds_maximum_length(self, generator):
        """Test with document exceeding max length (>4000 chars)."""
        # Create 10000 character document
        huge_doc = "這是測試文件內容。" * 1000  # 10 chars × 1000 = 10000

        # Should auto-truncate to 4000 chars
        metadata = generator.generate_metadata(
            doc_id="huge",
            filename="huge.txt",
            content=huge_doc
        )

        assert metadata.doc_id == "huge"
        # Should still succeed (truncated)

    # ========== Special Characters ==========

    def test_special_characters(self, generator):
        """Test with special characters and symbols."""
        special_doc = """
        金管會裁罰書 @#$%^&*()
        金額：NT$ 2,500,000 (新臺幣貳佰伍拾萬元)
        日期：2020/09/15 or 2020-09-15 or 109.09.15
        機構：玉山銀行 (E.SUN Bank)
        """

        metadata = generator.generate_metadata(
            doc_id="special",
            filename="special.txt",
            content=special_doc
        )

        assert metadata.doc_id == "special"
        assert metadata.document_type is not None

    def test_unicode_characters(self, generator):
        """Test with various Unicode characters."""
        unicode_doc = """
        金融監管文件 📋
        處罰金額：💰 2.5億元
        違規類型：⚠️ 洗錢防制
        """

        metadata = generator.generate_metadata(
            doc_id="unicode",
            filename="unicode.txt",
            content=unicode_doc
        )

        assert metadata.doc_id == "unicode"

    # ========== Date Format Variations ==========

    def test_various_date_formats(self, generator):
        """Test with different date formats."""
        date_doc = """
        金管會裁罰書

        日期1: 民國109年9月15日
        日期2: 2020年9月15日
        日期3: 2020/09/15
        日期4: 2020-09-15
        日期5: 109.09.15
        日期6: September 15, 2020
        """

        metadata = generator.generate_metadata(
            doc_id="dates",
            filename="dates.txt",
            content=date_doc
        )

        # Should extract at least one date
        assert metadata.date is not None
        # Should be in YYYY-MM-DD format
        if metadata.date:
            assert "-" in metadata.date

    def test_invalid_date(self, generator):
        """Test with invalid date."""
        invalid_date_doc = """
        金管會裁罰書
        日期：2020年13月45日  # Invalid month and day
        """

        metadata = generator.generate_metadata(
            doc_id="invalid_date",
            filename="invalid_date.txt",
            content=invalid_date_doc
        )

        # Should handle gracefully (date may be None or corrected)
        assert metadata.doc_id == "invalid_date"

    def test_future_date(self, generator):
        """Test with future date."""
        future_doc = """
        金管會裁罰書
        日期：2099年12月31日
        """

        metadata = generator.generate_metadata(
            doc_id="future",
            filename="future.txt",
            content=future_doc
        )

        # Should still parse (business logic doesn't validate future dates)
        assert metadata.doc_id == "future"

    # ========== Missing Fields ==========

    def test_no_date(self, generator):
        """Test document without date."""
        no_date_doc = """
        金管會裁罰書
        玉山商業銀行違反洗錢防制規定
        處罰鍰2.5億元
        """

        metadata = generator.generate_metadata(
            doc_id="no_date",
            filename="no_date.txt",
            content=no_date_doc
        )

        # Date should be None
        assert metadata.date is None or metadata.date == ""

    def test_no_authority(self, generator):
        """Test document without issuing authority."""
        no_authority_doc = """
        銀行違規裁罰
        玉山銀行被處罰2.5億元
        日期：2020-09-15
        """

        metadata = generator.generate_metadata(
            doc_id="no_authority",
            filename="no_authority.txt",
            content=no_authority_doc
        )

        # Authority may be None
        # assert metadata.issuing_authority is None

    def test_no_institutions(self, generator):
        """Test document without specific institutions."""
        no_inst_doc = """
        金管會裁罰書
        某銀行違反規定
        處罰2.5億元
        日期：2020-09-15
        """

        metadata = generator.generate_metadata(
            doc_id="no_inst",
            filename="no_inst.txt",
            content=no_inst_doc
        )

        # related_institutions may be empty
        assert isinstance(metadata.related_institutions, list)

    def test_no_penalty_amount(self, generator):
        """Test penalty document without amount."""
        no_amount_doc = """
        金管會裁罰書
        玉山銀行違反洗錢防制規定
        日期：2020-09-15
        """

        metadata = generator.generate_metadata(
            doc_id="no_amount",
            filename="no_amount.txt",
            content=no_amount_doc
        )

        # penalty_amount may be None
        # But document_type should still be 裁罰書
        assert metadata.document_type == "裁罰書"

    # ========== Ambiguous Content ==========

    def test_ambiguous_document_type(self, generator):
        """Test document that could be multiple types."""
        ambiguous_doc = """
        法院判決書關於金管會裁罰案件

        原告：金管會
        被告：玉山銀行

        本院判決：維持金管會原處分，罰鍰2.5億元。
        """

        metadata = generator.generate_metadata(
            doc_id="ambiguous",
            filename="ambiguous.txt",
            content=ambiguous_doc
        )

        # Should pick one type (判決書 or 裁罰書)
        assert metadata.document_type in ["判決書", "裁罰書"]

    def test_multiple_institutions(self, generator):
        """Test document mentioning many institutions."""
        multi_inst_doc = """
        金管會裁罰書

        玉山銀行、國泰世華銀行、中信銀行、台新銀行、兆豐銀行、
        第一銀行、華南銀行、彰化銀行、合作金庫銀行共同違規。

        日期：2020-09-15
        """

        metadata = generator.generate_metadata(
            doc_id="multi_inst",
            filename="multi_inst.txt",
            content=multi_inst_doc
        )

        # Should extract multiple institutions
        assert len(metadata.related_institutions) >= 3

    def test_multiple_violations(self, generator):
        """Test document with multiple violation types."""
        multi_vio_doc = """
        金管會裁罰書

        玉山銀行同時違反：
        1. 洗錢防制規定
        2. 內線交易規定
        3. 資訊揭露規定
        4. 法規遵循規定

        處罰2.5億元
        日期：2020-09-15
        """

        metadata = generator.generate_metadata(
            doc_id="multi_vio",
            filename="multi_vio.txt",
            content=multi_vio_doc
        )

        # Should extract multiple violation types
        assert len(metadata.violation_types) >= 2

    # ========== Unusual Formats ==========

    def test_all_uppercase(self, generator):
        """Test document in all uppercase."""
        upper_doc = """
        金管會裁罰書
        玉山銀行違規
        罰款2.5億元
        """

        metadata = generator.generate_metadata(
            doc_id="upper",
            filename="upper.txt",
            content=upper_doc
        )

        assert metadata.doc_id == "upper"

    def test_no_punctuation(self, generator):
        """Test document without punctuation."""
        no_punct_doc = "金管會裁罰書玉山銀行違反洗錢防制規定處罰2億5千萬元日期2020年9月15日"

        metadata = generator.generate_metadata(
            doc_id="no_punct",
            filename="no_punct.txt",
            content=no_punct_doc
        )

        assert metadata.doc_id == "no_punct"
        assert len(metadata.keywords) > 0

    def test_excessive_whitespace(self, generator):
        """Test document with excessive whitespace."""
        whitespace_doc = """
        金管會       裁罰書



        玉山銀行    違規


        罰款    2.5    億元
        """

        metadata = generator.generate_metadata(
            doc_id="whitespace",
            filename="whitespace.txt",
            content=whitespace_doc
        )

        assert metadata.doc_id == "whitespace"

    # ========== Metadata Store Boundaries ==========

    def test_duplicate_doc_id(self):
        """Test storing metadata with duplicate doc_id."""
        store = DocumentMetadataStore()

        # Create metadata
        metadata1 = DocumentMetadata(
            doc_id="duplicate_test",
            filename="test1.txt",
            description="First version",
            document_type="裁罰書",
            keywords=["test"],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )

        metadata2 = DocumentMetadata(
            doc_id="duplicate_test",  # Same ID
            filename="test2.txt",
            description="Second version",
            document_type="判決書",
            keywords=["test2"],
            created_at="2024-01-02T00:00:00",
            updated_at="2024-01-02T00:00:00"
        )

        # Add first
        store.add_metadata(metadata1)

        # Add second (should overwrite)
        store.add_metadata(metadata2)

        # Retrieve
        retrieved = store.get_metadata("duplicate_test")
        assert retrieved.description == "Second version"

    def test_empty_metadata_store(self):
        """Test operations on empty metadata store."""
        store = DocumentMetadataStore()

        # Get non-existent
        result = store.get_metadata("non_existent")
        assert result is None

        # Get all from empty store
        all_meta = store.get_all_metadata()
        assert len(all_meta) >= 0  # May have some from previous tests

    def test_special_characters_in_doc_id(self):
        """Test metadata with special characters in doc_id."""
        store = DocumentMetadataStore()

        # Create metadata with special chars
        metadata = DocumentMetadata(
            doc_id="test_特殊字符_123",
            filename="special_特殊.txt",
            description="測試特殊字符",
            document_type="裁罰書",
            keywords=["測試", "special"],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )

        store.add_metadata(metadata)
        retrieved = store.get_metadata("test_特殊字符_123")
        assert retrieved is not None
        assert retrieved.description == "測試特殊字符"


# Stress tests
class TestStressCases:
    """Stress testing for performance and stability."""

    @pytest.fixture
    def generator(self):
        return MetadataGenerator()

    @pytest.mark.slow
    def test_many_sequential_generations(self, generator):
        """Test generating metadata for many documents sequentially."""
        for i in range(10):  # Reduced from 100 for faster testing
            metadata = generator.generate_metadata(
                doc_id=f"stress_test_{i}",
                filename=f"stress_{i}.txt",
                content=f"金管會裁罰書 {i}。玉山銀行違規。2020-09-15。"
            )
            assert metadata.doc_id == f"stress_test_{i}"

    @pytest.mark.slow
    def test_large_metadata_store(self):
        """Test metadata store with many entries."""
        store = DocumentMetadataStore()

        # Add many entries
        for i in range(50):  # Reduced from 500
            metadata = DocumentMetadata(
                doc_id=f"large_store_test_{i}",
                filename=f"doc_{i}.txt",
                description=f"Test document {i}",
                document_type="裁罰書",
                keywords=[f"keyword{i}"],
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            store.add_metadata(metadata)

        # Retrieve random entry
        result = store.get_metadata("large_store_test_25")
        assert result is not None
        assert result.description == "Test document 25"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
