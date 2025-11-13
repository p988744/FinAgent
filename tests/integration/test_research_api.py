"""Integration tests for research API."""

import pytest


@pytest.mark.integration
def test_submit_query_sync(client, sample_query):
    """Test synchronous query submission."""
    response = client.post("/api/v1/research/query/sync", json=sample_query)

    assert response.status_code == 200
    data = response.json()

    # Verify answer structure
    assert "executive_summary" in data
    assert "key_findings" in data
    assert "detailed_analysis" in data
    assert "citations" in data
    assert "confidence_score" in data
    assert "confidence_explanation" in data

    # Verify citations
    assert len(data["citations"]) > 0
    citation = data["citations"][0]
    assert "id" in citation
    assert "type" in citation
    assert "authority" in citation
    assert "formatted_citation" in citation


@pytest.mark.integration
def test_submit_query_async(client, sample_query):
    """Test asynchronous query submission."""
    # Submit query
    response = client.post("/api/v1/research/query", json=sample_query)

    assert response.status_code == 202
    data = response.json()
    assert "query_id" in data
    assert data["status"] in ["completed", "processing"]

    # Retrieve results
    query_id = data["query_id"]
    response = client.get(f"/api/v1/research/query/{query_id}")

    assert response.status_code == 200
    result = response.json()
    assert "executive_summary" in result


@pytest.mark.integration
def test_query_not_found(client):
    """Test retrieving non-existent query."""
    response = client.get("/api/v1/research/query/nonexistent-id")
    assert response.status_code == 404
