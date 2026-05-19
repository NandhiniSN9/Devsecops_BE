"""Unit tests for the overview route endpoint.

Tests verify the route handler correctly delegates to OverviewService
and returns a properly structured BaseResponse.

Validates: Requirements 1.1, 1.9, 1.11, 10.1, 10.2, 12.1
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.response.overview_response import (
    KpiTileResponse,
    OverviewDataResponse,
    OverviewMetricsResponse,
    StatusBreakdownItemResponse,
    StatusDistributionResponse,
    SyncDetailResponse,
)
from src.routes.overview_route import router
from src.services.dependencies import get_overview_service
from src.services.overview_service import OverviewService


@pytest.fixture
def mock_overview_service():
    """Create a mock OverviewService."""
    return AsyncMock(spec=OverviewService)


@pytest.fixture
def sample_overview_data():
    """Create sample OverviewDataResponse for testing."""
    return OverviewDataResponse(
        sync_detail=SyncDetailResponse(
            last_sync_datetime="18 May 2026, 09:30",
            is_sync_in_progress=False,
        ),
        metrics=OverviewMetricsResponse(
            total_projects=KpiTileResponse(count=10, trend="increase", change=2),
            completed=KpiTileResponse(count=5, trend="increase", change=1),
            active=KpiTileResponse(count=3, trend="decrease", change=1),
            inactive=KpiTileResponse(count=1, trend="flat", change=0),
            at_risk=KpiTileResponse(count=1, trend="increase", change=1),
            not_applicable=KpiTileResponse(count=0, trend="flat", change=0),
        ),
        status_distribution=StatusDistributionResponse(
            total=10,
            breakdown=[
                StatusBreakdownItemResponse(status="Active", count=7, percentage=70.0),
                StatusBreakdownItemResponse(status="Completed", count=3, percentage=30.0),
            ],
        ),
    )


@pytest.fixture
def app(mock_overview_service):
    """Create a FastAPI test app with the overview router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")

    # Override the dependency to use our mock
    test_app.dependency_overrides[get_overview_service] = lambda: mock_overview_service

    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestGetOverviewRoute:
    """Tests for GET /api/v1/overview endpoint."""

    def test_success_returns_200_with_base_response(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Successful request returns 200 with BaseResponse structure.

        Validates: Requirements 1.1, 10.1, 10.2
        """
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        assert response.status_code == 200
        body = response.json()
        assert body["status_code"] == 200
        assert body["status"] == "success"
        assert body["message"] == "Overview data retrieved successfully"
        assert body["data"] is not None

    def test_response_data_contains_metrics(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Response data contains metrics, status_distribution, and sync_detail.

        Validates: Requirements 1.1, 10.2
        """
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        data = response.json()["data"]
        assert "metrics" in data
        assert "status_distribution" in data
        assert "sync_detail" in data

    def test_period_query_param_passed_to_service(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Period query parameter is passed to the service."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview?period=last_month")

        mock_overview_service.get_overview.assert_called_once_with("last_month")

    def test_specialization_query_param_ignored(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Specialization query parameter is no longer passed to the service."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview?specialization=abc,def")

        mock_overview_service.get_overview.assert_called_once_with(None)

    def test_period_param_passed_to_service(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Period param is passed to the service; specialization is ignored."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview?period=last_week&specialization=uuid1,uuid2")

        mock_overview_service.get_overview.assert_called_once_with("last_week")

    def test_no_params_passes_none_to_service(
        self, client, mock_overview_service, sample_overview_data
    ):
        """No query params passes None for period."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview")

        mock_overview_service.get_overview.assert_called_once_with(None)

    def test_response_content_type_is_json(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Response Content-Type is application/json.

        Validates: Requirements 10.1
        """
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        assert "application/json" in response.headers["content-type"]

    def test_data_field_contains_model_dump(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Data field contains the model_dump() output of OverviewDataResponse."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        data = response.json()["data"]
        assert data["metrics"]["total_projects"]["count"] == 10
        assert data["metrics"]["total_projects"]["trend"] == "increase"
        assert data["metrics"]["total_projects"]["change"] == 2
        assert data["status_distribution"]["total"] == 10
        assert data["sync_detail"]["is_sync_in_progress"] is False
