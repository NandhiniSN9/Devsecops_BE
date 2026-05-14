## SOLDEF-ZDAD-58 - ServiceNow Integration for Project Ingestion and DevSecOps Ticket Fetching

### <u>Project Details</u>
- **Project ID:** ZDAD  
- **Project Name:** DevSecOps Jira Dashboard  

### <u>Story Details</u>
- **Story ID:** ZDAD-58  
- **Story Name:** ServiceNow Integration for Project Ingestion and DevSecOps Ticket Fetching  
- **Story Description:**  
  When a new project is created in ServiceNow, the system needs to automatically receive and ingest the project details so that the DevSecOps Dashboard stays up to date without manual intervention. When viewing project details, the system needs to have the ability to fetch associated DevSecOps ticket information from ServiceNow so that full project context is available in one place.
- **Context:**  
  The goal is to integrate the DevSecOps Dashboard with ServiceNow to enable two-way data flow. A webhook endpoint will be configured in ServiceNow. This will trigger the `POST /api/v1/sync/servicenow/projects` endpoint when a new project is created. This ensures real-time ingestion of new projects into the DevSecOps Dashboard without manual data entry. A separate `POST /api/v1/sync/servicenow/devsecops-tickets` endpoint will receive ticket details associated with a project. This allows the dashboard to display full project context, including ticket status, priority, assignment, and resolution details alongside pipeline and adoption data. This integration will eliminate manual data synchronization between ServiceNow and the DevSecOps Dashboard, ensuring project information is accurate and current.
- **Acceptance Criteria:**
  - The `POST /api/v1/sync/servicenow/projects` endpoint validates the payload, ensuring required fields exist and data types are correct. It rejects invalid payloads with appropriate error responses.
  - Duplicate project ingestion is handled gracefully — if a project with the same `sn_project_id` already exists, the record is skipped without creating a duplicate.
  - The `POST /api/v1/sync/servicenow/devsecops-tickets` endpoint receives DevSecOps ticket data from ServiceNow and inserts ticket details including repositories for the requested project.
  - Both endpoints handle errors such as ServiceNow unavailability, authentication failures, invalid payloads, and data store errors, returning meaningful messages.
  - All API endpoints comply with platform standards defined in the SD artifacts, including logging, request and response contracts, and error response structure.
  - Unit tests cover positive and negative cases for both endpoints; all defects identified during testing are resolved before release.
  - Code review is completed and the reviewing team confirms readiness for release.

