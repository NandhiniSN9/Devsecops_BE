## SOLDEF-ZDAD-48 - Implement API to Fetch and Update Project DevSecOps Applicability and Completion Status

### <u>Project Details</u>
- **Project ID:** ZDAD  
- **Project Name:** DevSecOps Jira Dashboard  

### <u>Story Details</u>
- **Story ID:** ZDAD-48  
- **Story Name:** Implement API to Fetch and Update Project DevSecOps Applicability and Completion Status  
- **Story Description:**  
  The DevSecOps Dashboard Projects module provides the ability to retrieve a paginated list of projects with filtering capabilities (search, status, client, specialization, period), expand each project to view its associated repositories with onboarded date and status, sort projects by name or onboarded date, and perform actions on projects: mark as "Not Applicable" (with reason, comments, and optional evidence file) or mark as "Complete".
- **Scope:**  
  Implement the Projects API for the DevSecOps Dashboard. The `GET /api/v1/projects` endpoint returns a paginated, filterable, sortable list of projects with nested repositories. The `POST /api/v1/projects/action` endpoint allows marking a project as "Not Applicable" (creating a Jira ticket record with reason, comments, and optional evidence) or "Complete" (updating status and setting completed_at timestamp). All service errors are logged to the `error_log` table.
- **Acceptance Criteria:**
  - The `GET /api/v1/projects` endpoint returns a paginated list of projects with id, name, onboardedDate, repositoryCount, status, and nested repositories array.
  - The endpoint supports filtering by search text, status, client, specialization, and period.
  - The endpoint supports sorting by project name or onboarded date in ascending or descending order.
  - The `POST /api/v1/projects/action` endpoint marks a project as "Not Applicable" with reason_category, comments, and optional evidence_file, creating a Jira ticket record.
  - The `POST /api/v1/projects/action` endpoint marks a project as "Complete", updating status to Completed and setting completed_at.
  - Invalid inputs return HTTP 400 with descriptive validation error messages.
  - Non-existent projects return HTTP 404.
  - All unhandled exceptions are logged to the `error_log` table with full context.
  - Unit tests cover positive and negative cases for both endpoints; all defects found during testing are fixed before release.

