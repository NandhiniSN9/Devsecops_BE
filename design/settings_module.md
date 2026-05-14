## SOLDEF-ZDAD-59 - Configure and Deliver Notification Alerts for DevSecOps Dashboard

### <u>Project Details</u>
- **Project ID:** ZDAD  
- **Project Name:** DevSecOps Jira Dashboard  

### <u>Story Details</u>
- **Story ID:** ZDAD-59  
- **Story Name:** Configure and Deliver Notification Alerts for DevSecOps Dashboard  
- **Story Description:**  
  The DevSecOps Dashboard Settings module allows users to configure notification alert settings per specialization. This includes configuring the "at risk" threshold (number of days since onboarding without a repository before a project is considered at risk), enabling/disabling email digest reports and at-risk alerts, setting the report frequency (daily, weekly, monthly), and managing email recipients (add/remove) who receive the scheduled reports.
- **Scope:**  
  Implement the Settings API for the DevSecOps Dashboard. The `GET /api/v1/specializations/{specializationId}/settings` endpoint retrieves settings for a given specialization including email recipients. The `PUT /api/v1/specializations/settings/manage` endpoint partially updates settings and manages email recipients via an action-based approach (add/remove). All service errors are logged to the `error_log` table.
- **Acceptance Criteria:**
  - The `GET /api/v1/specializations/{specializationId}/settings` endpoint returns the settings record including at_risk_threshold, email_digest, at_risk_alert, report_frequency, specialization name, and email recipients list.
  - The `PUT /api/v1/specializations/settings/manage` endpoint partially updates settings fields and manages email recipients via add/remove actions.
  - Invalid inputs return HTTP 400 with descriptive validation error messages.
  - Non-existent specializations return HTTP 404.
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

The Settings API is a core component of the DevSecOps Jira Dashboard backend that enables delivery leads and administrators to configure notification alert settings on a per-specialization basis. The API exposes two endpoints: `GET /api/v1/specializations/{specializationId}/settings` which retrieves the complete settings record including the at-risk threshold, email digest schedule, at-risk alert schedule, report frequency, last sync timestamp, and the list of configured email recipients; and `PUT /api/v1/specializations/settings/manage` which allows partial updates to settings fields and manages email recipients through an action-based approach (add new recipients or soft-delete existing ones). The settings data drives the Email Notification Service (ZDAD-60) by defining when and to whom reports are delivered. The at-risk threshold determines how many days after onboarding without a repository a project is flagged as "at risk" on the Overview Dashboard. Both endpoints require JWT Bearer token authentication and return standardized JSON responses following the `BaseResponse` schema. All unhandled exceptions are logged to the `error_log` database table for traceability and debugging. The implementation follows the layered architecture pattern: Routes → Services → Repositories → Schema, with Pydantic models for request/response validation.

#### <u> 1.2 Requirement Details </u>

- **ZDAD-59-FR01: Retrieve Settings for a Specialization**
- **ZDAD-59-FR02: Update Settings (Partial Update)**
- **ZDAD-59-FR03: Email Recipient Management**
- **ZDAD-59-FR04: Input Validation**
- **ZDAD-59-FR05: Error Logging**


##### <u> 1.2.1 ZDAD-59-FR01: Retrieve Settings for a Specialization </u>

##### Description:
The system shall expose a `GET /api/v1/specializations/{specializationId}/settings` endpoint that returns the complete settings record for a given specialization. The response includes the settings configuration (at-risk threshold, email digest, at-risk alert, report frequency), the specialization name, the last sync timestamp, and the full list of active email recipients configured for that specialization.

##### Request Parameters:
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `specializationId` | Path | UUID | Yes | Unique identifier of the specialization |

