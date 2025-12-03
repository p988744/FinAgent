#!/usr/bin/env python3
"""Extract metadata for documents that only have vector indexing."""

import asyncio
import json
import logging
import sqlite3
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def extract_metadata_for_documents():
    """Extract metadata for all documents that lack metadata."""
    from finagent.document_processing.metadata_extractor import MetadataExtractor

    # Connect to database
    db_path = Path(__file__).parent.parent / "data" / "finagent.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get documents without metadata
    cursor.execute("""
        SELECT doc_id, filename, file_path, full_content
        FROM documents
        WHERE metadata_extracted = 0 OR metadata_extracted IS NULL
        ORDER BY created_at
    """)
    documents = cursor.fetchall()

    if not documents:
        print("✅ No documents need metadata extraction")
        conn.close()
        return

    print(f"\n📋 Found {len(documents)} documents without metadata")
    print("=" * 60)

    # Initialize metadata extractor with new model
    extractor = MetadataExtractor(use_new_model=True)

    extracted = 0
    errors = 0
    total_cost = 0.0
    total_tokens = 0

    for doc in documents:
        doc_id = doc["doc_id"]
        filename = doc["filename"]
        file_path = doc["file_path"]
        full_content = doc["full_content"]

        print(f"\n📄 Processing: {filename}")
        print(f"   Doc ID: {doc_id}")

        try:
            # If full_content is not populated, read from file
            if not full_content:
                full_path = Path(__file__).parent.parent / file_path
                if not full_path.exists():
                    print(f"   ⚠️  File not found: {file_path}")
                    errors += 1
                    continue

                with open(full_path, 'r', encoding='utf-8') as f:
                    full_content = f.read()

                # Update full_content in database
                cursor.execute(
                    "UPDATE documents SET full_content = ? WHERE doc_id = ?",
                    (full_content, doc_id)
                )

            # Extract metadata using LLM
            result = await extractor.extract_new(
                doc_id=doc_id,
                filename=filename,
                content=full_content
            )

            if not result.success or not result.metadata:
                print(f"   ❌ Extraction failed: {result.error}")
                errors += 1

                # Update error status
                cursor.execute("""
                    UPDATE documents
                    SET
                        metadata_extraction_status = 'failed',
                        metadata_extraction_error = ?,
                        metadata_extraction_attempts = metadata_extraction_attempts + 1
                    WHERE doc_id = ?
                """, (result.error, doc_id))
                continue

            metadata = result.metadata

            # Update document in database
            cursor.execute("""
                UPDATE documents
                SET
                    title = ?,
                    description = ?,
                    document_type = ?,
                    issuing_authority = ?,
                    case_number = ?,
                    document_date = ?,
                    related_institutions = ?,
                    violation_types = ?,
                    penalty_amount = ?,
                    keywords = ?,
                    extraction_confidence = ?,
                    extraction_method = ?,
                    metadata_extracted = 1,
                    metadata_extraction_status = 'completed',
                    metadata_last_extracted_at = CURRENT_TIMESTAMP,
                    metadata_extraction_attempts = metadata_extraction_attempts + 1,
                    pipeline_stage = 'complete',
                    pipeline_status = 'success',
                    pipeline_completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (
                metadata.title,
                metadata.description,
                metadata.document_type,
                metadata.issuing_authority,
                metadata.case_number,
                metadata.document_date,
                json.dumps(metadata.related_institutions, ensure_ascii=False),
                json.dumps(metadata.violation_types, ensure_ascii=False),
                metadata.penalty_amount,
                json.dumps(metadata.keywords, ensure_ascii=False),
                metadata.extraction_confidence,
                metadata.extraction_method,
                doc_id
            ))

            extracted += 1
            total_cost += result.llm_cost_usd or 0.0
            total_tokens += result.llm_tokens_used or 0

            print(f"   ✅ Extracted metadata:")
            print(f"      Type: {metadata.document_type}")
            print(f"      Authority: {metadata.issuing_authority}")
            print(f"      Institutions: {len(metadata.related_institutions)}")
            print(f"      Violations: {len(metadata.violation_types)}")
            print(f"      Confidence: {metadata.extraction_confidence:.2f}")
            print(f"      Tokens: {result.llm_tokens_used}")
            print(f"      Cost: ${result.llm_cost_usd:.4f}")
            print(f"      Time: {result.processing_time:.2f}s")

        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            logger.exception(f"Error processing {doc_id}")
            errors += 1

            # Update error status
            cursor.execute("""
                UPDATE documents
                SET
                    metadata_extraction_status = 'failed',
                    metadata_extraction_error = ?,
                    metadata_extraction_attempts = metadata_extraction_attempts + 1
                WHERE doc_id = ?
            """, (str(e), doc_id))

    # Commit all changes
    conn.commit()
    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Metadata Extraction Summary")
    print("=" * 60)
    print(f"✅ Successfully extracted: {extracted}")
    print(f"❌ Failed: {errors}")
    print(f"📄 Total documents: {len(documents)}")
    print(f"💰 Total cost: ${total_cost:.4f}")
    print(f"🔢 Total tokens: {total_tokens:,}")
    if extracted > 0:
        print(f"📈 Average cost per document: ${total_cost/extracted:.4f}")
        print(f"📊 Average tokens per document: {total_tokens//extracted:,}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(extract_metadata_for_documents())
