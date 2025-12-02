"""
Statistics Engine for Wiki System

Calculates and stores statistics about documents, categories, and trends.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from finagent.database.document_db import DocumentDatabase

logger = logging.getLogger(__name__)


class StatisticsEngine:
    """
    Calculates statistics and metrics for the wiki system.

    Statistics include:
    - Total document counts
    - Distribution by authority, institution, violation type, document type
    - Timeline data (documents by year, month)
    - Top entities (most penalized institutions, most common violations)
    """

    def __init__(self, db: DocumentDatabase | None = None):
        """
        Initialize StatisticsEngine.

        Args:
            db: DocumentDatabase instance (creates new if None)
        """
        self.db = db or DocumentDatabase()

    def calculate_all_statistics(self) -> dict[str, Any]:
        """
        Calculate all statistics for the wiki.

        Returns:
            Dictionary with all calculated statistics
        """
        logger.info("Calculating wiki statistics...")

        stats = {
            "generated_at": datetime.now().isoformat(),
            "document_stats": self.calculate_document_stats(),
            "timeline_stats": self.calculate_timeline_stats(),
            "top_entities": self.calculate_top_entities(),
            "category_stats": self.calculate_category_stats(),
        }

        logger.info("Statistics calculation complete")
        logger.info(f"  - Total documents: {stats['document_stats']['total_documents']}")
        logger.info(f"  - Documents with metadata: {stats['document_stats']['with_metadata']}")
        logger.info(f"  - Total categories: {stats['category_stats']['total_concepts']}")

        return stats

    def calculate_document_stats(self) -> dict[str, Any]:
        """
        Calculate basic document statistics.

        Returns:
            Dictionary with document counts and distributions
        """
        all_docs = self.db.list_documents()

        stats = {
            "total_documents": len(all_docs),
            "with_metadata": 0,
            "without_metadata": 0,
            "indexed": 0,
            "by_type": defaultdict(int),
            "by_authority": defaultdict(int),
            "avg_confidence": 0.0,
        }

        confidence_scores = []

        for doc in all_docs:
            # Check metadata
            if doc.get("extraction_confidence") is not None:
                stats["with_metadata"] += 1
                confidence_scores.append(doc["extraction_confidence"])
            else:
                stats["without_metadata"] += 1

            # Check indexed
            if doc.get("indexed"):
                stats["indexed"] += 1

            # Count by type
            doc_type = doc.get("document_type")
            if doc_type:
                stats["by_type"][doc_type] += 1

            # Count by authority
            authority = doc.get("issuing_authority")
            if authority:
                stats["by_authority"][authority] += 1

        # Calculate average confidence
        if confidence_scores:
            stats["avg_confidence"] = sum(confidence_scores) / len(confidence_scores)

        # Convert defaultdicts to regular dicts
        stats["by_type"] = dict(stats["by_type"])
        stats["by_authority"] = dict(stats["by_authority"])

        return stats

    def calculate_timeline_stats(self) -> dict[str, Any]:
        """
        Calculate timeline statistics (documents by year, month).

        Returns:
            Dictionary with timeline data
        """
        all_docs = self.db.list_documents()

        by_year = defaultdict(int)
        by_month = defaultdict(int)
        by_year_month = defaultdict(int)

        for doc in all_docs:
            doc_date = doc.get("document_date")
            if doc_date:
                try:
                    # Parse date (format: YYYY-MM-DD)
                    date_parts = doc_date.split("-")
                    if len(date_parts) >= 2:
                        year = date_parts[0]
                        month = date_parts[1]

                        by_year[year] += 1
                        by_month[month] += 1
                        by_year_month[f"{year}-{month}"] += 1
                except Exception as e:
                    logger.warning(f"Failed to parse date {doc_date}: {e}")
                    continue

        # Sort by key
        stats = {
            "by_year": dict(sorted(by_year.items())),
            "by_month": dict(by_month),
            "by_year_month": dict(sorted(by_year_month.items())),
            "earliest_year": min(by_year.keys()) if by_year else None,
            "latest_year": max(by_year.keys()) if by_year else None,
        }

        return stats

    def calculate_top_entities(self, top_n: int = 10) -> dict[str, Any]:
        """
        Calculate top entities (institutions, violations, etc.).

        Args:
            top_n: Number of top entities to return

        Returns:
            Dictionary with top entity lists
        """
        all_docs = self.db.list_documents()

        institution_counts = defaultdict(int)
        violation_counts = defaultdict(int)
        penalty_amounts = []

        for doc in all_docs:
            # Count institutions
            related_inst = doc.get("related_institutions")
            if related_inst:
                try:
                    inst_list = json.loads(related_inst) if isinstance(related_inst, str) else related_inst
                    for institution in inst_list:
                        if institution:
                            institution_counts[institution] += 1
                except (json.JSONDecodeError, TypeError):
                    pass

            # Count violations
            violations = doc.get("violation_types")
            if violations:
                try:
                    viol_list = json.loads(violations) if isinstance(violations, str) else violations
                    for violation in viol_list:
                        if violation:
                            violation_counts[violation] += 1
                except (json.JSONDecodeError, TypeError):
                    pass

            # Collect penalty amounts
            penalty = doc.get("penalty_amount")
            if penalty:
                penalty_amounts.append({
                    "doc_id": doc["doc_id"],
                    "filename": doc.get("filename", ""),
                    "amount": penalty,
                    "institution": self._get_first_institution(doc),
                })

        # Sort and get top N
        top_institutions = sorted(
            institution_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        top_violations = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        stats = {
            "top_institutions": [
                {"name": name, "count": count}
                for name, count in top_institutions
            ],
            "top_violations": [
                {"name": name, "count": count}
                for name, count in top_violations
            ],
            "total_institutions": len(institution_counts),
            "total_violations": len(violation_counts),
            "documents_with_penalties": len(penalty_amounts),
        }

        return stats

    def calculate_category_stats(self) -> dict[str, Any]:
        """
        Calculate statistics about categories.

        Returns:
            Dictionary with category statistics
        """
        conn = self.db._get_connection()

        stats = {
            "total_concepts": 0,
            "by_type": {},
            "total_mappings": 0,
            "avg_docs_per_category": 0.0,
        }

        # Count concepts by type
        cursor = conn.execute(
            """
            SELECT concept_type, COUNT(*) as count, AVG(document_count) as avg_docs
            FROM concepts
            GROUP BY concept_type
            """
        )

        total_avg = []
        for row in cursor.fetchall():
            concept_type, count, avg_docs = row
            stats["by_type"][concept_type] = {
                "count": count,
                "avg_documents": round(avg_docs, 2) if avg_docs else 0.0,
            }
            stats["total_concepts"] += count
            total_avg.append(avg_docs or 0.0)

        # Count total mappings (category memberships only, relevance = 1.0)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM document_concepts WHERE relevance_score = 1.0"
        )
        stats["total_mappings"] = cursor.fetchone()[0]

        # Calculate average documents per category
        if total_avg:
            stats["avg_docs_per_category"] = round(sum(total_avg) / len(total_avg), 2)

        return stats

    def store_statistics(self, stats: dict[str, Any]):
        """
        Store statistics in the database.

        Stores statistics in a special concept with concept_type='statistics'.

        Args:
            stats: Statistics dictionary to store
        """
        logger.info("Storing statistics in database...")

        conn = self.db._get_connection()

        stats_json = json.dumps(stats, ensure_ascii=False, indent=2)

        # Check if statistics concept exists
        cursor = conn.execute(
            "SELECT id FROM concepts WHERE name = 'wiki_statistics' AND concept_type = 'statistics'"
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing
            conn.execute(
                """
                UPDATE concepts
                SET metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (stats_json, existing[0]),
            )
            logger.info(f"Updated statistics (concept ID: {existing[0]})")
        else:
            # Insert new
            cursor = conn.execute(
                """
                INSERT INTO concepts (
                    name, concept_type, description, metadata, document_count
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "wiki_statistics",
                    "statistics",
                    "Wiki-wide statistics and metrics",
                    stats_json,
                    0,
                ),
            )
            logger.info(f"Created statistics concept (ID: {cursor.lastrowid})")

        conn.commit()

    def get_stored_statistics(self) -> dict[str, Any] | None:
        """
        Retrieve stored statistics from database.

        Returns:
            Statistics dictionary or None if not found
        """
        conn = self.db._get_connection()

        cursor = conn.execute(
            "SELECT metadata FROM concepts WHERE name = 'wiki_statistics' AND concept_type = 'statistics'"
        )
        result = cursor.fetchone()

        if result and result[0]:
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                logger.error("Failed to parse stored statistics")
                return None

        return None

    def _get_first_institution(self, doc: dict) -> str | None:
        """
        Get the first institution from a document's related_institutions.

        Args:
            doc: Document dictionary

        Returns:
            First institution name or None
        """
        related_inst = doc.get("related_institutions")
        if related_inst:
            try:
                inst_list = json.loads(related_inst) if isinstance(related_inst, str) else related_inst
                if inst_list and len(inst_list) > 0:
                    return inst_list[0]
            except (json.JSONDecodeError, TypeError):
                pass
        return None
