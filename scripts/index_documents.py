"""
Script to index documents into Chroma vector database.

Usage:
    python scripts/index_documents.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing import (
    DocumentLoader,
    DocumentIndexer,
)


def main():
    """Index all documents in the data/documents directory."""
    print("🚀 Starting document indexing...")

    # Get absolute paths
    base_dir = Path(__file__).parent.parent
    docs_path = base_dir / "data" / "documents"
    vector_db_path = base_dir / "data" / "vector_db"

    # Initialize loader and indexer
    loader = DocumentLoader(base_path=str(docs_path))
    indexer = DocumentIndexer(collection_name="legal_documents", persist_directory=str(vector_db_path))

    # Load all TXT files (recursively from subdirectories)
    print("\n📄 Loading documents...")
    documents = loader.load_directory(".", pattern="*.txt", recursive=True)

    print(f"   Found {len(documents)} documents:")
    for doc in documents:
        filename = doc.metadata.get("filename", "unknown")
        size = doc.metadata.get("file_size", 0)
        print(f"   - {filename} ({size} bytes)")

    # Index documents
    print("\n🔍 Indexing documents...")
    total_chunks = 0

    for doc in documents:
        filename = doc.metadata.get("filename", "unknown")
        print(f"\n   Processing: {filename}")

        # Check if already indexed
        if indexer.document_exists(doc.id):
            print(f"   ⚠️  Document already indexed, skipping...")
            continue

        # Index document
        chunks = indexer.index_document(doc)
        total_chunks += chunks
        print(f"   ✅ Indexed {chunks} chunks")

    # Show stats
    print("\n📊 Indexing complete!")
    stats = indexer.get_collection_stats()
    print(f"   Total chunks in collection: {stats['total_chunks']}")
    print(f"   Collection: {stats['collection_name']}")
    print(f"   Persist directory: {stats['persist_directory']}")

    print("\n✨ Done!")


if __name__ == "__main__":
    main()
