"""API client for communicating with FinAgent backend."""

import os
from typing import Optional

import httpx
from pydantic import ValidationError

from finagent.models.answers import LegalAnswer
from finagent.models.queries import Query, QueryResponse


class ApiClient:
    """Client for FinAgent backend API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0):
        """
        Initialize API client.

        Args:
            base_url: Backend API base URL (defaults to env var or localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("FINAGENT_API_URL", "http://localhost:8000")
        self.timeout = timeout
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def check_health(self) -> bool:
        """
        Check if backend is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    def submit_query_sync(self, query: Query) -> LegalAnswer:
        """
        Submit a query synchronously and wait for results.

        Args:
            query: Query object

        Returns:
            LegalAnswer

        Raises:
            httpx.HTTPError: If request fails
            ValidationError: If response validation fails
        """
        # Convert query to dict
        query_data = query.model_dump(exclude_none=True)

        # Submit to sync endpoint
        response = self.client.post("/api/v1/research/query/sync", json=query_data)
        response.raise_for_status()

        # Parse response
        answer_data = response.json()
        return LegalAnswer(**answer_data)

    def submit_query_async(self, query: Query) -> str:
        """
        Submit a query asynchronously.

        Args:
            query: Query object

        Returns:
            Query ID for retrieving results later

        Raises:
            httpx.HTTPError: If request fails
        """
        query_data = query.model_dump(exclude_none=True)

        response = self.client.post("/api/v1/research/query", json=query_data)
        response.raise_for_status()

        # Parse response
        query_response = QueryResponse(**response.json())
        return query_response.query_id

    def get_query_result(self, query_id: str) -> Optional[LegalAnswer]:
        """
        Retrieve results for an async query.

        Args:
            query_id: Query ID from submit_query_async

        Returns:
            LegalAnswer if available, None if still processing

        Raises:
            httpx.HTTPError: If request fails (except 404)
        """
        try:
            response = self.client.get(f"/api/v1/research/query/{query_id}")
            response.raise_for_status()

            answer_data = response.json()
            return LegalAnswer(**answer_data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_api_info(self) -> dict:
        """
        Get API information.

        Returns:
            API info dict
        """
        response = self.client.get("/")
        response.raise_for_status()
        return response.json()
