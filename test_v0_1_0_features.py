"""Test v0.1.0 features: Query History and Export."""

import sys
import time
from pathlib import Path

# Test imports
try:
    from finagent.utils.cost_calculator import (
        calculate_token_cost,
        calculate_total_cost,
        format_cost_usd,
        normalize_model_name,
    )
    from finagent.database.db import Database
    from finagent.cli.formatters.export import (
        export_to_markdown,
        export_to_json,
        export_to_text,
    )
    from finagent.models.answers import LegalAnswer
    from finagent.models.citations import LegalCitation, CitationType, CitationAuthority

    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def test_cost_calculator():
    """Test cost calculation utility."""
    print("\n" + "="*60)
    print("Testing Cost Calculator")
    print("="*60)

    # Test OpenAI model
    cost1 = calculate_token_cost(1000, 500, "gpt-4o-mini")
    print(f"✓ GPT-4o-mini (1000 input + 500 output): {format_cost_usd(cost1)}")
    assert cost1 > 0, "Cost should be > 0 for paid model"

    # Test local model (should be free)
    cost2 = calculate_token_cost(1000, 500, "ollama/gpt-oss:20b")
    print(f"✓ Local model (1000 input + 500 output): {format_cost_usd(cost2)}")
    assert cost2 == 0, "Cost should be 0 for local model"

    # Test total cost estimation
    cost3 = calculate_total_cost(1500, "gpt-4o-mini")
    print(f"✓ Total cost estimate (1500 tokens): {format_cost_usd(cost3)}")

    # Test model name normalization
    normalized = normalize_model_name("gpt-4o-2024-08-06")
    print(f"✓ Normalized 'gpt-4o-2024-08-06' -> '{normalized}'")
    assert normalized == "gpt-4o", "Should normalize to gpt-4o"

    print("✅ Cost calculator tests passed")


def test_database_history():
    """Test database history logging."""
    print("\n" + "="*60)
    print("Testing Database History")
    print("="*60)

    db = Database()

    # Add test history entry
    session_id = "test-session-123"
    history_entry = db.add_history(
        session_id=session_id,
        query="測試查詢：玉山銀行洗錢防制裁罰",
        response="這是測試回應內容...",
        model_used="gpt-4o-mini",
        tokens_used=1500,
        cost_usd=0.00045,
        processing_time_seconds=42.3,
        success=True,
        error_message=None,
        metadata={"test": True, "version": "v0.1.0"},
    )

    print(f"✓ Added history entry ID: {history_entry.id}")
    print(f"  Query: {history_entry.query[:30]}...")
    print(f"  Model: {history_entry.model_used}")
    print(f"  Cost: ${history_entry.cost_usd}")
    print(f"  Time: {history_entry.processing_time_seconds}s")

    # Retrieve history
    history_list = db.get_history(limit=5, session_id=session_id)
    print(f"✓ Retrieved {len(history_list)} history entries")
    assert len(history_list) >= 1, "Should have at least 1 entry"

    # Get stats
    stats = db.get_history_stats()
    print(f"✓ History stats:")
    print(f"  Total queries: {stats['total_queries']}")
    print(f"  Successful: {stats['successful_queries']}")
    if stats['avg_processing_time']:
        print(f"  Avg time: {stats['avg_processing_time']:.1f}s")

    print("✅ Database history tests passed")


def test_export_functionality():
    """Test export formatters."""
    print("\n" + "="*60)
    print("Testing Export Functionality")
    print("="*60)

    # Create mock answer for testing
    citation = LegalCitation(
        id=1,
        title="金管會裁罰書 - 玉山銀行洗錢防制",
        formatted_citation="金融監督管理委員會，金管銀法字第10912345678號裁罰書，受處分者：玉山商業銀行股份有限公司（民國109年9月15日）",
        type=CitationType.ENFORCEMENT_DOCUMENT,
        authority=CitationAuthority.PRIMARY,
        date="2020-09-15",
        url="https://example.com/document.pdf",
    )

    answer = LegalAnswer(
        executive_summary="玉山商業銀行於2020年因洗錢防制內部控制缺失，遭金管會依銀行法第61條之1規定，處以新臺幣2億5000萬元罰鍰 [引用1]。",
        key_findings=[
            "罰款金額：新台幣2.5億元罰鍰 [引用1]",
            "監管機構：金融監督管理委員會（金管會）",
            "違規類型：洗錢防制法相關規定 [引用1]",
        ],
        detailed_analysis="根據金管會裁罰書，玉山商業銀行因洗錢防制內部控制缺失，遭金管會依銀行法第61條之1規定，處以新臺幣2億5000萬元罰鍰。該銀行未能維持適當的洗錢防制控制機制，違反洗錢防制法相關規定。",
        final_answer="玉山銀行因洗錢防制缺失遭罰2.5億元",
        citations=[citation],
        confidence_score="高",
        confidence_explanation="基於官方裁罰書主要來源，所有關鍵事實已驗證",
        limitations=[],
    )

    query = "玉山銀行洗錢防制裁罰"

    # Test Markdown export
    md_file = export_to_markdown(answer, query, filename="test_export.md")
    print(f"✓ Markdown export: {md_file}")
    assert md_file.exists(), "Markdown file should exist"
    md_content = md_file.read_text(encoding="utf-8")
    assert "玉山銀行" in md_content, "Should contain query text"
    assert "引用" in md_content, "Should contain citations"
    print(f"  File size: {len(md_content)} bytes")

    # Test JSON export
    json_file = export_to_json(answer, query, filename="test_export.json")
    print(f"✓ JSON export: {json_file}")
    assert json_file.exists(), "JSON file should exist"
    json_content = json_file.read_text()
    assert '"query"' in json_content, "Should be valid JSON"
    print(f"  File size: {len(json_content)} bytes")

    # Test Text export
    txt_file = export_to_text(answer, query, filename="test_export.txt")
    print(f"✓ Text export: {txt_file}")
    assert txt_file.exists(), "Text file should exist"
    txt_content = txt_file.read_text()
    assert "FinAgent" in txt_content, "Should contain header"
    print(f"  File size: {len(txt_content)} bytes")

    # Cleanup test files
    md_file.unlink()
    json_file.unlink()
    txt_file.unlink()
    print("✓ Test files cleaned up")

    print("✅ Export functionality tests passed")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("v0.1.0 Feature Tests")
    print("="*60)
    print("Testing:")
    print("  - Cost Calculator")
    print("  - Database History")
    print("  - Export Functionality")
    print()

    start_time = time.time()

    try:
        test_cost_calculator()
        test_database_history()
        test_export_functionality()

        elapsed = time.time() - start_time

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print(f"Completed in {elapsed:.2f} seconds")
        print()
        print("v0.1.0 features are working correctly!")
        print("Ready for manual CLI testing.")

        return 0

    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
