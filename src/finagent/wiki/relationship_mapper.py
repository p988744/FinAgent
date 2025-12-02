"""
Relationship Mapper for Wiki System

Detects and maps relationships between documents based on shared metadata.
"""

import json
import logging
from datetime import datetime
from typing import Any

from finagent.database.document_db import DocumentDatabase

logger = logging.getLogger(__name__)


class RelationshipMapper:
    """
    Detects relationships between documents.

    Relationships are based on:
    - Shared institutions (same bank involved)
    - Shared violation types (same type of violation)
    - Temporal proximity (similar dates)
    - Same authority (same regulator)

    Relationship strength is scored from 0.0 to 1.0:
    - Institution match: +0.3
    - Violation match: +0.3
    - Date proximity: +0.2 (closer = higher)
    - Same authority: +0.2
    """

    def __init__(
        self,
        db: DocumentDatabase | None = None,
        min_strength: float = 0.3,
    ):
        """
        Initialize RelationshipMapper.

        Args:
            db: DocumentDatabase instance (creates new if None)
            min_strength: Minimum relationship strength to store (0.0-1.0)
        """
        self.db = db or DocumentDatabase()
        self.min_strength = min_strength

    def detect_all_relationships(self, clear_existing: bool = False) -> int:
        """
        Detect relationships for all documents.

        Args:
            clear_existing: Whether to clear existing relationships first

        Returns:
            Number of relationships detected
        """
        if clear_existing:
            self._clear_all_relationships()

        logger.info("Detecting document relationships...")

        # Get all documents with metadata
        all_docs = self.db.list_documents()

        # Filter to only documents with metadata
        docs_with_metadata = [
            doc for doc in all_docs
            if doc.get("extraction_confidence") is not None
        ]

        logger.info(f"Processing {len(docs_with_metadata)} documents with metadata...")

        relationship_count = 0

        # Compare each document with all others
        for i, doc1 in enumerate(docs_with_metadata):
            if (i + 1) % 50 == 0:
                logger.info(f"Processed {i + 1}/{len(docs_with_metadata)} documents...")

            related = self.find_related_documents(doc1, docs_with_metadata)

            for doc2, strength in related:
                # Only store if strength >= threshold
                if strength >= self.min_strength:
                    # Create bidirectional relationship
                    # Note: We store as document_concepts with doc_id as both document and concept
                    # This is a bit of a hack but reuses existing table
                    self._store_relationship(doc1["doc_id"], doc2["doc_id"], strength)
                    relationship_count += 1

        logger.info(f"Detected {relationship_count} relationships (strength >= {self.min_strength})")

        return relationship_count

    def find_related_documents(
        self,
        doc: dict,
        candidates: list[dict] | None = None,
    ) -> list[tuple[dict, float]]:
        """
        Find documents related to the given document.

        Args:
            doc: Document to find relationships for
            candidates: List of candidate documents (uses all if None)

        Returns:
            List of (related_doc, strength) tuples, sorted by strength descending
        """
        if candidates is None:
            # Get all documents with metadata
            all_docs = self.db.list_documents()
            candidates = [
                d for d in all_docs
                if d.get("extraction_confidence") is not None
                and d["doc_id"] != doc["doc_id"]
            ]

        related = []

        for candidate in candidates:
            # Skip self
            if candidate["doc_id"] == doc["doc_id"]:
                continue

            # Calculate relationship strength
            strength = self.calculate_relationship_strength(doc, candidate)

            if strength >= self.min_strength:
                related.append((candidate, strength))

        # Sort by strength descending
        related.sort(key=lambda x: x[1], reverse=True)

        return related

    def calculate_relationship_strength(self, doc1: dict, doc2: dict) -> float:
        """
        Calculate relationship strength between two documents.

        Scoring:
        - Institution overlap: +0.3
        - Violation overlap: +0.3
        - Date proximity: +0.2 (within 1 year = full score, decreases linearly)
        - Same authority: +0.2

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            Relationship strength score (0.0-1.0)
        """
        strength = 0.0

        # Check institution overlap
        if self._has_institution_overlap(doc1, doc2):
            strength += 0.3

        # Check violation overlap
        if self._has_violation_overlap(doc1, doc2):
            strength += 0.3

        # Check date proximity
        date_score = self._calculate_date_proximity(doc1, doc2)
        strength += date_score * 0.2

        # Check same authority
        auth1 = doc1.get("issuing_authority")
        auth2 = doc2.get("issuing_authority")
        if auth1 and auth2 and auth1 == auth2:
            strength += 0.2

        return min(strength, 1.0)  # Cap at 1.0

    def _has_institution_overlap(self, doc1: dict, doc2: dict) -> bool:
        """
        Check if documents share any institutions.

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            True if documents share at least one institution
        """
        inst1 = self._get_institutions_set(doc1)
        inst2 = self._get_institutions_set(doc2)

        if not inst1 or not inst2:
            return False

        return bool(inst1 & inst2)  # Set intersection

    def _has_violation_overlap(self, doc1: dict, doc2: dict) -> bool:
        """
        Check if documents share any violation types.

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            True if documents share at least one violation type
        """
        viol1 = self._get_violations_set(doc1)
        viol2 = self._get_violations_set(doc2)

        if not viol1 or not viol2:
            return False

        return bool(viol1 & viol2)  # Set intersection

    def _calculate_date_proximity(self, doc1: dict, doc2: dict) -> float:
        """
        Calculate date proximity score (0.0-1.0).

        Full score (1.0) if documents are within 1 year.
        Score decreases linearly to 0.0 at 5+ years apart.

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            Date proximity score (0.0-1.0)
        """
        date1_str = doc1.get("document_date")
        date2_str = doc2.get("document_date")

        if not date1_str or not date2_str:
            return 0.0

        try:
            # Parse dates (format: YYYY-MM-DD)
            date1 = datetime.strptime(date1_str, "%Y-%m-%d")
            date2 = datetime.strptime(date2_str, "%Y-%m-%d")

            # Calculate difference in days
            delta = abs((date1 - date2).days)

            # Calculate score
            # Within 1 year (365 days) = 1.0
            # 5+ years (1825 days) = 0.0
            # Linear interpolation in between
            if delta <= 365:
                return 1.0
            elif delta >= 1825:
                return 0.0
            else:
                # Linear decrease from 1.0 to 0.0
                return 1.0 - ((delta - 365) / (1825 - 365))

        except Exception as e:
            logger.warning(f"Failed to calculate date proximity: {e}")
            return 0.0

    def _get_institutions_set(self, doc: dict) -> set[str]:
        """
        Get set of institutions from document.

        Args:
            doc: Document dictionary

        Returns:
            Set of institution names
        """
        related_inst = doc.get("related_institutions")
        if not related_inst:
            return set()

        try:
            inst_list = json.loads(related_inst) if isinstance(related_inst, str) else related_inst
            return set(inst for inst in inst_list if inst)
        except (json.JSONDecodeError, TypeError):
            return set()

    def _get_violations_set(self, doc: dict) -> set[str]:
        """
        Get set of violation types from document.

        Args:
            doc: Document dictionary

        Returns:
            Set of violation type names
        """
        violations = doc.get("violation_types")
        if not violations:
            return set()

        try:
            viol_list = json.loads(violations) if isinstance(violations, str) else violations
            return set(viol for viol in viol_list if viol)
        except (json.JSONDecodeError, TypeError):
            return set()

    def _store_relationship(self, doc_id1: str, doc_id2: str, strength: float):
        """
        Store a relationship between two documents.

        Note: This is a simplified implementation that stores relationships
        in the document_concepts table. In a full implementation, you might
        want a dedicated document_relationships table.

        Args:
            doc_id1: First document ID
            doc_id2: Second document ID (treated as "concept")
            strength: Relationship strength (0.0-1.0)
        """
        conn = self.db._get_connection()

        # Create a pseudo-concept for the related document
        # First, check if concept exists for this document
        cursor = conn.execute(
            "SELECT id FROM concepts WHERE name = ? AND concept_type = 'related_doc'",
            (doc_id2,),
        )
        existing = cursor.fetchone()

        if existing:
            concept_id = existing[0]
        else:
            # Create pseudo-concept
            cursor = conn.execute(
                """
                INSERT INTO concepts (
                    name, concept_type, description, document_count
                )
                VALUES (?, ?, ?, 0)
                """,
                (doc_id2, "related_doc", f"Related document: {doc_id2}"),
            )
            conn.commit()
            concept_id = cursor.lastrowid

        # Now create the mapping with relevance_score = strength
        # Check if mapping already exists
        cursor = conn.execute(
            "SELECT id FROM document_concepts WHERE doc_id = ? AND concept_id = ?",
            (doc_id1, concept_id),
        )
        existing_mapping = cursor.fetchone()

        if existing_mapping:
            # Update strength
            conn.execute(
                "UPDATE document_concepts SET relevance_score = ? WHERE id = ?",
                (strength, existing_mapping[0]),
            )
        else:
            # Insert new mapping
            conn.execute(
                """
                INSERT INTO document_concepts (doc_id, concept_id, relevance_score)
                VALUES (?, ?, ?)
                """,
                (doc_id1, concept_id, strength),
            )

        conn.commit()

    def _clear_all_relationships(self):
        """Clear all existing relationships."""
        logger.info("Clearing existing relationships...")

        conn = self.db._get_connection()

        # Delete all related_doc concepts
        conn.execute("DELETE FROM concepts WHERE concept_type = 'related_doc'")

        conn.commit()

        logger.info("Existing relationships cleared")

    def get_relationship_stats(self) -> dict[str, Any]:
        """
        Get statistics about relationships.

        Returns:
            Dictionary with relationship statistics
        """
        conn = self.db._get_connection()

        # Count relationships (mappings with relevance < 1.0)
        cursor = conn.execute(
            """
            SELECT COUNT(*), AVG(relevance_score), MIN(relevance_score), MAX(relevance_score)
            FROM document_concepts
            WHERE relevance_score < 1.0
            """
        )
        count, avg_strength, min_strength, max_strength = cursor.fetchone()

        # Distribution by strength range
        cursor = conn.execute(
            """
            SELECT
                CASE
                    WHEN relevance_score >= 0.8 THEN 'strong (0.8-1.0)'
                    WHEN relevance_score >= 0.6 THEN 'medium (0.6-0.8)'
                    WHEN relevance_score >= 0.4 THEN 'weak (0.4-0.6)'
                    ELSE 'very_weak (0.0-0.4)'
                END as strength_range,
                COUNT(*) as count
            FROM document_concepts
            WHERE relevance_score < 1.0
            GROUP BY strength_range
            """
        )

        distribution = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total_relationships": count or 0,
            "avg_strength": round(avg_strength, 3) if avg_strength else 0.0,
            "min_strength": round(min_strength, 3) if min_strength else 0.0,
            "max_strength": round(max_strength, 3) if max_strength else 0.0,
            "distribution": distribution,
        }
