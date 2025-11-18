"""
Wiki API Routes

REST endpoints for accessing wiki data, categories, and statistics.
"""

import json
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from finagent.api.schemas.wiki import (
    CategoryDetail,
    CategorySummary,
    CategoryTree,
    DocumentDetail,
    DocumentList,
    DocumentStats,
    DocumentSummary,
    ErrorResponse,
    RelatedDocument,
    SearchFilters,
    SearchResponse,
    SearchResult,
    StatsRefreshResponse,
    TimelineDataPoint,
    TimelineStats,
    TopEntitiesStats,
    TopEntity,
    WikiOverview,
    WikiRebuildResponse,
)
from finagent.database.document_db import DocumentDatabase
from finagent.wiki.generator import WikiGenerator
from finagent.wiki.statistics import StatisticsEngine

router = APIRouter(prefix="/api/v1/wiki", tags=["wiki"])
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================


def _get_db() -> DocumentDatabase:
    """Get database instance."""
    return DocumentDatabase()


def _get_wiki_generator() -> WikiGenerator:
    """Get wiki generator instance."""
    db = _get_db()
    return WikiGenerator(db)


def _db_doc_to_summary(doc: dict[str, Any]) -> DocumentSummary:
    """Convert database document to DocumentSummary."""
    # Parse JSON fields
    related_inst = doc.get("related_institutions") or "[]"
    if isinstance(related_inst, str):
        related_inst = json.loads(related_inst)

    violation_types = doc.get("violation_types") or "[]"
    if isinstance(violation_types, str):
        violation_types = json.loads(violation_types)

    return DocumentSummary(
        doc_id=doc["doc_id"],
        filename=doc["filename"],
        document_type=doc.get("document_type"),
        issuing_authority=doc.get("issuing_authority"),
        date=doc.get("date"),
        related_institutions=related_inst,
        violation_types=violation_types,
        extraction_confidence=doc.get("extraction_confidence"),
    )


def _db_doc_to_detail(doc: dict[str, Any], include_content: bool = True) -> DocumentDetail:
    """Convert database document to DocumentDetail."""
    # Parse JSON fields
    related_inst = doc.get("related_institutions") or "[]"
    if isinstance(related_inst, str):
        related_inst = json.loads(related_inst)

    violation_types = doc.get("violation_types") or "[]"
    if isinstance(violation_types, str):
        violation_types = json.loads(violation_types)

    keywords = doc.get("keywords") or "[]"
    if isinstance(keywords, str):
        keywords = json.loads(keywords)

    # Get full content if requested
    full_content = None
    if include_content:
        db = _get_db()
        full_content = db.get_full_content(doc["doc_id"])

    return DocumentDetail(
        doc_id=doc["doc_id"],
        filename=doc["filename"],
        file_path=doc.get("file_path", ""),
        document_type=doc.get("document_type"),
        issuing_authority=doc.get("issuing_authority"),
        date=doc.get("date"),
        case_number=doc.get("case_number"),
        related_institutions=related_inst,
        violation_types=violation_types,
        penalty_amount=doc.get("penalty_amount"),
        keywords=keywords,
        extraction_confidence=doc.get("extraction_confidence"),
        full_content=full_content,
        chunk_count=doc.get("chunk_count", 0),
        indexed=bool(doc.get("indexed", 0)),
        file_size=doc.get("file_size"),
        created_at=doc.get("created_at", ""),
        updated_at=doc.get("updated_at", ""),
        related_documents=[],  # Will be populated separately if needed
    )


def _db_concept_to_summary(concept: dict[str, Any]) -> CategorySummary:
    """Convert database concept to CategorySummary."""
    keywords = concept.get("keywords") or "[]"
    if isinstance(keywords, str):
        keywords = json.loads(keywords)

    return CategorySummary(
        id=concept["id"],
        name=concept["concept_name"],
        type=concept["concept_type"],
        document_count=concept.get("document_count", 0),
        description=concept.get("description"),
        keywords=keywords,
    )


