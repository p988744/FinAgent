#!/usr/bin/env python3
"""
Wiki Generation Script

Generates the complete wiki structure from document metadata.

Usage:
    uv run python scripts/generate_wiki.py
    uv run python scripts/generate_wiki.py --clear
    uv run python scripts/generate_wiki.py --no-relationships
    uv run python scripts/generate_wiki.py --threshold 0.5
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.wiki import WikiGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Generate wiki structure from document metadata"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing wiki data before generating",
    )
    parser.add_argument(
        "--no-relationships",
        action="store_true",
        help="Skip relationship detection (faster)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Minimum relationship strength to store (0.0-1.0, default: 0.3)",
    )
    parser.add_argument(
        "--export",
        type=str,
        metavar="FILE",
        help="Export results to JSON file",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show wiki summary instead of generating",
    )

    args = parser.parse_args()

    # Initialize generator
    generator = WikiGenerator()

    if args.summary:
        # Show summary of existing wiki
        print("Fetching wiki summary...")
        summary = generator.get_wiki_summary()

        print("\n" + "=" * 80)
        print("📊 WIKI SUMMARY")
        print("=" * 80)

        if summary.get("generated_at"):
            print(f"Last Generated: {summary['generated_at']}")
        print()

        # Document stats
        doc_stats = summary.get("document_stats", {})
        print("📄 DOCUMENTS")
        print("-" * 80)
        print(f"Total:         {doc_stats.get('total_documents', 0)}")
        print(f"With Metadata: {doc_stats.get('with_metadata', 0)}")
        print(f"Indexed:       {doc_stats.get('indexed', 0)}")
        print(f"Avg Confidence: {doc_stats.get('avg_confidence', 0):.3f}")
        print()

        # Category stats
        cat_stats = summary.get("category_stats", {})
        print("📁 CATEGORIES")
        print("-" * 80)
        print(f"Total: {cat_stats.get('total_concepts', 0)}")
        for cat_type, data in cat_stats.get("by_type", {}).items():
            if isinstance(data, dict):
                print(f"  {cat_type:15} {data.get('count', 0):4d} categories")
            else:
                print(f"  {cat_type:15} {data:4d} categories")
        print()

        # Relationship stats
        rel_stats = summary.get("relationship_stats", {})
        print("🔗 RELATIONSHIPS")
        print("-" * 80)
        print(f"Total:        {rel_stats.get('total_relationships', 0)}")
        print(f"Avg Strength: {rel_stats.get('avg_strength', 0):.3f}")
        print(f"Min Strength: {rel_stats.get('min_strength', 0):.3f}")
        print(f"Max Strength: {rel_stats.get('max_strength', 0):.3f}")
        print()

        # Top entities
        top_entities = summary.get("top_entities", {})
        if top_entities.get("top_institutions"):
            print("🏦 TOP INSTITUTIONS")
            print("-" * 80)
            for item in top_entities["top_institutions"][:10]:
                print(f"  {item['name'][:50]:50} {item['count']:3d} documents")
            print()

        if top_entities.get("top_violations"):
            print("⚠️  TOP VIOLATIONS")
            print("-" * 80)
            for item in top_entities["top_violations"][:10]:
                print(f"  {item['name'][:50]:50} {item['count']:3d} documents")
            print()

        print("=" * 80)

        return 0

    # Generate wiki
    print("Starting wiki generation...")
    print()
    print(f"Options:")
    print(f"  Clear existing: {args.clear}")
    print(f"  Include relationships: {not args.no_relationships}")
    print(f"  Relationship threshold: {args.threshold}")
    print()

    try:
        results = generator.generate_wiki(
            clear_existing=args.clear,
            include_relationships=not args.no_relationships,
            relationship_threshold=args.threshold,
        )

        # Print results
        print("\n" + "=" * 80)
        print("📊 GENERATION RESULTS")
        print("=" * 80)

        if results["success"]:
            print(f"✅ Success")
            print(f"Started:  {results['started_at']}")
            print(f"Completed: {results['completed_at']}")
            print(f"Duration: {results['total_duration_seconds']:.2f}s")
            print()

            # Phase details
            print("Phase Timings:")
            for phase_name, phase_data in results["phases"].items():
                duration = phase_data["duration_seconds"]
                print(f"  {phase_name:15} {duration:6.2f}s")
            print()

            # Categories
            cat_phase = results["phases"].get("categories", {})
            print("Categories Created:")
            for cat_type, count in cat_phase.get("counts", {}).items():
                print(f"  {cat_type:15} {count:4d}")
            print(f"  {'TOTAL':15} {cat_phase.get('total_categories', 0):4d}")
            print()

            # Relationships
            if not args.no_relationships:
                rel_phase = results["phases"].get("relationships", {})
                rel_count = rel_phase.get("count", 0)
                print(f"Relationships Detected: {rel_count}")
                print()

            # Validation
            val_phase = results["phases"].get("validation", {})
            validation = val_phase.get("results", {})

            print("Validation:")
            print(f"  Passed: {'✅ Yes' if validation.get('passed') else '❌ No'}")

            if validation.get("warnings"):
                print(f"  Warnings: {len(validation['warnings'])}")
                for warning in validation["warnings"]:
                    print(f"    ⚠️  {warning}")

            if validation.get("errors"):
                print(f"  Errors: {len(validation['errors'])}")
                for error in validation["errors"]:
                    print(f"    ❌ {error}")

            print()

        else:
            print(f"❌ Failed")
            print(f"Error: {results.get('error')}")
            return 1

        # Export if requested
        if args.export:
            export_path = Path(args.export)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results exported to: {export_path}")

        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