##### Processing Logic:
1. Validate that `specializationId` is a valid UUID format. Return HTTP 400 if invalid.
2. Query the `specializations` table to verify the specialization exists and `is_active = 1`. Return HTTP 404 if not found or inactive.
3. Query the `settings` table where `specialization_id` matches and `is_active = 1`. If no settings record exists, return HTTP 404.
4. Query the `email_recipient` table where `specialization_id` matches and `is_active = 1` to retrieve all active recipients.
5. Compose the response object combining settings data, specialization name, and email recipients list.
6. Return HTTP 200 with the standardized success response.

##### Response Structure (200):
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Settings retrieved successfully",
  "data": {
    "setting_id": "uuid",
    "specialization_id": "uuid",
    "specialization_name": "Cloud Engineering",
    "at_risk_threshold": 10,
    "email_digest": "weekly",
    "at_risk_alert": "daily",
    "report_frequency": "weekly",
    "last_synced": "2026-05-10T14:30:00Z",
    "email_recipients": [
      {
        "email_recipient_id": "uuid",
        "alert_recipient": "manager@org.com"
      }
    ]
  }
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid UUID format for `specializationId` |
| 401 | Missing or invalid JWT Bearer token |
| 404 | Specialization not found or inactive, or no settings record exists |
| 500 | Unexpected server error (logged to `error_log`) |

##### Acceptance Criteria:
- The endpoint returns HTTP 200 with correct settings data for a valid specialization.
- The response includes `specialization_name` resolved from the `specializations` table.
- The `email_recipients` array contains only active recipients (`is_active = 1`).
- Invalid UUID format returns HTTP 400 with a descriptive error message.
- Non-existent specialization returns HTTP 404 with message "Specialization not found".
- The endpoint requires JWT Bearer token authentication.
- Response follows the standardized `BaseResponse` schema with `status_code`, `status`, `message`, and `data` fields.

##### <u> 1.2.2 ZDAD-59-FR02: Update Settings (Partial Update) </u>

##### Description:
The system shall expose a `PUT /api/v1/specializations/settings/manage` endpoint that partially updates the settings record for a given specialization. Only the fields included in the request body are updated; omitted fields remain unchanged. The endpoint also supports email recipient management via an action-based array (covered in FR03).

##### Request Body:
```json
{
  "specialization_id": "uuid (required)",
  "at_risk_threshold": 10,
  "email_digest": "weekly",
  "at_risk_alert": "daily",
  "report_frequency": "weekly",
  "email_recipients": [
    {
      "action": "add",
      "alert_recipient": "newuser@org.com"
    },
    {
      "action": "remove",
      "email_recipient_id": "uuid"
    }
  ]
}
```

##### Field Validation Rules:
| Field | Type | Constraints |
|-------|------|-------------|
| `specialization_id` | UUID | Required. Must exist in `specializations` table with `is_active = 1` |
| `at_risk_threshold` | Integer | Optional. Minimum value: 1 |
| `email_digest` | String | Optional. Accepted values: "daily", "weekly", "monthly", "disabled" |
| `at_risk_alert` | String | Optional. Accepted values: "daily", "weekly", "monthly", "disabled" |
| `report_frequency` | String (enum) | Optional. Accepted values: "daily", "weekly", "monthly" |
| `email_recipients` | Array | Optional. Array of add/remove actions (see FR03) |

##### Processing Logic:
1. Validate the request body using Pydantic model. Return HTTP 400 for validation failures.
2. Validate `specialization_id` — verify it exists in `specializations` table with `is_active = 1`. Return HTTP 404 if not found.
3. Retrieve the existing `settings` record for the specialization. Return HTTP 404 if no settings record exists.
4. For each provided field (`at_risk_threshold`, `email_digest`, `at_risk_alert`, `report_frequency`), update the corresponding column in the `settings` table.
5. Process `email_recipients` actions if provided (see FR03).
6. Update `modified_at` timestamp and `modified_by` field on the settings record.
7. Commit the transaction.
8. Return the updated settings response (same structure as GET endpoint).

