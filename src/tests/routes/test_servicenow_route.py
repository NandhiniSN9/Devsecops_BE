"""Unit tests for ServiceNow sync route endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from src.services.dependencies import get_servicenow_service


@pytest.fixture
def mock_servicenow_service():
    """Create a mock ServiceNow service."""
    service = AsyncMock()
    service.sync_projects = AsyncMock(return_value={"created": 1, "updated": 0, "total": 1})
    service.sync_devsecops_tickets = AsyncMock(return_value={"created": 1, "failed": 0, "total": 1})
    return service


@pytest.fixture
def client(mock_servicenow_service):
    """Create a test client with mocked service and auth bypassed."""
    app.dependency_overrides[get_servicenow_service] = lambda: mock_servicenow_service
    with patch(
        "src.routes.servicenow_route._validate_servicenow_auth",
        new_callable=AsyncMock,
        return_value="servicenow@test.local",
    ):
        yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


class TestSyncProjectsEndpoint:
    """Tests for POST /api/v1/sync/servicenow/projects."""

    def test_sync_projects_success(self, client, mock_servicenow_service):
        """Should return 200 with success message on valid request."""
        payload = {
            "projects": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test Project",
                    "onboarded_date": "2026-01-15",
                    "project_type": "Application",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["message"] == "Sync completed successfully"
        mock_servicenow_service.sync_projects.assert_called_once()

    def test_sync_projects_returns_data_with_created_updated_total(self, client, mock_servicenow_service):
        """Should return data with created, updated, and total counts."""
        mock_servicenow_service.sync_projects.return_value = {"created": 2, "updated": 1, "total": 3}
        payload = {
            "projects": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Project 1",
                    "onboarded_date": "2026-01-15",
                    "project_type": "App",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["created"] == 2
        assert data["updated"] == 1
        assert data["total"] == 3

    def test_sync_projects_empty_projects_list_rejected(self, client):
        """Should return 422 when projects list is empty."""
        payload = {"projects": []}
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 422

    def test_sync_projects_missing_required_fields(self, client):
        """Should return 422 when required fields are missing."""
        payload = {
            "projects": [
                {
                    "sn_project_id": "SN-001",
                    # missing project_name, onboarded_date, project_type
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 422

    def test_sync_projects_invalid_date_format(self, client):
        """Should return 422 when onboarded_date is not a valid date."""
        payload = {
            "projects": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    "onboarded_date": "not-a-date",
                    "project_type": "App",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 422

    def test_sync_projects_whitespace_stripped(self, client, mock_servicenow_service):
        """Should strip whitespace from string fields."""
        payload = {
            "projects": [
                {
                    "sn_project_id": "  SN-001  ",
                    "project_name": "  Test Project  ",
                    "onboarded_date": "2026-01-15",
                    "project_type": "  Application  ",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 200
        call_args = mock_servicenow_service.sync_projects.call_args[0][0]
        assert call_args.projects[0].sn_project_id == "SN-001"
        assert call_args.projects[0].project_name == "Test Project"

    def test_sync_projects_method_not_allowed(self, client):
        """Should return 405 for GET requests."""
        response = client.get("/api/v1/sync/servicenow/projects")

        assert response.status_code == 405

    def test_sync_projects_service_error_returns_500(self, client, mock_servicenow_service):
        """Should return 500 when service raises an unhandled exception."""
        mock_servicenow_service.sync_projects.side_effect = RuntimeError("DB connection lost")
        payload = {
            "projects": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    "onboarded_date": "2026-01-15",
                    "project_type": "App",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 500
        assert response.json()["status"] == "error"

    def test_sync_projects_auth_returns_email(self, client, mock_servicenow_service):
        """Auth validation returns email which is passed as created_by."""
        payload = {
            "projects": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    "onboarded_date": "2026-01-15",
                    "project_type": "App",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/projects", json=payload)

        assert response.status_code == 200
        # The second arg to sync_projects is created_by (the email from auth)
        call_args = mock_servicenow_service.sync_projects.call_args[0]
        assert call_args[1] == "servicenow@test.local"


class TestSyncDevsecopsTicketsEndpoint:
    """Tests for POST /api/v1/sync/servicenow/devsecops-tickets."""

    def test_sync_tickets_success(self, client, mock_servicenow_service):
        """Should return 200 with success message on valid request."""
        payload = {
            "tickets": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test Project",
                    "specialization_name": "DevSecOps",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        mock_servicenow_service.sync_devsecops_tickets.assert_called_once()

    def test_sync_tickets_returns_data_with_created_failed_total(self, client, mock_servicenow_service):
        """Should return data with created, failed, and total counts."""
        mock_servicenow_service.sync_devsecops_tickets.return_value = {"created": 3, "failed": 1, "total": 4}
        payload = {
            "tickets": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    "specialization_name": "Backend",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["created"] == 3
        assert data["failed"] == 1
        assert data["total"] == 4

    def test_sync_tickets_empty_list_rejected(self, client):
        """Should return 422 when tickets list is empty."""
        payload = {"tickets": []}
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 422

    def test_sync_tickets_with_repositories(self, client, mock_servicenow_service):
        """Should accept tickets with repository data."""
        payload = {
            "tickets": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    "specialization_name": "Backend",
                    "repositories": [
                        {
                            "repo_name": "my-repo",
                            "ado_repo_id": "ADO-001",
                            "lead_approvers": ["lead@company.com"],
                        }
                    ],
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 200

    def test_sync_tickets_with_devsec_project_id_alias(self, client, mock_servicenow_service):
        """Should accept devSec_project_id alias field."""
        payload = {
            "tickets": [
                {
                    "sn_project_id": "SN-001",
                    "devSec_project_id": "ADO-PRJ-001",
                    "project_name": "Test",
                    "specialization_name": "Backend",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 200
        call_args = mock_servicenow_service.sync_devsecops_tickets.call_args[0][0]
        assert call_args.tickets[0].devsec_project_id == "ADO-PRJ-001"

    def test_sync_tickets_missing_specialization_name(self, client):
        """Should return 422 when specialization_name is missing."""
        payload = {
            "tickets": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    # missing specialization_name
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 422

    def test_sync_tickets_server_error(self, client, mock_servicenow_service):
        """Should return 500 when service raises an unhandled exception."""
        mock_servicenow_service.sync_devsecops_tickets.side_effect = RuntimeError("DB error")

        payload = {
            "tickets": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    "specialization_name": "Backend",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 500
        assert response.json()["status"] == "error"

    def test_sync_tickets_auth_returns_email_as_created_by(self, client, mock_servicenow_service):
        """Auth validation returns email which is passed as created_by."""
        payload = {
            "tickets": [
                {
                    "sn_project_id": "SN-001",
                    "project_name": "Test",
                    "specialization_name": "Backend",
                }
            ]
        }
        response = client.post("/api/v1/sync/servicenow/devsecops-tickets", json=payload)

        assert response.status_code == 200
        call_args = mock_servicenow_service.sync_devsecops_tickets.call_args[0]
        assert call_args[1] == "servicenow@test.local"