def _db_concept_to_detail(concept: dict[str, Any]) -> CategoryDetail:
    """Convert database concept to CategoryDetail."""
    keywords = concept.get("keywords") or "[]"
    if isinstance(keywords, str):
        keywords = json.loads(keywords)

    metadata = concept.get("metadata") or "{}"
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    return CategoryDetail(
        id=concept["id"],
        name=concept["concept_name"],
        type=concept["concept_type"],
        document_count=concept.get("document_count", 0),
        description=concept.get("description"),
        keywords=keywords,
        metadata=metadata,
        created_at=concept.get("created_at", ""),
        updated_at=concept.get("updated_at", ""),
    )


# ============================================================================
# Wiki Overview Endpoints
# ============================================================================


@router.get("/overview", response_model=WikiOverview)
async def get_wiki_overview():
    """
    Get complete wiki overview with statistics.

    Returns:
        WikiOverview with document stats, categories, and recent documents
    """
    try:
        generator = _get_wiki_generator()
        summary = generator.get_wiki_summary()

        db = _get_db()

        # Get total counts
        all_docs = db.list_documents()
        total_documents = len(all_docs)

        # Get categories by type
        conn = db._get_connection()
        cursor = conn.execute(
            """
            SELECT concept_type, COUNT(*) as count
            FROM concepts
            WHERE concept_type IN ('authority', 'institution', 'violation', 'doc_type')
            GROUP BY concept_type
            """
        )
        categories_by_type = {row[0]: row[1] for row in cursor.fetchall()}
        total_categories = sum(categories_by_type.values())

        # Get document stats
        docs_with_metadata = [d for d in all_docs if d.get("extraction_confidence")]
        doc_stats = DocumentStats(
            total_documents=total_documents,
            with_metadata=len(docs_with_metadata),
            without_metadata=total_documents - len(docs_with_metadata),
            by_type=summary.get("document_stats", {}).get("by_type", {}),
            by_authority=summary.get("document_stats", {}).get("by_authority", {}),
            avg_confidence=summary.get("document_stats", {}).get("avg_confidence"),
        )

        # Get recent documents (last 10)
        recent_docs = sorted(
            all_docs,
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )[:10]
        recent_summaries = [_db_doc_to_summary(doc) for doc in recent_docs]

        # Get top entities
        top_ents = summary.get("top_entities", {})
        top_entities = TopEntitiesStats(
            institutions=[
                TopEntity(name=item["name"], count=item["count"], percentage=item["percentage"])
                for item in top_ents.get("institutions", [])
            ],
            violations=[
                TopEntity(name=item["name"], count=item["count"], percentage=item["percentage"])
                for item in top_ents.get("violations", [])
            ],
            authorities=[
                TopEntity(name=item["name"], count=item["count"], percentage=item["percentage"])
                for item in top_ents.get("authorities", [])
            ],
        )

        return WikiOverview(
            total_documents=total_documents,
            total_categories=total_categories,
            categories_by_type=categories_by_type,
            document_stats=doc_stats,
            recent_documents=recent_summaries,
            top_entities=top_entities,
            generated_at=summary.get("generated_at"),
        )

    except Exception as e:
        logger.error(f"Error getting wiki overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Category Endpoints
# ============================================================================


@router.get("/categories", response_model=CategoryTree)
async def get_categories(
    type: str = Query(..., description="Category type: authority, institution, violation, or doc_type")
):
    """
    Get category tree for a specific type.

    Args:
        type: Category type (authority, institution, violation, doc_type)

    Returns:
        CategoryTree with all categories of that type
    """
    valid_types = ["authority", "institution", "violation", "doc_type"]
    if type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category type. Must be one of: {', '.join(valid_types)}",
        )

    try:
        db = _get_db()
        conn = db._get_connection()

        cursor = conn.execute(
            """
            SELECT id, concept_name, concept_type, document_count, description, keywords
            FROM concepts
            WHERE concept_type = ?
            ORDER BY concept_name
            """,
            (type,),
        )

        categories = []
        for row in cursor.fetchall():
            concept = {
                "id": row[0],
                "concept_name": row[1],
                "concept_type": row[2],
                "document_count": row[3],
                "description": row[4],
                "keywords": row[5],
            }
            categories.append(_db_concept_to_summary(concept))

        return CategoryTree(
            type=type,
            total_count=len(categories),
            categories=categories,
        )

    except Exception as e:
        logger.error(f"Error getting categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category_id}", response_model=CategoryDetail)
