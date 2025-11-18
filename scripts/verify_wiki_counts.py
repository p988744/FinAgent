#!/usr/bin/env python3
"""
Wiki Count Verification Script

Verifies that wiki category counts are accurate and consistent.

Usage:
    uv run python scripts/verify_wiki_counts.py
    uv run python scripts/verify_wiki_counts.py --detailed
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.database.document_db import DocumentDatabase


def verify_category_counts(db: DocumentDatabase, detailed: bool = False):
    """Verify that category document_count matches actual mappings."""
    print("=" * 80)
    print("📊 WIKI CATEGORY COUNT VERIFICATION")
    print("=" * 80)
    print()

    conn = db._get_connection()

    # Get all categories
    cursor = conn.execute(
        """
        SELECT c.id, c.concept_name, c.concept_type, c.document_count,
               COUNT(dc.doc_id) as actual_count
        FROM concepts c
        LEFT JOIN document_concepts dc ON c.id = dc.concept_id AND dc.relevance_score = 1.0
        WHERE c.concept_type IN ('authority', 'institution', 'violation', 'doc_type')
        GROUP BY c.id
        ORDER BY c.concept_type, c.concept_name
        """
    )

    categories = cursor.fetchall()

    # Track results
    total = len(categories)
    matched = 0
    mismatched = 0
    mismatched_list = []

    by_type = {}

    for cat_id, name, cat_type, stored_count, actual_count in categories:
        if cat_type not in by_type:
            by_type[cat_type] = {"total": 0, "matched": 0, "mismatched": 0}

        by_type[cat_type]["total"] += 1

        if stored_count == actual_count:
            matched += 1
            by_type[cat_type]["matched"] += 1
        else:
            mismatched += 1
            by_type[cat_type]["mismatched"] += 1
            mismatched_list.append({
                "id": cat_id,
                "name": name,
                "type": cat_type,
                "stored": stored_count,
                "actual": actual_count,
            })

    # Print summary
    print("OVERALL SUMMARY")
    print("-" * 80)
    print(f"Total Categories:  {total}")
    print(f"Matched:           {matched} ({matched/total*100:.1f}%)")
    print(f"Mismatched:        {mismatched} ({mismatched/total*100:.1f}%)")
    print()

    # Print by type
    print("BY CATEGORY TYPE")
    print("-" * 80)
    for cat_type in ["authority", "institution", "violation", "doc_type"]:
        if cat_type in by_type:
            data = by_type[cat_type]
            print(f"{cat_type:15} Total: {data['total']:3d}  Matched: {data['matched']:3d}  Mismatched: {data['mismatched']:3d}")
    print()

    # Print mismatches
    if mismatched_list:
        print("❌ MISMATCHED CATEGORIES")
        print("-" * 80)
        for item in mismatched_list[:20]:  # Show first 20
            diff = item["actual"] - item["stored"]
            sign = "+" if diff > 0 else ""
            print(f"  [{item['type']:10}] {item['name'][:40]:40} Stored: {item['stored']:3d}  Actual: {item['actual']:3d}  ({sign}{diff})")

        if len(mismatched_list) > 20:
            print(f"  ... and {len(mismatched_list) - 20} more")
        print()

    # Detailed view
    if detailed and mismatched_list:
        print("DETAILED MISMATCH ANALYSIS")
        print("-" * 80)
        for item in mismatched_list:
            print(f"\nCategory: {item['name']} ({item['type']})")
            print(f"  ID: {item['id']}")
            print(f"  Stored count: {item['stored']}")
            print(f"  Actual count: {item['actual']}")

            # Show documents
            cursor = conn.execute(
                """
                SELECT doc_id
                FROM document_concepts
                WHERE concept_id = ? AND relevance_score = 1.0
                """,
                (item['id'],)
            )
            doc_ids = [row[0] for row in cursor.fetchall()]

            print(f"  Documents ({len(doc_ids)}):")
            for doc_id in doc_ids[:5]:  # Show first 5
                print(f"    - {doc_id}")
            if len(doc_ids) > 5:
                print(f"    ... and {len(doc_ids) - 5} more")

    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 80)
    if mismatched == 0:
        print("✅ All category counts are accurate!")
    else:
        print("⚠️  Some category counts are inaccurate. This may happen if:")
        print("  1. Database triggers did not fire properly")
        print("  2. Direct database modifications bypassed triggers")
        print("  3. Manual corrections needed")
        print()
        print("To fix: Re-run wiki generation with --clear flag:")
        print("  uv run python scripts/generate_wiki.py --clear")

    print()
    print("=" * 80)

    return mismatched == 0


def verify_orphaned_documents(db: DocumentDatabase):
    """Check for documents without categories."""
    print("\n")
    print("=" * 80)
    print("📄 ORPHANED DOCUMENT CHECK")
    print("=" * 80)
    print()

    conn = db._get_connection()

    # Get documents with metadata but no categories
    cursor = conn.execute(
        """
        SELECT d.doc_id, d.filename, d.document_type, d.extraction_confidence
        FROM documents d
        WHERE d.extraction_confidence IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM document_concepts dc
            WHERE dc.doc_id = d.doc_id AND dc.relevance_score = 1.0
        )
        """
    )

    orphaned = cursor.fetchall()

    if not orphaned:
        print("✅ No orphaned documents found!")
        print("   All documents with metadata are categorized.")
    else:
        print(f"❌ Found {len(orphaned)} orphaned documents")
        print()
        print("Documents with metadata but no categories:")
        print("-" * 80)

        for doc_id, filename, doc_type, confidence in orphaned[:20]:
            print(f"  {filename[:50]:50} Type: {doc_type or 'N/A':10} Conf: {confidence:.2f}")

        if len(orphaned) > 20:
            print(f"  ... and {len(orphaned) - 20} more")

        print()
        print("💡 RECOMMENDATION:")
        print("  Re-run wiki generation to categorize these documents:")
        print("  uv run python scripts/generate_wiki.py")

    print()
    print("=" * 80)

    return len(orphaned) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Verify wiki category counts are accurate"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed mismatch analysis",
    )

    args = parser.parse_args()

    # Initialize database
    db = DocumentDatabase()

    # Run verifications
    counts_ok = verify_category_counts(db, detailed=args.detailed)
    orphans_ok = verify_orphaned_documents(db)

    # Return 0 if all checks passed
    if counts_ok and orphans_ok:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
