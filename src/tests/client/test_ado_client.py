"""Unit tests for AdoClient."""

from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from src.client.ado_client import AdoClient


@pytest.fixture
def client():
    """Create an AdoClient instance."""
    return AdoClient(
        org_url="https://dev.azure.com/testorg",
        pat="test-pat-token",
        project="TestProject",
    )


class TestGetPipelineRuns:
    """Tests for AdoClient.get_pipeline_runs."""

    @pytest.mark.asyncio
    async def test_returns_builds_on_success(self, client):
        """Should return list of builds from ADO API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [{"buildNumber": 1, "result": "succeeded"}],
            "count": 1,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.get.return_value = mock_response

            result = await client.get_pipeline_runs("repo-123")

        assert len(result) == 1
        assert result[0]["buildNumber"] == 1

    @pytest.mark.asyncio
    async def test_returns_empty_on_http_error(self, client):
        """Should return empty list on HTTP error."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            error_response = MagicMock()
            error_response.status_code = 404
            error_response.text = "Not Found"
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=error_response
            )

            result = await client.get_pipeline_runs("repo-123")

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_request_error(self, client):
        """Should return empty list on connection error."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.get.side_effect = httpx.RequestError("Connection failed")

            result = await client.get_pipeline_runs("repo-123")

        assert result == []


class TestGetCommits:
    """Tests for AdoClient.get_commits."""

    @pytest.mark.asyncio
    async def test_returns_commits_on_success(self, client):
        """Should return list of commits from ADO API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [{"commitId": "abc123", "comment": "test"}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.get.return_value = mock_response

            result = await client.get_commits("repo-123")

        assert len(result) == 1
        assert result[0]["commitId"] == "abc123"
