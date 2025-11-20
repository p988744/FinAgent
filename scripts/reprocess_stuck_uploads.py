#!/usr/bin/env python3
"""Reprocess documents stuck at 'uploaded' stage due to background task failures."""

import asyncio
import sqlite3
from pathlib import Path

async def reprocess_stuck_uploads():
    """Find and reprocess documents stuck at uploaded stage."""

    # Connect to database
    db_path = Path(__file__).parent.parent / "data" / "finagent.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find stuck documents
    cursor.execute("""
        SELECT doc_id, filename, file_path
        FROM documents
        WHERE pipeline_stage = 'uploaded'
        AND pipeline_status = 'in_progress'
        AND full_content IS NULL
        ORDER BY created_at
    """)
    stuck_docs = cursor.fetchall()

    if not stuck_docs:
        print("✅ No stuck documents found")
        conn.close()
        return

    print(f"\n📋 Found {len(stuck_docs)} stuck documents")
    print("=" * 60)

    processed = 0
    errors = 0

    for doc in stuck_docs:
        doc_id = doc["doc_id"]
        filename = doc["filename"]
        file_path = doc["file_path"]

        print(f"\n📄 Processing: {filename}")
        print(f"   Doc ID: {doc_id}")

        try:
            # Read file content
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                print(f"   ❌ File not found: {file_path}")
                # Mark as failed - file missing
                cursor.execute("""
                    UPDATE documents
                    SET
                        pipeline_stage = 'uploaded',
                        pipeline_status = 'failed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE doc_id = ?
                """, (doc_id,))
                errors += 1
                continue

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate content
            if not content or len(content.strip()) == 0:
                print(f"   ❌ File is empty or contains only whitespace")
                # Mark as failed - empty content
                cursor.execute("""
                    UPDATE documents
                    SET
                        pipeline_stage = 'uploaded',
                        pipeline_status = 'failed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE doc_id = ?
                """, (doc_id,))
                errors += 1
                continue

            print(f"   ✅ Read {len(content)} characters from file")

            # Update database with full content and mark as parsed
            cursor.execute("""
                UPDATE documents
                SET
                    full_content = ?,
                    pipeline_stage = 'parsed',
                    pipeline_status = 'success',
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (content, doc_id))

            processed += 1
            print(f"   ✅ Updated database - stage now 'parsed'")

        except UnicodeDecodeError as e:
            print(f"   ❌ File encoding error: {e}")
            # Mark as failed - encoding issue
            cursor.execute("""
                UPDATE documents
                SET
                    pipeline_stage = 'uploaded',
                    pipeline_status = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (doc_id,))
            errors += 1

        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            # Mark as failed - other error
            cursor.execute("""
                UPDATE documents
                SET
                    pipeline_stage = 'uploaded',
                    pipeline_status = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (doc_id,))
            errors += 1

    # Commit changes
    conn.commit()
    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Reprocessing Summary")
    print("=" * 60)
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {errors}")
    print(f"📄 Total documents: {len(stuck_docs)}")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   - Run indexing to create vector embeddings:")
    print("     uv run finagent reindex --skip-init")
    print("   - Or extract metadata:")
    print("     uv run python scripts/extract_metadata.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(reprocess_stuck_uploads())
