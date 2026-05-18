"""Tests for GraphClient Microsoft Graph API operations."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.client.graph_client import GraphClient


@pytest.fixture
def graph_client():
    """Create a GraphClient instance with test credentials."""
    return GraphClient(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-client-secret",
        sender_email="sender@example.com",
    )


class TestAcquireToken:
    """Tests for _acquire_token method."""

    @pytest.mark.asyncio
    async def test_acquire_token_success(self, graph_client):
        """Should acquire and return access token on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test-token-123"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            token = await graph_client._acquire_token()

            assert token == "test-token-123"
            assert graph_client._access_token == "test-token-123"

    @pytest.mark.asyncio
    async def test_acquire_token_failure(self, graph_client):
        """Should raise RuntimeError on token acquisition failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError, match="Graph API token acquisition failed"):
                await graph_client._acquire_token()


class TestSendEmail:
    """Tests for send_email method."""

    @pytest.mark.asyncio
    async def test_send_email_success(self, graph_client):
        """Should return True when email is sent successfully."""
        graph_client._access_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 202

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await graph_client.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_body="<p>Test body</p>",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_failure(self, graph_client):
        """Should return False when email send fails."""
        graph_client._access_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await graph_client.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_body="<p>Test body</p>",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_timeout(self, graph_client):
        """Should return False on timeout."""
        graph_client._access_token = "test-token"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await graph_client.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_body="<p>Test body</p>",
            )

            assert result is False


class TestGetToken:
    """Tests for get_token method."""

    @pytest.mark.asyncio
    async def test_get_token_cached(self, graph_client):
        """Should return cached token without re-acquiring."""
        graph_client._access_token = "cached-token"

        token = await graph_client.get_token()

        assert token == "cached-token"

    @pytest.mark.asyncio
    async def test_get_token_acquires_new(self, graph_client):
        """Should acquire new token when none is cached."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new-token"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            token = await graph_client.get_token()

            assert token == "new-token"
