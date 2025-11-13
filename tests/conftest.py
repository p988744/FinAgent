"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from finagent.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return {
        "text": "玉山銀行在2020年因洗錢防制違規受到什麼處分？",
        "max_results": 5,
        "include_full_documents": False,
    }
