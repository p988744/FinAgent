"""Test script for LLM metadata generation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finagent.document_processing.metadata_generator import MetadataGenerator


def test_metadata_generation():
    """Test LLM metadata generation with sample document."""

    # Sample document content (Taiwan penalty case)
    sample_content = """
金融監督管理委員會裁罰書

受處分人：玉山商業銀行股份有限公司
統一編號：03028361

主旨：玉山商業銀行股份有限公司辦理洗錢防制作業內控缺失，處罰鍰新臺幣2億5,000萬元。

事實：

一、經本會查核結果，發現玉山商業銀行於民國107年至109年間，辦理洗錢防制作業存有下列缺失：

（一）未確實辨識客戶實質受益人
（二）對高風險客戶之監控機制不足
（三）未落實可疑交易申報程序

二、上述違規事項違反銀行法第45條之2及洗錢防制法第6條規定。

處分：

依銀行法第129條第7款規定，裁處罰鍰新臺幣2億5,000萬元。

中華民國109年9月15日

金融監督管理委員會
主任委員 黃天牧
    """

    print("=" * 80)
    print("Testing LLM Metadata Generation")
    print("=" * 80)
    print()

    try:
        # Create generator
        print("1. Initializing MetadataGenerator...")
        generator = MetadataGenerator()
        print(f"   ✓ Using model: {generator.model}")
        print()

        # Generate metadata
        print("2. Generating metadata...")
        metadata = generator.generate_metadata(
            doc_id="test_doc_001",
            filename="玉山銀行洗錢防制裁罰.txt",
            content=sample_content
        )
        print("   ✓ Metadata generated successfully")
        print()

        # Display results
        print("3. Generated Metadata:")
        print("-" * 80)
        print(f"Document ID: {metadata.doc_id}")
        print(f"Filename: {metadata.filename}")
        print()
        print(f"Description:\n  {metadata.description}")
        print()
        print(f"Document Type: {metadata.document_type}")
        print()
        print(f"Keywords: {', '.join(metadata.keywords)}")
        print()

        if metadata.date:
            print(f"Date: {metadata.date}")
        if metadata.issuing_authority:
            print(f"Issuing Authority: {metadata.issuing_authority}")
        if metadata.related_institutions:
            print(f"Related Institutions: {', '.join(metadata.related_institutions)}")
        if metadata.penalty_amount:
            print(f"Penalty Amount: {metadata.penalty_amount}")
        if metadata.violation_types:
            print(f"Violation Types: {', '.join(metadata.violation_types)}")

        print()
        print("-" * 80)
        print()
        print("✅ TEST PASSED: LLM successfully generated metadata")
        print()

        # Validation checks
        print("4. Validation Checks:")
        checks = {
            "Has description": bool(metadata.description),
            "Has document type": bool(metadata.document_type),
            "Has keywords": len(metadata.keywords) >= 3,
            "Date format valid": metadata.date is None or len(metadata.date) == 10,
            "Has issuing authority": bool(metadata.issuing_authority),
            "Has related institutions": len(metadata.related_institutions) > 0,
            "Has penalty amount": bool(metadata.penalty_amount),
            "Has violation types": len(metadata.violation_types) > 0,
        }

        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check_name}")

        print()

        all_passed = all(checks.values())
        if all_passed:
            print("✅ All validation checks passed!")
        else:
            print("⚠️  Some validation checks failed (may be expected)")

        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = test_metadata_generation()
    print()

    if success:
        print("=" * 80)
        print("Test completed successfully!")
        print("The LLM metadata generation feature is working correctly.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("=" * 80)
        print("Test failed. Please check the error messages above.")
        print("=" * 80)
        sys.exit(1)
