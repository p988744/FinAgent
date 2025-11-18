"""
Backfill full_content field for existing documents.

This script reads the original files and stores full content in the database
for wiki display purposes.

Usage:
    uv run python scripts/backfill_full_content.py
    uv run python scripts/backfill_full_content.py --dry-run  # Preview without writing
"""

import argparse
import logging
from pathlib import Path

from finagent.database.document_db import DocumentDatabase

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Backfill full_content for existing documents."""
    parser = argparse.ArgumentParser(
        description="Backfill full_content field from original files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview documents without writing to database",
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Starting Full Content Backfill")
    logger.info("=" * 80)

    # Initialize database
    db = DocumentDatabase()

    # Get all documents
    logger.info("Fetching documents from database...")
    documents = db.list_documents()
    logger.info(f"Found {len(documents)} documents")

    # Filter documents that need backfill (full_content is NULL or empty)
    docs_to_backfill = [
        doc for doc in documents if not doc.get("full_content")
    ]

    if not docs_to_backfill:
        logger.info("✓ All documents already have full_content. Nothing to backfill.")
        return 0

    logger.info(f"Documents needing backfill: {len(docs_to_backfill)}")

    # Preview mode
    if args.dry_run:
        logger.info("\n" + "=" * 80)
        logger.info("DRY RUN - Preview of documents to backfill:")
        logger.info("=" * 80)

        for idx, doc in enumerate(docs_to_backfill, 1):
            file_path = doc.get("file_path")
            filename = doc.get("filename")
            file_exists = Path(file_path).exists() if file_path else False

            logger.info(f"\n{idx}. {filename}")
            logger.info(f"   Path: {file_path}")
            logger.info(f"   Exists: {'✓' if file_exists else '✗'}")

        logger.info("\n" + "=" * 80)
        logger.info(f"Total: {len(docs_to_backfill)} documents to backfill")
        logger.info("=" * 80)
        logger.info("Run without --dry-run to write to database")
        return 0

    # Backfill full content
    logger.info("\n" + "=" * 80)
    logger.info("Backfilling full_content...")
    logger.info("=" * 80)

    success_count = 0
    error_count = 0
    missing_file_count = 0

    for idx, doc in enumerate(docs_to_backfill, 1):
        doc_id = doc["doc_id"]
        file_path = doc.get("file_path")
        filename = doc.get("filename")

        try:
            # Check if file exists
            if not file_path or not Path(file_path).exists():
                logger.warning(f"✗ [{idx}/{len(docs_to_backfill)}] File not found: {filename}")
                missing_file_count += 1
                continue

            # Read full content
            with open(file_path, "r", encoding="utf-8") as f:
                full_content = f.read()

            # Update database
            db.upsert_document(
                doc_id=doc_id,
                filename=filename,
                file_path=file_path,
                full_content=full_content,
            )

            content_size_kb = len(full_content) / 1024
            logger.info(f"✓ [{idx}/{len(docs_to_backfill)}] {filename} ({content_size_kb:.1f} KB)")
            success_count += 1

        except Exception as e:
            logger.error(f"✗ [{idx}/{len(docs_to_backfill)}] Failed: {filename} - {e}")
            error_count += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Backfill Complete")
    logger.info("=" * 80)
    logger.info(f"✓ Success: {success_count} documents")
    logger.info(f"⚠ Missing files: {missing_file_count} documents")
    logger.info(f"✗ Errors: {error_count} documents")

    # Verify
    logger.info("\nVerifying backfill...")
    all_docs = db.list_documents()
    with_content = sum(1 for doc in all_docs if doc.get("full_content"))
    logger.info(f"Documents with full_content: {with_content}/{len(all_docs)}")

    if with_content == len(all_docs):
        logger.info("\n✓ Backfill successful! All documents have full_content.")
        return 0
    else:
        logger.warning(f"\n⚠ {len(all_docs) - with_content} documents still missing full_content")
        return 1


if __name__ == "__main__":
    exit(main())
