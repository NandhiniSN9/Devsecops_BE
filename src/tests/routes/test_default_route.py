"""Unit tests for health and readiness check routes.

Tests verify the /health and /ready endpoints return correct responses
under normal and failure conditions.

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.default_route import router
from src.services.dependencies import get_db_session


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def app(mock_db_session):
    """Create a FastAPI test app with the default router."""
    test_app = FastAPI()
    test_app.include_router(router)

    # Override the dependency to use our mock session
    test_app.dependency_overrides[get_db_session] = lambda: mock_db_session

    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200_with_healthy_status(self, client):
        """Health endpoint returns 200 with status healthy.

        Validates: Requirements 9.1
        """
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_response_content_type_is_json(self, client):
        """Health endpoint returns application/json content type.

        Validates: Requirements 9.1
        """
        response = client.get("/health")

        assert "application/json" in response.headers["content-type"]

    def test_health_does_not_require_auth(self, client):
        """Health endpoint is accessible without authentication.

        Validates: Requirements 9.4
        """
        # No Authorization header provided
        response = client.get("/health")

        assert response.status_code == 200


class TestReadinessEndpoint:
    """Tests for GET /ready endpoint."""

    def test_ready_returns_200_when_db_is_available(self, client, mock_db_session):
        """Ready endpoint returns 200 with status ready when DB responds.

        Validates: Requirements 9.2
        """
        mock_db_session.execute.return_value = None

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    def test_ready_executes_db_connectivity_check(self, client, mock_db_session):
        """Ready endpoint executes a database query to verify connectivity.

        Validates: Requirements 9.2
        """
        mock_db_session.execute.return_value = None

        client.get("/ready")

        mock_db_session.execute.assert_called_once()

    def test_ready_returns_503_when_db_timeout(self, client, mock_db_session):
        """Ready endpoint returns 503 when DB check times out.

        Validates: Requirements 9.3
        """
        mock_db_session.execute.side_effect = TimeoutError()

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}

    def test_ready_returns_503_when_db_connection_error(self, client, mock_db_session):
        """Ready endpoint returns 503 when DB connection fails.

        Validates: Requirements 9.3
        """
        mock_db_session.execute.side_effect = ConnectionError("Database unreachable")

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}

    def test_ready_returns_503_when_unexpected_exception(self, client, mock_db_session):
        """Ready endpoint returns 503 for any unexpected exception.

        Validates: Requirements 9.3
        """
        mock_db_session.execute.side_effect = RuntimeError("Unexpected error")

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}

    def test_ready_does_not_require_auth(self, client, mock_db_session):
        """Ready endpoint is accessible without authentication.

        Validates: Requirements 9.4
        """
        mock_db_session.execute.return_value = None

        # No Authorization header provided
        response = client.get("/ready")

        assert response.status_code == 200

    def test_ready_response_content_type_is_json(self, client, mock_db_session):
        """Ready endpoint returns application/json content type.

        Validates: Requirements 9.2
        """
        mock_db_session.execute.return_value = None

        response = client.get("/ready")

        assert "application/json" in response.headers["content-type"]
