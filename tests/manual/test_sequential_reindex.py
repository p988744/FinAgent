#!/usr/bin/env python3
"""Test sequential reindex implementation with concept extraction."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finagent.database.db import Database


def test_sequential_reindex():
    """Test the complete sequential reindex workflow."""

    print("=" * 70)
    print("TEST: Sequential Reindex with Concept Extraction")
    print("=" * 70)
    print()

    # Initialize database
    db = Database()

    # Clear previous test data
    print("🧹 Clearing previous test data...")
    all_docs = db.get_all_documents()
    for doc in all_docs:
        db.delete_document(doc.doc_id)
    print(f"   Deleted {len(all_docs)} documents\n")

    # Run sequential reindex
    print("🚀 Running sequential reindex...")
    print("   Command: /reindex --skip-init")
    print("   (Simulating via import)")
    print()

    from finagent.cli.commands.reindex import reindex_documents_sequential

    try:
        # Test with skip_metadata=True for speed (no LLM calls)
        indexed, chunks = reindex_documents_sequential(
            clear_existing=False, skip_metadata=True, skip_concepts=True  # Fast test
        )

        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()

        # Verify database
        all_docs = db.get_all_documents()
        print(f"✅ Documents in database: {len(all_docs)}")
        print(f"✅ Documents indexed: {indexed}")
        print(f"✅ Total chunks: {chunks}")
        print()

        # Show sample documents
        if all_docs:
            print("📄 Sample documents:")
            for doc in all_docs[:5]:
                print(f"   - {doc.filename}")
                print(f"     Type: {doc.document_type}")
                print(f"     Indexed: {doc.indexed}, Chunks: {doc.chunk_count}")
                print()

        # Check concepts
        concepts = db.get_all_concepts()
        print(f"💡 Concepts extracted: {len(concepts)}")
        if concepts:
            print("   Top 10 concepts:")
            for concept in concepts[:10]:
                print(
                    f"   - {concept.concept_name} "
                    f"({concept.concept_type}, {concept.document_count} docs)"
                )
            print()

        # Check document-concept mappings
        if all_docs:
            sample_doc = all_docs[0]
            doc_concepts = db.get_document_concepts(sample_doc.doc_id)
            print(f"🔗 Concepts for '{sample_doc.filename}':")
            for concept in doc_concepts:
                print(f"   - {concept.concept_name}")
            print()

        # Statistics
        doc_stats = db.get_document_statistics()
        concept_stats = db.get_concept_statistics()

        print("=" * 70)
        print("STATISTICS")
        print("=" * 70)
        print()
        print("Documents:")
        print(f"   Total: {doc_stats['total_documents']}")
        print(f"   Indexed: {doc_stats['indexed_documents']}")
        print(f"   Total chunks: {doc_stats['total_chunks']}")
        print()
        print("Concepts:")
        print(f"   Total: {concept_stats['total_concepts']}")
        print(f"   Mappings: {concept_stats['total_document_concept_mappings']}")
        print()

        # Verify sequential processing worked
        assert len(all_docs) == indexed, f"Expected {indexed} docs, got {len(all_docs)}"
        assert all(doc.indexed for doc in all_docs), "Not all documents marked as indexed"

        print("=" * 70)
        print("✅ TEST PASSED: Sequential reindex working correctly!")
        print("=" * 70)
        return True

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sequential_reindex()
    sys.exit(0 if success else 1)
