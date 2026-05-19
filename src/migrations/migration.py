"""Auto-migration module for creating database tables on startup.

Uses SQLAlchemy Base.metadata.create_all() to create any missing tables.
This respects foreign key dependencies automatically.
"""

from src.repositories.schema.artifact import Artifact
from src.repositories.schema.base import Base
from src.repositories.schema.commit import Commit
from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.email_history import EmailHistory
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.email_template import EmailTemplate
from src.repositories.schema.error_log import ErrorLog
from src.repositories.schema.jira_ticket import JiraTicket
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.pipeline_run import PipelineRun
from src.repositories.schema.project import Project
from src.repositories.schema.pull_request import PullRequest
from src.repositories.schema.repository import Repository
from src.repositories.schema.security_scan import SecurityScan
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.utils.logger import logger

# Ensure all models are imported so Base.metadata knows about them
_ALL_MODELS = [
    Specialization, Status, ErrorLog, EmailTemplate, CronJob,
    Project, DevsecopsTicket, Setting, KpiHistory,
    Repository, EmailRecipient, EmailHistory, JiraTicket,
    PipelineRun, Commit, PullRequest, SecurityScan, Artifact,
]


def run_migration(connection) -> None:
    """Create all missing tables using Base.metadata.create_all.

    This is called via engine.run_sync() from the lifespan handler.
    SQLAlchemy's create_all uses checkfirst=True by default, so it
    only creates tables that don't already exist.

    Args:
        connection: A sync connection from run_sync.
    """
    try:
        Base.metadata.create_all(bind=connection)
        logger.info("Database migration completed — all tables ensured")
    except Exception as exc:
        logger.error("Migration failed", error=str(exc))
        raise
