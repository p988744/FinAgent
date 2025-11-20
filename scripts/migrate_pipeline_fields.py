#!/usr/bin/env python3
"""
Migrate existing documents to add pipeline monitoring fields.
This script updates all existing documents in the database to have the new pipeline fields.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Path to database
DB_PATH = Path(__file__).parent.parent / "data" / "finagent.db"


def migrate_pipeline_fields():
    """Add pipeline fields to existing documents."""
    print("🔧 Migrating pipeline fields for existing documents...\n")

    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if pipeline fields exist in schema
        cursor.execute("PRAGMA table_info(documents)")
        columns = [row[1] for row in cursor.fetchall()]

        if "pipeline_stage" not in columns:
            print("⚠️  Pipeline fields not in schema. Running schema migration...\n")

            # Add pipeline fields to documents table
            # Note: SQLite doesn't allow CURRENT_TIMESTAMP in ALTER TABLE, so we use NULL and update later
            cursor.execute(
                """
                ALTER TABLE documents ADD COLUMN pipeline_stage TEXT DEFAULT 'uploaded'
                """
            )
            cursor.execute(
                """
                ALTER TABLE documents ADD COLUMN pipeline_status TEXT DEFAULT 'in_progress'
                """
            )
            cursor.execute(
                """
                ALTER TABLE documents ADD COLUMN pipeline_data TEXT
                """
            )
            cursor.execute(
                """
                ALTER TABLE documents ADD COLUMN pipeline_started_at TIMESTAMP
                """
            )
            cursor.execute(
                """
                ALTER TABLE documents ADD COLUMN pipeline_completed_at TIMESTAMP
                """
            )

            conn.commit()
            print("✅ Pipeline fields added to schema\n")

        # Get all documents
        cursor.execute("SELECT doc_id, filename, indexed, metadata_extracted FROM documents")
        documents = cursor.fetchall()

        print(f"Found {len(documents)} documents to migrate\n")

        migrated = 0
        for doc_id, filename, indexed, metadata_extracted in documents:
            # Determine pipeline stage based on current status
            if metadata_extracted:
                stage = "metadata_extracted"
                status = "success"
            elif indexed:
                stage = "indexed"
                status = "success"
            else:
                stage = "uploaded"
                status = "in_progress"

            # Update document with pipeline fields
            # Check if pipeline_stage is already set
            cursor.execute(
                "SELECT pipeline_stage FROM documents WHERE doc_id = ?", (doc_id,)
            )
            current = cursor.fetchone()

            if not current or not current[0] or current[0] == "uploaded":
                cursor.execute(
                    """
                    UPDATE documents
                    SET pipeline_stage = ?,
                        pipeline_status = ?
                    WHERE doc_id = ?
                    """,
                    (stage, status, doc_id),
                )
                migrated += 1
                print(f"  {migrated}. {filename}: {stage} ({status})")
            else:
                print(f"  SKIP: {filename} (already migrated: {current[0]})")

        conn.commit()
        print(f"\n✅ Migrated {migrated} documents successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_pipeline_fields()
