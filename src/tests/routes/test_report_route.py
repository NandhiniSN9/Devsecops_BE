"""Tests for report generation route endpoint."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app
from src.services.dependencies import get_report_service


@pytest.fixture
def mock_report_service():
    """Create a mock report service."""
    service = AsyncMock()
    service.generate_reports = AsyncMock(
        return_value={"status": "completed", "specializations_processed": 3}
    )
    return service


@pytest.fixture
def client(mock_report_service):
    """Create a test client with mocked report service."""
    app.dependency_overrides[get_report_service] = lambda: mock_report_service
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


class TestGenerateReportsEndpoint:
    """Tests for GET /api/v1/reports/generate endpoint."""

    def test_generate_reports_success(self, client, mock_report_service):
        """Should return 200 with success message when reports are generated."""
        response = client.get("/api/v1/reports/generate")

        assert response.status_code == 200
        data = response.json()
        assert data["status_code"] == 200
        assert data["status"] == "success"
        assert data["message"] == "Email sent successfully"
        mock_report_service.generate_reports.assert_called_once()

    def test_generate_reports_server_error(self, client, mock_report_service):
        """Should return 500 when an unhandled exception occurs."""
        mock_report_service.generate_reports.side_effect = RuntimeError("PDF generation failed")

        response = client.get("/api/v1/reports/generate")

        assert response.status_code == 500
        data = response.json()
        assert data["status_code"] == 500
        assert data["status"] == "error"

    def test_generate_reports_no_body_required(self, client, mock_report_service):
        """Should accept request without any body."""
        response = client.get("/api/v1/reports/generate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_generate_reports_method_not_allowed(self, client):
        """Should return 405 for POST requests."""
        response = client.post("/api/v1/reports/generate")

        assert response.status_code == 405

    def test_generate_reports_response_data_is_empty_list(self, client, mock_report_service):
        """Should return data as empty list on success."""
        response = client.get("/api/v1/reports/generate")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
