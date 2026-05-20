"""Unit tests for settings route endpoints."""

from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.response.base_response import BaseResponse
from src.models.response.settings_response import SettingsDataResponse
from src.routes.settings_route import router
from src.services.dependencies import get_settings_service
from src.services.settings_service import SettingsService


@pytest.fixture
def mock_settings_service():
    """Create a mock SettingsService."""
    return AsyncMock(spec=SettingsService)


@pytest.fixture
def app(mock_settings_service):
    """Create a FastAPI test app with settings router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_settings_service] = lambda: mock_settings_service
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_settings_response():
    """Create sample settings response."""
    return BaseResponse(
        status_code=200,
        status="success",
        message="Settings retrieved successfully",
        data=SettingsDataResponse(
            setting_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            specialization_name="DevSecOps",
            at_risk_threshold=30,
            email_digest="weekly",
            at_risk_alert="daily",
            email_recipients=[],
        ),
    )


class TestGetSettings:
    """Tests for GET /api/v1/settings/{specialization_id} endpoint."""

    def test_get_settings_success_returns_200(
        self, client, mock_settings_service, sample_settings_response
    ):
        """Should return 200 with settings data."""
        specialization_id = uuid.uuid4()
        mock_settings_service.get_settings.return_value = sample_settings_response

        response = client.get(f"/api/v1/settings/{specialization_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["status_code"] == 200
        assert body["status"] == "success"
        assert "data" in body

    def test_get_settings_calls_service_with_correct_id(
        self, client, mock_settings_service, sample_settings_response
    ):
        """Should pass specialization_id to service."""
        specialization_id = uuid.uuid4()
        mock_settings_service.get_settings.return_value = sample_settings_response

        client.get(f"/api/v1/settings/{specialization_id}")

        mock_settings_service.get_settings.assert_called_once_with(
            specialization_id=specialization_id
        )

    def test_get_settings_invalid_uuid_returns_422(
        self, client, mock_settings_service
    ):
        """Should return 422 for invalid UUID format."""
        response = client.get("/api/v1/settings/invalid-uuid")

        assert response.status_code == 422


class TestUpdateSettings:
    """Tests for PUT /api/v1/settings/manage endpoint."""

    def test_update_settings_success_returns_200(
        self, client, mock_settings_service
    ):
        """Should return 200 when settings updated successfully."""
        mock_settings_service.update_settings.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Settings updated successfully",
            data=None,
        )

        payload = {
            "specialization_id": str(uuid.uuid4()),
            "at_risk_threshold": 45,
            "email_digest": "daily",
            "at_risk_alert": "bi-weekly",
        }

        response = client.put("/api/v1/settings/manage", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_update_settings_with_recipients(
        self, client, mock_settings_service
    ):
        """Should handle email_recipients in payload."""
        mock_settings_service.update_settings.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Settings updated successfully",
            data=None,
        )

        payload = {
            "specialization_id": str(uuid.uuid4()),
            "email_recipients": [
                {"action": "add", "email": "new@example.com"},
                {"action": "remove", "email_recipient_id": str(uuid.uuid4())},
            ],
        }

        response = client.put("/api/v1/settings/manage", json=payload)

        assert response.status_code == 200

    def test_update_settings_partial_update(
        self, client, mock_settings_service
    ):
        """Should allow partial updates (only changed fields)."""
        mock_settings_service.update_settings.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Settings updated successfully",
            data=None,
        )

        payload = {
            "specialization_id": str(uuid.uuid4()),
            "at_risk_threshold": 60,  # Only update threshold
        }

        response = client.put("/api/v1/settings/manage", json=payload)

        assert response.status_code == 200

    def test_update_settings_invalid_payload_returns_422(
        self, client, mock_settings_service
    ):
        """Should return 422 for invalid payload."""
        payload = {
            "specialization_id": "invalid-uuid",
        }

        response = client.put("/api/v1/settings/manage", json=payload)

        assert response.status_code == 422

    def test_update_settings_missing_specialization_id_returns_422(
        self, client, mock_settings_service
    ):
        """Should return 422 when specialization_id is missing."""
        payload = {
            "at_risk_threshold": 30,
        }

        response = client.put("/api/v1/settings/manage", json=payload)

        assert response.status_code == 422
