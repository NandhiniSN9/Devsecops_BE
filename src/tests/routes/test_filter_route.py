"""Unit tests for the filter route endpoint.

Tests verify the route handler correctly delegates to FilterService
and returns a properly structured BaseResponse with Cache-Control header.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.response.filter_response import FilterItemResponse, FiltersDataResponse
from src.routes.filter_route import router
from src.services.dependencies import get_filter_service
from src.services.filter_service import FilterService


@pytest.fixture
def mock_filter_service():
    """Create a mock FilterService."""
    return AsyncMock(spec=FilterService)


@pytest.fixture
def sample_filters_data():
    """Create sample FiltersDataResponse for testing."""
    return FiltersDataResponse(
        specializations=[
            FilterItemResponse(id="uuid-spec-1", name="AppSec"),
            FilterItemResponse(id="uuid-spec-2", name="CloudSec"),
        ],
        clients=[
            FilterItemResponse(id="uuid-client-1", name="Acme Corp"),
            FilterItemResponse(id="uuid-client-2", name="Beta Inc"),
        ],
        statuses=[
            FilterItemResponse(id="uuid-status-1", name="Active"),
            FilterItemResponse(id="uuid-status-2", name="Completed"),
            FilterItemResponse(id="uuid-status-3", name="Inactive"),
        ],
    )


@pytest.fixture
def app(mock_filter_service):
    """Create a FastAPI test app with the filter router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_filter_service] = lambda: mock_filter_service
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestGetFiltersRoute:
    """Tests for GET /api/v1/filters endpoint."""

    def test_success_returns_200_with_base_response(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Successful request returns 200 with BaseResponse structure."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        assert response.status_code == 200
        body = response.json()
        assert body["status_code"] == 200
        assert body["status"] == "success"
        assert body["message"] == "Filters retrieved successfully"
        assert body["data"] is not None

    def test_response_contains_specializations(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Response data contains specializations array."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        data = response.json()["data"]
        assert "specializations" in data
        assert len(data["specializations"]) == 2
        assert data["specializations"][0]["id"] == "uuid-spec-1"
        assert data["specializations"][0]["name"] == "AppSec"

    def test_response_contains_clients(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Response data contains clients array."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        data = response.json()["data"]
        assert "clients" in data
        assert len(data["clients"]) == 2
        assert data["clients"][0]["id"] == "uuid-client-1"
        assert data["clients"][0]["name"] == "Acme Corp"

    def test_response_contains_statuses(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Response data contains statuses array."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        data = response.json()["data"]
        assert "statuses" in data
        assert len(data["statuses"]) == 3
        assert data["statuses"][0]["name"] == "Active"

    def test_response_has_cache_control_header(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Response includes Cache-Control header with max-age."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        assert "cache-control" in response.headers
        assert "max-age=" in response.headers["cache-control"]

    def test_cache_control_header_value(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Cache-Control header has max-age=3600."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        assert response.headers["cache-control"] == "max-age=3600"

    def test_response_matches_base_response_format(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Response body matches BaseResponse format with all required fields."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        body = response.json()
        assert "status_code" in body
        assert "status" in body
        assert "message" in body
        assert "data" in body
        assert isinstance(body["status_code"], int)
        assert body["status"] in ("success", "failed", "error")

    def test_response_content_type_is_json(
        self, client, mock_filter_service, sample_filters_data
    ):
        """Response Content-Type is application/json."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        response = client.get("/api/v1/filters")

        assert "application/json" in response.headers["content-type"]

    def test_empty_filters_returns_empty_arrays(self, client, mock_filter_service):
        """Empty filter data returns 200 with empty arrays."""
        empty_data = FiltersDataResponse(
            specializations=[],
            clients=[],
            statuses=[],
        )
        mock_filter_service.get_filters.return_value = empty_data

        response = client.get("/api/v1/filters")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["specializations"] == []
        assert data["clients"] == []
        assert data["statuses"] == []

    def test_service_called_once(
        self, client, mock_filter_service, sample_filters_data
    ):
        """FilterService.get_filters is called exactly once per request."""
        mock_filter_service.get_filters.return_value = sample_filters_data

        client.get("/api/v1/filters")

        mock_filter_service.get_filters.assert_called_once()