##### Response Structure (200):
Returns the full updated settings object (same schema as the GET response in FR01).

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Validation error (invalid field values, missing required `specialization_id`) |
| 401 | Missing or invalid JWT Bearer token |
| 404 | Specialization not found or no settings record exists |
| 500 | Unexpected server error (logged to `error_log`) |

##### Acceptance Criteria:
- Only fields present in the request body are updated; omitted fields remain unchanged.
- `at_risk_threshold` with value less than 1 returns HTTP 400.
- Invalid `report_frequency` values return HTTP 400 with accepted values listed.
- The response reflects the updated values immediately after the update.
- The `modified_at` timestamp is updated on every successful PUT request.
- Non-existent specialization returns HTTP 404.
- The endpoint requires JWT Bearer token authentication.


##### <u> 1.2.3 ZDAD-59-FR03: Email Recipient Management </u>

##### Description:
The system shall support managing email recipients through an action-based approach within the PUT settings endpoint. Recipients can be added (creating a new record in `email_recipient` table) or removed (soft-deleting by setting `is_active = 0`). This approach allows multiple recipient operations in a single API call.

##### Action Types:

**Add Action:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | String | Yes | Must be "add" |
| `alert_recipient` | String (email) | Yes | Valid email address of the new recipient |

**Remove Action:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | String | Yes | Must be "remove" |
| `email_recipient_id` | UUID | Yes | UUID of the recipient record to soft-delete |

##### Processing Logic — Add:
1. Validate that `alert_recipient` is a valid email format. Return HTTP 400 if invalid.
2. Check if the email already exists as an active recipient for this specialization. If duplicate, return HTTP 400 with message "Recipient already exists".
3. Retrieve the `setting_id` from the settings record for this specialization.
4. Insert a new record into `email_recipient` table with:
   - `email_recipient_id`: Auto-generated UUID
   - `setting_id`: FK to the settings record
   - `specialization_id`: From the request
   - `alert_recipient`: The email address
   - `is_active`: 1
   - `created_at`: Current timestamp
   - `created_by`: Authenticated user identifier

##### Processing Logic — Remove:
1. Validate that `email_recipient_id` is a valid UUID format. Return HTTP 400 if invalid.
2. Query `email_recipient` table for the record with matching `email_recipient_id` and `is_active = 1`.
3. If not found, return HTTP 400 with message "Recipient not found or already removed".
4. Set `is_active = 0` on the record (soft delete).
5. Update `modified_at` and `modified_by` fields.

##### Acceptance Criteria:
- Adding a recipient with a valid email creates a new active record in `email_recipient` table.
- Adding a duplicate email (already active for the same specialization) returns HTTP 400.
- Removing a recipient sets `is_active = 0` (soft delete), not a hard delete.
- Removing a non-existent or already-removed recipient returns HTTP 400.
- Invalid email format in add action returns HTTP 400 with a descriptive message.
- Multiple add/remove actions can be processed in a single request.
- The response includes the updated list of active email recipients after all actions are processed.

##### <u> 1.2.4 ZDAD-59-FR04: Input Validation </u>

##### Description:
The system shall validate all incoming request data for both the GET and PUT endpoints. Invalid inputs must result in an HTTP 400 response with a descriptive error message indicating which field is invalid and what values are accepted. Validation is implemented using Pydantic v2 models with strict type constraints.

##### Validation Rules:
| Field | Rule | Error Message |
|-------|------|---------------|
| `specializationId` (path) | Must be valid UUID format | "Invalid specialization ID format" |
| `specialization_id` (body) | Required, must be valid UUID | "specialization_id is required and must be a valid UUID" |
| `at_risk_threshold` | Integer, minimum 1 | "at_risk_threshold must be an integer greater than or equal to 1" |
| `email_digest` | One of: daily, weekly, monthly, disabled | "email_digest must be one of [daily, weekly, monthly, disabled]" |
| `at_risk_alert` | One of: daily, weekly, monthly, disabled | "at_risk_alert must be one of [daily, weekly, monthly, disabled]" |
| `report_frequency` | One of: daily, weekly, monthly | "report_frequency must be one of [daily, weekly, monthly]" |
| `alert_recipient` | Valid email format (RFC 5322) | "Invalid email format for alert_recipient" |
| `email_recipient_id` | Valid UUID format | "Invalid email_recipient_id format" |
| `action` | One of: add, remove | "action must be one of [add, remove]" |

