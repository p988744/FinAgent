"""
Wiki Generator - Orchestrates Wiki Generation Process

Coordinates CategoryBuilder, StatisticsEngine, and RelationshipMapper
to generate a complete wiki from document metadata.
"""

import logging
import time
from typing import Any

from finagent.database.document_db import DocumentDatabase
from finagent.wiki.category_builder import CategoryBuilder
from finagent.wiki.relationship_mapper import RelationshipMapper
from finagent.wiki.statistics import StatisticsEngine

logger = logging.getLogger(__name__)


class WikiGenerator:
    """
    Orchestrates the wiki generation process.

    Workflow:
    1. Build categories from document metadata
    2. Calculate statistics and metrics
    3. Detect document relationships
    4. Store results in database
    5. Validate data quality
    """

    def __init__(self, db: DocumentDatabase | None = None):
        """
        Initialize WikiGenerator.

        Args:
            db: DocumentDatabase instance (creates new if None)
        """
        self.db = db or DocumentDatabase()

        # Initialize components
        self.category_builder = CategoryBuilder(self.db)
        self.statistics_engine = StatisticsEngine(self.db)
        self.relationship_mapper = RelationshipMapper(self.db)

    def generate_wiki(
        self,
        clear_existing: bool = False,
        include_relationships: bool = True,
        relationship_threshold: float = 0.3,
    ) -> dict[str, Any]:
        """
        Generate complete wiki from document metadata.

        Args:
            clear_existing: Whether to clear existing wiki data first
            include_relationships: Whether to detect document relationships
            relationship_threshold: Minimum relationship strength to store (0.0-1.0)

        Returns:
            Dictionary with generation results and statistics
        """
        logger.info("=" * 80)
        logger.info("Starting Wiki Generation")
        logger.info("=" * 80)

        start_time = time.time()

        # Update relationship mapper threshold
        self.relationship_mapper.min_strength = relationship_threshold

        results = {
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "clear_existing": clear_existing,
            "include_relationships": include_relationships,
            "phases": {},
        }

        try:
            # Phase 1: Build Categories
            logger.info("\n[Phase 1/4] Building Categories...")
            phase1_start = time.time()

            category_counts = self.category_builder.build_all_categories(
                clear_existing=clear_existing
            )

            phase1_time = time.time() - phase1_start
            results["phases"]["categories"] = {
                "duration_seconds": round(phase1_time, 2),
                "counts": category_counts,
                "total_categories": sum(category_counts.values()),
            }

            logger.info(f"Phase 1 complete in {phase1_time:.2f}s")

            # Phase 2: Calculate Statistics
            logger.info("\n[Phase 2/4] Calculating Statistics...")
            phase2_start = time.time()

            statistics = self.statistics_engine.calculate_all_statistics()
            self.statistics_engine.store_statistics(statistics)

            phase2_time = time.time() - phase2_start
            results["phases"]["statistics"] = {
                "duration_seconds": round(phase2_time, 2),
                "summary": {
                    "total_documents": statistics["document_stats"]["total_documents"],
                    "with_metadata": statistics["document_stats"]["with_metadata"],
                    "total_categories": statistics["category_stats"]["total_concepts"],
                },
            }

            logger.info(f"Phase 2 complete in {phase2_time:.2f}s")

            # Phase 3: Detect Relationships (optional)
            if include_relationships:
                logger.info("\n[Phase 3/4] Detecting Relationships...")
                phase3_start = time.time()

                relationship_count = self.relationship_mapper.detect_all_relationships(
                    clear_existing=clear_existing
                )

                phase3_time = time.time() - phase3_start
                results["phases"]["relationships"] = {
                    "duration_seconds": round(phase3_time, 2),
                    "count": relationship_count,
                    "threshold": relationship_threshold,
                }

                logger.info(f"Phase 3 complete in {phase3_time:.2f}s")
            else:
                logger.info("\n[Phase 3/4] Skipping Relationships (disabled)")
                results["phases"]["relationships"] = {
                    "duration_seconds": 0,
                    "count": 0,
                    "skipped": True,
                }

            # Phase 4: Validate Results
            logger.info("\n[Phase 4/4] Validating Wiki Data...")
            phase4_start = time.time()

            validation = self.validate_wiki()

            phase4_time = time.time() - phase4_start
            results["phases"]["validation"] = {
                "duration_seconds": round(phase4_time, 2),
                "results": validation,
            }

            logger.info(f"Phase 4 complete in {phase4_time:.2f}s")

            # Calculate total time
            total_time = time.time() - start_time
            results["total_duration_seconds"] = round(total_time, 2)
            results["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            results["success"] = True

            logger.info("\n" + "=" * 80)
            logger.info(f"Wiki Generation Complete in {total_time:.2f}s")
            logger.info("=" * 80)
            logger.info(f"  Categories:    {results['phases']['categories']['total_categories']}")
            logger.info(f"  Documents:     {statistics['document_stats']['total_documents']}")
            logger.info(f"  With Metadata: {statistics['document_stats']['with_metadata']}")
            if include_relationships:
                logger.info(f"  Relationships: {results['phases']['relationships']['count']}")
            logger.info("=" * 80)

        except Exception as e:
            total_time = time.time() - start_time
            results["total_duration_seconds"] = round(total_time, 2)
            results["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            results["success"] = False
            results["error"] = str(e)

            logger.error(f"\n❌ Wiki generation failed after {total_time:.2f}s: {e}")
            raise

        return results

    def validate_wiki(self) -> dict[str, Any]:
        """
        Validate wiki data quality.

        Checks:
        - All documents belong to at least one category
        - Category counts are accurate
        - No orphaned documents
        - Relationship strength scores are reasonable

        Returns:
            Dictionary with validation results
        """
        validation = {
            "checks": {},
            "warnings": [],
            "errors": [],
            "passed": True,
        }

        # Check 1: All documents have categories
        all_docs = self.db.list_documents()
        docs_with_metadata = [
            doc for doc in all_docs
            if doc.get("extraction_confidence") is not None
        ]

        conn = self.db._get_connection()

        # Count documents with category mappings
        cursor = conn.execute(
            """
            SELECT COUNT(DISTINCT doc_id)
            FROM document_concepts
            WHERE relevance_score = 1.0
            """
        )
        docs_with_categories = cursor.fetchone()[0]

        validation["checks"]["documents_categorized"] = {
            "total_with_metadata": len(docs_with_metadata),
            "with_categories": docs_with_categories,
            "percentage": round(
                (docs_with_categories / len(docs_with_metadata) * 100)
                if docs_with_metadata else 0,
                1
            ),
        }

        if docs_with_categories < len(docs_with_metadata):
            missing = len(docs_with_metadata) - docs_with_categories
            validation["warnings"].append(
                f"{missing} documents with metadata have no categories"
            )

        # Check 2: Category counts are accurate
        cursor = conn.execute(
            """
            SELECT concept_type, SUM(document_count) as total_count
            FROM concepts
            WHERE concept_type IN ('authority', 'institution', 'violation', 'doc_type')
            GROUP BY concept_type
            """
        )

        category_counts = {row[0]: row[1] for row in cursor.fetchall()}

        validation["checks"]["category_counts"] = category_counts

        # Check 3: No orphaned categories (document_count should match actual mappings)
        cursor = conn.execute(
            """
            SELECT c.id, c.concept_name, c.document_count,
                   COUNT(dc.doc_id) as actual_count
            FROM concepts c
            LEFT JOIN document_concepts dc ON c.id = dc.concept_id AND dc.relevance_score = 1.0
            WHERE c.concept_type IN ('authority', 'institution', 'violation', 'doc_type')
            GROUP BY c.id
            HAVING c.document_count != actual_count
            """
        )

        mismatched = cursor.fetchall()
        if mismatched:
            validation["warnings"].append(
                f"{len(mismatched)} categories have mismatched document counts (trigger may not have fired)"
            )
            validation["checks"]["mismatched_counts"] = len(mismatched)

        # Check 4: Relationship strength scores are reasonable
        rel_stats = self.relationship_mapper.get_relationship_stats()

        validation["checks"]["relationships"] = rel_stats

        if rel_stats["total_relationships"] > 0:
            if rel_stats["min_strength"] < 0.3:
                validation["warnings"].append(
                    f"Some relationships have very low strength (min: {rel_stats['min_strength']})"
                )

            if rel_stats["max_strength"] > 1.0:
                validation["errors"].append(
                    f"Some relationships have invalid strength (max: {rel_stats['max_strength']})"
                )
                validation["passed"] = False

        # Overall pass/fail
        if validation["errors"]:
            validation["passed"] = False

        return validation

    def get_wiki_summary(self) -> dict[str, Any]:
        """
        Get a summary of the current wiki state.

        Returns:
            Dictionary with wiki summary
        """
        # Get stored statistics
        stats = self.statistics_engine.get_stored_statistics()

        if not stats:
            stats = self.statistics_engine.calculate_all_statistics()

        # Get category stats
        category_stats = self.category_builder.get_category_stats()

        # Get relationship stats
        relationship_stats = self.relationship_mapper.get_relationship_stats()

        summary = {
            "generated_at": stats.get("generated_at") if stats else None,
            "document_stats": stats.get("document_stats") if stats else {},
            "category_stats": category_stats,
            "relationship_stats": relationship_stats,
            "timeline_stats": stats.get("timeline_stats") if stats else {},
            "top_entities": stats.get("top_entities") if stats else {},
        }

        return summary
