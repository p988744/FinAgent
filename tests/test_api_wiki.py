"""
Integration Tests for Wiki REST API

Tests all wiki endpoints including:
- Wiki overview
- Category browsing
- Document management
- Search functionality
- Statistics endpoints
- Wiki operations
"""

import pytest
from fastapi.testclient import TestClient

from finagent.main import app

client = TestClient(app)


# ============================================================================
# Wiki Overview Tests
# ============================================================================


def test_get_wiki_overview():
    """Test GET /api/v1/wiki/overview endpoint."""
    response = client.get("/api/v1/wiki/overview")

    assert response.status_code == 200
    data = response.json()

    # Verify required fields
    assert "total_documents" in data
    assert "total_categories" in data
    assert "categories_by_type" in data
    assert "document_stats" in data
    assert "recent_documents" in data
    assert "top_entities" in data

    # Verify types
    assert isinstance(data["total_documents"], int)
    assert isinstance(data["total_categories"], int)
    assert isinstance(data["categories_by_type"], dict)
    assert isinstance(data["recent_documents"], list)

    # Verify categories_by_type has expected keys
    assert set(data["categories_by_type"].keys()).issubset(
        {"authority", "institution", "violation", "doc_type"}
    )


# ============================================================================
# Category Endpoints Tests
# ============================================================================


def test_get_categories_authority():
    """Test GET /api/v1/wiki/categories with type=authority."""
    response = client.get("/api/v1/wiki/categories?type=authority")

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "authority"
    assert "total_count" in data
    assert "categories" in data
    assert isinstance(data["categories"], list)

    # Verify category structure
    if data["categories"]:
        category = data["categories"][0]
        assert "id" in category
        assert "name" in category
        assert "type" in category
        assert "document_count" in category
        assert category["type"] == "authority"


def test_get_categories_institution():
    """Test GET /api/v1/wiki/categories with type=institution."""
    response = client.get("/api/v1/wiki/categories?type=institution")

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "institution"
    assert isinstance(data["categories"], list)


def test_get_categories_violation():
    """Test GET /api/v1/wiki/categories with type=violation."""
    response = client.get("/api/v1/wiki/categories?type=violation")

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "violation"
    assert isinstance(data["categories"], list)


def test_get_categories_doc_type():
    """Test GET /api/v1/wiki/categories with type=doc_type."""
    response = client.get("/api/v1/wiki/categories?type=doc_type")

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "doc_type"
    assert isinstance(data["categories"], list)


def test_get_categories_invalid_type():
    """Test GET /api/v1/wiki/categories with invalid type."""
    response = client.get("/api/v1/wiki/categories?type=invalid")

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_get_categories_missing_type():
    """Test GET /api/v1/wiki/categories without type parameter."""
    response = client.get("/api/v1/wiki/categories")

    assert response.status_code == 422  # Validation error


