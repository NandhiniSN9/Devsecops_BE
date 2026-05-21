"""AWS Secrets Manager loader.

Fetches all secrets from a single JSON secret at startup and injects them
into environment variables so pydantic-settings can pick them up as normal.

Usage (ECS task definition):
    Set only these two env vars on the container:
        AWS_SECRET_NAME = "aipe-dashboard/dev/app-secrets"
        AWS_REGION      = "us-east-1"

    The secret value in Secrets Manager must be a flat JSON object containing
    ALL keys listed below. Example secret JSON:

    {
        "DATABASE_URL":                "postgresql+asyncpg://dbadmin:<pwd>@host:5432/mydb",
        "TOKEN_PRIVATE_KEY":           "VrPmuTPLIB01e8fm5_S-qQkN1ahWz9YQ-BxJVCjSKmg=",

        "JIRA_BASE_URL":               "https://zeb-ai.atlassian.net",
        "JIRA_API_TOKEN":              "ATATT3x...",
        "JIRA_SERVICE_ACCOUNT_EMAIL":  "svc_jira.tools@zeb.co",
        "JIRA_LABS_HUB_PROJECT_KEY":   "SBT",
        "JIRA_LABS_HUB_PROJECT_ID":    "12432",

        "SERVICENOW_ALLOWED_EMAIL":    "servicenow@your-org.com",

        "GRAPH_CLIENT_ID":             "efb6886c-...",
        "GRAPH_CLIENT_SECRET":         "USf8Q~...",
        "GRAPH_TENANT_ID":             "248786b7-...",
        "GRAPH_SENDER_EMAIL":          "noreply@your-org.com",

        "S3_BUCKET_NAME":              "devsecops-reports-bucket",
        "AWS_REGION":                  "us-east-1",
        "S3_URL_EXPIRY_DAYS":          "7",

        "ADO_ORG_URL":                 "https://dev.azure.com/your-org",
        "ADO_PAT":                     "your-ado-pat",
        "ADO_SYNC_CONCURRENCY":        "5",
        "ADO_SYNC_RECORD_LIMIT":       "5"
    }

Local dev:
    Do NOT set AWS_SECRET_NAME — loader is skipped entirely and
    pydantic-settings falls back to .env file as before.
"""

import json
import os
import sys

from src.utils.logger import logger


def load_secrets_into_env() -> None:
    """Fetch secrets from AWS Secrets Manager and inject into os.environ.

    Called once at application startup before Settings is instantiated.
    If AWS_SECRET_NAME is not set this is a no-op — local .env still works.
    """
    secret_name = os.environ.get("AWS_SECRET_NAME")
    if not secret_name:
        logger.info("AWS_SECRET_NAME not set — using local .env for configuration")
        return

    region = os.environ.get("AWS_REGION", "us-east-1")

    try:
        import boto3

        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString")

        if not secret_string:
            logger.error(
                "Secrets Manager returned empty SecretString",
                secret_name=secret_name,
            )
            sys.exit(1)

        secrets: dict = json.loads(secret_string)

        # Inject into environment — skip keys already set (allows ECS task-level overrides)
        loaded = 0
        for key, value in secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)
                loaded += 1

        logger.info(
            "Secrets loaded from AWS Secrets Manager",
            secret_name=secret_name,
            region=region,
            keys_loaded=loaded,
            keys_skipped=len(secrets) - loaded,
        )

    except ImportError:
        logger.error("boto3 not installed — cannot load from AWS Secrets Manager")
        sys.exit(1)
    except Exception as exc:
        logger.error(
            "Failed to load secrets from AWS Secrets Manager",
            secret_name=secret_name,
            region=region,
            error=str(exc),
        )
        sys.exit(1)
