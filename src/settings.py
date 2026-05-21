"""Application settings and constants for the Overview Dashboard API."""

import re
import sys
import uuid
from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

# ============================================================
# Application Constants
# ============================================================

# Period filter mapping: enum value → number of days
PERIOD_DAYS_MAP: dict[str, int] = {
    "last_week": 7,
    "last_month": 30,
    "last_3_months": 90,
}

# At-risk count threshold for "critical" severity banner
SEVERITY_CRITICAL_THRESHOLD: int = 5

# Cache-Control max-age for filters endpoint (seconds)
FILTER_CACHE_MAX_AGE: int = 3600

# Timeout for Jira API validation calls (seconds)
JIRA_VALIDATION_TIMEOUT: int = 10

# Service identifier for error logging
OVERVIEW_SERVICE_IDENTIFIER: str = "overview_service"

# Service identifier for ServiceNow sync error logging
SERVICENOW_SERVICE_IDENTIFIER: str = "servicenow_sync_service"

# Service identifier for report generation error logging
REPORT_SERVICE_IDENTIFIER: str = "report_service"

# Default S3 pre-signed URL expiration in days
S3_URL_EXPIRY_DAYS_DEFAULT: int = 7

# Sync method identifier for tickets created via ServiceNow
SERVICENOW_SYNC_METHOD: str = "servicenow"

# Maximum number of specialization IDs allowed in filter
MAX_SPECIALIZATION_FILTER_COUNT: int = 50

# Service identifier for projects error logging
PROJECTS_SERVICE_IDENTIFIER: str = "projects_service"

# Period filter mapping for projects endpoint: enum value → number of days
PROJECTS_PERIOD_DAYS_MAP: dict[str, int] = {
    "all": 0,
    "last_week": 7,
    "last_month": 30,
    "last_3_months": 90,
    "last_6_months": 180,
    "last_year": 365,
}

# Fixed UUID namespace for deterministic client ID generation (UUID v5)
CLIENT_UUID_NAMESPACE: uuid.UUID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# Jira Labs Hub project space for Not Applicable bug creation
JIRA_LABS_HUB_PROJECT_KEY: str = "SBT"
JIRA_LABS_HUB_PROJECT_ID: str = "12432"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    TOKEN_PRIVATE_KEY: str
    JIRA_BASE_URL: str
    JIRA_API_TOKEN: str
    SERVICENOW_ALLOWED_EMAIL: str = ""

    # Email Notification Service - Microsoft Graph API
    GRAPH_CLIENT_ID: str = ""
    GRAPH_CLIENT_SECRET: str = ""
    GRAPH_TENANT_ID: str = ""
    GRAPH_SENDER_EMAIL: str = ""

    # Email Notification Service - AWS S3
    S3_BUCKET_NAME: str = ""
    S3_URL_EXPIRY_DAYS: int = 7
    AWS_REGION: str = "us-east-1"

    # Azure DevOps API
    ADO_ORG_URL: str = ""
    ADO_PAT: str = ""
    ADO_SYNC_CONCURRENCY: int = 5  # Max parallel repository syncs
    ADO_SYNC_RECORD_LIMIT: int = 5  # Max records per data type to upsert per repository sync

    # Jira Labs Hub service account for bug creation
    JIRA_SERVICE_ACCOUNT_EMAIL: str = "svc_jira.tools@zeb.co"

    model_config = ConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton instance."""
    return Settings()


# ============================================================
# Startup Validation
# ============================================================

# Regex pattern for valid PostgreSQL connection strings
_DATABASE_URL_PATTERN = re.compile(
    r"^postgresql(\+asyncpg)?://"  # scheme
    r".+@"  # user:password@
    r"[^:/]+"  # host
    r":\d+"  # :port
    r"/.+"  # /database
)


def validate_settings_at_startup() -> Settings:
    """Validate all required settings at application startup.

    Exits with non-zero code and logs to stderr if validation fails.
    Returns the validated Settings instance on success.
    """
    errors: list[str] = []

    # Check required environment variables are present and non-empty
    try:
        settings = get_settings()
    except Exception as exc:
        # Pydantic will raise ValidationError for missing fields
        print(f"ERROR: Failed to load settings: {exc}", file=sys.stderr)
        sys.exit(1)

    # Validate DATABASE_URL is not empty
    if not settings.DATABASE_URL.strip():
        errors.append("DATABASE_URL is missing or empty")
    elif not _DATABASE_URL_PATTERN.match(settings.DATABASE_URL):
        errors.append(
            "DATABASE_URL has invalid format. "
            "Expected: postgresql:// or postgresql+asyncpg:// with host, port, and database"
        )

    # Validate TOKEN_PRIVATE_KEY length
    if not settings.TOKEN_PRIVATE_KEY.strip():
        errors.append("TOKEN_PRIVATE_KEY is missing or empty")
    elif len(settings.TOKEN_PRIVATE_KEY) < 10:
        errors.append("TOKEN_PRIVATE_KEY must be at least 10 characters")

    # Validate JIRA_BASE_URL starts with https://
    if not settings.JIRA_BASE_URL.strip():
        errors.append("JIRA_BASE_URL is missing or empty")
    elif not settings.JIRA_BASE_URL.startswith("https://"):
        errors.append("JIRA_BASE_URL must start with https://")

    # Validate JIRA_API_TOKEN is not empty
    if not settings.JIRA_API_TOKEN.strip():
        errors.append("JIRA_API_TOKEN is missing or empty")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    return settings
