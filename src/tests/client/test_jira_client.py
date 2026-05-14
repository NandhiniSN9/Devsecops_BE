"""Unit tests for JiraClient.validate_email method."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.client.jira_client import JiraClient


@pytest.fixture
def jira_client():
    """Create a JiraClient instance for testing."""
    return JiraClient()


@pytest.fixture
def mock_settings():
    """Mock settings with test values."""
    with patch("src.client.jira_client.get_settings") as mock:
        settings = mock.return_value
        settings.JIRA_BASE_URL = "https://jira.example.com"
        settings.JIRA_API_TOKEN = "test-api-token"
        yield mock


class TestValidateEmailSuccess:
    """Tests for successful email validation scenarios."""

    async def test_returns_true_when_user_found(self, jira_client, mock_settings):
        """validate_email returns True when Jira returns a non-empty user list."""
        mock_response = httpx.Response(
            status_code=200,
            json=[{"accountId": "123", "emailAddress": "user@example.com"}],
            request=httpx.Request("GET", "https://jira.example.com/rest/api/2/user/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await jira_client.validate_email("user@example.com")

        assert result is True

    async def test_returns_true_when_multiple_users_found(self, jira_client, mock_settings):
        """validate_email returns True when Jira returns multiple matching users."""
        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"accountId": "123", "emailAddress": "user@example.com"},
                {"accountId": "456", "emailAddress": "user@example.com"},
            ],
            request=httpx.Request("GET", "https://jira.example.com/rest/api/2/user/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await jira_client.validate_email("user@example.com")

        assert result is True

    async def test_calls_correct_url_with_params(self, jira_client, mock_settings):
        """validate_email calls the correct Jira endpoint with proper parameters."""
        mock_response = httpx.Response(
            status_code=200,
            json=[{"accountId": "123"}],
            request=httpx.Request("GET", "https://jira.example.com/rest/api/2/user/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response) as mock_get:
            await jira_client.validate_email("test@company.com")

        mock_get.assert_called_once_with(
            "https://jira.example.com/rest/api/2/user/search",
            headers={
                "Authorization": "Bearer test-api-token",
                "Accept": "application/json",
            },
            params={"username": "test@company.com"},
        )


class TestValidateEmailFailure:
    """Tests for email validation failure scenarios."""

    async def test_returns_false_when_empty_list(self, jira_client, mock_settings):
        """validate_email returns False when Jira returns an empty user list."""
        mock_response = httpx.Response(
            status_code=200,
            json=[],
            request=httpx.Request("GET", "https://jira.example.com/rest/api/2/user/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await jira_client.validate_email("unknown@example.com")

        assert result is False

    async def test_returns_false_on_timeout(self, jira_client, mock_settings):
        """validate_email returns False when the Jira API times out."""
        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("Connection timed out"),
        ):
            result = await jira_client.validate_email("user@example.com")

        assert result is False

    async def test_returns_false_on_network_error(self, jira_client, mock_settings):
        """validate_email returns False on network connectivity errors."""
        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await jira_client.validate_email("user@example.com")

        assert result is False

    async def test_returns_false_on_non_2xx_response(self, jira_client, mock_settings):
        """validate_email returns False when Jira returns a non-2xx status code."""
        mock_response = httpx.Response(
            status_code=403,
            json={"errorMessages": ["Forbidden"]},
            request=httpx.Request("GET", "https://jira.example.com/rest/api/2/user/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await jira_client.validate_email("user@example.com")

        assert result is False

    async def test_returns_false_on_500_server_error(self, jira_client, mock_settings):
        """validate_email returns False when Jira returns a 500 error."""
        mock_response = httpx.Response(
            status_code=500,
            json={"errorMessages": ["Internal Server Error"]},
            request=httpx.Request("GET", "https://jira.example.com/rest/api/2/user/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await jira_client.validate_email("user@example.com")

        assert result is False

    async def test_returns_false_on_unexpected_response_format(self, jira_client, mock_settings):
        """validate_email returns False when response is not a list."""
        mock_response = httpx.Response(
            status_code=200,
            json={"error": "unexpected format"},
            request=httpx.Request("GET", "https://jira.example.com/rest/api/2/user/search"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await jira_client.validate_email("user@example.com")

        assert result is False

    async def test_returns_false_on_unexpected_exception(self, jira_client, mock_settings):
        """validate_email returns False on any unexpected exception."""
        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected error"),
        ):
            result = await jira_client.validate_email("user@example.com")

        assert result is False
