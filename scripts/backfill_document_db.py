"""
Backfill script to populate SQLite with existing documents from Chroma.

This script:
1. Reads all documents from Chroma vector database
2. Extracts unique document IDs
3. Populates SQLite documents table with metadata
4. Marks documents as indexed with chunk counts

Usage:
    uv run python scripts/backfill_document_db.py
    uv run python scripts/backfill_document_db.py --dry-run  # Preview without writing
"""

import argparse
import logging
from collections import defaultdict
from pathlib import Path

import chromadb
from chromadb.config import Settings

from finagent.config import settings
from finagent.database.document_db import DocumentDatabase

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Backfill SQLite with documents from Chroma."""
    parser = argparse.ArgumentParser(description="Backfill document database from Chroma")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview documents without writing to database",
    )
    parser.add_argument(
        "--collection",
        default="legal_documents",
        help="Chroma collection name (default: legal_documents)",
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Starting Document Database Backfill")
    logger.info("=" * 80)

    # Initialize Chroma client
    persist_directory = settings.chroma_persist_directory
    logger.info(f"Connecting to Chroma: {persist_directory}")

    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        collection = client.get_collection(name=args.collection)
    except Exception as e:
        logger.error(f"Failed to get collection '{args.collection}': {e}")
        logger.error("Run 'uv run finagent init' to create the collection first")
        return 1

    # Get all documents from Chroma
    logger.info(f"Reading from collection: {args.collection}")
    total_chunks = collection.count()
    logger.info(f"Total chunks in Chroma: {total_chunks}")

    if total_chunks == 0:
        logger.warning("No chunks found in Chroma. Nothing to backfill.")
        return 0

    # Fetch all chunks (in batches if needed)
    logger.info("Fetching all chunks from Chroma...")
    all_chunks = collection.get(include=["metadatas"])

    if not all_chunks or not all_chunks["ids"]:
        logger.error("Failed to fetch chunks from Chroma")
        return 1

    # Group chunks by document
    logger.info("Grouping chunks by document...")
    doc_chunks = defaultdict(list)
    doc_metadata = {}

    for i, chunk_id in enumerate(all_chunks["ids"]):
        metadata = all_chunks["metadatas"][i]
        doc_id = metadata.get("doc_id")

        if not doc_id:
            logger.warning(f"Chunk {chunk_id} has no doc_id, skipping")
            continue

        doc_chunks[doc_id].append(chunk_id)

        # Store first occurrence of metadata for each document
        if doc_id not in doc_metadata:
            doc_metadata[doc_id] = metadata

    unique_docs = len(doc_chunks)
    logger.info(f"Found {unique_docs} unique documents")

    # Preview mode
    if args.dry_run:
        logger.info("\n" + "=" * 80)
        logger.info("DRY RUN - Preview of documents to backfill:")
        logger.info("=" * 80)

        for idx, (doc_id, chunks) in enumerate(sorted(doc_chunks.items()), 1):
            metadata = doc_metadata[doc_id]
            source = metadata.get("source", "Unknown")
            filename = Path(source).name if source else "Unknown"

            logger.info(f"\n{idx}. Document ID: {doc_id}")
            logger.info(f"   Filename: {filename}")
            logger.info(f"   Source: {source}")
            logger.info(f"   Chunks: {len(chunks)}")
            logger.info(f"   Metadata: {metadata}")

        logger.info("\n" + "=" * 80)
        logger.info(f"Total: {unique_docs} documents with {total_chunks} chunks")
        logger.info("=" * 80)
        logger.info("Run without --dry-run to write to database")
        return 0

    # Initialize database
    logger.info("Initializing SQLite database...")
    db = DocumentDatabase()

    # Backfill documents
    logger.info("\n" + "=" * 80)
    logger.info("Backfilling documents to SQLite...")
    logger.info("=" * 80)

    success_count = 0
    error_count = 0

    for idx, (doc_id, chunks) in enumerate(sorted(doc_chunks.items()), 1):
        try:
            metadata = doc_metadata[doc_id]
            source = metadata.get("source", "")
            filename = Path(source).name if source else f"document_{doc_id}.txt"

            # Read file for content preview and size
            content_preview = None
            file_size = None

            if source and Path(source).exists():
                try:
                    with open(source, "r", encoding="utf-8") as f:
                        content = f.read()
                        content_preview = content[:500] if content else None

                    file_size = Path(source).stat().st_size
                except Exception as e:
                    logger.warning(f"Failed to read file {source}: {e}")

            # Prepare metadata for SQLite
            # Remove Chroma-specific fields
            clean_metadata = {
                k: v
                for k, v in metadata.items()
                if k not in ["doc_id", "chunk_id", "start_char", "end_char"]
            }

            # Upsert document
            db.upsert_document(
                doc_id=doc_id,
                filename=filename,
                file_path=source,
                content_preview=content_preview,
                file_size=file_size,
                metadata=clean_metadata,
            )

            # Mark as indexed
            db.mark_as_indexed(doc_id, chunk_count=len(chunks))

            logger.info(f"✓ [{idx}/{unique_docs}] {filename} ({len(chunks)} chunks)")
            success_count += 1

        except Exception as e:
            logger.error(f"✗ [{idx}/{unique_docs}] Failed to backfill {doc_id}: {e}")
            error_count += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Backfill Complete")
    logger.info("=" * 80)
    logger.info(f"✓ Success: {success_count} documents")
    logger.info(f"✗ Errors: {error_count} documents")
    logger.info(f"Total chunks: {total_chunks}")

    # Verify database
    logger.info("\nVerifying SQLite database...")
    stats = db.get_statistics()
    logger.info(f"Documents in SQLite: {stats['total_documents']}")
    logger.info(f"Indexed documents: {stats['indexed_documents']}")
    logger.info(f"Total chunks: {stats['total_chunks']}")

    if stats["total_documents"] != unique_docs:
        logger.warning(
            f"Mismatch: Expected {unique_docs} documents, found {stats['total_documents']}"
        )
        return 1

    logger.info("\n✓ Backfill successful! All documents verified.")
    return 0


if __name__ == "__main__":
    exit(main())
