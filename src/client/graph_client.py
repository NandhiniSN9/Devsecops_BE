"""Microsoft Graph API client for sending emails.

Uses client credentials flow (app-only) to acquire a fresh access token
before every API call and sends emails via the /users/{sender}/sendMail endpoint.
No token caching — each operation gets a fresh token to guarantee validity.
"""

import asyncio
import base64
import traceback

import httpx

from src.utils.helpers import log_error_to_db
from src.utils.logger import logger

# Microsoft Graph API constants
MS_LOGIN_URL = "https://login.microsoftonline.com"
MS_GRAPH_URL = "https://graph.microsoft.com/v1.0"
MS_GRAPH_SCOPE = "https://graph.microsoft.com/.default"

# HTTP timeout for Graph API calls (seconds)
GRAPH_API_TIMEOUT = 30


class GraphClient:
    """Client for Microsoft Graph API email operations.

    Acquires a fresh OAuth2 token via client credentials flow before
    every API call. No caching — guarantees token is always valid.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        sender_email: str,
    ) -> None:
        """Initialize the Graph client with credentials.

        Args:
            tenant_id: Azure AD tenant ID.
            client_id: Application (client) ID.
            client_secret: Client secret value.
            sender_email: Email address of the sender (must have sendMail permission).
        """
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._sender_email = sender_email
    async def _acquire_token(self) -> str:
        """Acquire a fresh access token via client credentials flow.

        Called before every Graph API operation — no caching.
        This ensures the token is always valid regardless of elapsed time.

        Returns:
            The access token string.

        Raises:
            RuntimeError: If token acquisition fails.
        """
        try:
            url = f"{MS_LOGIN_URL}/{self._tenant_id}/oauth2/v2.0/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": MS_GRAPH_SCOPE,
            }

            async with httpx.AsyncClient(timeout=GRAPH_API_TIMEOUT) as client:
                response = await client.post(url, data=data)
                if response.status_code != 200:
                    error_detail = response.text[:500]
                    logger.error(
                        "Failed to acquire Graph API token",
                        status_code=response.status_code,
                        error=error_detail,
                    )
                    raise RuntimeError(f"Graph API token acquisition failed: HTTP {response.status_code}")

                token_data = response.json()
                access_token = token_data["access_token"]
                logger.info("Graph API access token acquired successfully")
                return access_token
        except RuntimeError:
            raise
        except httpx.TimeoutException as exc:
            logger.error("Timeout acquiring Graph API token", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_acquire_token",
                error_file="src/client/graph_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise RuntimeError(f"Graph API token acquisition timed out: {exc}") from exc
        except Exception as exc:
            logger.error("Unexpected error in _acquire_token", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_acquire_token",
                error_file="src/client/graph_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_token(self) -> str:
        """Get a valid access token, acquiring one if needed.

        Note: This method always acquires a fresh token as per the design
        (no caching). The _access_token attribute is not used.

        Returns:
            The access token string.
        """
        return await self._acquire_token()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachment_bytes: bytes | None = None,
        attachment_filename: str | None = None,
    ) -> bool:
        """Send an email to a single recipient via Microsoft Graph API.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_body: HTML content for the email body.
            attachment_bytes: Optional PDF or file bytes to attach.
            attachment_filename: Optional filename for the attachment.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        try:
            token = await self._acquire_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": html_body,
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": to_email}},
                    ],
                },
                "saveToSentItems": "false",
            }

            # Add attachment if provided
            if attachment_bytes and attachment_filename:
                base64_content = base64.b64encode(attachment_bytes).decode('utf-8')
                payload["message"]["attachments"] = [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": attachment_filename,
                        "contentType": "application/pdf",
                        "contentBytes": base64_content,
                    }
                ]
                logger.debug("Attachment added", filename=attachment_filename, size_bytes=len(attachment_bytes))

            url = f"{MS_GRAPH_URL}/users/{self._sender_email}/sendMail"
            async with httpx.AsyncClient(timeout=GRAPH_API_TIMEOUT) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in (200, 202):
                    logger.info("Email sent successfully", to=to_email, subject=subject, has_attachment=bool(attachment_bytes))
                    return True
                else:
                    error_detail = response.text[:500]
                    logger.warning(
                        "Email send failed",
                        to=to_email,
                        status_code=response.status_code,
                        error=error_detail,
                    )
                    return False

        except httpx.TimeoutException:
            logger.warning("Email send timed out", to=to_email)
            return False
        except httpx.HTTPError as exc:
            logger.warning("Email send HTTP error", to=to_email, error=str(exc))
            return False
        except Exception as exc:
            logger.error("Unexpected error in send_email", to=to_email, error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="send_email",
                error_file="src/client/graph_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
