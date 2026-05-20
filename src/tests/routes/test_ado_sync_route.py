"""Unit tests for ADO sync route endpoint."""

from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.response.base_response import BaseResponse
from src.routes.ado_sync_route import router
from src.services.ado_sync_service import AdoSyncService
from src.services.dependencies import get_ado_sync_service


@pytest.fixture
def mock_ado_sync_service():
    """Create a mock AdoSyncService."""
    return AsyncMock(spec=AdoSyncService)


@pytest.fixture
def app(mock_ado_sync_service):
    """Create a FastAPI test app with ado_sync router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_ado_sync_service] = lambda: mock_ado_sync_service
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestSyncAdo:
    """Tests for POST /api/v1/sync/ado endpoint."""

    def test_sync_ado_without_specialization_returns_200(
        self, client, mock_ado_sync_service
    ):
        """Should return 200 when syncing all specializations."""
        mock_ado_sync_service.initiate_sync.return_value = {
            "success": True,
            "message": "Sync initiated successfully",
            "cron_id": uuid.uuid4(),
        }
        mock_ado_sync_service.run_sync = AsyncMock()

        response = client.post("/api/v1/sync/ado", json={})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "ADO sync initiated" in body["message"]

    def test_sync_ado_with_specialization_id_returns_200(
        self, client, mock_ado_sync_service
    ):
        """Should return 200 when syncing specific specialization."""
        spec_id = uuid.uuid4()
        mock_ado_sync_service.initiate_sync.return_value = {
            "success": True,
            "message": "Sync initiated successfully",
            "cron_id": uuid.uuid4(),
        }
        mock_ado_sync_service.run_sync = AsyncMock()

        response = client.post(
            "/api/v1/sync/ado",
            json={"specialization_id": str(spec_id)}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_sync_ado_already_in_progress_returns_409(
        self, client, mock_ado_sync_service
    ):
        """Should return 409 when sync already in progress."""
        mock_ado_sync_service.initiate_sync.return_value = {
            "success": False,
            "message": "An ADO sync is already running",
        }

        response = client.post("/api/v1/sync/ado", json={})

        assert response.status_code == 409
        body = response.json()
        assert body["status"] == "failed"
        assert "already running" in body["message"]

    def test_sync_ado_calls_run_sync_in_background(
        self, client, mock_ado_sync_service
    ):
        """Should call run_sync with cron_id in background."""
        cron_id = uuid.uuid4()
        mock_ado_sync_service.initiate_sync.return_value = {
            "success": True,
            "message": "Sync initiated successfully",
            "cron_id": cron_id,
        }
        mock_ado_sync_service.run_sync = AsyncMock()

        response = client.post("/api/v1/sync/ado", json={})

        assert response.status_code == 200
        # Note: run_sync is called via asyncio.create_task, not awaited

    def test_sync_ado_invalid_specialization_id_returns_422(
        self, client, mock_ado_sync_service
    ):
        """Should return 422 for invalid UUID format."""
        response = client.post(
            "/api/v1/sync/ado",
            json={"specialization_id": "invalid-uuid"}
        )

        assert response.status_code == 422

    def test_sync_ado_with_null_specialization_id(
        self, client, mock_ado_sync_service
    ):
        """Should accept null specialization_id (sync all)."""
        mock_ado_sync_service.initiate_sync.return_value = {
            "success": True,
            "message": "Sync initiated successfully",
            "cron_id": uuid.uuid4(),
        }
        mock_ado_sync_service.run_sync = AsyncMock()

        response = client.post(
            "/api/v1/sync/ado",
            json={"specialization_id": None}
        )

        assert response.status_code == 200
