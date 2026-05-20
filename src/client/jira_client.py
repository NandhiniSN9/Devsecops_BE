"""Jira REST API client for email validation and bug creation."""

import asyncio
import base64
import traceback
from dataclasses import dataclass

import httpx

from src.settings import (
    JIRA_LABS_HUB_PROJECT_ID,
    JIRA_LABS_HUB_PROJECT_KEY,
    JIRA_VALIDATION_TIMEOUT,
    get_settings,
)
from src.utils.logger import logger


@dataclass
class JiraBugResult:
    """Result returned after creating a Jira bug."""

    jira_id: str
    """The issue key returned by Jira (e.g. SBT-42)."""

    issue_url: str
    """Browser URL to the created Jira issue."""


class JiraClient:
    """Client for interacting with the Jira REST API.

    Supports:
    - Validating that an email corresponds to an existing Jira user.
    - Creating a Bug issue in the Labs Hub project space (SBT) for
      mark_not_applicable project actions.
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth_header(self) -> str:
        """Build a Basic-auth header value from the service account credentials.

        Jira Cloud REST API v3 requires Basic auth encoded as
        ``base64(email:api_token)``.
        """
        settings = get_settings()
        credentials = f"{settings.JIRA_SERVICE_ACCOUNT_EMAIL}:{settings.JIRA_API_TOKEN}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _common_headers(self) -> dict[str, str]:
        """Return headers shared by all Jira API calls."""
        return {
            "Authorization": self._auth_header(),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def validate_email(self, email: str) -> bool:
        """Validate that an email corresponds to an existing Jira user.

        Calls the Jira user search endpoint and returns True if at least
        one user is found matching the provided email.

        Args:
            email: The email address to validate against Jira.

        Returns:
            True if the user exists in Jira, False otherwise.
            Returns False on any error (timeout, network error, non-2xx response).
        """
        try:
            settings = get_settings()
            url = f"{settings.JIRA_BASE_URL}/rest/api/2/user/search"
            headers = self._common_headers()
            params = {"username": email}
            async with httpx.AsyncClient(timeout=JIRA_VALIDATION_TIMEOUT) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                users = response.json()
                return isinstance(users, list) and len(users) > 0

        except httpx.TimeoutException:
            logger.warning("Jira API validation timed out", extra={"email": email})
            return False

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Jira API returned non-2xx status",
                extra={"email": email, "status_code": exc.response.status_code},
            )
            return False

        except httpx.HTTPError as exc:
            logger.warning("Jira API request failed", extra={"email": email, "error": str(exc)})
            return False

        except Exception as exc:
            logger.error(
                "Unexpected error during Jira email validation",
                extra={"email": email, "error": str(exc)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="validate_email",
                error_file="src/client/jira_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            return False

    async def create_bug(
        self,
        project_id: str,
        project_name: str,
        reason_category: str,
        comments: str,
        evidence_url: str | None,
        reporter_email: str,
    ) -> JiraBugResult:
        """Create a Bug issue in the Jira Labs Hub project (SBT).

        The issue is created under project key ``SBT`` (project ID 12432).
        ``reason_category`` becomes the issue summary, ``comments`` and
        ``evidence_url`` are appended to the description body.

        Args:
            project_id: UUID string of the project being marked not applicable.
            project_name: Human-readable project name for the issue summary.
            reason_category: Short reason category (used as issue summary prefix).
            comments: Detailed comments added to the issue description.
            evidence_url: Optional pre-signed S3 URL attached to the description.
            reporter_email: Email of the user performing the action (for logging).

        Returns:
            JiraBugResult with the created issue key and browser URL.

        Raises:
            httpx.HTTPStatusError: If Jira returns a non-2xx response.
            httpx.HTTPError: On network-level failures.
        """
        settings = get_settings()
        url = f"{settings.JIRA_BASE_URL}/rest/api/3/issue"

        # Build ADF (Atlassian Document Format) description
        description_content: list[dict] = [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"Project ID: {project_id}"},
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"Project Name: {project_name}"},
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"Reason Category: {reason_category}"},
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"Comments: {comments}"},
                ],
            },
        ]

        if evidence_url:
            description_content.append(
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Evidence: "},
                        {
                            "type": "inlineCard",
                            "attrs": {"url": evidence_url},
                        },
                    ],
                }
            )

        payload = {
            "fields": {
                "project": {
                    "id": JIRA_LABS_HUB_PROJECT_ID,
                    "key": JIRA_LABS_HUB_PROJECT_KEY,
                },
                "summary": f"[Not Applicable] {project_name} - {reason_category}",
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Medium"},
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": description_content,
                },
            }
        }

        try:
            async with httpx.AsyncClient(timeout=JIRA_VALIDATION_TIMEOUT) as client:
                response = await client.post(
                    url,
                    headers=self._common_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                jira_key: str = data["key"]
                issue_url = f"{settings.JIRA_BASE_URL}/browse/{jira_key}"

                logger.info(
                    "Jira bug created for not-applicable project",
                    extra={
                        "jira_key": jira_key,
                        "project_id": str(project_id),
                        "project_name": project_name,
                        "reporter_email": reporter_email,
                    },
                )
                return JiraBugResult(jira_id=jira_key, issue_url=issue_url)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Jira bug creation failed with non-2xx status",
                extra={
                    "status_code": exc.response.status_code,
                    "response_body": exc.response.text,
                    "project_id": str(project_id),
                },
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_bug",
                error_file="src/client/jira_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

        except httpx.HTTPError as exc:
            logger.error(
                "Jira bug creation failed due to network error",
                extra={"error": str(exc), "project_id": str(project_id)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_bug",
                error_file="src/client/jira_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