async def get_category_detail(category_id: int):
    """
    Get detailed information about a specific category.

    Args:
        category_id: Category ID

    Returns:
        CategoryDetail with full metadata
    """
    try:
        db = _get_db()
        conn = db._get_connection()

        cursor = conn.execute(
            """
            SELECT id, concept_name, concept_type, document_count, description,
                   keywords, metadata, created_at, updated_at
            FROM concepts
            WHERE id = ?
            """,
            (category_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found")

        concept = {
            "id": row[0],
            "concept_name": row[1],
            "concept_type": row[2],
            "document_count": row[3],
            "description": row[4],
            "keywords": row[5],
            "metadata": row[6],
            "created_at": row[7],
            "updated_at": row[8],
        }

        return _db_concept_to_detail(concept)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting category detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Document Endpoints
# ============================================================================


@router.get("/documents", response_model=DocumentList)
async def get_documents(
    category_id: int | None = Query(None, description="Filter by category ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Get paginated list of documents.

    Args:
        category_id: Optional category filter
        limit: Results per page (1-100)
        offset: Pagination offset

    Returns:
        DocumentList with paginated results
    """
    try:
        db = _get_db()

        if category_id is not None:
            # Get documents in specific category
            conn = db._get_connection()
            cursor = conn.execute(
                """
                SELECT d.doc_id, d.filename, d.document_type, d.issuing_authority,
                       d.date, d.related_institutions, d.violation_types, d.extraction_confidence
                FROM documents d
                INNER JOIN document_concepts dc ON d.doc_id = dc.doc_id
                WHERE dc.concept_id = ? AND dc.relevance_score = 1.0
                ORDER BY d.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (category_id, limit, offset),
            )

            total_cursor = conn.execute(
                """
                SELECT COUNT(DISTINCT d.doc_id)
                FROM documents d
                INNER JOIN document_concepts dc ON d.doc_id = dc.doc_id
                WHERE dc.concept_id = ? AND dc.relevance_score = 1.0
                """,
                (category_id,),
            )
            total = total_cursor.fetchone()[0]

            docs = []
            for row in cursor.fetchall():
                doc = {
                    "doc_id": row[0],
                    "filename": row[1],
                    "document_type": row[2],
                    "issuing_authority": row[3],
                    "date": row[4],
                    "related_institutions": row[5],
                    "violation_types": row[6],
                    "extraction_confidence": row[7],
                }
                docs.append(_db_doc_to_summary(doc))

        else:
            # Get all documents
            all_docs = db.list_documents()
            total = len(all_docs)

            # Sort by created_at descending
            sorted_docs = sorted(
                all_docs,
                key=lambda x: x.get("created_at", ""),
                reverse=True,
            )

            # Paginate
            paginated = sorted_docs[offset : offset + limit]
            docs = [_db_doc_to_summary(doc) for doc in paginated]

        return DocumentList(
            total=total,
            offset=offset,
            limit=limit,
            documents=docs,
        )

    except Exception as e:
        logger.error(f"Error getting documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{doc_id}", response_model=DocumentDetail)
async def get_document_detail(
    doc_id: str,
    include_content: bool = Query(True, description="Include full document content"),
    include_related: bool = Query(True, description="Include related documents"),
):
    """
    Get detailed information about a specific document.

    Args:
        doc_id: Document ID
        include_content: Include full document content
        include_related: Include related documents

    Returns:
        DocumentDetail with full metadata and optional content
    """
    try:
        db = _get_db()
        doc = db.get_document(doc_id)

        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        detail = _db_doc_to_detail(doc, include_content=include_content)

        # Get related documents if requested
        if include_related:
            conn = db._get_connection()
            cursor = conn.execute(
                """
                SELECT dr.related_doc_id, dr.relationship_type, dr.strength,
                       d.filename
                FROM document_relationships dr
                INNER JOIN documents d ON dr.related_doc_id = d.doc_id
                WHERE dr.doc_id = ?
                ORDER BY dr.strength DESC
                LIMIT 10
                """,
                (doc_id,),
            )

            related = []
            for row in cursor.fetchall():
                related.append(
                    RelatedDocument(
                        doc_id=row[0],
                        filename=row[3],
                        relationship_type=row[1],
                        strength=row[2],
                        reason=None,  # Could be enhanced
                    )
                )

            detail.related_documents = related

        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Search Endpoint
# ============================================================================


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    document_type: str | None = Query(None, description="Filter by document type"),
    authority: str | None = Query(None, description="Filter by authority"),
    institution: str | None = Query(None, description="Filter by institution"),
    violation: str | None = Query(None, description="Filter by violation type"),
    date_from: str | None = Query(None, description="Filter by date from (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter by date to (YYYY-MM-DD)"),
    min_confidence: float | None = Query(None, ge=0, le=1, description="Minimum extraction confidence"),
):
    """
    Search for documents within the wiki.

    Simple keyword search implementation for alpha version.
    Future: Integrate with vector search for semantic search.

    Args:
        q: Search query
        limit: Results per page
        offset: Pagination offset
        document_type, authority, institution, violation: Filters
        date_from, date_to: Date range filter
        min_confidence: Minimum confidence threshold

    Returns:
        SearchResponse with matching documents
    """
    try:
        db = _get_db()
        all_docs = db.list_documents()

        # Build filter object
        filters = SearchFilters(
            document_type=document_type,
            authority=authority,
            institution=institution,
            violation=violation,
            date_from=date_from,
            date_to=date_to,
            min_confidence=min_confidence,
        )

        # Simple keyword search (case-insensitive)
        query_lower = q.lower()
        results = []

        for doc in all_docs:
            # Apply filters
            if document_type and doc.get("document_type") != document_type:
                continue
            if authority and doc.get("issuing_authority") != authority:
                continue
            if min_confidence and (doc.get("extraction_confidence") or 0) < min_confidence:
                continue

            # Check institution filter
            if institution:
                related_inst = doc.get("related_institutions") or "[]"
                if isinstance(related_inst, str):
                    related_inst = json.loads(related_inst)
                if institution not in related_inst:
                    continue

            # Check violation filter
            if violation:
                violation_types = doc.get("violation_types") or "[]"
                if isinstance(violation_types, str):
                    violation_types = json.loads(violation_types)
                if violation not in violation_types:
                    continue

            # Date filters
            doc_date = doc.get("date")
            if date_from and doc_date and doc_date < date_from:
                continue
            if date_to and doc_date and doc_date > date_to:
                continue

            # Keyword match (simple)
            filename_lower = doc.get("filename", "").lower()
            doc_type_lower = (doc.get("document_type") or "").lower()

            if query_lower in filename_lower or query_lower in doc_type_lower:
                # Calculate simple relevance score
                relevance = 1.0 if query_lower in filename_lower else 0.5

                results.append(
                    SearchResult(
                        doc_id=doc["doc_id"],
                        filename=doc["filename"],
                        document_type=doc.get("document_type"),
                        relevance_score=relevance,
                        snippet=doc.get("filename"),
                        highlights=[query_lower],
                    )
                )

        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Paginate
        total = len(results)
        paginated = results[offset : offset + limit]

        return SearchResponse(
            query=q,
            total_results=total,
            offset=offset,
            limit=limit,
            results=paginated,
            filters_applied=filters,
        )

    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics Endpoints
# ============================================================================


@router.get("/stats/timeline", response_model=TimelineStats)
async def get_timeline_stats(
    granularity: str = Query("year", description="Time granularity: year or month")
):
    """
    Get document timeline statistics.

    Args:
        granularity: Time granularity (year or month)

    Returns:
        TimelineStats with document counts over time
    """
    valid_granularities = ["year", "month"]
    if granularity not in valid_granularities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid granularity. Must be one of: {', '.join(valid_granularities)}",
        )

    try:
        generator = _get_wiki_generator()
        stats_engine = StatisticsEngine(_get_db())

        # Get timeline data
        all_stats = stats_engine.calculate_all_statistics()
        timeline_data = all_stats.get("timeline_stats", {})

        if granularity == "year":
            by_period = timeline_data.get("by_year", {})
        else:
            by_period = timeline_data.get("by_month", {})

        # Convert to data points
        data_points = []
        for period, count in sorted(by_period.items()):
            data_points.append(
                TimelineDataPoint(
                    period=period,
                    count=count,
                    label=period,
                )
            )

        return TimelineStats(
            granularity=granularity,
            data=data_points,
            total_count=sum(by_period.values()),
            date_range={
                "earliest": timeline_data.get("earliest_date"),
                "latest": timeline_data.get("latest_date"),
            },
        )

    except Exception as e:
        logger.error(f"Error getting timeline stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-authority", response_model=list[TopEntity])
async def get_stats_by_authority():
    """
    Get document counts grouped by authority.

    Returns:
        List of authorities with document counts
    """
    try:
        db = _get_db()
        conn = db._get_connection()

        cursor = conn.execute(
            """
            SELECT concept_name, document_count
            FROM concepts
            WHERE concept_type = 'authority'
            ORDER BY document_count DESC
            """
        )

        total_docs = sum(row[1] for row in cursor.fetchall())
        cursor = conn.execute(
            """
            SELECT concept_name, document_count
            FROM concepts
            WHERE concept_type = 'authority'
            ORDER BY document_count DESC
            """
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                TopEntity(
                    name=row[0],
                    count=row[1],
                    percentage=round((row[1] / total_docs * 100), 2) if total_docs > 0 else 0,
                )
            )

        return results

    except Exception as e:
        logger.error(f"Error getting authority stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-violation", response_model=list[TopEntity])
async def get_stats_by_violation():
    """
    Get document counts grouped by violation type.

    Returns:
        List of violation types with document counts
    """
    try:
        db = _get_db()
        conn = db._get_connection()

        cursor = conn.execute(
            """
            SELECT concept_name, document_count
            FROM concepts
            WHERE concept_type = 'violation'
            ORDER BY document_count DESC
            """
        )

        total_docs = sum(row[1] for row in cursor.fetchall())
        cursor = conn.execute(
            """
            SELECT concept_name, document_count
            FROM concepts
            WHERE concept_type = 'violation'
            ORDER BY document_count DESC
            """
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                TopEntity(
                    name=row[0],
                    count=row[1],
                    percentage=round((row[1] / total_docs * 100), 2) if total_docs > 0 else 0,
                )
            )

        return results

    except Exception as e:
        logger.error(f"Error getting violation stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Wiki Management Endpoints
# ============================================================================


@router.post("/rebuild", response_model=WikiRebuildResponse)
async def rebuild_wiki(
    clear_existing: bool = Query(False, description="Clear existing wiki data"),
    include_relationships: bool = Query(True, description="Detect document relationships"),
    relationship_threshold: float = Query(0.3, ge=0, le=1, description="Relationship strength threshold"),
):
    """
    Rebuild the entire wiki from document metadata.

    Args:
        clear_existing: Whether to clear existing wiki data
        include_relationships: Whether to detect relationships
        relationship_threshold: Minimum relationship strength (0.0-1.0)

    Returns:
        WikiRebuildResponse with rebuild results
    """
    try:
        start_time = time.time()

        generator = _get_wiki_generator()
        results = generator.generate_wiki(
            clear_existing=clear_existing,
            include_relationships=include_relationships,
            relationship_threshold=relationship_threshold,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return WikiRebuildResponse(
            success=results["success"],
            rebuild_time_ms=elapsed_ms,
            categories_created=results["phases"]["categories"]["total_categories"],
            documents_categorized=results["phases"]["statistics"]["summary"]["with_metadata"],
            relationships_detected=results["phases"]["relationships"]["count"],
            statistics_updated=True,
            message=f"Wiki rebuilt successfully in {elapsed_ms}ms",
        )

    except Exception as e:
        logger.error(f"Error rebuilding wiki: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-stats", response_model=StatsRefreshResponse)
async def refresh_statistics():
    """
    Refresh cached wiki statistics.

    Returns:
        StatsRefreshResponse with update status
    """
    try:
        stats_engine = StatisticsEngine(_get_db())

        # Recalculate and store statistics
        statistics = stats_engine.calculate_all_statistics()
        stats_engine.store_statistics(statistics)

        return StatsRefreshResponse(
            success=True,
            statistics_updated=True,
            cached_at=statistics.get("generated_at", ""),
            message="Statistics refreshed successfully",
        )

    except Exception as e:
        logger.error(f"Error refreshing statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