##### Error Response Format:
```json
{
  "status_code": 400,
  "status": "failed",
  "message": "Validation error: at_risk_threshold must be an integer greater than or equal to 1",
  "data": []
}
```

##### Acceptance Criteria:
- All validation rules are enforced before any database operations.
- Error messages clearly identify the invalid field and accepted values.
- Multiple validation errors are reported (first error encountered is returned).
- Valid requests with all optional fields omitted are processed successfully.
- Pydantic validation errors are caught and transformed into the standardized error response format.

##### <u> 1.2.5 ZDAD-59-FR05: Error Logging </u>

##### Description:
The system shall log all unhandled exceptions occurring during settings retrieval or update operations to the `error_log` database table. This provides a persistent audit trail for debugging and incident investigation. The error logging mechanism uses the same global exception handler established in ZDAD-34.

##### Error Log Table Fields:
- `error_id` — Auto-generated UUID primary key.
- `error_message` — The exception message text.
- `error_function` — The function name where the error occurred (e.g., "get_settings", "update_settings", "add_recipient").
- `error_file` — The file path where the error originated (e.g., "src/services/settings_service.py").
- `stack_trace` — Full Python stack trace for debugging.
- `created_at` — Timestamp when the error was logged.
- `created_by` — "settings_service".

##### Acceptance Criteria:
- All unhandled exceptions in the Settings API are captured and logged to `error_log`.
- The error log entry contains the function name, file name, error message, and stack trace.
- Error logging does not interfere with the error response returned to the client (non-blocking).
- HTTP 500 responses are always accompanied by an `error_log` entry.
- Validation errors (HTTP 400) and not-found errors (HTTP 404) are NOT logged to `error_log` (they are expected application behavior).


#### <u> 1.3 Database Schema </u>

The following tables are directly involved in the Settings API (as defined in `design/er_diagram.mmd`):

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

##### settings
| Column | Type | Constraints |
|--------|------|-------------|
| setting_id | UUID | PK |
| specialization_id | UUID | FK → specializations.specialization_id |
| at_risk_threshold | INTEGER | NOT NULL |
| email_digest | VARCHAR | Schedule value (daily/weekly/monthly/disabled) |
| at_risk_alert | VARCHAR | Schedule value (daily/weekly/monthly/disabled) |
| last_synced | DATETIME | Timestamp of last sync operation |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### email_recipient
| Column | Type | Constraints |
|--------|------|-------------|
| email_recipient_id | UUID | PK |
| setting_id | UUID | FK → settings.setting_id |
| specialization_id | UUID | FK → specializations.specialization_id |
| alert_recipient | VARCHAR | NOT NULL (email address) |
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

##### cron_jobs
| Column | Type | Constraints |
|--------|------|-------------|
| cron_id | UUID | PK |
| specialization_id | VARCHAR | NOT NULL |
| type | VARCHAR | NOT NULL, ENUM(azure, email) |
| sync_status | VARCHAR | NOT NULL, ENUM(pending, success, fail) |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### Key Relationships:
- `settings.specialization_id` → `specializations.specialization_id` (1:1 — each specialization has at most one settings record)
- `email_recipient.setting_id` → `settings.setting_id` (recipients belong to a settings record)
- `email_recipient.specialization_id` → `specializations.specialization_id` (recipients are per specialization)

#### <u> 1.4 Project Artifacts </u>

