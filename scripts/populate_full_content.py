#!/usr/bin/env python3
"""Populate full_content column in documents table by reading files."""

import sqlite3
from pathlib import Path

def populate_full_content():
    """Read document files and populate full_content column."""
    # Connect to database
    db_path = Path(__file__).parent.parent / "data" / "finagent.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all documents
    cursor.execute("SELECT doc_id, file_path FROM documents")
    documents = cursor.fetchall()

    updated = 0
    errors = 0

    for doc in documents:
        doc_id = doc["doc_id"]
        file_path = doc["file_path"]

        try:
            # Read file content
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                print(f"⚠️  File not found: {file_path}")
                errors += 1
                continue

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update database
            cursor.execute(
                "UPDATE documents SET full_content = ? WHERE doc_id = ?",
                (content, doc_id)
            )
            updated += 1
            print(f"✅ Updated {doc_id[:15]}... ({len(content)} chars)")

        except Exception as e:
            print(f"❌ Error processing {doc_id}: {e}")
            errors += 1

    # Commit changes
    conn.commit()
    conn.close()

    print(f"\n📊 Summary:")
    print(f"  ✅ Updated: {updated}")
    print(f"  ❌ Errors: {errors}")
    print(f"  📄 Total: {len(documents)}")

if __name__ == "__main__":
    populate_full_content()