def test_get_category_detail():
    """Test GET /api/v1/wiki/category/{category_id}."""
    # First get a valid category ID
    categories_response = client.get("/api/v1/wiki/categories?type=authority")
    categories = categories_response.json()["categories"]

    if categories:
        category_id = categories[0]["id"]

        response = client.get(f"/api/v1/wiki/category/{category_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify detailed fields
        assert "id" in data
        assert "name" in data
        assert "type" in data
        assert "document_count" in data
        assert "description" in data
        assert "keywords" in data
        assert "metadata" in data
        assert "created_at" in data
        assert "updated_at" in data

        assert data["id"] == category_id


def test_get_category_detail_not_found():
    """Test GET /api/v1/wiki/category/{category_id} with non-existent ID."""
    response = client.get("/api/v1/wiki/category/999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# ============================================================================
# Document Endpoints Tests
# ============================================================================


def test_get_documents_all():
    """Test GET /api/v1/wiki/documents without filters."""
    response = client.get("/api/v1/wiki/documents")

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "offset" in data
    assert "limit" in data
    assert "documents" in data

    assert isinstance(data["documents"], list)
    assert data["offset"] == 0
    assert data["limit"] == 20  # Default limit


def test_get_documents_pagination():
    """Test GET /api/v1/wiki/documents with pagination."""
    # Get first page
    response1 = client.get("/api/v1/wiki/documents?limit=5&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()

    # Get second page
    response2 = client.get("/api/v1/wiki/documents?limit=5&offset=5")
    assert response2.status_code == 200
    data2 = response2.json()

    assert data1["limit"] == 5
    assert data2["limit"] == 5
    assert data1["offset"] == 0
    assert data2["offset"] == 5

    # Verify different documents (if we have more than 5)
    if data1["total"] > 5:
        assert len(data1["documents"]) > 0
        assert len(data2["documents"]) > 0


def test_get_documents_by_category():
    """Test GET /api/v1/wiki/documents with category filter."""
    # Get a valid category ID first
    categories_response = client.get("/api/v1/wiki/categories?type=authority")
    categories = categories_response.json()["categories"]

    if categories:
        category_id = categories[0]["id"]

        response = client.get(f"/api/v1/wiki/documents?category_id={category_id}")

        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert isinstance(data["documents"], list)


def test_get_document_detail():
    """Test GET /api/v1/wiki/document/{doc_id}."""
    # Get a valid document ID first
    docs_response = client.get("/api/v1/wiki/documents?limit=1")
    docs = docs_response.json()["documents"]

    if docs:
        doc_id = docs[0]["doc_id"]

        response = client.get(f"/api/v1/wiki/document/{doc_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify detailed fields
        assert "doc_id" in data
        assert "filename" in data
        assert "file_path" in data
        assert "chunk_count" in data
        assert "indexed" in data
        assert "related_documents" in data

        assert data["doc_id"] == doc_id


def test_get_document_detail_no_content():
    """Test GET /api/v1/wiki/document/{doc_id} with include_content=false."""
    docs_response = client.get("/api/v1/wiki/documents?limit=1")
    docs = docs_response.json()["documents"]

    if docs:
        doc_id = docs[0]["doc_id"]

        response = client.get(f"/api/v1/wiki/document/{doc_id}?include_content=false")

        assert response.status_code == 200
        data = response.json()

        assert data["full_content"] is None


def test_get_document_detail_not_found():
    """Test GET /api/v1/wiki/document/{doc_id} with non-existent ID."""
    response = client.get("/api/v1/wiki/document/nonexistent_doc_id")

    assert response.status_code == 404


# ============================================================================
# Search Endpoint Tests
# ============================================================================


def test_search_documents():
    """Test GET /api/v1/wiki/search with query."""
    response = client.get("/api/v1/wiki/search?q=銀行")

    assert response.status_code == 200
    data = response.json()

    assert "query" in data
    assert "total_results" in data
    assert "offset" in data
    assert "limit" in data
    assert "results" in data
    assert "filters_applied" in data

    assert data["query"] == "銀行"
    assert isinstance(data["results"], list)

    # Verify search result structure
    if data["results"]:
        result = data["results"][0]
        assert "doc_id" in result
        assert "filename" in result
        assert "relevance_score" in result


def test_search_documents_with_filters():
    """Test GET /api/v1/wiki/search with filters."""
    response = client.get(
        "/api/v1/wiki/search?q=銀行&document_type=裁罰書&limit=5"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["limit"] == 5
    assert data["filters_applied"]["document_type"] == "裁罰書"


def test_search_documents_pagination():
    """Test GET /api/v1/wiki/search with pagination."""
    response = client.get("/api/v1/wiki/search?q=銀行&limit=3&offset=2")

    assert response.status_code == 200
    data = response.json()

    assert data["limit"] == 3
    assert data["offset"] == 2


def test_search_documents_no_query():
    """Test GET /api/v1/wiki/search without query parameter."""
    response = client.get("/api/v1/wiki/search")

    assert response.status_code == 422  # Validation error


# ============================================================================
# Statistics Endpoints Tests
# ============================================================================


def test_get_timeline_stats_year():
    """Test GET /api/v1/wiki/stats/timeline with granularity=year."""
    response = client.get("/api/v1/wiki/stats/timeline?granularity=year")

    assert response.status_code == 200
    data = response.json()

    assert "granularity" in data
    assert "data" in data
    assert "total_count" in data
    assert "date_range" in data

    assert data["granularity"] == "year"
    assert isinstance(data["data"], list)

    # Verify data point structure
    if data["data"]:
        point = data["data"][0]
        assert "period" in point
        assert "count" in point
        assert "label" in point


def test_get_timeline_stats_month():
    """Test GET /api/v1/wiki/stats/timeline with granularity=month."""
    response = client.get("/api/v1/wiki/stats/timeline?granularity=month")

    assert response.status_code == 200
    data = response.json()

    assert data["granularity"] == "month"


def test_get_timeline_stats_invalid_granularity():
    """Test GET /api/v1/wiki/stats/timeline with invalid granularity."""
    response = client.get("/api/v1/wiki/stats/timeline?granularity=invalid")

    assert response.status_code == 400


def test_get_stats_by_authority():
    """Test GET /api/v1/wiki/stats/by-authority."""
    response = client.get("/api/v1/wiki/stats/by-authority")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    # Verify entity structure
    if data:
        entity = data[0]
        assert "name" in entity
        assert "count" in entity
        assert "percentage" in entity
        assert isinstance(entity["count"], int)
        assert isinstance(entity["percentage"], (int, float))


def test_get_stats_by_violation():
    """Test GET /api/v1/wiki/stats/by-violation."""
    response = client.get("/api/v1/wiki/stats/by-violation")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if data:
        entity = data[0]
        assert "name" in entity
        assert "count" in entity
        assert "percentage" in entity


# ============================================================================
# Wiki Management Endpoints Tests
# ============================================================================


def test_refresh_stats():
    """Test POST /api/v1/wiki/refresh-stats."""
    response = client.post("/api/v1/wiki/refresh-stats")

    assert response.status_code == 200
    data = response.json()

    assert "success" in data
    assert "statistics_updated" in data
    assert "cached_at" in data
    assert "message" in data

    assert data["success"] is True
    assert data["statistics_updated"] is True


def test_rebuild_wiki_no_clear():
    """Test POST /api/v1/wiki/rebuild without clearing existing data."""
    response = client.post("/api/v1/wiki/rebuild?clear_existing=false")

    assert response.status_code == 200
    data = response.json()

    assert "success" in data
    assert "rebuild_time_ms" in data
    assert "categories_created" in data
    assert "documents_categorized" in data
    assert "relationships_detected" in data
    assert "statistics_updated" in data
    assert "message" in data

    assert data["success"] is True
    assert isinstance(data["rebuild_time_ms"], int)
    assert data["rebuild_time_ms"] > 0


def test_rebuild_wiki_with_relationships():
    """Test POST /api/v1/wiki/rebuild with relationship detection."""
    response = client.post(
        "/api/v1/wiki/rebuild?include_relationships=true&relationship_threshold=0.5"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "relationships_detected" in data


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_invalid_endpoint():
    """Test accessing non-existent wiki endpoint."""
    response = client.get("/api/v1/wiki/nonexistent")

    assert response.status_code == 404


def test_invalid_method():
    """Test using wrong HTTP method."""
    response = client.post("/api/v1/wiki/overview")  # Should be GET

    assert response.status_code == 405  # Method not allowed


# ============================================================================
# Performance Tests
# ============================================================================


def test_overview_performance():
    """Test that wiki overview responds within acceptable time."""
    import time

    start = time.time()
    response = client.get("/api/v1/wiki/overview")
    elapsed = (time.time() - start) * 1000  # Convert to ms

    assert response.status_code == 200
    assert elapsed < 500  # Should be under 500ms


def test_search_performance():
    """Test that search responds within acceptable time."""
    import time

    start = time.time()
    response = client.get("/api/v1/wiki/search?q=test")
    elapsed = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed < 500


# ============================================================================
# Data Consistency Tests
# ============================================================================


def test_category_document_count_consistency():
    """Test that category document counts match actual document counts."""
    # Get all categories
    categories_response = client.get("/api/v1/wiki/categories?type=authority")
    categories = categories_response.json()["categories"]

    for category in categories[:3]:  # Test first 3
        category_id = category["id"]
        expected_count = category["document_count"]

        # Get actual documents in category
        docs_response = client.get(
            f"/api/v1/wiki/documents?category_id={category_id}&limit=100"
        )
        actual_count = len(docs_response.json()["documents"])

        # Should match (or be close if paginated)
        assert actual_count <= expected_count


def test_total_documents_consistency():
    """Test that total document count is consistent across endpoints."""
    # Get count from overview
    overview_response = client.get("/api/v1/wiki/overview")
    overview_total = overview_response.json()["total_documents"]

    # Get count from documents list
    docs_response = client.get("/api/v1/wiki/documents")
    docs_total = docs_response.json()["total"]

    # Should match
    assert overview_total == docs_total


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
