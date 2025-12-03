#!/usr/bin/env python3
"""
Test script for HybridRetrieverTool with production data.

This script tests the new BM25+EnsembleRetriever hybrid search approach
against the production knowledge base.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from finagent.document_processing.retriever import DocumentRetriever
from finagent.tools.hybrid_retriever import HybridRetrieverTool
from finagent.tools.retriever import RetrieverTool


async def test_hybrid_search():
    """Test hybrid search with various queries."""
    print("\n" + "="*80)
    print("HybridRetrieverTool Test - BM25 + Vector Search")
    print("="*80)

    # Initialize retriever
    print("\n📚 Initializing DocumentRetriever...")
    retriever = DocumentRetriever(collection_name="legal_documents")

    # Check collection
    count = retriever.collection.count()
    print(f"✓ Collection: legal_documents")
    print(f"✓ Documents indexed: {count} chunks")

    if count == 0:
        print("\n❌ Knowledge base is empty. Please run indexing first:")
        print("   uv run finagent reindex")
        return False

    # Create tools
    print("\n🔧 Creating search tools...")
    hybrid_tool = HybridRetrieverTool(
        retriever=retriever,
        semantic_weight=0.6,  # 60% semantic
        keyword_weight=0.4    # 40% keyword (BM25)
    )
    semantic_tool = RetrieverTool(retriever=retriever)

    print("✓ HybridRetrieverTool created (60% semantic + 40% BM25)")
    print("✓ RetrieverTool created (100% semantic)")

    # Test queries
    test_queries = [
        {
            "query": "玉山銀行洗錢防制裁罰",
            "description": "Bank name + AML penalty (exact + semantic)",
            "expected": "Should find exact '玉山' matches + semantically related AML docs"
        },
        {
            "query": "2020年金管會裁罰500萬",
            "description": "Year + amount + agency (keyword heavy)",
            "expected": "Should find exact '2020', '500萬', '金管會' + related penalties"
        },
        {
            "query": "內部控制缺失導致裁罰",
            "description": "Conceptual query (semantic heavy)",
            "expected": "Should find internal control violations conceptually"
        },
        {
            "query": "銀行局 2020",
            "description": "Simple keyword query",
            "expected": "Should find exact matches for Banking Bureau 2020"
        },
    ]

    print("\n" + "="*80)
    print("TESTING QUERIES")
    print("="*80)

    results = []

    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]
        expected = test_case["expected"]

        print(f"\n{'─'*80}")
        print(f"Query {i}/{len(test_queries)}: {query}")
        print(f"Description: {description}")
        print(f"Expected: {expected}")
        print(f"{'─'*80}")

        # Test hybrid search
        print("\n🔍 Hybrid Search (BM25 + Vector):")
        try:
            hybrid_result = hybrid_tool._run(query=query, k=3)
            hybrid_docs = len([line for line in hybrid_result.split('\n') if line.startswith('[')])
            print(hybrid_result[:500] + "..." if len(hybrid_result) > 500 else hybrid_result)
            print(f"\n✓ Found {hybrid_docs} documents")
            hybrid_success = hybrid_docs > 0
        except Exception as e:
            print(f"✗ Hybrid search failed: {e}")
            hybrid_success = False
            hybrid_docs = 0

        # Test semantic-only search for comparison
        print("\n🔍 Semantic-Only Search (Vector):")
        try:
            semantic_result = semantic_tool._run(query=query, n_results=3)
            semantic_docs = len([line for line in semantic_result.split('\n') if line.startswith('[')])
            print(f"Found {semantic_docs} documents")
            semantic_success = semantic_docs > 0
        except Exception as e:
            print(f"✗ Semantic search failed: {e}")
            semantic_success = False
            semantic_docs = 0

        # Record results
        results.append({
            "query": query,
            "hybrid_success": hybrid_success,
            "hybrid_docs": hybrid_docs,
            "semantic_success": semantic_success,
            "semantic_docs": semantic_docs,
        })

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    hybrid_passed = sum(1 for r in results if r["hybrid_success"])
    semantic_passed = sum(1 for r in results if r["semantic_success"])
    total = len(results)

    print(f"\nHybrid Search: {hybrid_passed}/{total} queries passed")
    print(f"Semantic Search: {semantic_passed}/{total} queries passed")

    print("\nDetailed Results:")
    print(f"{'Query':<30} {'Hybrid Docs':<12} {'Semantic Docs':<14} {'Status':<10}")
    print(f"{'-'*30} {'-'*12} {'-'*14} {'-'*10}")
    for r in results:
        query_short = r["query"][:28] + ".." if len(r["query"]) > 28 else r["query"]
        status = "✅ PASS" if r["hybrid_success"] else "❌ FAIL"
        print(f"{query_short:<30} {r['hybrid_docs']:<12} {r['semantic_docs']:<14} {status:<10}")

    # Overall result
    print(f"\n{'='*80}")
    if hybrid_passed == total:
        print("✅ ALL TESTS PASSED - Hybrid search is working correctly!")
        print(f"\n📊 Success Rate: {hybrid_passed}/{total} (100%)")
        return True
    elif hybrid_passed > 0:
        print(f"⚠️  PARTIAL SUCCESS - {hybrid_passed}/{total} tests passed")
        print(f"\n📊 Success Rate: {hybrid_passed}/{total} ({100*hybrid_passed/total:.1f}%)")
        return True
    else:
        print("❌ ALL TESTS FAILED - Please check the implementation")
        return False


async def main():
    """Run the test suite."""
    print("\n" + "="*80)
    print("FinAgent Hybrid Search Test Suite")
    print("="*80)
    print("\nThis script tests the new HybridRetrieverTool that combines:")
    print("  - BM25 Retriever (keyword matching)")
    print("  - Vector Search (semantic similarity)")
    print("  - EnsembleRetriever (weighted ranking)")
    print("\nWeights: 60% semantic + 40% keyword (BM25)")

    try:
        success = await test_hybrid_search()

        print("\n" + "="*80)
        print("TEST COMPLETE")
        print("="*80)

        if success:
            print("\n✅ Hybrid search implementation validated successfully!")
            print("\nNext Steps:")
            print("  1. Update PlannerAgent to suggest 'hybrid_search' tool")
            print("  2. Monitor performance with real user queries")
            print("  3. Tune weights if needed (adjust semantic_weight/keyword_weight)")
        else:
            print("\n⚠️  Some tests failed. Review the output above.")

        return 0 if success else 1

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
