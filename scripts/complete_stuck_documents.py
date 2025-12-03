#!/usr/bin/env python3
"""Complete processing for the 5 stuck documents - index and extract metadata."""

import asyncio
import json
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def complete_stuck_documents():
    """Index and extract metadata for the 5 stuck documents."""
    from finagent.document_processing.loader import DocumentLoader
    from finagent.document_processing.indexer import DocumentIndexer

    # Connect to database
    db_path = Path(__file__).parent.parent / "data" / "finagent.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find the 5 recently reprocessed documents
    cursor.execute("""
        SELECT doc_id, filename, file_path, full_content
        FROM documents
        WHERE pipeline_stage = 'parsed'
        AND pipeline_status = 'success'
        AND doc_id IN ('doc_8b2d8ae7', 'doc_720caadd', 'doc_6ef787df', 'doc_1b27c45d', 'doc_0768f6da')
        ORDER BY created_at
    """)
    documents = cursor.fetchall()

    if not documents:
        print("✅ No documents need processing")
        conn.close()
        return

    print(f"\n📋 Processing {len(documents)} documents")
    print("=" * 60)

    # Initialize components
    loader = DocumentLoader()
    indexer = DocumentIndexer(extract_metadata=True)

    processed = 0
    errors = 0

    for doc in documents:
        doc_id = doc["doc_id"]
        filename = doc["filename"]
        file_path = doc["file_path"]

        print(f"\n📄 {filename}")
        print(f"   Doc ID: {doc_id}")

        try:
            # Load document
            print(f"   [1/2] Loading document...")
            try:
                document = loader.load_txt(filename)
            except FileNotFoundError:
                print(f"   ❌ File not found: {filename}")
                raise ValueError(f"File not found: {filename}")
            except Exception as load_err:
                print(f"   ❌ Failed to load document: {load_err}")
                raise ValueError(f"Document loading failed: {load_err}")

            # Validate document
            if not document or not document.content or len(document.content.strip()) == 0:
                print(f"   ❌ Document has no content")
                raise ValueError("Document content is empty")

            print(f"   ✅ Loaded successfully ({len(document.content)} chars)")

            # Index document (this also extracts metadata)
            print(f"   [2/2] Indexing and extracting metadata...")
            try:
                num_chunks = await indexer.index_document(document)

                # Validate indexing result
                if num_chunks == 0:
                    print(f"   ❌ Indexing produced 0 chunks")
                    raise ValueError("Indexing failed - no chunks created")

                print(f"   ✅ Indexed {num_chunks} chunks")
            except Exception as index_err:
                print(f"   ❌ Indexing failed: {index_err}")
                raise ValueError(f"Indexing failed: {index_err}")

            # Update database - mark as complete
            cursor.execute("""
                UPDATE documents
                SET
                    indexed = 1,
                    chunk_count = ?,
                    pipeline_stage = 'complete',
                    pipeline_status = 'success',
                    pipeline_completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (num_chunks, doc_id))

            processed += 1
            print(f"   ✅ Marked as complete")

        except ValueError as e:
            # Expected validation errors
            print(f"   ❌ Validation error: {e}")
            errors += 1

            # Mark as failed with specific error
            cursor.execute("""
                UPDATE documents
                SET
                    pipeline_stage = 'parsed',
                    pipeline_status = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (doc_id,))

        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            logger.exception(f"Error processing {doc_id}")
            errors += 1

            # Mark as failed
            cursor.execute("""
                UPDATE documents
                SET
                    pipeline_stage = 'parsed',
                    pipeline_status = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (doc_id,))

    # Commit all changes
    conn.commit()
    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Processing Summary")
    print("=" * 60)
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {errors}")
    print(f"📄 Total documents: {len(documents)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(complete_stuck_documents())
