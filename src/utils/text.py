"""Text normalization utilities for the DevSecOps Dashboard API."""

import re


def normalize_project_name(name: str) -> str:
    """Normalize a project name for comparison.

    Normalization steps:
    1. Lowercase the name
    2. Strip leading/trailing whitespace
    3. Remove 'zeb-' prefix if present
    4. Replace all hyphens with spaces
    5. Collapse multiple spaces into one
    6. Strip again after transformations

    Examples:
        "zeb-touchpoint-pj" → "touchpoint pj"
        "Touchpoint PJ"     → "touchpoint pj"
        "ZEB-My-Project"    → "my project"
        "  some-name  "     → "some name"

    Args:
        name: The raw project name string.

    Returns:
        Normalized lowercase string suitable for comparison.
    """
    if not name:
        return ""

    result = name.lower().strip()
    result = re.sub(r"^zeb-", "", result)
    result = result.replace("-", " ")
    result = re.sub(r"\s+", " ", result).strip()

    return result