### <u> Table of Contents </u>
- [Section 1: Functional Requirements](#Section-1:-Functional-Requirements)
    - [1.1 Overview](#1.1-Overview)
    - [1.2 Requirement Details](#1.2-Requirement-Details)
    - [1.3 Database Schema](#1.3-Database-Schema)
    - [1.4 Project Artifacts](#1.4-Project-Artifacts)
    - [1.5 Dependencies](#1.5-Dependencies)
- [Section 2: Non Functional Requirements](#Section-2:-Non-Functional-Requirements)
- [2.1 Infrastructure and Deployment](#2.1-Infrastructure-and-Deployment)
    - [2.1.1 Overview](#2.1-Overview)
    - [2.1.2 Requirement Details](#2.2-Requirement-Details)
    - [2.1.3 Project Artifacts](#2.3-Project-Artifacts)
- [2.2 Architecture and System Design](#2.2-Architecture-and-System-Design)
    - [2.2.1 Security and Compliance](#2.2.1-Security-and-Compliance)
    - [2.2.2 System Performance](#2.2.2-System-Performance)
    - [2.2.3 Availability and Reliability](#2.2.3-Availability-and-Reliability)
    - [2.2.4 Cost Efficiency](#2.2.4-Cost-Efficiency)
    - [2.2.5 Traceability and Observability](#2.2.5-Traceability-and-Observability)
- [Section 3: In Scope and Out Scope](#Section-3:-In-Scope-and-Out-Scope)
    - [3.1 In Scope Details](#3.1-In-Scope-Details)
    - [3.2 Out Scope Details](#3.2-Out-Scope-Details)
- [Section 4: Solution Diagrams](#Section-4:-Solution-Diagrams)
    - [4.1 UI/UX Design Diagram](#4.1-UI/UX-Design-Diagram)
    - [4.2 Architecture Design Diagram](#4.2-Architecture-Design-Diagram)
    - [4.3 Infrastructure Design Diagram](#4.3-Infrastructure-Design-Diagram)


### <u> Section 1: Functional Requirements </u>

#### <u> 1.1 Overview </u>

The Projects API is a core component of the DevSecOps Jira Dashboard backend that enables delivery leads and stakeholders to view, filter, sort, and manage the portfolio of onboarded projects. The API exposes two endpoints: `GET /api/v1/projects` which returns a paginated list of projects with comprehensive filtering (free-text search, status, client, specialization, time period), sorting (by project name or onboarded date), and nested repository expansion; and `POST /api/v1/projects/action` which allows performing lifecycle actions on projects — marking them as "Not Applicable" (with reason category, comments, and optional evidence file attachment, which creates a Jira ticket record) or marking them as "Complete" (updating the project status to Completed and recording the completion timestamp). Projects are linked to repositories through the `devsecops_tickets` table, and each project's repository count and nested repository details (name, onboarded date, status) are resolved through this relationship. Both endpoints require JWT Bearer token authentication and return standardized JSON responses following the `BaseResponse` schema. All unhandled exceptions are logged to the `error_log` database table for traceability and debugging. The implementation follows the layered architecture pattern: Routes → Services → Repositories → Schema, with Pydantic models for request/response validation.

#### <u> 1.2 Requirement Details </u>

- **ZDAD-48-FR01: Paginated Project List with Filtering and Sorting**
- **ZDAD-48-FR02: Project Action — Mark Not Applicable**
- **ZDAD-48-FR03: Project Action — Mark Complete**
- **ZDAD-48-FR04: Input Validation**
- **ZDAD-48-FR05: Error Logging**


##### <u> 1.2.1 ZDAD-48-FR01: Paginated Project List with Filtering and Sorting </u>

##### Description:
The system shall expose a `GET /api/v1/projects` endpoint that returns a paginated list of projects with support for filtering by search text, status, client, specialization, and time period. The response includes each project's metadata and a nested array of associated repositories. Sorting is supported by project name or onboarded date in ascending or descending order.

##### Request Parameters:
| Parameter | Location | Type | Required | Default | Description |
|-----------|----------|------|----------|---------|-------------|
| `period` | Query | String (enum) | No | `last_month` | Time period filter: `last_week`, `last_month`, `last_3_months`, `last_6_months`, `last_year` |
| `search` | Query | String | No | — | Free text search on project name (case-insensitive partial match) |
| `status` | Query | String (CSV) | No | — | Comma-separated list of status IDs to filter by |
| `client` | Query | String (CSV) | No | — | Comma-separated list of client IDs to filter by |
| `specialization` | Query | String (CSV) | No | — | Comma-separated list of specialization IDs to filter by |
| `offset` | Query | Integer | No | `0` | Number of items to skip for pagination |
| `limit` | Query | Integer | No | `10` | Number of items per page |
| `sort_by` | Query | String (enum) | No | `project` | Field to sort by: `project`, `onboarded_date` |
| `sort_order` | Query | String (enum) | No | `asc` | Sort direction: `asc`, `desc` |

##### Processing Logic:
1. Validate all query parameters using Pydantic models. Return HTTP 400 for invalid values.
2. Build the base query on the `projects` table where `is_active = 1`.
3. Apply `period` filter: only include projects with `onboarded_date` within the specified time range relative to the current date.
4. Apply `search` filter: case-insensitive partial match on `projects.project_name` using SQL `ILIKE`.
5. Apply `status` filter: join with `statuses` table and filter by matching `status_id` values from the comma-separated list.
6. Apply `client` filter: filter by matching `projects.client` values from the comma-separated list.
7. Apply `specialization` filter: join with `devsecops_tickets` table and filter by matching `specialization_id` values.
8. Compute `totalItems` count before applying pagination.
9. Apply sorting by the specified field (`project_name` or `onboarded_date`) and direction.
10. Apply pagination using `offset` and `limit`.
11. For each project in the result set, resolve the nested repositories by querying `repositories` through `devsecops_tickets` where `devsecops_tickets.project_id = projects.project_id` or `devsecops_tickets.sn_project_id = projects.sn_project_id`.
12. Determine each repository's status based on pipeline run results (PASSED if latest pipeline run succeeded, FAILED otherwise).
13. Compose the response with projects array and pagination metadata.

##### Response Structure (200):
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Projects retrieved successfully",
  "data": {
    "projects": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Project Xenon",
        "onboardedDate": "2026-02-20",
        "repositoryCount": 3,
        "status": "COMPLETED",
        "repositories": [
          {
            "id": "880e8400-e29b-41d4-a716-446655440030",
            "name": "xenon-infra-core",
            "onboardedDate": "2026-02-27",
            "status": "PASSED"
          }
        ]
      }
    ],
    "pagination": {
      "offset": 0,
      "limit": 10,
      "totalItems": 44
    }
  }
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid query parameter values (invalid period, sort_by, sort_order, non-integer offset/limit) |
| 401 | Missing or invalid JWT Bearer token |
| 500 | Unexpected server error (logged to `error_log`) |

##### Data Source:
- Projects are read from the `projects` table joined with `statuses` for status name resolution.
- Repositories are resolved through `devsecops_tickets` → `repositories` relationship.
- Specialization filtering uses `devsecops_tickets.specialization_id`.
- Repository status is derived from the latest `pipeline_runs` record for each repository.

##### Acceptance Criteria:
- The endpoint returns HTTP 200 with correct project list when called with valid parameters.
- Default values are applied when optional parameters are omitted (period=last_month, offset=0, limit=10, sort_by=project, sort_order=asc).
- Free-text search performs case-insensitive partial matching on project name.
- Multiple filter values (comma-separated) are applied with OR logic within the same filter and AND logic across different filters.
- Pagination metadata (`offset`, `limit`, `totalItems`) accurately reflects the filtered result set.
- Each project includes a `repositoryCount` matching the length of the `repositories` array.
- Repositories nested within each project include `id`, `name`, `onboardedDate`, and `status`.
- Sorting by `project` sorts alphabetically by project name; sorting by `onboarded_date` sorts chronologically.
- Response follows the standardized `BaseResponse` schema with `status_code`, `status`, `message`, and `data` fields.


##### <u> 1.2.2 ZDAD-48-FR02: Project Action — Mark Not Applicable </u>

##### Description:
The system shall support marking a project as "Not Applicable" through the `POST /api/v1/projects/action` endpoint. This action indicates that the project is not eligible for DevSecOps onboarding. When triggered, the system updates the project's `is_applicable` flag to FALSE, changes the project status to "Not Applicable", and creates a Jira ticket record in the `jira_tickets` table to track the reason, comments, and optional evidence file.

##### Request Format:
- **Content Type:** `multipart/form-data`
- **Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | UUID | Yes | UUID of the project to perform the action on |
| `action` | String | Yes | Must be `mark_not_applicable` |
| `reason_category` | String | Yes (for this action) | Reason category explaining why the project is not applicable |
| `comments` | String | Yes (for this action) | Detailed comments explaining the reason |
| `evidence_file` | Binary | No | Optional evidence file attachment supporting the decision |

##### Processing Logic:
1. Validate the request body using Pydantic model. Return HTTP 400 for missing required fields.
2. Validate `project_id` is a valid UUID format. Return HTTP 400 if invalid.
3. Query the `projects` table for the project with matching `project_id` and `is_active = 1`. Return HTTP 404 if not found.
4. Validate that `reason_category` and `comments` are provided (required for `mark_not_applicable`). Return HTTP 400 if missing.
5. Look up the "Not Applicable" status from the `statuses` table.
6. Update the project record:
   - Set `is_applicable = FALSE`
   - Set `status_id` to the "Not Applicable" status UUID
   - Set `modified_at = NOW()`
   - Set `modified_by` to the authenticated user identifier
7. If `evidence_file` is provided, upload it to external storage (e.g., S3) and obtain the URL.
8. Create a new record in the `jira_tickets` table:
   - `jira_ticket_id`: Auto-generated UUID
   - `project_id`: The project UUID
   - `jira_id`: Auto-generated identifier (format: "ZDAD-NA-{timestamp}")
   - `type`: "Not Applicable"
   - `assignee`: Authenticated user identifier
   - `priority`: "Medium"
   - `status`: "Open"
   - `reason_category`: From request
   - `comments`: From request
   - `evidence_url`: URL of uploaded file (or NULL if no file)
   - `created_at`: Current timestamp
   - `created_by`: Authenticated user identifier
9. Commit the transaction.
10. Return HTTP 200 with success response.

##### Response Structure (200):
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Action performed successfully"
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Missing required fields (reason_category, comments), invalid UUID format, invalid action value |
| 401 | Missing or invalid JWT Bearer token |
| 404 | Project not found or inactive |
| 500 | Unexpected server error (logged to `error_log`) |

##### Acceptance Criteria:
- A valid request with action `mark_not_applicable` sets `is_applicable = FALSE` on the project.
- The project status is updated to "Not Applicable" in the `statuses` lookup.
- A new record is created in `jira_tickets` with the reason_category, comments, and evidence_url.
- Missing `reason_category` or `comments` returns HTTP 400 with a descriptive error message.
- Optional `evidence_file` is uploaded and its URL stored in the Jira ticket record.
- Non-existent `project_id` returns HTTP 404 with message "Project not found".
- The operation is atomic — if any step fails, the entire transaction is rolled back.


##### <u> 1.2.3 ZDAD-48-FR03: Project Action — Mark Complete </u>

##### Description:
The system shall support marking a project as "Complete" through the `POST /api/v1/projects/action` endpoint. This action indicates that the project has successfully completed DevSecOps onboarding. When triggered, the system updates the project status to "Completed" and records the completion timestamp.

##### Request Format:
- **Content Type:** `multipart/form-data`
- **Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | UUID | Yes | UUID of the project to perform the action on |
| `action` | String | Yes | Must be `mark_complete` |

##### Processing Logic:
1. Validate the request body using Pydantic model. Return HTTP 400 for missing required fields.
2. Validate `project_id` is a valid UUID format. Return HTTP 400 if invalid.
3. Query the `projects` table for the project with matching `project_id` and `is_active = 1`. Return HTTP 404 if not found.
4. Look up the "Completed" status from the `statuses` table.
5. Update the project record:
   - Set `status_id` to the "Completed" status UUID
   - Set `completed_at = NOW()`
   - Set `modified_at = NOW()`
   - Set `modified_by` to the authenticated user identifier
6. Commit the transaction.
7. Return HTTP 200 with success response.

##### Response Structure (200):
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Action performed successfully"
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Missing required fields (project_id, action), invalid UUID format |
| 401 | Missing or invalid JWT Bearer token |
| 404 | Project not found or inactive |
| 500 | Unexpected server error (logged to `error_log`) |

##### Acceptance Criteria:
- A valid request with action `mark_complete` updates the project status to "Completed".
- The `completed_at` field is set to the current timestamp.
- No additional fields (reason_category, comments, evidence_file) are required for this action.
- Non-existent `project_id` returns HTTP 404 with message "Project not found".
- The `modified_at` timestamp is updated on the project record.


##### <u> 1.2.4 ZDAD-48-FR04: Input Validation </u>

##### Description:
The system shall validate all incoming request data for both the GET and POST endpoints. Invalid inputs must result in an HTTP 400 response with a descriptive error message indicating which parameter or field is invalid and what values are accepted. Validation is implemented using Pydantic v2 models with strict type constraints.

##### Validation Rules — GET `/api/v1/projects`:
| Parameter | Rule | Error Message |
|-----------|------|---------------|
| `period` | Must be one of: last_week, last_month, last_3_months, last_6_months, last_year | "Invalid query parameter: 'period' must be one of [last_week, last_month, last_3_months, last_6_months, last_year]" |
| `offset` | Must be a non-negative integer | "Invalid query parameter: 'offset' must be a non-negative integer" |
| `limit` | Must be a positive integer (1-100) | "Invalid query parameter: 'limit' must be between 1 and 100" |
| `sort_by` | Must be one of: project, onboarded_date | "Invalid query parameter: 'sort_by' must be one of [project, onboarded_date]" |
| `sort_order` | Must be one of: asc, desc | "Invalid query parameter: 'sort_order' must be one of [asc, desc]" |

##### Validation Rules — POST `/api/v1/projects/action`:
| Field | Rule | Error Message |
|-------|------|---------------|
| `project_id` | Required, must be valid UUID format | "project_id is required and must be a valid UUID" |
| `action` | Required, must be one of: mark_not_applicable, mark_complete | "action must be one of [mark_not_applicable, mark_complete]" |
| `reason_category` | Required when action is mark_not_applicable | "reason_category is required for mark_not_applicable action" |
| `comments` | Required when action is mark_not_applicable | "comments is required for mark_not_applicable action" |

##### Error Response Format:
```json
{
  "status_code": 400,
  "status": "failed",
  "message": "Invalid query parameter: 'period' must be one of [last_week, last_month, last_3_months, last_6_months, last_year]",
  "data": []
}
```

##### Acceptance Criteria:
- All validation rules are enforced before any database operations.
- Error messages clearly identify the invalid parameter/field and accepted values.
- Valid requests with all optional parameters omitted are processed successfully with defaults.
- Pydantic validation errors are caught and transformed into the standardized error response format.
- Comma-separated filter values (status, client, specialization) with invalid UUIDs are handled gracefully (invalid IDs are ignored).


##### <u> 1.2.5 ZDAD-48-FR05: Error Logging </u>

##### Description:
The system shall log all unhandled exceptions occurring during project list retrieval or project action operations to the `error_log` database table. This provides a persistent audit trail for debugging and incident investigation. The error logging mechanism uses the same global exception handler established in ZDAD-34.

##### Error Log Table Fields:
- `error_id` — Auto-generated UUID primary key.
- `error_message` — The exception message text.
- `error_function` — The function name where the error occurred (e.g., "get_projects", "perform_project_action").
- `error_file` — The file path where the error originated (e.g., "src/services/projects_service.py").
- `stack_trace` — Full Python stack trace for debugging.
- `created_at` — Timestamp when the error was logged.
- `created_by` — "projects_service".

##### Acceptance Criteria:
- All unhandled exceptions in the Projects API are captured and logged to `error_log`.
- The error log entry contains the function name, file name, error message, and stack trace.
- Error logging does not interfere with the error response returned to the client (non-blocking).
- HTTP 500 responses are always accompanied by an `error_log` entry.
- Validation errors (HTTP 400) and not-found errors (HTTP 404) are NOT logged to `error_log` (they are expected application behavior).


#### <u> 1.3 Database Schema </u>

The following tables are directly involved in the Projects API (as defined in `design/er_diagram.mmd`):

##### projects
| Column | Type | Constraints |
|--------|------|-------------|
| project_id | UUID | PK |
| status_id | UUID | FK → statuses.status_id |
| sn_project_id | VARCHAR | ServiceNow project identifier |
| project_name | VARCHAR | NOT NULL |
| onboarded_date | DATE | NOT NULL |
| project_type | VARCHAR | NOT NULL |
| is_applicable | BOOLEAN | DEFAULT TRUE |
| client | VARCHAR | |
| completed_at | DATETIME | |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### statuses
| Column | Type | Constraints |
|--------|------|-------------|
| status_id | UUID | PK |
| status_name | VARCHAR | NOT NULL |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### devsecops_tickets
| Column | Type | Constraints |
|--------|------|-------------|
| ticket_id | UUID | PK |
| specialization_id | UUID | FK → specializations.specialization_id |
| project_id | UUID | NULLABLE |
| sn_project_id | VARCHAR | FK → projects.sn_project_id |
| project_name | VARCHAR | NOT NULL |
| client | VARCHAR | |
| requested_by | VARCHAR | |
| approver | VARCHAR | |
| sync_method | VARCHAR | |
| requested_at | DATETIME | |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### repositories
| Column | Type | Constraints |
|--------|------|-------------|
| repository_id | UUID | PK |
| ticket_id | UUID | FK → devsecops_tickets.ticket_id |
| repository_name | VARCHAR | NOT NULL |
| ado_repo_id | VARCHAR | |
| pipeline_runs_count | INTEGER | DEFAULT 0 |
| success_rate | FLOAT | DEFAULT 0 |
| last_run_at | DATETIME | |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### jira_tickets
| Column | Type | Constraints |
|--------|------|-------------|
| jira_ticket_id | UUID | PK |
| project_id | UUID | FK → projects.project_id |
| jira_id | VARCHAR | NOT NULL |
| type | VARCHAR | NOT NULL |
| assignee | VARCHAR | NOT NULL |
| priority | VARCHAR | NOT NULL |
| status | VARCHAR | NOT NULL |
| reason_category | VARCHAR | NOT NULL |
| comments | TEXT | NOT NULL |
| evidence_url | TEXT | |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### specializations
| Column | Type | Constraints |
|--------|------|-------------|
| specialization_id | UUID | PK |
| specialization_name | VARCHAR | NOT NULL |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### error_log
| Column | Type | Constraints |
|--------|------|-------------|
| error_id | UUID | PK |
| error_message | TEXT | NOT NULL |
| error_function | TEXT | NOT NULL |
| error_file | TEXT | NOT NULL |
| stack_trace | TEXT | |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### Key Relationships:
- `projects.status_id` → `statuses.status_id` (each project has one status)
- `devsecops_tickets.specialization_id` → `specializations.specialization_id` (links tickets to specializations)
- `devsecops_tickets.sn_project_id` → `projects.sn_project_id` (links tickets to projects)
- `devsecops_tickets.project_id` → `projects.project_id` (direct project link, nullable)
- `repositories.ticket_id` → `devsecops_tickets.ticket_id` (repositories belong to tickets)
- `jira_tickets.project_id` → `projects.project_id` (Jira tickets linked to projects)


#### <u> 1.4 Project Artifacts </u>

- `api/openapi.yaml` — Full OpenAPI 3.0.3 specification defining the `GET /api/v1/projects` and `POST /api/v1/projects/action` endpoints, request/response schemas (`ProjectsListSuccessResponse`, `ProjectItem`, `RepositoryItem`, `Pagination`, `ProjectActionRequest`, `ProjectActionSuccessResponse`), and error response formats.
- `design/er_diagram.mmd` — Mermaid ER diagram showing all database tables and relationships including `projects`, `statuses`, `devsecops_tickets`, `repositories`, `jira_tickets`, `specializations`, and `error_log`.
- `design/requirements.md` — High-level requirements document for the Projects module (ZDAD-48) with acceptance criteria and affected components.

#### <u> 1.5 Dependencies </u>

- **Python 3.12+** — Runtime environment
- **FastAPI** — Web framework for building the REST API
- **SQLAlchemy** — ORM for PostgreSQL database access (queries on `projects`, `statuses`, `devsecops_tickets`, `repositories`, `jira_tickets`, `error_log`)
- **Pydantic v2** — Request/response model validation and serialization
- **PostgreSQL** — Primary database storing projects, repositories, Jira tickets, and error logs
- **python-jose / PyJWT** — JWT token decoding and validation (shared with existing auth middleware)
- **Uvicorn** — ASGI server for running the FastAPI application
- **python-multipart** — Required for `multipart/form-data` parsing (evidence file upload)
- **File Storage Service** — External storage (e.g., Azure Blob Storage / S3) for evidence file uploads



### <u> Section 2: Non Functional Requirements </u>

### 2.1 Infrastructure and Deployment

#### <u> 2.1.1 Overview </u>

The Projects API is deployed as part of the existing DevSecOps Jira Dashboard backend application on Azure App Service. No separate service or infrastructure is required — the projects routes are registered within the existing FastAPI application alongside the Overview API, Settings API, and ServiceNow Sync routes. The application is a Python FastAPI service running on Uvicorn, packaged as a Docker container image and deployed to Azure App Service. The service connects to the same Azure Database for PostgreSQL instance and shares the same JWT middleware, error handling, and logging infrastructure established in ZDAD-34. The `POST /api/v1/projects/action` endpoint requires `multipart/form-data` support for evidence file uploads, which are stored in external blob storage. Environment-specific configurations are managed through Azure App Service application settings and environment variables, ensuring no secrets are hardcoded in the application code. The deployment pipeline ensures zero-downtime deployments with health check validation before traffic routing.

#### <u> 2.1.2 Requirement Details </u>

- **ZDAD-48-NFR01: Shared Deployment with Existing Application**
- **ZDAD-48-NFR02: Environment Configuration**
- **ZDAD-48-NFR03: Health Check Compatibility**

##### <u> 2.1.2.1 ZDAD-48-NFR01: Shared Deployment with Existing Application </u>

##### Description:
The Projects API endpoints shall be deployed as additional routes within the existing FastAPI application. No separate service or deployment is required. The projects routes are registered via a dedicated `APIRouter` with appropriate prefix and share the same database connection pool, JWT middleware, and error handling infrastructure established in ZDAD-34.

##### Deployment Configuration:
- **Runtime:** Python 3.12+ container image
- **ASGI Server:** Uvicorn with configurable workers
- **Port:** Application listens on port 8080 (configurable via `PORT` environment variable)
- **Route Registration:** Projects routes are added via `APIRouter` with prefix `/api/v1`.
- **Database:** Uses the same SQLAlchemy engine and session factory.
- **Authentication:** Uses the same JWT middleware.
- **Error Handling:** Uses the same global exception handler that logs to `error_log`.
- **File Upload:** `python-multipart` dependency required for multipart/form-data parsing.

##### Acceptance Criteria:
- The projects endpoints are accessible after deployment without additional infrastructure changes.
- Existing endpoints (Overview, Filters, Settings, Sync) continue to function without disruption.
- The application starts successfully with the new routes registered.
- Health check and readiness endpoints remain unaffected.
- Evidence file uploads are handled correctly via multipart/form-data.

##### <u> 2.1.2.2 ZDAD-48-NFR02: Environment Configuration </u>

##### Description:
All application configuration shall be managed through environment variables. The Projects API uses the same environment variables as the existing application. An additional optional variable for file storage configuration may be required for evidence file uploads.

##### Required Environment Variables (shared with existing application):
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT token validation | Yes |
| `JWT_ALGORITHM` | Algorithm used for JWT (default: HS256) | No |
| `APP_ENV` | Environment identifier (development, staging, production) | Yes |
| `LOG_LEVEL` | Application log level (default: INFO) | No |
| `PORT` | Application port (default: 8080) | No |
| `STORAGE_CONNECTION_STRING` | Azure Blob Storage / S3 connection string for evidence files | Yes (for mark_not_applicable with evidence) |

##### Acceptance Criteria:
- No new mandatory environment variables are required beyond the existing set (storage is optional if no evidence file is uploaded).
- The application uses the existing `DATABASE_URL` for all projects-related database operations.
- The existing JWT configuration is reused for projects endpoint authentication.

##### <u> 2.1.2.3 ZDAD-48-NFR03: Health Check Compatibility </u>

##### Description:
The addition of Projects API routes shall not affect the existing health check (`/health`) and readiness (`/ready`) endpoints. The readiness endpoint continues to validate database connectivity, which implicitly covers the projects-related tables.

##### Acceptance Criteria:
- `GET /health` continues to return HTTP 200 with `{"status": "healthy"}`.
- `GET /ready` continues to validate database connectivity.
- Adding projects routes does not increase application startup time significantly.

#### <u> 2.1.3 Project Artifacts </u>

- `api/openapi.yaml` — API specification including projects endpoints
- `design/er_diagram.mmd` — Database schema reference for projects-related tables



### 2.2 Architecture and System Design

#### <u> 2.2.1 Security and Compliance </u>

##### JWT Authentication:
All Projects API endpoints require a valid JWT Bearer token in the `Authorization` header. The middleware validates the token signature, expiration, and required claims before allowing the request to proceed to the route handler. Invalid or expired tokens result in an HTTP 401 Unauthorized response.

##### Token Validation Flow:
1. Extract the `Authorization` header from the incoming request.
2. Verify the header contains a `Bearer` prefix followed by the token.
3. Decode and validate the JWT token using the configured secret key and algorithm.
4. Check token expiration (`exp` claim) — reject if expired.
5. Attach decoded token claims to the request context for downstream use.
6. If validation fails at any step, return HTTP 401 with standardized error response.

##### Input Validation:
- All query parameters and request body fields are validated using Pydantic models with strict type constraints.
- SQL injection is prevented by using SQLAlchemy ORM with parameterized queries (no raw SQL).
- UUID format validation prevents malformed identifiers from reaching the database layer.
- File upload validation ensures only allowed file types and sizes are accepted for evidence files.

##### File Upload Security:
- Evidence files are validated for maximum size (configurable, default 10MB).
- File content type is validated against an allowlist (PDF, PNG, JPG, DOCX).
- Files are stored in external blob storage with unique generated names to prevent path traversal.
- File URLs are not directly exposed to end users — access is controlled via pre-signed URLs or internal references.

#### <u> 2.2.2 System Performance </u>

##### Database Query Optimization:
- The GET endpoint uses efficient JOINs between `projects`, `statuses`, `devsecops_tickets`, and `repositories` tables.
- Database indexes are maintained on frequently queried columns: `projects.status_id`, `projects.project_name`, `projects.onboarded_date`, `projects.client`, `projects.is_active`, `devsecops_tickets.specialization_id`, `devsecops_tickets.project_id`.
- Pagination is applied at the database level using SQL `OFFSET` and `LIMIT` to avoid loading unnecessary records into memory.
- The `totalItems` count query is executed separately with the same filters but without pagination for accurate count.
- SQLAlchemy connection pooling is configured to reuse database connections efficiently.

##### Response Efficiency:
- Repositories are eagerly loaded with the project query to minimize N+1 query problems.
- The response includes all necessary data in a single call, eliminating the need for subsequent API calls to fetch repository details.

#### <u> 2.2.3 Availability and Reliability </u>

##### Error Resilience:
- All unhandled exceptions are caught by the global exception handler that returns HTTP 500 and logs the error to the `error_log` table.
- Database connection failures are handled gracefully with appropriate error responses.
- The POST endpoint uses database transactions — if any operation fails (status update, Jira ticket creation), the entire update is rolled back to maintain data consistency.
- File upload failures do not prevent the project status update — the system handles partial failures gracefully.

##### Deployment Reliability:
- Azure App Service provides built-in auto-restart on application crashes.
- Health check endpoints enable Azure to detect and replace unhealthy instances.
- The Projects API is stateless — any instance can serve any request.

#### <u> 2.2.4 Cost Efficiency </u>

##### Resource Optimization:
- The Projects API adds minimal overhead to the existing application — no additional infrastructure or services are required beyond file storage.
- Database queries use indexed columns for efficient filtering and sorting.
- Pagination limits the amount of data transferred per request, reducing bandwidth costs.
- Evidence files are stored in cost-effective blob storage with lifecycle policies for archival.
- SQLAlchemy connection pooling minimizes the number of active database connections.

#### <u> 2.2.5 Traceability and Observability </u>

##### Structured Logging:
- All application logs use JSON-formatted structured logging with fields: `timestamp`, `level`, `logger`, `filename`, `line_number`, `message`.
- Each request is assigned a `trace_id` for end-to-end request tracing.
- Log levels: DEBUG for development, INFO for production request/response logging, ERROR for exceptions.

##### Error Persistence:
- All application errors are persisted to the `error_log` database table with full context (function name, file name, stack trace).
- Error log entries include `created_at` timestamp and `created_by` identifier for audit purposes.

##### Request Logging:
- Incoming requests are logged at INFO level with method, path, and query parameters.
- Response status codes and latency are logged for monitoring purposes.
- Sensitive data (JWT tokens, file contents) is never included in log output.
- Project action operations (mark_not_applicable, mark_complete) are logged at INFO level with project_id and action type for audit trail.



### <u> Section 3: In Scope and Out Scope </u>

#### <u> 3.1 Inscope Details </u>

- Implementation of `GET /api/v1/projects` endpoint returning a paginated list of projects with nested repositories
- Free-text search filtering on project name (case-insensitive partial match)
- Multi-value filtering by status, client, and specialization (comma-separated IDs)
- Time period filtering by onboarded date (last_week, last_month, last_3_months, last_6_months, last_year)
- Sorting by project name or onboarded date in ascending or descending order
- Pagination support with configurable offset and limit, returning totalItems count
- Nested repository expansion within each project (id, name, onboardedDate, status)
- Implementation of `POST /api/v1/projects/action` endpoint for project lifecycle actions
- Mark Not Applicable action: updates is_applicable flag, changes status, creates Jira ticket record with reason_category, comments, and optional evidence_file
- Mark Complete action: updates project status to Completed and sets completed_at timestamp
- Evidence file upload handling via multipart/form-data with external storage
- JWT Bearer token authentication for both endpoints (shared middleware)
- Query parameter validation with descriptive error messages (HTTP 400)
- Project existence validation with HTTP 404 for non-existent projects
- Standardized response format following `BaseResponse` schema (`status_code`, `status`, `message`, `data`)
- Error handling with HTTP 400, 401, 404, and 500 responses with meaningful messages
- Error logging to the `error_log` database table for all unhandled exceptions
- Layered architecture implementation: Route → Service → Repository → Schema
- Pydantic v2 models for request/response validation and serialization
- SQLAlchemy ORM for all database operations (no raw SQL)
- Unit tests covering positive and negative cases for both endpoints

#### <u> 3.2 Outscope Details </u>

- Repository detail view (covered in separate story ZDAD-49)
- Jira ticket creation in external Jira system (only internal `jira_tickets` table record is created)
- Azure DevOps sync operations (covered in separate story)
- ServiceNow integration and project sync (covered in ZDAD-58)
- Settings and notification configuration (covered in ZDAD-59)
- Overview dashboard metrics and KPI calculations (covered in ZDAD-34)
- Email notification delivery
- Cron job scheduling for automated reports
- User management and role-based access control beyond JWT validation
- Frontend/UI implementation
- Database migration scripts (tables are assumed to be pre-provisioned)
- Load testing and performance benchmarking
- CI/CD pipeline configuration


### <u> Section 4: Solution Diagrams </u>

#### <u> 4.1 UI/UX Design Diagram </u>

**Diagram Location:** Refer to the Project Onboarding Tracker UI mockups (provided separately)

#### <u> 4.2 Architecture Design Diagram </u>

**Diagram Location:** `design/er_diagram.mmd`

#### <u> 4.3 Infrastructure Design Diagram </u>

**Diagram Location:** N/A (shared infrastructure with existing ZDAD-34 deployment)
