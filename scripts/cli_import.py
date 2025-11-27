#!/usr/bin/env python3
"""
CLI Document Import Tool - Import and index documents into the knowledge base.

This tool allows users to import documents from various sources and index them
for use with the research and retrieval tools.

Usage:
    python scripts/cli_import.py /path/to/documents       # Import from directory
    python scripts/cli_import.py /path/to/file.txt        # Import single file
    python scripts/cli_import.py --clear                  # Clear all documents
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing.loader import DocumentLoader
from finagent.document_processing.chunker import ChineseTextChunker
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.retriever import DocumentRetriever


def print_header():
    """Print CLI header."""
    print()
    print("=" * 80)
    print("  FinAgent Document Import CLI")
    print("  Load and Index Documents into Knowledge Base")
    print("=" * 80)
    print()


def print_progress(message: str, current: int = None, total: int = None):
    """Print progress message."""
    if current is not None and total is not None:
        percentage = (current / total) * 100 if total > 0 else 0
        print(f"  [{current}/{total}] ({percentage:.0f}%) {message}")
    else:
        print(f"  {message}")


async def clear_documents(collection_name: str = "legal_documents", skip_confirm: bool = False):
    """
    Clear all documents from the knowledge base.

    Args:
        collection_name: Name of the collection to clear
        skip_confirm: Skip confirmation prompt
    """
    if not skip_confirm:
        print("⚠️  WARNING: This will delete ALL documents from the knowledge base!")
        confirm = input("Type 'yes' to confirm: ").strip().lower()

        if confirm != 'yes':
            print("❌ Cancelled")
            return False
    else:
        print("⚠️  Clearing ALL documents from the knowledge base...")

    print()
    print("Clearing knowledge base...")

    try:
        retriever = DocumentRetriever(collection_name=collection_name)

        if retriever.collection_exists():
            # Delete collection
            retriever.client.delete_collection(name=collection_name)
            print("✅ All documents cleared")
            return True
        else:
            print("⚠️  Collection does not exist (nothing to clear)")
            return True

    except Exception as e:
        print(f"❌ Error clearing documents: {e}")
        return False


async def import_documents(
    source_path: str,
    collection_name: str = "legal_documents",
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    verbose: bool = False
):
    """
    Import and index documents from a file or directory.

    Args:
        source_path: Path to file or directory
        collection_name: Name of the collection to store documents
        chunk_size: Size of text chunks in tokens
        chunk_overlap: Overlap between chunks in tokens
        verbose: Show detailed progress
    """
    source = Path(source_path)

    if not source.exists():
        print(f"❌ Error: Path does not exist: {source_path}")
        return False

    print(f"Source: {source_path}")
    print(f"Collection: {collection_name}")
    print()

    # Step 1: Load documents
    print("📂 Step 1/2: Loading documents...")

    try:
        # Use the parent directory of source as base_path, or None for absolute paths
        if source.is_absolute():
            # For absolute paths, don't use base_path
            loader = DocumentLoader(base_path=None)
        else:
            # For relative paths, use current directory
            loader = DocumentLoader(base_path=".")

        if source.is_file():
            # Load single file
            if verbose:
                print(f"  Loading file: {source.name}")
            # Use absolute path
            documents = [loader.load_txt(str(source.absolute()))]
            print(f"  ✅ Loaded 1 document")

        elif source.is_dir():
            # Load from directory
            txt_files = list(source.rglob("*.txt"))

            if not txt_files:
                print(f"  ⚠️  No .txt files found in {source_path}")
                return False

            print(f"  Found {len(txt_files)} .txt files")

            documents = []
            for i, file_path in enumerate(txt_files, 1):
                if verbose:
                    print(f"  [{i}/{len(txt_files)}] Loading: {file_path.name}")
                try:
                    # Use absolute path
                    doc = loader.load_txt(str(file_path.absolute()))
                    documents.append(doc)
                except Exception as e:
                    print(f"  ⚠️  Error loading {file_path.name}: {e}")

            print(f"  ✅ Loaded {len(documents)} documents")
        else:
            print(f"❌ Error: Invalid path type")
            return False

    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        return False

    if not documents:
        print("❌ No documents loaded")
        return False

    print()

    # Step 2: Index documents (chunking is handled internally by DocumentIndexer)
    print(f"🔍 Step 2/2: Indexing documents into vector database...")

    try:
        indexer = DocumentIndexer(collection_name=collection_name)

        # Index documents using async index_documents method
        if verbose:
            print(f"  Indexing {len(documents)} documents...")

        total_chunks = await indexer.index_documents(documents)

        print(f"  ✅ Indexed {len(documents)} documents ({total_chunks} chunks)")

    except Exception as e:
        print(f"❌ Error indexing documents: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 80)
    print("✅ Import completed successfully!")
    print()
    print(f"  Documents loaded:  {len(documents)}")
    print(f"  Chunks indexed:    {total_chunks}")
    print(f"  Collection:        {collection_name}")
    print()
    print("You can now use the research and retrieval tools:")
    print(f"  python scripts/cli_research.py \"your research question\"")
    print(f"  python scripts/cli_retrieval.py \"your search query\"")
    print("=" * 80)
    print()

    return True


async def show_status(collection_name: str = "legal_documents"):
    """
    Show current status of the knowledge base.

    Args:
        collection_name: Name of the collection to check
    """
    print("📊 Knowledge Base Status")
    print("─" * 80)
    print()

    try:
        retriever = DocumentRetriever(collection_name=collection_name)

        if not retriever.collection_exists():
            print("  Status: Empty (no documents indexed)")
            print()
            print("  To import documents:")
            print(f"    python scripts/cli_import.py /path/to/documents")
            return

        # Get collection info
        collection = retriever.collection
        count = collection.count()

        print(f"  Collection: {collection_name}")
        print(f"  Chunks indexed: {count}")
        print()

        if count > 0:
            # Sample a few documents to show metadata
            results = collection.get(limit=5)

            if results and 'metadatas' in results:
                unique_docs = set()
                for metadata in results['metadatas']:
                    if metadata and 'filename' in metadata:
                        unique_docs.add(metadata['filename'])

                print(f"  Sample documents:")
                for doc in sorted(unique_docs)[:5]:
                    print(f"    • {doc}")

                if len(unique_docs) > 5:
                    print(f"    ... and {len(unique_docs) - 5} more")

        print()
        print("  You can:")
        print(f"    - Query: python scripts/cli_research.py \"your question\"")
        print(f"    - Search: python scripts/cli_retrieval.py \"your query\"")
        print(f"    - Clear: python scripts/cli_import.py --clear")

    except Exception as e:
        print(f"❌ Error checking status: {e}")


async def main():
    """Main entry point."""
    print_header()

    if len(sys.argv) < 2:
        # No arguments - show status
        await show_status()
        return

    # Parse arguments
    args = sys.argv[1:]

    # Check for flags
    if "--help" in args or "-h" in args:
        print("Usage:")
        print("  python scripts/cli_import.py <path>          # Import documents")
        print("  python scripts/cli_import.py --clear         # Clear all documents")
        print("  python scripts/cli_import.py --status        # Show status")
        print()
        print("Options:")
        print("  --clear, -c        Clear all documents from knowledge base")
        print("  --status, -s       Show knowledge base status")
        print("  --verbose, -v      Show detailed progress")
        print("  --chunk-size N     Chunk size in tokens (default: 512)")
        print("  --chunk-overlap N  Chunk overlap in tokens (default: 128)")
        print("  --collection NAME  Collection name (default: legal_documents)")
        print("  --help, -h         Show this help")
        print()
        print("Examples:")
        print("  python scripts/cli_import.py data/documents/")
        print("  python scripts/cli_import.py /path/to/file.txt")
        print("  python scripts/cli_import.py data/documents/ --verbose")
        print("  python scripts/cli_import.py --clear")
        print()
        return

    if "--clear" in args or "-c" in args:
        skip_confirm = "--yes" in args or "-y" in args
        await clear_documents(skip_confirm=skip_confirm)
        return

    if "--status" in args or "-s" in args:
        await show_status()
        return

    # Extract options
    verbose = "--verbose" in args or "-v" in args
    chunk_size = 512
    chunk_overlap = 128
    collection_name = "legal_documents"

    # Parse custom options
    i = 0
    source_path = None
    while i < len(args):
        arg = args[i]

        if arg == "--chunk-size":
            if i + 1 < len(args):
                chunk_size = int(args[i + 1])
                i += 2
            else:
                print("Error: --chunk-size requires a value")
                return
        elif arg == "--chunk-overlap":
            if i + 1 < len(args):
                chunk_overlap = int(args[i + 1])
                i += 2
            else:
                print("Error: --chunk-overlap requires a value")
                return
        elif arg == "--collection":
            if i + 1 < len(args):
                collection_name = args[i + 1]
                i += 2
            else:
                print("Error: --collection requires a value")
                return
        elif arg in ["--verbose", "-v"]:
            i += 1
        else:
            # This is the source path
            source_path = arg
            i += 1

    if not source_path:
        print("Error: No source path provided")
        print("Usage: python scripts/cli_import.py <path>")
        print("Run with --help for more options")
        return

    # Import documents
    success = await import_documents(
        source_path=source_path,
        collection_name=collection_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        verbose=verbose
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
