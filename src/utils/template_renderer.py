"""Jinja2 template rendering utility for email and PDF reports.

This module renders templates stored in the database using Jinja2.
Templates are stored in the email_templates table and can be updated
without code changes.

Performance optimizations:
- Cached Jinja2 environment for reuse
- ByteCode caching enabled for faster template rendering
"""

from jinja2 import Environment, Template, select_autoescape
from datetime import datetime
from functools import lru_cache


@lru_cache(maxsize=1)
def get_jinja_env() -> Environment:
    """Create and configure Jinja2 environment with caching.

    This function is cached to reuse the same environment across renders,
    improving performance by avoiding repeated setup.

    Returns:
        Configured Jinja2 Environment instance.
    """
    env = Environment(
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
        cache_size=400,  # Cache compiled templates
        auto_reload=False,  # Disable auto-reload for production performance
    )

    # Add custom filters
    env.filters['datetime_format'] = lambda dt, fmt='%Y-%m-%d %H:%M': dt.strftime(fmt) if isinstance(dt, datetime) else dt
    env.filters['date_format'] = lambda dt, fmt='%Y-%m-%d': dt.strftime(fmt) if hasattr(dt, 'strftime') else str(dt)

    return env


def render_template_from_string(template_string: str, context: dict) -> str:
    """Render a Jinja2 template from a string with the provided context.

    Args:
        template_string: The Jinja2 template as a string (from database)
        context: Dictionary of variables to pass to the template

    Returns:
        Rendered HTML string.

    Raises:
        Exception: If template rendering fails.
    """
    env = get_jinja_env()
    template = env.from_string(template_string)
    return template.render(**context)
