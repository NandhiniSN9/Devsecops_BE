"""Script to add log_error_to_db calls to report_repository.py"""

with open('src/repositories/report_repository.py', 'r') as f:
    content = f.read()

# Add imports
old_imports = '''"""Repository for report generation data access operations.

Provides queries for specializations, settings, email templates,
email recipients, email history, KPI data, at-risk projects,
and cron job tracking for the email notification service.
"""

import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.email_history import EmailHistory
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.email_template import EmailTemplate
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.project import Project
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.utils.logger import logger'''

new_imports = '''"""Repository for report generation data access operations.

Provides queries for specializations, settings, email templates,
email recipients, email history, KPI data, at-risk projects,
and cron job tracking for the email notification service.
"""

import asyncio
import traceback
import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.email_history import EmailHistory
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.email_template import EmailTemplate
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.project import Project
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.utils.helpers import log_error_to_db
from src.utils.logger import logger'''

content = content.replace(old_imports, new_imports)

# List of all functions in report_repository
functions = [
    "get_active_specializations",
    "get_settings_by_specialization_id",
    "get_last_sent_email_history",
    "get_email_template_by_name",
    "get_active_recipients_by_specialization",
    "get_kpi_history_by_specialization",
    "get_at_risk_projects",
    "create_email_history",
    "create_cron_job",
    "update_cron_job_status",
]

for func_name in functions:
    for error_var, error_type, prefix in [("db_exc", "SQLAlchemyError", "Database"), ("exc", "Exception", "Unexpected")]:
        old = f'''        except {error_type} as {error_var}:
            logger.error("{prefix} error in {func_name}", error=str({error_var}))
            raise'''
        
        new = f'''        except {error_type} as {error_var}:
            logger.error("{prefix} error in {func_name}", error=str({error_var}))
            asyncio.create_task(log_error_to_db(
                error_message=str({error_var}),
                error_function="{func_name}",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
        
        content = content.replace(old, new)

with open('src/repositories/report_repository.py', 'w') as f:
    f.write(content)

print("Done! Updated report_repository.py")
