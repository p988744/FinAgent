#!/usr/bin/env python3
"""
Metadata Quality Validation Script

Analyzes the quality of extracted metadata across all indexed documents.
Generates a comprehensive quality report with metrics and recommendations.

Usage:
    uv run python scripts/check_metadata_quality.py
    uv run python scripts/check_metadata_quality.py --detailed
    uv run python scripts/check_metadata_quality.py --export report.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.database.document_db import DocumentDatabase


def analyze_metadata_quality(db: DocumentDatabase, detailed: bool = False) -> dict[str, Any]:
    """
    Analyze metadata quality across all documents.

    Args:
        db: DocumentDatabase instance
        detailed: Include detailed per-document analysis

    Returns:
        Dictionary with quality metrics and analysis
    """
    # Get all documents
    all_docs = db.get_all_documents()

    if not all_docs:
        return {
            "error": "No documents found in database",
            "total_documents": 0,
        }

    total = len(all_docs)

    # Metrics
    metrics = {
        "total_documents": total,
        "with_metadata": 0,
        "without_metadata": 0,
        "metadata_extraction_rate": 0.0,
        "avg_confidence": 0.0,
        "confidence_distribution": {
            "high (0.9-1.0)": 0,
            "good (0.8-0.9)": 0,
            "medium (0.7-0.8)": 0,
            "low (0.5-0.7)": 0,
            "very_low (0.0-0.5)": 0,
        },
        "field_completion": {
            "title": 0,
            "description": 0,
            "document_type": 0,
            "issuing_authority": 0,
            "case_number": 0,
            "document_date": 0,
            "related_institutions": 0,
            "violation_types": 0,
            "penalty_amount": 0,
            "keywords": 0,
        },
        "document_type_distribution": {},
        "extraction_method_distribution": {},
    }

    confidence_scores = []
    low_confidence_docs = []
    missing_metadata_docs = []
    detailed_results = []

    for doc in all_docs:
        doc_id = doc["doc_id"]
        filename = doc.get("filename", "unknown")

        # Check if metadata extracted
        has_metadata = doc.get("extraction_confidence") is not None

        if has_metadata:
            metrics["with_metadata"] += 1

            # Confidence score
            confidence = doc.get("extraction_confidence", 0.0)
            confidence_scores.append(confidence)

            # Confidence distribution
            if confidence >= 0.9:
                metrics["confidence_distribution"]["high (0.9-1.0)"] += 1
            elif confidence >= 0.8:
                metrics["confidence_distribution"]["good (0.8-0.9)"] += 1
            elif confidence >= 0.7:
                metrics["confidence_distribution"]["medium (0.7-0.8)"] += 1
            elif confidence >= 0.5:
                metrics["confidence_distribution"]["low (0.5-0.7)"] += 1
            else:
                metrics["confidence_distribution"]["very_low (0.0-0.5)"] += 1

            # Track low confidence
            if confidence < 0.7:
                low_confidence_docs.append({
                    "doc_id": doc_id,
                    "filename": filename,
                    "confidence": confidence,
                    "document_type": doc.get("document_type"),
                })

            # Field completion
            if doc.get("document_type"):
                metrics["field_completion"]["document_type"] += 1

                # Document type distribution
                doc_type = doc["document_type"]
                metrics["document_type_distribution"][doc_type] = \
                    metrics["document_type_distribution"].get(doc_type, 0) + 1

            if doc.get("issuing_authority"):
                metrics["field_completion"]["issuing_authority"] += 1

            if doc.get("case_number"):
                metrics["field_completion"]["case_number"] += 1

            if doc.get("document_date"):
                metrics["field_completion"]["document_date"] += 1

            # Check JSON fields
            try:
                institutions = json.loads(doc.get("related_institutions", "[]"))
                if institutions:
                    metrics["field_completion"]["related_institutions"] += 1
            except:
                pass

            try:
                violations = json.loads(doc.get("violation_types", "[]"))
                if violations:
                    metrics["field_completion"]["violation_types"] += 1
            except:
                pass

            if doc.get("penalty_amount"):
                metrics["field_completion"]["penalty_amount"] += 1

            try:
                keywords = json.loads(doc.get("keywords", "[]"))
                if keywords:
                    metrics["field_completion"]["keywords"] += 1
            except:
                pass

            # Extraction method
            method = doc.get("extraction_method", "unknown")
            metrics["extraction_method_distribution"][method] = \
                metrics["extraction_method_distribution"].get(method, 0) + 1

            # Detailed per-document info
            if detailed:
                detailed_results.append({
                    "doc_id": doc_id,
                    "filename": filename,
                    "confidence": confidence,
                    "document_type": doc.get("document_type"),
                    "issuing_authority": doc.get("issuing_authority"),
                    "has_case_number": bool(doc.get("case_number")),
                    "has_date": bool(doc.get("document_date")),
                    "num_institutions": len(json.loads(doc.get("related_institutions", "[]"))),
                    "num_violations": len(json.loads(doc.get("violation_types", "[]"))),
                    "num_keywords": len(json.loads(doc.get("keywords", "[]"))),
                })
        else:
            metrics["without_metadata"] += 1
            missing_metadata_docs.append({
                "doc_id": doc_id,
                "filename": filename,
            })

    # Calculate rates
    metrics["metadata_extraction_rate"] = (metrics["with_metadata"] / total) * 100

    if confidence_scores:
        metrics["avg_confidence"] = sum(confidence_scores) / len(confidence_scores)

    # Convert field completion to percentages
    for field in metrics["field_completion"]:
        count = metrics["field_completion"][field]
        if metrics["with_metadata"] > 0:
            metrics["field_completion"][field] = {
                "count": count,
                "percentage": (count / metrics["with_metadata"]) * 100,
            }
        else:
            metrics["field_completion"][field] = {
                "count": 0,
                "percentage": 0.0,
            }

    # Build result
    result = {
        "generated_at": datetime.now().isoformat(),
        "metrics": metrics,
        "low_confidence_documents": low_confidence_docs,
        "missing_metadata_documents": missing_metadata_docs,
    }

    if detailed:
        result["detailed_documents"] = detailed_results

    return result


def print_quality_report(report: dict[str, Any]):
    """Print formatted quality report to console."""
    print("=" * 80)
    print("📊 METADATA QUALITY REPORT")
    print("=" * 80)
    print(f"Generated: {report['generated_at']}")
    print()

    metrics = report["metrics"]

    print("📈 EXTRACTION METRICS")
    print("-" * 80)
    print(f"Total Documents:           {metrics['total_documents']}")
    print(f"With Metadata:             {metrics['with_metadata']} ({metrics['metadata_extraction_rate']:.1f}%)")
    print(f"Without Metadata:          {metrics['without_metadata']}")
    print(f"Average Confidence:        {metrics['avg_confidence']:.3f}")
    print()

    print("🎯 CONFIDENCE DISTRIBUTION")
    print("-" * 80)
    for level, count in metrics["confidence_distribution"].items():
        percentage = (count / metrics["total_documents"] * 100) if metrics["total_documents"] > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"{level:20} {count:4d} ({percentage:5.1f}%) {bar}")
    print()

    print("📋 FIELD COMPLETION RATES")
    print("-" * 80)
    for field, data in metrics["field_completion"].items():
        count = data["count"]
        pct = data["percentage"]
        bar = "█" * int(pct / 2)
        print(f"{field:25} {count:4d} ({pct:5.1f}%) {bar}")
    print()

    if metrics["document_type_distribution"]:
        print("📁 DOCUMENT TYPE DISTRIBUTION")
        print("-" * 80)
        for doc_type, count in sorted(metrics["document_type_distribution"].items(),
                                      key=lambda x: x[1], reverse=True):
            percentage = (count / metrics["with_metadata"] * 100) if metrics["with_metadata"] > 0 else 0
            bar = "█" * int(percentage / 2)
            print(f"{doc_type:25} {count:4d} ({percentage:5.1f}%) {bar}")
        print()

    # Quality assessment
    print("✅ QUALITY ASSESSMENT")
    print("-" * 80)

    issues = []
    recommendations = []

    # Check extraction rate
    if metrics["metadata_extraction_rate"] < 100:
        issues.append(f"⚠️  Only {metrics['metadata_extraction_rate']:.1f}% of documents have metadata")
        recommendations.append("Run reindex with --extract-metadata to extract missing metadata")

    # Check confidence
    if metrics["avg_confidence"] < 0.85:
        issues.append(f"⚠️  Average confidence ({metrics['avg_confidence']:.3f}) below target (0.85)")
        recommendations.append("Review low-confidence documents and improve extraction prompts")

    # Check low confidence docs
    low_conf_count = len(report["low_confidence_documents"])
    if low_conf_count > 0:
        issues.append(f"⚠️  {low_conf_count} documents with low confidence (<0.7)")
        recommendations.append(f"Review low-confidence documents (see below)")

    # Check field completion
    for field, data in metrics["field_completion"].items():
        if field in ["document_type", "keywords"] and data["percentage"] < 90:
            issues.append(f"⚠️  {field} completion rate ({data['percentage']:.1f}%) below 90%")

    if not issues:
        print("✅ All quality checks passed!")
        print(f"   - Extraction rate: {metrics['metadata_extraction_rate']:.1f}%")
        print(f"   - Average confidence: {metrics['avg_confidence']:.3f}")
        print(f"   - High confidence docs: {metrics['confidence_distribution']['high (0.9-1.0)']}")
    else:
        print("Issues found:")
        for issue in issues:
            print(f"   {issue}")

    print()

    if recommendations:
        print("💡 RECOMMENDATIONS")
        print("-" * 80)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()

    # Low confidence documents
    if report["low_confidence_documents"]:
        print(f"⚠️  LOW CONFIDENCE DOCUMENTS ({len(report['low_confidence_documents'])} total)")
        print("-" * 80)
        for doc in report["low_confidence_documents"][:10]:  # Show first 10
            print(f"   {doc['confidence']:.3f}  {doc['filename'][:60]}")

        if len(report["low_confidence_documents"]) > 10:
            print(f"   ... and {len(report['low_confidence_documents']) - 10} more")
        print()

    # Missing metadata
    if report["missing_metadata_documents"]:
        print(f"❌ MISSING METADATA ({len(report['missing_metadata_documents'])} total)")
        print("-" * 80)
        for doc in report["missing_metadata_documents"][:10]:  # Show first 10
            print(f"   {doc['filename'][:60]}")

        if len(report["missing_metadata_documents"]) > 10:
            print(f"   ... and {len(report['missing_metadata_documents']) - 10} more")
        print()

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze metadata quality across all indexed documents"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include detailed per-document analysis",
    )
    parser.add_argument(
        "--export",
        type=str,
        metavar="FILE",
        help="Export report to JSON file",
    )

    args = parser.parse_args()

    # Initialize database
    db = DocumentDatabase()

    # Analyze quality
    print("Analyzing metadata quality...")
    report = analyze_metadata_quality(db, detailed=args.detailed)

    if "error" in report:
        print(f"Error: {report['error']}")
        return 1

    # Print report
    print_quality_report(report)

    # Export if requested
    if args.export:
        export_path = Path(args.export)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report exported to: {export_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
