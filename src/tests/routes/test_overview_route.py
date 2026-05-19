"""Unit tests for the overview route endpoint.

Tests verify the route handler correctly delegates to OverviewService
and returns a properly structured BaseResponse.
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
from src.utils.exceptions.exception_handlers import register_exception_handlers


@pytest.fixture
def mock_overview_service():
    """Create a mock OverviewService."""
    return AsyncMock(spec=OverviewService)


@pytest.fixture
def sample_overview_data():
    """Create sample OverviewDataResponse for testing with all 7 metrics."""
    return OverviewDataResponse(
        sync_detail=SyncDetailResponse(
            last_sync_datetime="18 May 2026, 09:30",
            is_sync_in_progress=False,
        ),
        metrics=OverviewMetricsResponse(
            total_projects=KpiTileResponse(count=10, trend="increase", change=2),
            adopted=KpiTileResponse(count=4, trend="increase", change=1),
            completed=KpiTileResponse(count=3, trend="flat", change=0),
            active=KpiTileResponse(count=2, trend="decrease", change=1),
            inactive=KpiTileResponse(count=1, trend="flat", change=0),
            at_risk=KpiTileResponse(count=0, trend="flat", change=0),
            not_applicable=KpiTileResponse(count=0, trend="flat", change=0),
        ),
        status_distribution=StatusDistributionResponse(
            total=10,
            breakdown=[
                StatusBreakdownItemResponse(status="Adopted", count=4, percentage=40.0),
                StatusBreakdownItemResponse(status="Active", count=2, percentage=20.0),
                StatusBreakdownItemResponse(status="Completed", count=3, percentage=30.0),
                StatusBreakdownItemResponse(status="Inactive", count=1, percentage=10.0),
                StatusBreakdownItemResponse(status="At Risk", count=0, percentage=0.0),
                StatusBreakdownItemResponse(status="Not Applicable", count=0, percentage=0.0),
            ],
        ),
    )


@pytest.fixture
def app(mock_overview_service):
    """Create a FastAPI test app with the overview router."""
    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_overview_service] = lambda: mock_overview_service
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestGetOverviewRoute:
    """Tests for GET /api/v1/overview endpoint."""

    def test_success_returns_200_with_base_response(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Successful request returns 200 with BaseResponse structure."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        assert response.status_code == 200
        body = response.json()
        assert body["status_code"] == 200
        assert body["status"] == "success"
        assert body["message"] == "Overview data retrieved successfully"
        assert body["data"] is not None

    def test_response_data_contains_sync_detail_metrics_status_distribution(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Response data contains sync_detail, metrics, and status_distribution."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        data = response.json()["data"]
        assert "sync_detail" in data
        assert "metrics" in data
        assert "status_distribution" in data

    def test_response_metrics_contains_all_7_tiles(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Response metrics contains all 7 KPI tiles including adopted."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        metrics = response.json()["data"]["metrics"]
        expected_keys = [
            "total_projects", "adopted", "completed",
            "active", "inactive", "at_risk", "not_applicable",
        ]
        for key in expected_keys:
            assert key in metrics, f"Missing metric: {key}"
            assert "count" in metrics[key]
            assert "trend" in metrics[key]
            assert "change" in metrics[key]

    def test_period_query_param_passed_to_service(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Period query parameter is passed to the service."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview?period=last_month")

        mock_overview_service.get_overview.assert_called_once_with("last_month", None)

    def test_specialization_query_param_passed_to_service(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Specialization query parameter is passed to the service."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview?specialization=abc-123,def-456")

        mock_overview_service.get_overview.assert_called_once_with(None, "abc-123,def-456")

    def test_both_params_passed_to_service(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Both period and specialization params are passed to the service."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview?period=last_week&specialization=uuid1,uuid2")

        mock_overview_service.get_overview.assert_called_once_with("last_week", "uuid1,uuid2")

    def test_no_params_passes_none(
        self, client, mock_overview_service, sample_overview_data
    ):
        """No query params passes None for both period and specialization."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        client.get("/api/v1/overview")

        mock_overview_service.get_overview.assert_called_once_with(None, None)

    def test_response_content_type_is_json(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Response Content-Type is application/json."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        assert "application/json" in response.headers["content-type"]

    def test_service_error_returns_500(self, client, mock_overview_service):
        """Service error returns 500 with error status."""
        mock_overview_service.get_overview.side_effect = RuntimeError("Database connection failed")

        response = client.get("/api/v1/overview")

        assert response.status_code == 500

    def test_data_field_contains_correct_values(
        self, client, mock_overview_service, sample_overview_data
    ):
        """Data field contains the correct model_dump() output."""
        mock_overview_service.get_overview.return_value = sample_overview_data

        response = client.get("/api/v1/overview")

        data = response.json()["data"]
        assert data["metrics"]["total_projects"]["count"] == 10
        assert data["metrics"]["adopted"]["count"] == 4
        assert data["metrics"]["adopted"]["trend"] == "increase"
        assert data["status_distribution"]["total"] == 10
        assert data["sync_detail"]["is_sync_in_progress"] is False
        assert data["sync_detail"]["last_sync_datetime"] == "18 May 2026, 09:30"
