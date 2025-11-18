"""
Category Builder for Wiki System

Builds hierarchical categories from document metadata extracted in Checkpoint 2.
Categories are stored in the concepts table with different concept_types.
"""

import json
import logging
from typing import Any

from finagent.database.document_db import DocumentDatabase

logger = logging.getLogger(__name__)


class CategoryBuilder:
    """
    Builds hierarchical categories from document metadata.

    Categories are organized by:
    - Authority (按主管機關): 金管會, 中央銀行, 公平會
    - Institution (按金融機構): 玉山銀行, 國泰世華銀行
    - Violation Type (按違規類型): 洗錢防制, 內部控制, 內線交易
    - Document Type (按文件類型): 裁罰書, 判決書, 法規
    """

    def __init__(self, db: DocumentDatabase | None = None):
        """
        Initialize CategoryBuilder.

        Args:
            db: DocumentDatabase instance (creates new if None)
        """
        self.db = db or DocumentDatabase()

    def build_all_categories(self, clear_existing: bool = False) -> dict[str, int]:
        """
        Build all category types from document metadata.

        Args:
            clear_existing: Whether to clear existing categories first

        Returns:
            Dictionary with counts for each category type
        """
        if clear_existing:
            self._clear_all_categories()

        results = {}

        logger.info("Building wiki categories from document metadata...")

        # Build each category type
        results["authority"] = self.build_authority_categories()
        results["institution"] = self.build_institution_categories()
        results["violation"] = self.build_violation_categories()
        results["doc_type"] = self.build_doctype_categories()

        total = sum(results.values())
        logger.info(f"Category building complete: {total} total categories created")
        logger.info(f"  - Authority: {results['authority']}")
        logger.info(f"  - Institution: {results['institution']}")
        logger.info(f"  - Violation: {results['violation']}")
        logger.info(f"  - Document Type: {results['doc_type']}")

        return results

    def build_authority_categories(self) -> int:
        """
        Build categories for issuing authorities.

        Extracts from documents.issuing_authority field.

        Returns:
            Number of authority categories created
        """
        logger.info("Building authority categories...")

        # Get all documents with issuing_authority
        all_docs = self.db.list_documents()

        # Collect authorities
        authorities = {}
        for doc in all_docs:
            authority = doc.get("issuing_authority")
            if authority and authority.strip():
                if authority not in authorities:
                    authorities[authority] = []
                authorities[authority].append(doc["doc_id"])

        # Create concept for each authority
        count = 0
        for authority, doc_ids in authorities.items():
            concept_id = self._create_or_update_concept(
                name=authority,
                concept_type="authority",
                description=f"主管機關：{authority}",
                keywords=[authority],
            )

            # Link documents to this concept
            for doc_id in doc_ids:
                self._link_document_to_concept(doc_id, concept_id, relevance=1.0)

            count += 1

        logger.info(f"Created {count} authority categories")
        return count

    def build_institution_categories(self) -> int:
        """
        Build categories for financial institutions.

        Extracts from documents.related_institutions JSON field.

        Returns:
            Number of institution categories created
        """
        logger.info("Building institution categories...")

        # Get all documents
        all_docs = self.db.list_documents()

        # Collect institutions
        institutions = {}
        for doc in all_docs:
            related_inst = doc.get("related_institutions")
            if related_inst:
                try:
                    # Parse JSON array
                    inst_list = json.loads(related_inst) if isinstance(related_inst, str) else related_inst

                    for institution in inst_list:
                        if institution and institution.strip():
                            if institution not in institutions:
                                institutions[institution] = []
                            institutions[institution].append(doc["doc_id"])
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse related_institutions for {doc['doc_id']}: {e}")
                    continue

        # Create concept for each institution
        count = 0
        for institution, doc_ids in institutions.items():
            # Extract short name for keywords (e.g., "玉山銀行" from "玉山商業銀行股份有限公司")
            keywords = [institution]
            if "銀行" in institution:
                # Try to extract bank short name
                short_name = institution.split("商業銀行")[0] + "銀行" if "商業銀行" in institution else institution
                if short_name != institution:
                    keywords.append(short_name)

            concept_id = self._create_or_update_concept(
                name=institution,
                concept_type="institution",
                description=f"金融機構：{institution}",
                keywords=keywords,
            )

            # Link documents to this concept
            for doc_id in doc_ids:
                self._link_document_to_concept(doc_id, concept_id, relevance=1.0)

            count += 1

        logger.info(f"Created {count} institution categories")
        return count

    def build_violation_categories(self) -> int:
        """
        Build categories for violation types.

        Extracts from documents.violation_types JSON field.

        Returns:
            Number of violation categories created
        """
        logger.info("Building violation categories...")

        # Get all documents
        all_docs = self.db.list_documents()

        # Collect violations
        violations = {}
        for doc in all_docs:
            violation_types = doc.get("violation_types")
            if violation_types:
                try:
                    # Parse JSON array
                    viol_list = json.loads(violation_types) if isinstance(violation_types, str) else violation_types

                    for violation in viol_list:
                        if violation and violation.strip():
                            if violation not in violations:
                                violations[violation] = []
                            violations[violation].append(doc["doc_id"])
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse violation_types for {doc['doc_id']}: {e}")
                    continue

        # Create concept for each violation type
        count = 0
        for violation, doc_ids in violations.items():
            concept_id = self._create_or_update_concept(
                name=violation,
                concept_type="violation",
                description=f"違規類型：{violation}",
                keywords=[violation],
            )

            # Link documents to this concept
            for doc_id in doc_ids:
                self._link_document_to_concept(doc_id, concept_id, relevance=1.0)

            count += 1

        logger.info(f"Created {count} violation categories")
        return count

    def build_doctype_categories(self) -> int:
        """
        Build categories for document types.

        Extracts from documents.document_type field.

        Returns:
            Number of document type categories created
        """
        logger.info("Building document type categories...")

        # Get all documents
        all_docs = self.db.list_documents()

        # Collect document types
        doc_types = {}
        for doc in all_docs:
            doc_type = doc.get("document_type")
            if doc_type and doc_type.strip():
                if doc_type not in doc_types:
                    doc_types[doc_type] = []
                doc_types[doc_type].append(doc["doc_id"])

        # Create concept for each document type
        count = 0
        for doc_type, doc_ids in doc_types.items():
            concept_id = self._create_or_update_concept(
                name=doc_type,
                concept_type="doc_type",
                description=f"文件類型：{doc_type}",
                keywords=[doc_type],
            )

            # Link documents to this concept
            for doc_id in doc_ids:
                self._link_document_to_concept(doc_id, concept_id, relevance=1.0)

            count += 1

        logger.info(f"Created {count} document type categories")
        return count

    def _create_or_update_concept(
        self,
        name: str,
        concept_type: str,
        description: str | None = None,
        keywords: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Create or update a concept in the database.

        Args:
            name: Concept name
            concept_type: Type of concept (authority, institution, violation, doc_type)
            description: Brief description
            keywords: List of related keywords
            metadata: Additional metadata (JSON)

        Returns:
            Concept ID
        """
        # Check if concept already exists
        conn = self.db._get_connection()
        cursor = conn.execute(
            "SELECT id FROM concepts WHERE concept_name = ? AND concept_type = ?",
            (name, concept_type),
        )
        existing = cursor.fetchone()

        keywords_json = json.dumps(keywords or [], ensure_ascii=False)
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

        if existing:
            # Update existing concept
            concept_id = existing[0]
            conn.execute(
                """
                UPDATE concepts
                SET description = ?, keywords = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (description, keywords_json, metadata_json, concept_id),
            )
            conn.commit()
            logger.debug(f"Updated concept: {name} (ID: {concept_id})")
        else:
            # Insert new concept
            cursor = conn.execute(
                """
                INSERT INTO concepts (concept_name, concept_type, description, keywords, metadata, document_count)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (name, concept_type, description, keywords_json, metadata_json),
            )
            conn.commit()
            concept_id = cursor.lastrowid
            logger.debug(f"Created concept: {name} (ID: {concept_id})")

        return concept_id

    def _link_document_to_concept(self, doc_id: str, concept_id: int, relevance: float = 1.0):
        """
        Create a document-concept mapping.

        Args:
            doc_id: Document ID
            concept_id: Concept ID
            relevance: Relevance score (1.0 for category membership, <1.0 for relationships)
        """
        conn = self.db._get_connection()

        # Check if mapping already exists
        cursor = conn.execute(
            "SELECT id FROM document_concepts WHERE doc_id = ? AND concept_id = ?",
            (doc_id, concept_id),
        )
        existing = cursor.fetchone()

        if existing:
            # Update relevance score
            conn.execute(
                "UPDATE document_concepts SET relevance_score = ? WHERE id = ?",
                (relevance, existing[0]),
            )
        else:
            # Insert new mapping
            conn.execute(
                """
                INSERT INTO document_concepts (doc_id, concept_id, relevance_score)
                VALUES (?, ?, ?)
                """,
                (doc_id, concept_id, relevance),
            )

        conn.commit()

    def _clear_all_categories(self):
        """Clear all existing categories and mappings."""
        logger.info("Clearing existing categories...")

        conn = self.db._get_connection()

        # Delete all document-concept mappings
        conn.execute("DELETE FROM document_concepts")

        # Delete all concepts
        conn.execute("DELETE FROM concepts")

        conn.commit()

        logger.info("Existing categories cleared")

    def get_category_stats(self) -> dict[str, Any]:
        """
        Get statistics about categories.

        Returns:
            Dictionary with category statistics
        """
        conn = self.db._get_connection()

        stats = {
            "total_concepts": 0,
            "by_type": {},
            "total_mappings": 0,
        }

        # Count concepts by type
        cursor = conn.execute(
            """
            SELECT concept_type, COUNT(*) as count
            FROM concepts
            GROUP BY concept_type
            """
        )

        for row in cursor.fetchall():
            stats["by_type"][row[0]] = row[1]
            stats["total_concepts"] += row[1]

        # Count total mappings
        cursor = conn.execute("SELECT COUNT(*) FROM document_concepts WHERE relevance_score = 1.0")
        stats["total_mappings"] = cursor.fetchone()[0]

        return stats
