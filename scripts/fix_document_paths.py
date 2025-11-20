#!/usr/bin/env python3
"""
Fix corrupted document paths in the database.

This script fixes the path duplication bug where paths were stored as:
  data/documents/data/documents/filename.txt
instead of:
  data/documents/filename.txt

Usage:
    uv run python scripts/fix_document_paths.py
    uv run python scripts/fix_document_paths.py --dry-run  # Preview changes only
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def fix_document_paths(db_path: str, dry_run: bool = False):
    """Fix corrupted document paths in the database."""

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find corrupted paths
    cursor.execute("""
        SELECT doc_id, file_path
        FROM documents
        WHERE file_path LIKE '%data/documents/data/documents/%'
    """)

    corrupted = cursor.fetchall()

    if not corrupted:
        print("✅ No corrupted paths found!")
        conn.close()
        return 0

    print(f"Found {len(corrupted)} corrupted document paths")
    print()

    # Show examples
    print("Examples of corrupted paths:")
    for i, (doc_id, file_path) in enumerate(corrupted[:5]):
        fixed_path = file_path.replace('data/documents/data/documents/', 'data/documents/')
        print(f"  {doc_id}:")
        print(f"    OLD: {file_path}")
        print(f"    NEW: {fixed_path}")
        print()

    if len(corrupted) > 5:
        print(f"  ... and {len(corrupted) - 5} more")
        print()

    if dry_run:
        print("🔍 DRY RUN MODE - No changes made")
        print(f"Would fix {len(corrupted)} document paths")
        conn.close()
        return 0

    # Ask for confirmation
    response = input(f"Fix {len(corrupted)} document paths? (yes/no): ").lower()
    if response not in ['yes', 'y']:
        print("Aborted")
        conn.close()
        return 1

    # Fix paths
    print()
    print("Fixing paths...")

    fixed_count = 0
    for doc_id, file_path in corrupted:
        try:
            # Remove duplicate prefix
            fixed_path = file_path.replace('data/documents/data/documents/', 'data/documents/')

            # Update database
            cursor.execute("""
                UPDATE documents
                SET file_path = ?
                WHERE doc_id = ?
            """, (fixed_path, doc_id))

            fixed_count += 1

            if fixed_count % 50 == 0:
                print(f"  Fixed {fixed_count}/{len(corrupted)} documents...")

        except Exception as e:
            print(f"  ❌ Failed to fix {doc_id}: {e}")

    # Commit changes
    conn.commit()
    conn.close()

    print()
    print(f"✅ Successfully fixed {fixed_count}/{len(corrupted)} document paths!")
    print()
    print("Next steps:")
    print("  1. Run reindex-all to update the vector database:")
    print("     curl -X POST http://localhost:8000/api/v1/documents/reindex-all")
    print("  2. Or use the Web UI Documents page and click 'Reindex All'")

    return 0


def main():
    parser = argparse.ArgumentParser(description='Fix corrupted document paths in database')
    parser.add_argument(
        '--db-path',
        default='data/finagent.db',
        help='Path to SQLite database (default: data/finagent.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )

    args = parser.parse_args()

    # Check if database exists
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print(f"   Current directory: {Path.cwd()}")
        return 1

    print(f"Database: {db_path.absolute()}")
    print()

    return fix_document_paths(str(db_path), args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
