#!/usr/bin/env python3
"""
Metadata Sample Verification Script

Displays a random sample of documents with extracted metadata for manual review.
Helps validate extraction quality and identify patterns in errors.

Usage:
    uv run python scripts/verify_metadata_sample.py
    uv run python scripts/verify_metadata_sample.py --sample-size 10
    uv run python scripts/verify_metadata_sample.py --min-confidence 0.8
    uv run python scripts/verify_metadata_sample.py --document-type 裁罰書
"""

import argparse
import json
import random
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.database.document_db import DocumentDatabase


def display_document_metadata(doc: dict, index: int, total: int, show_content: bool = False):
    """Display metadata for a single document."""
    print("=" * 80)
    print(f"📄 DOCUMENT {index}/{total}")
    print("=" * 80)

    # Basic info
    print(f"ID:               {doc['doc_id']}")
    print(f"Filename:         {doc.get('filename', 'unknown')}")
    print(f"Indexed:          {'✅ Yes' if doc.get('indexed') else '❌ No'}")
    print(f"Chunks:           {doc.get('chunk_count', 0)}")
    print()

    # Extraction metadata
    confidence = doc.get("extraction_confidence")
    if confidence is not None:
        print("🤖 EXTRACTED METADATA")
        print("-" * 80)

        # Confidence
        conf_emoji = "✅" if confidence >= 0.9 else "⚠️" if confidence >= 0.7 else "❌"
        print(f"Confidence:       {conf_emoji} {confidence:.3f}")
        print(f"Method:           {doc.get('extraction_method', 'unknown')}")
        print()

        # Core fields
        print(f"Document Type:    {doc.get('document_type', 'N/A')}")
        print(f"Issuing Authority: {doc.get('issuing_authority', 'N/A')}")
        print(f"Case Number:      {doc.get('case_number', 'N/A')}")
        print(f"Document Date:    {doc.get('document_date', 'N/A')}")
        print(f"Penalty Amount:   {doc.get('penalty_amount', 'N/A')}")
        print()

        # List fields
        try:
            institutions = json.loads(doc.get("related_institutions", "[]"))
            if institutions:
                print(f"Related Institutions ({len(institutions)}):")
                for inst in institutions:
                    print(f"  • {inst}")
            else:
                print(f"Related Institutions: None")
        except:
            print(f"Related Institutions: [Parse Error]")

        print()

        try:
            violations = json.loads(doc.get("violation_types", "[]"))
            if violations:
                print(f"Violation Types ({len(violations)}):")
                for violation in violations:
                    print(f"  • {violation}")
            else:
                print(f"Violation Types: None")
        except:
            print(f"Violation Types: [Parse Error]")

        print()

        try:
            keywords = json.loads(doc.get("keywords", "[]"))
            if keywords:
                print(f"Keywords ({len(keywords)}):")
                print(f"  {', '.join(keywords)}")
            else:
                print(f"Keywords: None")
        except:
            print(f"Keywords: [Parse Error]")

        print()

    else:
        print("❌ NO METADATA EXTRACTED")
        print()

    # Content preview
    if show_content:
        content = doc.get("content_preview") or doc.get("full_content")
        if content:
            print("📝 CONTENT PREVIEW")
            print("-" * 80)
            print(content[:500])
            if len(content) > 500:
                print("...")
            print()

    print()


def sample_documents(
    db: DocumentDatabase,
    sample_size: int = 5,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    document_type: str | None = None,
    has_metadata: bool = True,
) -> list[dict]:
    """
    Get a random sample of documents matching criteria.

    Args:
        db: DocumentDatabase instance
        sample_size: Number of documents to sample
        min_confidence: Minimum confidence score filter
        max_confidence: Maximum confidence score filter
        document_type: Filter by document type
        has_metadata: Whether to require metadata

    Returns:
        List of sampled documents
    """
    # Get all documents
    all_docs = db.get_all_documents()

    # Apply filters
    filtered_docs = []

    for doc in all_docs:
        # Has metadata filter
        if has_metadata and doc.get("extraction_confidence") is None:
            continue
        if not has_metadata and doc.get("extraction_confidence") is not None:
            continue

        # Confidence filters
        if min_confidence is not None:
            if doc.get("extraction_confidence", 0) < min_confidence:
                continue

        if max_confidence is not None:
            if doc.get("extraction_confidence", 1) > max_confidence:
                continue

        # Document type filter
        if document_type is not None:
            if doc.get("document_type") != document_type:
                continue

        filtered_docs.append(doc)

    # Random sample
    if len(filtered_docs) <= sample_size:
        return filtered_docs
    else:
        return random.sample(filtered_docs, sample_size)


def main():
    parser = argparse.ArgumentParser(
        description="Display random sample of documents for metadata verification"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of documents to sample (default: 5)",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        help="Minimum confidence score (0.0-1.0)",
    )
    parser.add_argument(
        "--max-confidence",
        type=float,
        help="Maximum confidence score (0.0-1.0)",
    )
    parser.add_argument(
        "--document-type",
        type=str,
        help="Filter by document type (裁罰書, 判決書, etc.)",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Sample documents WITHOUT metadata",
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Show content preview for each document",
    )

    args = parser.parse_args()

    # Initialize database
    db = DocumentDatabase()

    # Sample documents
    print(f"Sampling {args.sample_size} documents...")
    print()

    has_metadata = not args.no_metadata

    docs = sample_documents(
        db,
        sample_size=args.sample_size,
        min_confidence=args.min_confidence,
        max_confidence=args.max_confidence,
        document_type=args.document_type,
        has_metadata=has_metadata,
    )

    if not docs:
        print("No documents found matching criteria.")
        return 1

    print(f"Found {len(docs)} documents for review")
    print()

    # Display each document
    for i, doc in enumerate(docs, 1):
        display_document_metadata(doc, i, len(docs), show_content=args.show_content)

    # Summary
    print("=" * 80)
    print("📊 SAMPLE SUMMARY")
    print("=" * 80)

    if has_metadata:
        confidences = [doc.get("extraction_confidence", 0) for doc in docs]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        print(f"Documents sampled:    {len(docs)}")
        print(f"Average confidence:   {avg_conf:.3f}")
        print(f"Min confidence:       {min(confidences):.3f}")
        print(f"Max confidence:       {max(confidences):.3f}")
        print()

        # Document types
        doc_types = {}
        for doc in docs:
            doc_type = doc.get("document_type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        if doc_types:
            print("Document Types:")
            for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {doc_type}: {count}")

    print()
    print("💡 Use --show-content to see document content")
    print("💡 Use --min-confidence to filter by confidence score")
    print("💡 Use --document-type to filter by type")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
