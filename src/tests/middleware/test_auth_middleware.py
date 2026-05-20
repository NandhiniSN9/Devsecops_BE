"""Unit tests for authentication middleware.

Tests verify token decryption, Jira email validation, excluded paths,
trace_id generation, and error handling.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from src.middleware.auth_middleware import AuthMiddleware
from src.utils.exceptions.exceptions import AuthenticationError


# Generate a valid Fernet key for testing
TEST_FERNET_KEY = Fernet.generate_key().decode()


@pytest.fixture
def mock_jira_client():
    """Create a mock JiraClient."""
    mock_client = MagicMock()
    mock_client.validate_email = AsyncMock()
    return mock_client


@pytest.fixture
def valid_token():
    """Create a valid encrypted token with email and jira_id."""
    fernet = Fernet(TEST_FERNET_KEY.encode())
    payload = {
        "email": "test.user@example.com",
        "jira_id": "abc123",
    }
    token = fernet.encrypt(json.dumps(payload).encode()).decode()
    return token


@pytest.fixture
def app_with_middleware(mock_jira_client):
    """Create a test FastAPI app with auth middleware."""
    from fastapi import FastAPI

    app = FastAPI()

    # Mock settings
    with patch("src.middleware.auth_middleware.get_settings") as mock_settings:
        mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY

        # Create middleware with mocked JiraClient
        with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
            middleware = AuthMiddleware(app)
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return JSONResponse({
            "email": request.state.email,
            "jira_id": request.state.jira_id,
            "trace_id": request.state.trace_id,
        })

    @app.get("/health")
    async def health():
        return JSONResponse({"status": "ok"})

    return app


@pytest.fixture
def client(app_with_middleware):
    """Create a test client."""
    return TestClient(app_with_middleware, raise_server_exceptions=False)


class TestAuthMiddlewareExcludedPaths:
    """Tests for excluded paths that skip authentication."""

    def test_health_endpoint_no_auth_required(self, client):
        """Health endpoint should not require authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_ready_endpoint_no_auth_required(self, client):
        """Ready endpoint should not require authentication."""
        # Note: /ready endpoint not defined in test app, so 404 is expected
        # but it should not return 401 (auth required)
        response = client.get("/ready")
        assert response.status_code == 404  # Not 401

    def test_docs_endpoint_no_auth_required(self, client):
        """Docs endpoint should not require authentication."""
        response = client.get("/docs")
        # FastAPI auto-generates docs, so should get 200 or redirect
        assert response.status_code != 401

    def test_openapi_json_no_auth_required(self, client):
        """OpenAPI schema endpoint should not require authentication."""
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestAuthMiddlewareTokenValidation:
    """Tests for token validation and decryption."""

    def test_missing_authorization_header_returns_401(self, client):
        """Request without Authorization header should return 401."""
        response = client.get("/test")
        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "failed"
        assert "Authentication token is missing" in body["message"]

    def test_invalid_authorization_header_format_returns_401(self, client):
        """Request with invalid Authorization format should return 401."""
        response = client.get("/test", headers={"Authorization": "InvalidFormat xyz"})
        assert response.status_code == 401

    def test_malformed_token_returns_401(self, client, mock_jira_client):
        """Request with malformed encrypted token should return 401."""
        response = client.get("/test", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
        mock_jira_client.validate_email.assert_not_called()

    def test_token_with_empty_email_returns_401(self, mock_jira_client):
        """Token with empty email field should return 401."""
        fernet = Fernet(TEST_FERNET_KEY.encode())
        payload = {"email": "", "jira_id": "abc123"}
        token = fernet.encrypt(json.dumps(payload).encode()).decode()

        # Need to create new client with this token
        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()
        with patch("src.middleware.auth_middleware.get_settings") as mock_settings:
            mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY
            with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
                middleware = AuthMiddleware(app)
                app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return JSONResponse({"status": "ok"})

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401
        mock_jira_client.validate_email.assert_not_called()


class TestAuthMiddlewareJiraValidation:
    """Tests for Jira email validation."""

    @patch("src.middleware.auth_middleware.get_settings")
    def test_valid_token_with_jira_validation_success(
        self, mock_settings, mock_jira_client, valid_token
    ):
        """Valid token with successful Jira validation should return 200."""
        mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY
        mock_jira_client.validate_email.return_value = True

        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()
        with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
            middleware = AuthMiddleware(app)
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return JSONResponse({
                "email": request.state.email,
                "jira_id": request.state.jira_id,
            })

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "test.user@example.com"
        assert body["jira_id"] == "abc123"
        mock_jira_client.validate_email.assert_awaited_once_with("test.user@example.com")

    @patch("src.middleware.auth_middleware.get_settings")
    def test_valid_token_but_jira_validation_fails_returns_401(
        self, mock_settings, mock_jira_client, valid_token
    ):
        """Valid token but Jira validation failure should return 401."""
        mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY
        mock_jira_client.validate_email.return_value = False

        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()
        with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
            middleware = AuthMiddleware(app)
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return JSONResponse({"status": "ok"})

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "failed"
        assert "Authentication failed" in body["message"]


class TestAuthMiddlewareTraceId:
    """Tests for trace_id generation."""

    @patch("src.middleware.auth_middleware.get_settings")
    def test_trace_id_is_generated_for_every_request(
        self, mock_settings, mock_jira_client, valid_token
    ):
        """Every request should have a unique trace_id."""
        mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY
        mock_jira_client.validate_email.return_value = True

        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()
        with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
            middleware = AuthMiddleware(app)
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return JSONResponse({"trace_id": request.state.trace_id})

        client = TestClient(app, raise_server_exceptions=False)

        # Make two requests
        response1 = client.get("/test", headers={"Authorization": f"Bearer {valid_token}"})
        response2 = client.get("/test", headers={"Authorization": f"Bearer {valid_token}"})

        assert response1.status_code == 200
        assert response2.status_code == 200

        trace_id_1 = response1.json()["trace_id"]
        trace_id_2 = response2.json()["trace_id"]

        # Verify they are valid UUIDs
        uuid.UUID(trace_id_1)
        uuid.UUID(trace_id_2)

        # Verify they are different
        assert trace_id_1 != trace_id_2

    def test_trace_id_generated_even_on_auth_failure(self, client):
        """trace_id should be generated even when auth fails."""
        # Trace ID is generated before auth check, so it might be logged
        # but not returned in the response. This test verifies no crash occurs.
        response = client.get("/test")
        assert response.status_code == 401
        # trace_id exists internally but not in error response by default


class TestAuthMiddlewareErrorHandling:
    """Tests for error handling and exception cases."""

    @patch("src.middleware.auth_middleware.get_settings")
    def test_unexpected_exception_during_jira_validation_returns_401(
        self, mock_settings, mock_jira_client, valid_token
    ):
        """Unexpected exception during Jira validation should return 401."""
        mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY
        mock_jira_client.validate_email.side_effect = Exception("Network error")

        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()
        with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
            middleware = AuthMiddleware(app)
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return JSONResponse({"status": "ok"})

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test", headers={"Authorization": f"Bearer {valid_token}"})

        # After our fix, exception should be caught and return 401
        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "failed"
        assert "server error" in body["message"].lower()

    @patch("src.middleware.auth_middleware.get_settings")
    def test_token_with_jira_account_id_instead_of_jira_id(
        self, mock_settings, mock_jira_client
    ):
        """Token with jira_account_id field should be accepted (backward compat)."""
        mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY
        mock_jira_client.validate_email.return_value = True

        fernet = Fernet(TEST_FERNET_KEY.encode())
        payload = {
            "email": "user@example.com",
            "jira_account_id": "account123",  # Old field name
        }
        token = fernet.encrypt(json.dumps(payload).encode()).decode()

        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()
        with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
            middleware = AuthMiddleware(app)
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return JSONResponse({
                "email": request.state.email,
                "jira_id": request.state.jira_id,
            })

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "user@example.com"
        assert body["jira_id"] == "account123"


class TestAuthMiddlewareIntegration:
    """Integration tests for complete authentication flow."""

    @patch("src.middleware.auth_middleware.get_settings")
    def test_complete_auth_flow_with_valid_credentials(
        self, mock_settings, mock_jira_client
    ):
        """Complete auth flow: decrypt token → validate Jira → attach state."""
        mock_settings.return_value.TOKEN_PRIVATE_KEY = TEST_FERNET_KEY
        mock_jira_client.validate_email.return_value = True

        # Create token with specific data
        fernet = Fernet(TEST_FERNET_KEY.encode())
        payload = {
            "email": "john.doe@company.com",
            "jira_id": "jira-user-123",
        }
        token = fernet.encrypt(json.dumps(payload).encode()).decode()

        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()
        with patch("src.middleware.auth_middleware.JiraClient", return_value=mock_jira_client):
            middleware = AuthMiddleware(app)
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)

        @app.get("/protected")
        async def protected_endpoint(request: Request):
            return JSONResponse({
                "user": {
                    "email": request.state.email,
                    "jira_id": request.state.jira_id,
                    "trace_id": request.state.trace_id,
                }
            })

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["user"]["email"] == "john.doe@company.com"
        assert body["user"]["jira_id"] == "jira-user-123"
        assert len(body["user"]["trace_id"]) == 36  # UUID length

        # Verify Jira validation was called with correct email
        mock_jira_client.validate_email.assert_awaited_once_with("john.doe@company.com")
