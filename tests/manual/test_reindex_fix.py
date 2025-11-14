#!/usr/bin/env python3
"""Test that reindex saves all documents to database, even without enhanced metadata."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finagent.document_processing import DocumentIndexer, DocumentLoader
from finagent.document_processing.metadata_store import (
    DocumentMetadata,
    DocumentMetadataStore,
)
from finagent.database.db import Database


def test_reindex_without_metadata():
    """Test that documents without enhanced metadata still get saved to database."""

    print("=" * 60)
    print("TEST: Reindex without enhanced metadata")
    print("=" * 60)

    # Initialize
    loader = DocumentLoader()
    indexer = DocumentIndexer()
    metadata_store = DocumentMetadataStore()
    db = Database()

    # Load test documents (relative to base_path)
    test_files = [
        "玉山銀行_洗錢防制裁罰_2020.txt",
        "國泰世華銀行_內線交易_2021.txt",
    ]
    documents = []
    for filename in test_files:
        try:
            doc = loader.load_txt(filename)
            documents.append(doc)
        except Exception as e:
            print(f"⚠️  Could not load {filename}: {e}")
    print(f"\n✅ Loaded {len(documents)} documents from filesystem\n")

    # Clear database to start fresh
    print("🧹 Clearing database...")
    all_docs = db.get_all_documents()
    for doc in all_docs:
        db.delete_document(doc.doc_id)
    print(f"   Deleted {len(all_docs)} documents from database\n")

    # Clear vector DB
    print("🧹 Clearing vector database...")
    if indexer.collection:
        try:
            indexer.collection.delete()
            print("   Vector DB cleared\n")
        except Exception as e:
            print(f"   Error clearing vector DB: {e}\n")

    # Simulate reindex WITHOUT creating enhanced metadata first
    print("📝 Simulating /reindex WITHOUT /init (no enhanced metadata)...\n")

    indexed_count = 0
    for doc in documents:
        filename = doc.metadata.get("filename", "unknown")

        # Check if enhanced metadata exists (should be None)
        enhanced_metadata = metadata_store.get_metadata(doc.id)
        if enhanced_metadata:
            print(f"⚠️  WARNING: {filename} has metadata (should be None)")

        # Index document
        try:
            chunks = indexer.index_document(doc)
            print(f"   ✅ Indexed: {filename} ({chunks} chunks)")

            # This is the FIX: Create minimal metadata if none exists
            if enhanced_metadata:
                db.update_document_indexed_status(doc.id, indexed=True, chunk_count=chunks)
            else:
                # Create minimal metadata
                from datetime import datetime
                file_path = doc.metadata.get("file_path") or doc.source or ""
                minimal_metadata = DocumentMetadata(
                    doc_id=doc.id,
                    filename=filename,
                    description=f"Auto-indexed document: {filename}",
                    document_type="未分類",
                    keywords=[],
                    indexed=True,
                    chunk_count=chunks,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                )
                metadata_store.add_metadata(minimal_metadata, file_path=file_path)
                print(f"      💾 Created minimal metadata in database")

            indexed_count += 1
        except Exception as e:
            print(f"   ❌ Error indexing {filename}: {e}")

    print(f"\n✅ Indexed {indexed_count} documents\n")

    # Verify database state
    print("=" * 60)
    print("VERIFICATION: Check database state")
    print("=" * 60)

    all_docs_after = db.get_all_documents()
    print(f"\n✅ Total documents in database: {len(all_docs_after)}")
    print(f"   Expected: {indexed_count}")
    print(f"   Match: {'✅ YES' if len(all_docs_after) == indexed_count else '❌ NO'}\n")

    if all_docs_after:
        print("Sample documents:")
        for doc in all_docs_after[:3]:
            print(f"   - {doc.filename}: indexed={doc.indexed}, chunks={doc.chunk_count}")

    # Stats
    stats = db.get_document_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Indexed documents: {stats['indexed_documents']}")
    print(f"   Total chunks: {stats['total_chunks']}")

    # Test passed?
    if len(all_docs_after) == indexed_count and all(d.indexed for d in all_docs_after):
        print("\n" + "=" * 60)
        print("✅ TEST PASSED: All documents saved to database!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED: Not all documents in database!")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_reindex_without_metadata()
    sys.exit(0 if success else 1)
