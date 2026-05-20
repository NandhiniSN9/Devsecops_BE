"""Unit tests for projects route endpoints."""

from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.response.base_response import BaseResponse
from src.models.response.projects_response import ProjectsDataResponse
from src.routes.projects_route import router
from src.services.dependencies import get_projects_service
from src.services.projects_service import ProjectsService


@pytest.fixture
def mock_projects_service():
    """Create a mock ProjectsService."""
    return AsyncMock(spec=ProjectsService)


@pytest.fixture
def app(mock_projects_service):
    """Create a FastAPI test app with projects router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_projects_service] = lambda: mock_projects_service
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_projects_response():
    """Create sample ProjectsDataResponse."""
    return BaseResponse(
        status_code=200,
        status="success",
        message="Projects retrieved successfully",
        data=ProjectsDataResponse(
            projects=[],
            pagination={"total": 0, "offset": 0, "limit": 10},
        ),
    )


class TestGetProjects:
    """Tests for GET /api/v1/projects endpoint."""

    def test_get_projects_no_filters_returns_200(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should return 200 with projects list when no filters applied."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get("/api/v1/projects")

        assert response.status_code == 200
        body = response.json()
        assert body["status_code"] == 200
        assert body["status"] == "success"
        assert "data" in body

    def test_get_projects_with_search_filter(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should pass search parameter to service."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get("/api/v1/projects?search=test")

        assert response.status_code == 200
        mock_projects_service.get_projects.assert_called_once()
        call_kwargs = mock_projects_service.get_projects.call_args.kwargs
        assert call_kwargs["search"] == "test"

    def test_get_projects_with_status_filter(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should pass status parameter to service."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get("/api/v1/projects?status=active,completed")

        assert response.status_code == 200
        call_kwargs = mock_projects_service.get_projects.call_args.kwargs
        assert call_kwargs["status"] == "active,completed"

    def test_get_projects_with_pagination(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should pass offset and limit to service."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get("/api/v1/projects?offset=20&limit=50")

        assert response.status_code == 200
        call_kwargs = mock_projects_service.get_projects.call_args.kwargs
        assert call_kwargs["offset"] == 20
        assert call_kwargs["limit"] == 50

    def test_get_projects_with_sorting(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should pass sort_by and sort_order to service."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get("/api/v1/projects?sort_by=onboarded_date&sort_order=desc")

        assert response.status_code == 200
        call_kwargs = mock_projects_service.get_projects.call_args.kwargs
        assert call_kwargs["sort_by"] == "onboarded_date"
        assert call_kwargs["sort_order"] == "desc"

    def test_get_projects_with_min_overdue_days(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should pass min_overdue_days to service."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get("/api/v1/projects?min_overdue_days=30")

        assert response.status_code == 200
        call_kwargs = mock_projects_service.get_projects.call_args.kwargs
        assert call_kwargs["min_overdue_days"] == 30

    def test_get_projects_with_all_filters(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should pass all filters to service."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get(
            "/api/v1/projects?"
            "period=last_month&"
            "search=alpha&"
            f"status={uuid.uuid4()}&"
            f"client={uuid.uuid4()}&"
            f"specialization={uuid.uuid4()}&"
            "min_overdue_days=15&"
            "offset=10&"
            "limit=25&"
            "sort_by=project&"
            "sort_order=asc"
        )

        assert response.status_code == 200
        call_kwargs = mock_projects_service.get_projects.call_args.kwargs
        assert call_kwargs["period"] == "last_month"
        assert call_kwargs["search"] == "alpha"
        assert call_kwargs["min_overdue_days"] == 15

    def test_get_projects_default_pagination(
        self, client, mock_projects_service, sample_projects_response
    ):
        """Should use default pagination values."""
        mock_projects_service.get_projects.return_value = sample_projects_response

        response = client.get("/api/v1/projects")

        assert response.status_code == 200
        call_kwargs = mock_projects_service.get_projects.call_args.kwargs
        assert call_kwargs["offset"] == 0
        assert call_kwargs["limit"] == 10


class TestProjectAction:
    """Tests for POST /api/v1/projects/action endpoint."""

    def test_project_action_mark_not_applicable_returns_200(
        self, client, mock_projects_service
    ):
        """Should return 200 when marking project as not applicable."""
        mock_projects_service.perform_project_action.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Project marked as not applicable",
            data=None,
        )

        # Create mock file
        files = {"evidence_file": ("test.pdf", b"fake pdf content", "application/pdf")}
        data = {
            "project_id": str(uuid.uuid4()),
            "action": "mark_not_applicable",
            "reason_category": "No longer needed",
            "comments": "Project cancelled",
        }

        response = client.post("/api/v1/projects/action", data=data, files=files)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_project_action_mark_complete_returns_200(
        self, client, mock_projects_service
    ):
        """Should return 200 when marking project as complete."""
        mock_projects_service.perform_project_action.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Project marked as completed",
            data=None,
        )

        data = {
            "project_id": str(uuid.uuid4()),
            "action": "mark_complete",
        }

        response = client.post("/api/v1/projects/action", data=data)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_project_action_without_evidence_file(
        self, client, mock_projects_service
    ):
        """Should allow marking not applicable without evidence file."""
        mock_projects_service.perform_project_action.return_value = BaseResponse(
            status_code=200,
            status="success",
            message="Project marked as not applicable",
            data=None,
        )

        data = {
            "project_id": str(uuid.uuid4()),
            "action": "mark_not_applicable",
            "reason_category": "Test reason",
            "comments": "Test comments",
        }

        response = client.post("/api/v1/projects/action", data=data)

        assert response.status_code == 200