- `api/openapi.yaml` — Full OpenAPI 3.0.3 specification defining the `GET /api/v1/specializations/{specializationId}/settings` and `PUT /api/v1/specializations/settings/manage` endpoints, request/response schemas (`SettingsSuccessResponse`, `SettingsUpdateRequest`, `EmailRecipientAction`), and error response formats.
- `design/er_diagram.mmd` — Mermaid ER diagram showing all database tables and relationships including `specializations`, `settings`, `email_recipient`, `error_log`, and `cron_jobs`.
- `design/requirements.md` — High-level requirements document for the Settings module (ZDAD-59) with acceptance criteria and affected components.
- `design/Settings - UI screenshots.docx` — Visual reference for the Settings configuration panel UI layout.

#### <u> 1.5 Dependencies </u>

- **Python 3.12+** — Runtime environment
- **FastAPI** — Web framework for building the REST API
- **SQLAlchemy** — ORM for PostgreSQL database access (queries on `settings`, `email_recipient`, `specializations`, `error_log`)
- **Pydantic v2** — Request/response model validation and serialization
- **PostgreSQL** — Primary database storing settings, email recipients, specializations, and error logs
- **python-jose / PyJWT** — JWT token decoding and validation (shared with existing auth middleware)
- **Uvicorn** — ASGI server for running the FastAPI application


### <u> Section 2: Non Functional Requirements </u>

### 2.1 Infrastructure and Deployment

#### <u> 2.1.1 Overview </u>

The Settings API is deployed as part of the existing DevSecOps Jira Dashboard backend application on Azure App Service. No separate service or infrastructure is required — the settings routes are registered within the existing FastAPI application alongside the Overview API, Projects API, and ServiceNow Sync routes. The application is a Python FastAPI service running on Uvicorn, packaged as a Docker container image and deployed to Azure App Service. The service connects to the same Azure Database for PostgreSQL instance and shares the same JWT middleware, error handling, and logging infrastructure established in ZDAD-34. Environment-specific configurations are managed through Azure App Service application settings and environment variables, ensuring no secrets are hardcoded in the application code. The deployment pipeline ensures zero-downtime deployments with health check validation before traffic routing.

#### <u> 2.1.2 Requirement Details </u>

- **ZDAD-59-NFR01: Shared Deployment with Existing Application**
- **ZDAD-59-NFR02: Environment Configuration**
- **ZDAD-59-NFR03: Health Check Compatibility**

##### <u> 2.1.2.1 ZDAD-59-NFR01: Shared Deployment with Existing Application </u>

##### Description:
The Settings API endpoints shall be deployed as additional routes within the existing FastAPI application. No separate service or deployment is required. The settings routes are registered via a dedicated `APIRouter` with appropriate prefix and share the same database connection pool, JWT middleware, and error handling infrastructure established in ZDAD-34.

##### Deployment Configuration:
- **Runtime:** Python 3.12+ container image
- **ASGI Server:** Uvicorn with configurable workers
- **Port:** Application listens on port 8080 (configurable via `PORT` environment variable)
- **Route Registration:** Settings routes are added via `APIRouter` with prefix `/api/v1`.
- **Database:** Uses the same SQLAlchemy engine and session factory.
- **Authentication:** Uses the same JWT middleware.
- **Error Handling:** Uses the same global exception handler that logs to `error_log`.

##### Acceptance Criteria:
- The settings endpoints are accessible after deployment without additional infrastructure changes.
- Existing endpoints (Overview, Filters, Projects, Sync) continue to function without disruption.
- The application starts successfully with the new routes registered.
- Health check and readiness endpoints remain unaffected.

##### <u> 2.1.2.2 ZDAD-59-NFR02: Environment Configuration </u>

##### Description:
All application configuration shall be managed through environment variables. The Settings API uses the same environment variables as the existing application — no additional environment variables are required for this story.