### <u> Table of Contents </u>
- [Section 1: Functional Requirements](#Section-1:-Functional-Requirements)
    - [1.1 Overview](#1.1-Overview)
    - [1.2 Requirement Details](#1.2-Requirement-Details)
        - [1.2.1 ZDAD-58-FR01: Project Sync from ServiceNow](#1.2.1-ZDAD-58-FR01:-Project-Sync-from-ServiceNow)
        - [1.2.2 ZDAD-58-FR02: DevSecOps Tickets Sync from ServiceNow](#1.2.2-ZDAD-58-FR02:-DevSecOps-Tickets-Sync-from-ServiceNow)
        - [1.2.3 ZDAD-58-FR03: Request Payload Validation](#1.2.3-ZDAD-58-FR03:-Request-Payload-Validation)
        - [1.2.4 ZDAD-58-FR04: Error Logging for Sync Operations](#1.2.4-ZDAD-58-FR04:-Error-Logging-for-Sync-Operations)
    - [1.3 Database Schema](#1.3-Database-Schema)
    - [1.4 Project Artifacts](#1.4-Project-Artifacts)
    - [1.5 Environment Variables](#1.5-Environment-Variables)
- [Section 2: In Scope and Out Scope](#Section-2:-In-Scope-and-Out-Scope)
    - [2.1 In Scope Details](#2.1-In-Scope-Details)
    - [2.2 Out Scope Details](#2.2-Out-Scope-Details)
- [Section 3: Solution Diagrams](#Section-3:-Solution-Diagrams)

### <u> Section 1: Functional Requirements </u>

#### <u> 1.1 Overview </u>
The ServiceNow Integration story implements two inbound sync endpoints that enable two-way data flow between ServiceNow and the DevSecOps Jira Dashboard. A webhook configured in ServiceNow triggers `POST /api/v1/sync/servicenow/projects` when a new project is created, ensuring real-time ingestion without manual data entry. The project sync is insert-only — if a project with the same `sn_project_id` already exists, the record is skipped (no duplicates created). The `POST /api/v1/sync/servicenow/devsecops-tickets` endpoint receives DevSecOps ticket data pushed by ServiceNow when a new ticket is created, inserting ticket and repository records into the database. Both endpoints authenticate by decrypting the token to extract the ServiceNow email ID and validating it against the allowed ServiceNow service account email stored in an environment variable (`SERVICENOW_ALLOWED_EMAIL`). If the email does not match, the request is rejected with HTTP 401. Partial success is supported for batch ticket syncing — valid tickets are processed while failures are logged. All errors are logged to the `error_log` database table for traceability.

#### <u> 1.2 Requirement Details </u>

- **ZDAD-58-FR01: Project Sync from ServiceNow**
- **ZDAD-58-FR02: DevSecOps Tickets Sync from ServiceNow**
- **ZDAD-58-FR03: Request Payload Validation**
- **ZDAD-58-FR04: Error Logging for Sync Operations**

##### <u> 1.2.1 ZDAD-58-FR01: Project Sync from ServiceNow </u>

##### Description:
The system shall expose a `POST /api/v1/sync/servicenow/projects` endpoint that receives project data from ServiceNow and inserts a new record in the `projects` table. The `sn_project_id` field serves as the unique identifier — if a project with the same `sn_project_id` already exists, the record is skipped (no duplicate created). This endpoint is triggered by a webhook configured in ServiceNow when a new project is created.

##### Request Payload:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sn_project_id | VARCHAR | ServiceNow project identifier (unique key for deduplication) |
| `project_name` | string | Yes | Name of the project |
| `onboarded_date` | date (ISO 8601) | Yes | Date when the project was onboarded (format: YYYY-MM-DD) |
| `project_type` | string | Yes | Type/category of the project (e.g., "Infrastructure") |
| `is_applicable` | boolean | No | Whether the project is applicable for DevSecOps (default: true) |
| `client` | string | No | Client name associated with the project |
| `approver` | string | No | Name or email of the approver for the project |

##### Processing Logic:
1. Authenticate the request by decrypting the token and validating the ServiceNow email against the `SERVICENOW_ALLOWED_EMAIL` environment variable. Return 401 if email does not match.
2. Validate the request payload against the Pydantic schema (required fields, data types, date format).
3. Look up the project by `sn_project_id` in the `projects` table:
   - **If found** → Skip the record (project already exists). Return success.
   - **If not found** → Create a new project record with:
     - A generated UUID as `project_id`
     - `status_id` set to the "Inactive" status (looked up from the `statuses` table by name)
     - `is_active` set to 1
     - `created_at` set to current timestamp
     - `created_by` set to the authenticated service account identifier
5. Return a success response with HTTP 200.

##### Success Response:
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Sync completed successfully"
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid or missing required fields (e.g., missing `sn_project_id`, invalid date format) |
| 401 | Missing/invalid token or email does not match allowed ServiceNow account |
| 500 | Unexpected server error (logged to `error_log` table) |

##### Acceptance Criteria:
- A new project is created in the `projects` table when `sn_project_id` does not exist.
- If `sn_project_id` already exists, the record is skipped — no duplicate is created.
- New projects are assigned the "Inactive" status by default (resolved from `statuses` table).
- The `created_by` field reflects the authenticated service account.
- Invalid payloads return HTTP 400 with a descriptive error message identifying the invalid field.
- Unauthorized requests (missing token or email mismatch) return HTTP 401.
- The endpoint is idempotent — calling it multiple times with the same data produces the same result.

##### <u> 1.2.2 ZDAD-58-FR02: DevSecOps Tickets Sync from ServiceNow </u>

##### Description:
The system shall expose a `POST /api/v1/sync/servicenow/devsecops-tickets` endpoint that receives a batch of DevSecOps ticket data from ServiceNow and performs insert operations in the `devsecops_tickets` and `repositories` tables. This endpoint is triggered by an event-driven script in ServiceNow when a DevSecOps ticket is completed. Each ticket is linked to a project (via `sn_project_id`) and a specialization (via `specialization_name`). The endpoint supports partial success — valid tickets are processed while invalid ones are logged and reported.

##### Request Payload:
**Root object:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tickets` | array | Yes | List of ticket objects to sync |

**Each ticket object:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sn_project_id` | string | Yes | ServiceNow project identifier (must reference an existing project) |
| `project_name` | string | Yes | Name of the project the ticket belongs to |
| `client` | string | No | Client name associated with the ticket |
| `specialization_name` | string | Yes | Specialization name (must match an existing active specialization) |
| `repositories` | array | No | List of repository objects associated with the ticket |
| `requested_by` | string | No | Name or email of the person who raised the request |
| `approver` | string | No | Name or email of the approver for the ticket |
| `requested_at` | datetime (ISO 8601) | No | Timestamp when the ticket was requested in ServiceNow |

**Each repository object:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repo_name` | string | Yes | Repository name |
| `ado_repo_id` | string | No | Azure DevOps repository identifier |

##### Processing Logic:
1. Authenticate the request by decrypting the token and validating the ServiceNow email against the `SERVICENOW_ALLOWED_EMAIL` environment variable. Return 401 if email does not match.
2. Validate the root payload structure (must contain a non-empty `tickets` array).
3. For each ticket in the array:
   a. **Resolve `specialization_name`** → Query the `specializations` table for a record where `specialization_name` matches (case-insensitive) and `is_active = 1`. If not found, mark this ticket as failed and continue to the next ticket.
   b. **Resolve project (3-step fallback)**:
      1. **Match by `sn_project_id`** → Query the `projects` table for a record where `sn_project_id` matches the request's `sn_project_id` and `is_active = 1`. If found, use that project's `project_id` and `sn_project_id`.
      2. **Match by `project_name`** → If no `sn_project_id` match, query the `projects` table for a record where `project_name` matches the request's `project_name` and `is_active = 1`. If found, use that project's `project_id` and `sn_project_id`.
      3. **Use default project** → If neither match is found, use the pre-existing default project record in the `projects` table. Map the ticket to the default project's `project_id` and `sn_project_id`.
   c. **Insert the ticket** → Create a new record in `devsecops_tickets` with:
      - Generated UUID as `ticket_id`
      - Resolved `specialization_id` and `project_id`
      - `is_active = 1`
      - `created_at` and `created_by` set to current timestamp and service account
   d. **Process repositories** → For each repository in the ticket:
      - Look up by `repo_name` + `ticket_id` in the `repositories` table.
      - **If found** → Skip (repository already exists).
      - **If not found** → Create a new repository record with generated UUID, linked to the ticket via `ticket_id`. Set `created_at` and `created_by`.
5. Return a success response indicating the sync completed. Failed tickets are logged to the application logs with the reason for failure.

##### Success Response:
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Sync completed successfully"
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid payload structure (missing `tickets` array, empty array, or missing required fields in ticket objects) |
| 401 | Missing/invalid token or email does not match allowed ServiceNow account |
| 500 | Unexpected server error (logged to `error_log` table) |

##### Partial Success Behavior:
- If some tickets in the batch fail validation (unknown specialization or project not found), the valid tickets are still processed.
- Failed tickets are logged at WARNING level with the reason (e.g., "Specialization 'Unknown' not found for ticket with sn_project_id 'SN-PRJ-999'").
- The response still returns HTTP 200 with "Sync completed successfully" as long as at least one ticket was processed.
- If ALL tickets in the batch fail, the response still returns HTTP 200 but the failures are logged.

##### Acceptance Criteria:
- A new ticket is always created in `devsecops_tickets` for each incoming ticket in the batch (one project can have multiple tickets).
- Project resolution follows the 3-step fallback: match by `sn_project_id` → match by `project_name` → use default project.
- When matched by `project_name`, the existing project's `project_id` and `sn_project_id` are used for the ticket.
- When no match is found, the ticket is mapped to the pre-existing default project in the database.
- Repositories are created and linked to the correct ticket via `ticket_id`. Existing repositories are skipped.
- Unknown `specialization_name` values cause the individual ticket to be skipped (not the entire batch).
- The `created_by` field reflects the authenticated service account.
- The endpoint handles empty `repositories` arrays gracefully (ticket is created without repositories).
- Failed tickets are logged with sufficient detail for debugging.

##### <u> 1.2.3 ZDAD-58-FR03: Request Payload Validation </u>

##### Description:
The system shall validate all incoming request payloads for the sync endpoints using Pydantic v2 models. Validation errors are returned as HTTP 400 responses with descriptive messages identifying which field failed validation and why.

##### Validation Rules — Project Sync:
- `sn_project_id`: Required, non-empty string.
- `project_name`: Required, non-empty string.
- `onboarded_date`: Required, valid ISO 8601 date format (YYYY-MM-DD).
- `project_type`: Required, non-empty string.
- `is_applicable`: Optional, must be boolean if provided.
- `client`: Optional, string.
- `approver`: Optional, string.

##### Validation Rules — DevSecOps Tickets Sync:
- `tickets`: Required, must be a non-empty array.
- Each ticket:
  - `sn_project_id`: Required, non-empty string.
  - `project_name`: Required, non-empty string.
  - `specialization_name`: Required, non-empty string.
  - `repositories`: Optional, must be an array if provided.
  - Each repository: `repo_name` is required and must be a non-empty string.
  - `requested_at`: Optional, must be valid ISO 8601 datetime if provided.

##### Error Response Format:
```json
{
  "status_code": 400,
  "status": "failed",
  "message": "Validation error: 'sn_project_id' is required",
  "data": []
}
```

##### Acceptance Criteria:
- Missing required fields return HTTP 400 with the field name in the error message.
- Invalid date formats return HTTP 400 with a descriptive message.
- Empty `tickets` array returns HTTP 400.
- Validation errors are returned before any database operations are attempted.
- The error response follows the standardized `BaseResponse` schema.

##### <u> 1.2.4 ZDAD-58-FR04: Error Logging for Sync Operations </u>

##### Description:
The system shall log all unhandled exceptions occurring during sync operations to the `error_log` database table. This provides a persistent audit trail for debugging sync failures. The error logging mechanism is the same as used by the Overview API (ZDAD-34-FR04) — a global exception handler captures unhandled exceptions and persists them.

##### Error Log Table Fields:
- `error_id` — Auto-generated UUID primary key.
- `error_message` — The exception message text.
- `error_function` — The function name where the error occurred (e.g., "sync_project", "sync_devsecops_tickets").
- `error_file` — The file path where the error originated.
- `stack_trace` — Full Python stack trace for debugging.
- `created_at` — Timestamp when the error was logged.
- `created_by` — System identifier (e.g., "servicenow_sync_service").

##### Acceptance Criteria:
- All unhandled exceptions in the sync endpoints are captured and logged to the `error_log` table.
- The error log entry contains the function name, file name, error message, and stack trace.
- Error logging does not interfere with the error response returned to ServiceNow (non-blocking).
- HTTP 500 responses are always accompanied by an `error_log` entry.
- Partial failures (individual ticket validation failures) are logged at application log level (WARNING), not in the `error_log` table.

#### <u> 1.3 Database Schema </u>

#### <u> 1.3 Database Schema </u>

The full database schema is defined in `design/er_diagram.mmd`. The following tables are directly involved in the ServiceNow sync operations:

- **projects** — Project records with `sn_project_id` (unique key for deduplication), `project_name`, `onboarded_date`, `status_id`, `client`.
- **devsecops_tickets** — Tickets linked to projects and specializations. Each ticket references a project via `sn_project_id` and a specialization via `specialization_id`.
- **repositories** — Repositories linked to tickets via `ticket_id`. Contains `repository_name` and `ado_repo_id`.
- **specializations** — Read-only reference for resolving `specialization_name` to `specialization_id`.
- **statuses** — Read-only reference for assigning default "Inactive" status to new projects.
- **error_log** — Persists unhandled exceptions for debugging.

##### Key Relationships:
- `projects.status_id` → `statuses.status_id` (each project has one status)
- `devsecops_tickets.specialization_id` → `specializations.specialization_id` (each ticket belongs to one specialization)
- `devsecops_tickets.sn_project_id` → `projects.sn_project_id` (each ticket references a project)
- `repositories.ticket_id` → `devsecops_tickets.ticket_id` (each repository belongs to one ticket)

#### <u> 1.4 Project Artifacts </u>

- `api/servicenow-openapi.yaml` — OpenAPI 3.0.3 specification for the sync endpoints.
- `design/er_diagram.mmd` — Mermaid ER diagram showing all database tables and relationships.
- `design/requirements.md` — Section 2 (ServiceNow Sync) contains the high-level requirements.
- `diagram/servicenow_integration.mmd` — Sequence diagram showing the sync flow.

#### <u> 1.5 Environment Variables </u>

##### Description:
All application configuration shall be managed through environment variables. The ServiceNow sync endpoints require the following variables.

##### Required Environment Variables:
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `TOKEN_PRIVATE_KEY` | Private key for token decryption (PEM format or path) | Yes |
| `SERVICENOW_ALLOWED_EMAIL` | Allowed ServiceNow service account email for validation | Yes |

### <u> Section 2: In Scope and Out Scope </u>

#### <u> 2.1 Inscope Details </u>

- Implementation of `POST /api/v1/sync/servicenow/projects` endpoint for project data ingestion from ServiceNow
- Implementation of `POST /api/v1/sync/servicenow/devsecops-tickets` endpoint for ticket and repository data ingestion from ServiceNow
- Encrypted token authentication with ServiceNow email validation against `SERVICENOW_ALLOWED_EMAIL` env var
- Pydantic v2 request models for payload validation
- Insert logic for projects keyed on `sn_project_id` (duplicates skipped)
- Insert logic for tickets — each incoming ticket is always created (one project can have multiple tickets)
- 3-step project resolution fallback for tickets: match `sn_project_id` → match `project_name` → use default project
- Insert logic for repositories keyed on `repo_name` + `ticket_id` combination (existing records skipped)
- Resolution of `specialization_name` to `specialization_id` from the `specializations` table
- Default status assignment ("Inactive") for newly created projects
- Partial success handling for batch ticket sync (valid tickets processed, invalid ones logged)
- Standardized response format following `BaseResponse` schema
- Error handling with HTTP 400, 401, and 500 responses
- Error logging to the `error_log` database table for unhandled exceptions
- Structured JSON logging with trace_id for sync request tracing
- Layered architecture: Middleware → Routes → Services → Repositories → Database
- Unit tests covering positive and negative cases for both endpoints

#### <u> 2.2 Outscope Details </u>

- ServiceNow script development (ServiceNow side is managed by the ServiceNow team)
- Azure DevOps (ADO) sync functionality (separate story)
- KPI history computation and population (handled by ADO Sync)
- Rate limiting implementation
- UI/frontend changes (backend-only story)
- Database migration scripts (schema assumed pre-existing)
- ServiceNow service account provisioning (handled by identity/access management team)
- Network/firewall configuration on Azure (handled by infrastructure team)
- Report generation and email delivery (ZDAD-60)
- Settings management endpoints
- Project action endpoints (mark_not_applicable, mark_complete)

### <u> Section 3: Solution Diagrams </u>

#### <u> 3.1 Architecture Diagram </u>

**Diagram Location:** `diagram/servicenow_integration.mmd`
