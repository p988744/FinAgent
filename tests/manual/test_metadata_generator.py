#!/usr/bin/env python3
"""Test MetadataGenerator with real document content."""

from finagent.document_processing.metadata_generator import MetadataGenerator

test_content = """金融監督管理委員會 裁罰書

受處分人：玉山商業銀行股份有限公司
地址：台北市松山區民生東路三段115號
統一編號：03782905

案由：
玉山商業銀行股份有限公司因洗錢防制及打擊資恐作業缺失，經本會審酌後，依銀行法第129條第7款規定，處新臺幣2億5千萬元罰鍰。

事實：
一、未能有效辨識客戶身分
二、未能妥適評估客戶風險
三、未能及時申報可疑交易

依據：銀行法第129條第7款

中華民國109年9月15日
"""

print("=" * 80)
print("Testing MetadataGenerator")
print("=" * 80)
print()

try:
    generator = MetadataGenerator()
    print("✅ MetadataGenerator initialized")
    print()

    print("Testing with sample document...")
    metadata = generator.generate_metadata(
        doc_id="test_doc_001",
        filename="玉山銀行_洗錢防制裁罰_2020.txt",
        content=test_content,
        max_content_length=4000
    )

    print("✅ Metadata generated successfully!")
    print()
    print("Results:")
    print(f"  Document Type: {metadata.document_type}")
    print(f"  Description: {metadata.description}")
    print(f"  Authority: {metadata.issuing_authority}")
    print(f"  Penalty: {metadata.penalty_amount}")
    print(f"  Violation Types: {metadata.violation_types}")
    print(f"  Related Institutions: {metadata.related_institutions}")
    print(f"  Keywords: {metadata.keywords}")
    print(f"  Date: {metadata.date}")
    print()

    print("=" * 80)
    print("✅ TEST PASSED")
    print("=" * 80)

except Exception as e:
    print(f"❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("=" * 80)
    print("❌ TEST FAILED")
    print("=" * 80)
