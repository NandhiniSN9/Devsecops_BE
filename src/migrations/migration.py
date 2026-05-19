"""Auto-migration module for creating database tables on startup.

Uses SQLAlchemy inspect to check if tables exist and creates them
in the correct order (respecting foreign key dependencies).
"""

from sqlalchemy import inspect
from src.repositories.schema.artifact import Artifact
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

TABLE_ORDER_CREATION = [
    Specialization.__tablename__,
    Status.__tablename__,
    ErrorLog.__tablename__,
    EmailTemplate.__tablename__,
    CronJob.__tablename__,
    Project.__tablename__,
    DevsecopsTicket.__tablename__,
    Setting.__tablename__,
    KpiHistory.__tablename__,
    Repository.__tablename__,
    EmailRecipient.__tablename__,
    EmailHistory.__tablename__,
    JiraTicket.__tablename__,
    PipelineRun.__tablename__,
    Commit.__tablename__,
    PullRequest.__tablename__,
    SecurityScan.__tablename__,
    Artifact.__tablename__,
]

MODEL_CLASSES = {
    Specialization.__tablename__: Specialization,
    Status.__tablename__: Status,
    ErrorLog.__tablename__: ErrorLog,
    EmailTemplate.__tablename__: EmailTemplate,
    CronJob.__tablename__: CronJob,
    Project.__tablename__: Project,
    DevsecopsTicket.__tablename__: DevsecopsTicket,
    Setting.__tablename__: Setting,
    KpiHistory.__tablename__: KpiHistory,
    Repository.__tablename__: Repository,
    EmailRecipient.__tablename__: EmailRecipient,
    EmailHistory.__tablename__: EmailHistory,
    JiraTicket.__tablename__: JiraTicket,
    PipelineRun.__tablename__: PipelineRun,
    Commit.__tablename__: Commit,
    PullRequest.__tablename__: PullRequest,
    SecurityScan.__tablename__: SecurityScan,
    Artifact.__tablename__: Artifact,
}


class Migration:
    """Handles automatic database table creation on application startup.

    Inspects the database to check which tables exist and creates
    any missing tables in the correct dependency order.
    """

    def __init__(self, connection):
        """Initialize with a SQLAlchemy sync connection.

        Args:
            connection: SQLAlchemy sync connection (from run_sync).
        """
        self.connection = connection
        self.inspector = inspect(connection)

    def create_tables(self) -> list[str]:
        """Create any missing tables in dependency order.

        Returns:
            List of table names that were created.
        """
        try:
            created_tables = []

            for table_name in TABLE_ORDER_CREATION:
                if not self.inspector.has_table(table_name):
                    MODEL_CLASSES[table_name].__table__.create(bind=self.connection)
                    created_tables.append(table_name)
                    logger.info("Table created", table=table_name)
                else:
                    logger.debug("Table already exists, skipping", table=table_name)

            if created_tables:
                logger.info(
                    "Migration completed",
                    tables_created=len(created_tables),
                    tables=created_tables,
                )
            else:
                logger.info("Migration check completed — all tables exist")

            return created_tables

        except Exception as e:
            logger.warning("Migration Failed...., migration.py, create_tables()")