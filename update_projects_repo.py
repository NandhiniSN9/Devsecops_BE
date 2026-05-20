"""Script to add log_error_to_db calls to projects_repository.py"""

with open('src/repositories/projects_repository.py', 'r') as f:
    content = f.read()

# Add imports
old_imports = '''"""Repository for projects data access operations.

Provides project listing with filtering, sorting, pagination,
and project action operations (mark not applicable, mark complete).
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.jira_ticket import JiraTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.status import Status
from src.utils.logger import logger'''

new_imports = '''"""Repository for projects data access operations.

Provides project listing with filtering, sorting, pagination,
and project action operations (mark not applicable, mark complete).
"""

import asyncio
import traceback
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.jira_ticket import JiraTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.status import Status
from src.utils.helpers import log_error_to_db
from src.utils.logger import logger'''

content = content.replace(old_imports, new_imports)

# The projects_repository uses logger.exception with extra={} pattern
# Pattern: except Exception as e:\n            logger.exception("...", extra={...})\n            raise

# get_projects
old = '''        except Exception as e:
            logger.exception("Failed to fetch projects", extra={"error": str(e)})
            raise'''
new = '''        except Exception as e:
            logger.exception("Failed to fetch projects", extra={"error": str(e)})
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_projects",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# get_repositories_for_project
old = '''        except Exception as e:
            logger.exception(
                "Failed to fetch repositories for project",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            raise'''
new = '''        except Exception as e:
            logger.exception(
                "Failed to fetch repositories for project",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_repositories_for_project",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# get_project_by_id
old = '''        except Exception as e:
            logger.exception(
                "Failed to fetch project by id",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            raise'''
new = '''        except Exception as e:
            logger.exception(
                "Failed to fetch project by id",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_project_by_id",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# get_status_by_name
old = '''        except Exception as e:
            logger.exception(
                "Failed to fetch status by name",
                extra={"status_name": status_name, "error": str(e)},
            )
            raise'''
new = '''        except Exception as e:
            logger.exception(
                "Failed to fetch status by name",
                extra={"status_name": status_name, "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_status_by_name",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# update_project_not_applicable
old = '''        except Exception:
            logger.exception(
                "Failed to update project to not-applicable",
                extra={"project_id": str(project_id)},
            )
            raise'''
new = '''        except Exception as exc:
            logger.exception(
                "Failed to update project to not-applicable",
                extra={"project_id": str(project_id)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_project_not_applicable",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# update_project_complete
old = '''        except Exception:
            logger.exception(
                "Failed to update project to complete",
                extra={"project_id": str(project_id)},
            )
            raise'''
new = '''        except Exception as exc:
            logger.exception(
                "Failed to update project to complete",
                extra={"project_id": str(project_id)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_project_complete",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# create_jira_ticket
old = '''        except Exception:
            logger.exception(
                "Failed to create local jira_ticket record",
                extra={"project_id": str(project_id), "jira_id": jira_id},
            )
            raise'''
new = '''        except Exception as exc:
            logger.exception(
                "Failed to create local jira_ticket record",
                extra={"project_id": str(project_id), "jira_id": jira_id},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_jira_ticket",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# commit
old = '''        except Exception as e:
            logger.exception("Failed to commit transaction", extra={"error": str(e)})
            raise'''
new = '''        except Exception as e:
            logger.exception("Failed to commit transaction", extra={"error": str(e)})
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="commit",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# rollback
old = '''        except Exception as e:
            logger.exception("Failed to rollback transaction", extra={"error": str(e)})
            raise'''
new = '''        except Exception as e:
            logger.exception("Failed to rollback transaction", extra={"error": str(e)})
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="rollback",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# get_status_name_for_project
old = '''        except Exception as e:
            logger.exception(
                "Failed to fetch status name for project",
                extra={"project_id": str(project.project_id), "error": str(e)},
            )
            raise'''
new = '''        except Exception as e:
            logger.exception(
                "Failed to fetch status name for project",
                extra={"project_id": str(project.project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_status_name_for_project",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

# get_not_applicable_details
old = '''        except Exception as e:
            logger.exception(
                "Failed to fetch not_applicable_details",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            raise'''
new = '''        except Exception as e:
            logger.exception(
                "Failed to fetch not_applicable_details",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_not_applicable_details",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
content = content.replace(old, new)

with open('src/repositories/projects_repository.py', 'w') as f:
    f.write(content)

print("Done! Updated projects_repository.py")