##### Required Environment Variables (shared with existing application):
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT token validation | Yes |
| `JWT_ALGORITHM` | Algorithm used for JWT (default: HS256) | No |
| `APP_ENV` | Environment identifier (development, staging, production) | Yes |
| `LOG_LEVEL` | Application log level (default: INFO) | No |
| `PORT` | Application port (default: 8080) | No |

##### Acceptance Criteria:
- No new environment variables are required for the Settings API.
- The application uses the existing `DATABASE_URL` for all settings-related database operations.
- The existing JWT configuration is reused for settings endpoint authentication.

##### <u> 2.1.2.3 ZDAD-59-NFR03: Health Check Compatibility </u>

##### Description:
The addition of Settings API routes shall not affect the existing health check (`/health`) and readiness (`/ready`) endpoints. The readiness endpoint continues to validate database connectivity, which implicitly covers the settings-related tables.

##### Acceptance Criteria:
- `GET /health` continues to return HTTP 200 with `{"status": "healthy"}`.
- `GET /ready` continues to validate database connectivity.
- Adding settings routes does not increase application startup time significantly.

#### <u> 2.1.3 Project Artifacts </u>

- `api/openapi.yaml` — API specification including settings endpoints
- `design/er_diagram.mmd` — Database schema reference for settings-related tables


### 2.2 Architecture and System Design

#### <u> 2.2.1 Security and Compliance </u>

##### JWT Authentication:
All Settings API endpoints require a valid JWT Bearer token in the `Authorization` header. The middleware validates the token signature, expiration, and required claims before allowing the request to proceed to the route handler. Invalid or expired tokens result in an HTTP 401 Unauthorized response.

##### Token Validation Flow:
1. Extract the `Authorization` header from the incoming request.
2. Verify the header contains a `Bearer` prefix followed by the token.
3. Decode and validate the JWT token using the configured secret key and algorithm.
4. Check token expiration (`exp` claim) — reject if expired.
5. Attach decoded token claims to the request context for downstream use.
6. If validation fails at any step, return HTTP 401 with standardized error response.

##### Input Validation:
- All path parameters and request body fields are validated using Pydantic models with strict type constraints.
- SQL injection is prevented by using SQLAlchemy ORM with parameterized queries (no raw SQL).
- UUID format validation prevents malformed identifiers from reaching the database layer.
- Email format validation uses RFC 5322 compliant regex patterns.

##### Data Protection:
- Email addresses stored in `email_recipient` table are not encrypted at rest (they are not classified as PII in this context — they are organizational email addresses).
- No sensitive data (passwords, tokens) is stored or returned by the Settings API.
- All database connections use SSL/TLS encryption in transit.

#### <u> 2.2.2 System Performance </u>

##### Database Query Optimization:
- The GET endpoint performs a maximum of 3 queries: specialization lookup, settings retrieval, and email recipients fetch. These can be optimized to 2 queries using a JOIN between `settings` and `specializations`.
- Database indexes are maintained on `settings.specialization_id` and `email_recipient.specialization_id` for efficient lookups.
- SQLAlchemy connection pooling is configured to reuse database connections efficiently.
- The PUT endpoint uses a single transaction for all updates (settings fields + recipient actions) to ensure atomicity.

##### Response Efficiency:
- The GET endpoint returns all settings data including recipients in a single response to minimize client round trips.
- The PUT endpoint returns the full updated settings object, eliminating the need for a subsequent GET call.

#### <u> 2.2.3 Availability and Reliability </u>

##### Error Resilience:
- All unhandled exceptions are caught by the global exception handler that returns HTTP 500 and logs the error to the `error_log` table.
- Database connection failures are handled gracefully with appropriate error responses.
- The PUT endpoint uses database transactions — if any operation fails, the entire update is rolled back to maintain data consistency.

##### Deployment Reliability:
- Azure App Service provides built-in auto-restart on application crashes.
- Health check endpoints enable Azure to detect and replace unhealthy instances.
- The Settings API is stateless — any instance can serve any request.

