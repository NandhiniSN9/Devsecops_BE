"""Jira REST API client for email validation."""

import httpx
from src.settings import JIRA_VALIDATION_TIMEOUT, get_settings
from src.utils.logger import logger


class JiraClient:
    """Client for interacting with the Jira REST API.

    Used by the authentication middleware to validate that a decrypted
    email corresponds to an existing Jira user.
    """

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
            headers = {
                "Authorization": f"Bearer {settings.JIRA_API_TOKEN}",
                "Accept": "application/json",
            }
            params = {"username": email}
            async with httpx.AsyncClient(timeout=JIRA_VALIDATION_TIMEOUT) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                users = response.json()
                return isinstance(users, list) and len(users) > 0

        except httpx.TimeoutException:
            logger.warning("Jira API validation timed out", email=email)
            return False

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Jira API returned non-2xx status",
                email=email,
                status_code=exc.response.status_code,
            )
            return False

        except httpx.HTTPError as exc:
            logger.warning("Jira API request failed", email=email, error=str(exc))
            return False
            
        except Exception as exc:
            logger.error("Unexpected error during Jira email validation", email=email, error=str(exc))
            return False
