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

# Maximum number of specialization IDs allowed in filter
MAX_SPECIALIZATION_FILTER_COUNT: int = 50

# Fixed UUID namespace for deterministic client ID generation (UUID v5)
CLIENT_UUID_NAMESPACE: uuid.UUID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


# ============================================================
# Settings Class
# ============================================================


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    TOKEN_PRIVATE_KEY: str
    JIRA_BASE_URL: str
    JIRA_API_TOKEN: str

    model_config = ConfigDict(env_file=".env")


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