#### <u> 2.2.4 Cost Efficiency </u>

##### Resource Optimization:
- The Settings API adds minimal overhead to the existing application — no additional infrastructure or services are required.
- Database queries are simple key-based lookups (by UUID) which are highly efficient with proper indexing.
- No caching is required for settings data as it changes infrequently and the queries are lightweight.
- SQLAlchemy connection pooling minimizes the number of active database connections.

#### <u> 2.2.5 Traceability and Observability </u>

##### Structured Logging:
- All application logs use JSON-formatted structured logging with fields: `timestamp`, `level`, `logger`, `filename`, `line_number`, `message`.
- Each request is assigned a `trace_id` for end-to-end request tracing.
- Settings operations are logged at INFO level: "Settings retrieved for specialization {id}", "Settings updated for specialization {id}".
- Recipient additions/removals are logged at INFO level with the action type and specialization.

##### Error Persistence:
- All application errors are persisted to the `error_log` database table with full context (function name, file name, stack trace).
- Error log entries include `created_at` timestamp and `created_by` identifier ("settings_service") for audit purposes.

##### Request Logging:
- Incoming requests are logged at INFO level with method, path, and relevant parameters.
- Response status codes and latency are logged for monitoring purposes.
- Sensitive data (JWT tokens) is never included in log output.


### <u> Section 3: In Scope and Out Scope </u>

#### <u> 3.1 Inscope Details </u>

- Implementation of `GET /api/v1/specializations/{specializationId}/settings` endpoint returning settings configuration and email recipients list
- Implementation of `PUT /api/v1/specializations/settings/manage` endpoint for partial settings updates
- Email recipient management via action-based approach (add new recipients, soft-delete existing ones)
- Input validation using Pydantic v2 models for all request parameters and body fields
- UUID format validation for path parameters and request body identifiers
- Email format validation (RFC 5322) for `alert_recipient` field
- JWT Bearer token authentication for both endpoints (reusing existing middleware)
- Standardized response format following `BaseResponse` schema (`status_code`, `status`, `message`, `data`)
- Error handling with HTTP 400 (validation), 401 (unauthorized), 404 (not found), and 500 (server error) responses
- Error logging to the `error_log` database table for all unhandled exceptions
- SQLAlchemy ORM models for `settings`, `email_recipient`, `specializations`, and `error_log` tables
- Pydantic request/response models for settings data validation and serialization
- Layered architecture: Route (`settings_route.py`) → Service (`settings_service.py`) → Repository (`settings_repository.py`) → Schema
- Unit tests covering positive and negative cases for both endpoints
- Soft delete pattern for email recipient removal (`is_active = 0`)
- Transaction management for PUT endpoint to ensure atomicity across settings update and recipient actions

#### <u> 3.2 Outscope Details </u>

- Report generation and email delivery logic (covered in ZDAD-60)
- Azure DevOps sync operations (covered in separate story)
- Cron job scheduling and execution for email delivery
- Overview Dashboard API implementation (covered in ZDAD-34)
- Projects list API and project actions (covered in separate story)
- ServiceNow sync endpoints (covered in separate story)
- Repository detail API (covered in separate story)
- UI/Frontend implementation for the Settings page
- Database migration scripts (assumes tables are already provisioned)
- Email template management (CRUD for `email_templates` table)
- Specialization CRUD operations (assumes specializations are pre-seeded)
- Hard deletion of any records (all deletions are soft deletes)
- Bulk settings update across multiple specializations
- Settings import/export functionality
- Audit trail for settings changes (beyond error logging)


### <u> Section 4: Solution Diagrams </u>

#### <u> 4.1 UI/UX Design Diagram </u>

**Diagram Location:** N/A

#### <u> 4.2 Architecture Design Diagram </u>

**Diagram Location:** N/A

#### <u> 4.3 Infrastructure Design Diagram </u>

**Diagram Location:** N/A
