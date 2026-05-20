"""Script to add log_error_to_db calls to settings_repository.py"""

with open('src/repositories/settings_repository.py', 'r') as f:
    content = f.read()

# Add imports
old_imports = '''"""Repository for settings data access operations.

Provides CRUD operations for settings and email recipient management.
"""

import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.utils.logger import logger'''

new_imports = '''"""Repository for settings data access operations.

Provides CRUD operations for settings and email recipient management.
"""

import asyncio
import traceback
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.utils.helpers import log_error_to_db
from src.utils.logger import logger'''

content = content.replace(old_imports, new_imports)

# List of all functions in settings_repository
functions = [
    "get_specialization",
    "get_settings_by_specialization",
    "get_email_recipients",
    "update_setting_fields",
    "add_email_recipient",
    "get_recipient_by_id",
    "check_duplicate_recipient",
    "reactivate_recipient",
    "soft_delete_recipient",
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
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
        
        content = content.replace(old, new)

with open('src/repositories/settings_repository.py', 'w') as f:
    f.write(content)

print("Done! Updated settings_repository.py")
