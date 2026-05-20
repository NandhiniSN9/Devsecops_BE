"""Azure DevOps REST API client for fetching pipeline data."""

import httpx

from src.utils.logger import logger

# ADO API version
_API_VERSION = "7.1"

# Timeout for ADO API calls (seconds)
_REQUEST_TIMEOUT = 30


class AdoClient:
    """Async HTTP client for Azure DevOps REST API communication."""

    def __init__(self, org_url: str, pat: str) -> None:
        """Initialize with ADO credentials.

        Args:
            org_url: Azure DevOps organization URL (e.g., https://dev.azure.com/org).
            pat: Personal Access Token for authentication.
        """
        self._org_url = org_url.rstrip("/")
        self._auth = httpx.BasicAuth(username="", password=pat)

    async def get_pipeline_runs(self, repo_id: str, project: str, top: int = 5) -> list[dict]:
        """Fetch the latest pipeline runs (builds) for a repository.

        Args:
            repo_id: Azure DevOps repository identifier.
            project: ADO project name.
            top: Number of records to fetch.

        Returns:
            List of build dictionaries from ADO API.
        """
        url = f"{self._org_url}/{project}/_apis/build/builds"
        params = {"repositoryId": repo_id, "repositoryType": "TfsGit", "$top": str(top), "api-version": _API_VERSION}
        data = await self._get_list(url, params, "value")
        logger.info("ADO pipeline_runs response", repo_id=repo_id, count=len(data), data=data)
        return data

    async def get_commits(self, repo_id: str, project: str, top: int = 5) -> list[dict]:
        """Fetch the latest commits for a repository.

        Args:
            repo_id: Azure DevOps repository identifier.
            project: ADO project name.
            top: Number of records to fetch.

        Returns:
            List of commit dictionaries from ADO API.
        """
        url = f"{self._org_url}/{project}/_apis/git/repositories/{repo_id}/commits"
        params = {"$top": str(top), "api-version": _API_VERSION}
        data = await self._get_list(url, params, "value")
        logger.info("ADO commits response", repo_id=repo_id, count=len(data), data=data)
        return data

    async def get_pull_requests(self, repo_id: str, project: str, top: int = 5) -> list[dict]:
        """Fetch the latest pull requests for a repository.

        Args:
            repo_id: Azure DevOps repository identifier.
            project: ADO project name.
            top: Number of records to fetch.

        Returns:
            List of pull request dictionaries from ADO API.
        """
        url = f"{self._org_url}/{project}/_apis/git/repositories/{repo_id}/pullrequests"
        params = {"$top": str(top), "status": "all", "api-version": _API_VERSION}
        data = await self._get_list(url, params, "value")
        logger.info("ADO pull_requests response", repo_id=repo_id, count=len(data), data=data)
        return data

    async def get_build_artifacts(self, build_id: int, project: str) -> list[dict]:
        """Fetch artifacts for a specific build.

        Args:
            build_id: The ADO build ID.
            project: ADO project name.

        Returns:
            List of artifact dictionaries from ADO API.
        """
        url = f"{self._org_url}/{project}/_apis/build/builds/{build_id}/artifacts"
        params = {"api-version": _API_VERSION}
        data = await self._get_list(url, params, "value")
        logger.info("ADO build_artifacts response", build_id=build_id, count=len(data), data=data)
        return data

    async def _get_list(self, url: str, params: dict, list_key: str) -> list[dict]:
        """Execute a GET request and extract the list from the response.

        Args:
            url: Full API URL.
            params: Query parameters.
            list_key: Key in the JSON response containing the list.

        Returns:
            List of dictionaries, or empty list on failure.
        """
        try:
            async with httpx.AsyncClient(auth=self._auth, timeout=_REQUEST_TIMEOUT) as client:
                logger.info( "_get_list", url=url, params=params)
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get(list_key, [])
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ADO API HTTP error",
                url=url,
                status_code=exc.response.status_code,
                detail=exc.response.text[:500],
            )
            return []
        except httpx.RequestError as exc:
            logger.error(
                "ADO API request error",
                url=url,
                error=str(exc),
            )
            return []
