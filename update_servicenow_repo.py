"""Script to add log_error_to_db calls to servicenow_repository.py"""
import re

with open('src/repositories/servicenow_repository.py', 'r') as f:
    content = f.read()

# Pattern to match: except blocks with logger.error followed by raise
# We need to add asyncio.create_task(log_error_to_db(...)) after each logger.error line

def add_log_error_to_db(content, func_name, error_var="db_exc", error_type="SQLAlchemyError"):
    """Add log_error_to_db call after logger.error for a specific function."""
    old = f'''        except {error_type} as {error_var}:
            logger.error("{("Database" if error_var == "db_exc" else "Unexpected")} error in {func_name}", error=str({error_var}))
            raise'''
    
    new = f'''        except {error_type} as {error_var}:
            logger.error("{("Database" if error_var == "db_exc" else "Unexpected")} error in {func_name}", error=str({error_var}))
            asyncio.create_task(log_error_to_db(
                error_message=str({error_var}),
                error_function="{func_name}",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise'''
    
    return content.replace(old, new)

# List of all functions in servicenow_repository
functions = [
    "get_project_by_sn_project_id",
    "get_project_by_name",
    "get_project_by_client",
    "get_project_by_normalized_name",
    "get_default_project",
    "get_inactive_status",
    "get_specialization_by_name",
    "create_project",
    "update_project",
    "create_ticket",
    "get_ticket_by_sn_or_devsec_id",
    "update_ticket",
    "get_repository_by_name_and_ticket",
    "get_repository_by_ado_repo_id_and_ticket",
    "update_repository",
    "create_repository",
    "mark_project_onboarded",
]

for func_name in functions:
    content = add_log_error_to_db(content, func_name, "db_exc", "SQLAlchemyError")
    content = add_log_error_to_db(content, func_name, "exc", "Exception")

with open('src/repositories/servicenow_repository.py', 'w') as f:
    f.write(content)

print("Done! Updated servicenow_repository.py")
