"""Unit tests for repository detail route endpoint."""

from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.response.base_response import BaseResponse
from src.routes.repository_detail_route import router
from src.services.dependencies import get_repository_detail_service
from src.services.repository_detail_service import RepositoryDetailService


@pytest.fixture
def mock_repository_detail_service():
    """Create a mock RepositoryDetailService."""
    return AsyncMock(spec=RepositoryDetailService)


@pytest.fixture
def app(mock_repository_detail_service):
    """Create a FastAPI test app with repository_detail router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_repository_detail_service] = lambda: mock_repository_detail_service
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestGetRepositoryDetail:
    """Tests for GET /api/v1/repositories/{repository_id} endpoint."""

    def test_get_repository_detail_success_returns_200(
        self, client, mock_repository_detail_service
    ):
        """Should return 200 with repository detail data."""
        repository_id = uuid.uuid4()
        mock_repository_detail_service.get_repository_detail.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Repository details retrieved successfully",
            data={
                "repository_id": str(repository_id),
                "repo_name": "test-repo",
                "status": "Active",
            },
        )

        response = client.get(f"/api/v1/repositories/{repository_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "data" in body

    def test_get_repository_detail_calls_service_with_correct_id(
        self, client, mock_repository_detail_service
    ):
        """Should pass repository_id to service."""
        repository_id = uuid.uuid4()
        mock_repository_detail_service.get_repository_detail.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Success",
            data={},
        )

        client.get(f"/api/v1/repositories/{repository_id}")

        mock_repository_detail_service.get_repository_detail.assert_called_once_with(
            repository_id=repository_id
        )

    def test_get_repository_detail_not_found_returns_404(
        self, client, mock_repository_detail_service
    ):
        """Should return 404 when repository not found."""
        from src.utils.exceptions.exceptions import NotFoundError

        repository_id = uuid.uuid4()
        mock_repository_detail_service.get_repository_detail.side_effect = NotFoundError(
            "Repository not found"
        )

        response = client.get(f"/api/v1/repositories/{repository_id}")

        assert response.status_code == 404

    def test_get_repository_detail_invalid_uuid_returns_422(
        self, client, mock_repository_detail_service
    ):
        """Should return 422 for invalid UUID format."""
        response = client.get("/api/v1/repositories/invalid-uuid")

        assert response.status_code == 422

    def test_get_repository_detail_includes_all_sections(
        self, client, mock_repository_detail_service
    ):
        """Should return data with all expected sections."""
        repository_id = uuid.uuid4()
        mock_repository_detail_service.get_repository_detail.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Success",
            data={
                "header": {},
                "pipeline_metrics": {},
                "adoption_timeline": [],
                "pipeline_activity": [],
                "commits": [],
                "pull_requests": [],
                "security_scans": [],
                "build_artifacts": [],
            },
        )

        response = client.get(f"/api/v1/repositories/{repository_id}")

        assert response.status_code == 200
        body = response.json()
        data = body["data"]
        assert "header" in data
        assert "pipeline_metrics" in data
        assert "adoption_timeline" in data
