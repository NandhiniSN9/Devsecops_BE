## SOLDEF-ZDAD-34 - Implement Overview Dashboard API

### <u>Project Details</u>
- **Project ID:** ZDAD  
- **Project Name:** DevSecOps Jira Dashboard  

### <u>Story Details</u>
- **Story ID:** ZDAD-34  
- **Story Name:** Implement Overview Dashboard API  
- **Story Description:**  
  When accessing the DevSecOps dashboard, the ability to view a consolidated overview of project KPIs, status distribution and specialization filters is needed so that delivery leads can quickly assess portfolio health and take timely action on at-risk projects.
- **Scope:**  
  The goal is to implement the Overview Dashboard API for the DevSecOps Dashboard. The `GET /api/v1/overview` endpoint will return KPI tiles, status distribution, and attention banner in a single call. The `GET /api/v1/filters` endpoint will provide all filter dropdown options (specializations, clients, statuses) — on the Overview screen, only the specialization value is used for filtering. This consolidation streamlines data retrieval, improves performance and enhances the user experience for team members accessing the dashboard.
- **Acceptance Criteria:**
  - The `GET /api/v1/overview` endpoint returns KPI tiles (Total Projects, Adopted, Adoption Rate, At Risk, Active, Inactive), status distribution data, and attention banner details in one response.
  - The `GET /api/v1/filters` endpoint returns filter values (specializations, clients, statuses) — the specialization values are used to populate the dropdown filter on the Overview page.
  - The overview data accurately reflects the current state of all onboarded projects.
  - Both endpoints handle errors like database unavailability and invalid requests, returning meaningful responses.
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

The Overview Dashboard API is the primary data source for the DevSecOps Jira Dashboard landing page. It provides delivery leads and stakeholders with a consolidated view of project health across the organization, enabling them to quickly assess portfolio status and take timely action on at-risk projects. The API exposes two endpoints: `GET /api/v1/overview` which returns KPI tiles (Total Projects, Adopted, Adoption Rate, At Risk, Active, Inactive), status distribution data, and an attention banner with critical alerts — all in a single response. The `GET /api/v1/filters` endpoint provides all filter dropdown options (specializations, clients, statuses) — on the Overview screen, only the specialization value is used to populate the query param for the overview API. Both endpoints require encrypted token authentication (with Jira email validation) and return standardized JSON responses. The KPI data is read directly from the `kpi_history` table which is populated by the ADO Azure Sync cron, ensuring the Overview API performs efficient read operations without any on-the-fly calculations. All errors encountered during request processing are logged to the `error_log` database table for traceability and debugging purposes.

#### <u> 1.2 Requirement Details </u>

- **ZDAD-34-FR01: Overview Dashboard Metrics and Data Retrieval**
- **ZDAD-34-FR02: Filters Endpoint**
- **ZDAD-34-FR03: Attention Banner**
- **ZDAD-34-FR04: Query Parameter Validation**
- **ZDAD-34-FR05: Error Logging**

##### <u> 1.2.1 ZDAD-34-FR01: Overview Dashboard Metrics and Data Retrieval </u>

##### Description:
The system shall expose a `GET /api/v1/overview` endpoint that returns KPI tiles, status distribution data, and attention banner details in a single consolidated response. The endpoint accepts optional query parameters for filtering by time period and specialization. The KPI data is read directly from the `kpi_history` table (populated by the ADO Azure Sync cron — out of scope). The trend is derived from the `increase_count` and `decrease_count` columns already stored in the table.

##### Request Parameters:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `period` | string (enum) | No | `last_week` | Time period for metric calculations |
| `specialization` | string (CSV) | No | All | Comma-separated specialization IDs to filter by |

##### Period Options:
- `last_week` — Last 7 days
- `last_month` — Last 30 days
- `last_3_months` — Last 90 days

##### Response Structure - KPI Tiles:
The response `data.metrics` object contains KPI tiles read directly from the `kpi_history` table (populated by the ADO Azure Sync cron — out of scope for this story). Each tile contains `count`, `trend`, and `change`:

- `totalProjects` — Total number of onboarded projects. Read from `projects_count`. Trend is determined by checking `projects_increase_count` and `projects_decrease_count`: if increase > 0 → `"increase"`, if decrease > 0 → `"decrease"`, if both are 0 → `"flat"`. Change value is whichever is non-zero.
- `completed` — Projects that have a `completed_at` date set in the `projects` table. Read from `completed_count`. Trend from `completed_increase_count` / `completed_decrease_count`.
- `active` — Projects with pipeline activity within the last 10 days. Read from the corresponding count in `kpi_history`. Trend from increase/decrease columns.
- `inactive` — Projects with no pipeline activity for 10+ days. Read from `inactive_count`. Trend from `inactive_increase_count` / `inactive_decrease_count`.
- `atRisk` — Projects where days since onboarding exceeds the `at_risk_threshold` (from `settings` table) and not yet completed. Read from `at_risk_count`. Trend from `at_risk_increase_count` / `at_risk_decrease_count`.
- `notApplicable` — Projects marked as not applicable (exception raised). Read from `not_applicable_count`. Trend from `not_applicable_increase_count` / `not_applicable_decrease_count`.

**Trend Logic (applies to all tiles):**
- If `{metric}_increase_count > 0` → trend = `"increase"`, change = `{metric}_increase_count`
- If `{metric}_decrease_count > 0` → trend = `"decrease"`, change = `{metric}_decrease_count`
- If both are 0 → trend = `"flat"`, change = 0

**Note:** The actual computation and insertion of these values into `kpi_history` is handled by the ADO Azure Sync cron job (out of scope for this story). The Overview API only reads and returns the pre-populated values.

##### Response Structure - Status Distribution:
The response `data.statusDistribution` object contains:
- `total` — Total project count.
- `breakdown[]` — Array of objects each with `status` (name), `count`, and `percentage` (float).

##### Data Source:
- All KPI tile values (`count`, `trend`, `change`) are read directly from the `kpi_history` table. The Overview API does not compute these values — they are pre-populated by the ADO Azure Sync cron job (out of scope).
- The `kpi_history` table stores counts and increase/decrease values per specialization, synced periodically by the cron.
- When a `specialization` filter is applied, the API reads the `kpi_history` record matching that `specialization_id`.
- When no specialization filter is provided, the API aggregates across all specializations.
- Status distribution is computed from the `projects` table joined with `statuses` table.
- Attention banner is derived from the `at_risk_count` in `kpi_history`.
- Database schema is defined in `design/er_diagram.mmd`.

##### Acceptance Criteria:
- The endpoint returns HTTP 200 with correct KPI tiles, status distribution, and attention banner when called with valid parameters.
- Default period is `last_week` when no period parameter is provided.
- When specialization filter is provided, only metrics for matching specializations are returned.
- When specialization filter is omitted, metrics across all specializations are aggregated.
- Trend values are one of: `increase`, `decrease`, `flat`, or `null`.
- The attention banner severity is `critical` when at-risk count > 5, `warning` when 1-5, and `info` when 0.
- Response follows the standardized `BaseResponse` schema with `status_code`, `status`, `message`, and `data` fields.
- The overview data accurately reflects the current state of all onboarded projects.

##### <u> 1.2.2 ZDAD-34-FR02: Filters Endpoint </u>

##### Description:
The system shall expose a `GET /api/v1/filters` endpoint that returns all filter dropdown options (specializations, clients, statuses) in a single consolidated response. On the Overview screen, only the specialization value is used to populate the query param for the overview API. Other filter values (clients, statuses) are available for use by other screens (e.g., Projects list).

##### Response Structure:
The response `data` object contains:
- `specializations` — Array of objects each containing:
  - `id` — Unique identifier for the specialization (UUID).
  - `name` — Display name of the specialization (e.g., "DevSecOps", "DevOps", "Cloud Security").
- `clients` — Array of objects each containing:
  - `id` — Unique identifier for the client.
  - `name` — Display name of the client (e.g., "ABN AMRO", "Barclays").
- `statuses` — Array of objects each containing:
  - `id` — Unique identifier for the status.
  - `name` — Display name of the status (e.g., "Active", "At Risk", "Completed").

##### Data Source:
- Specializations are read from the `specializations` table where `is_active = 1`.
- Clients are derived from distinct `client` values in the `projects` table where `is_active = 1`.
- Statuses are read from the `statuses` table where `is_active = 1`.

##### Acceptance Criteria:
- The endpoint returns HTTP 200 with all filter options (specializations, clients, statuses) in a single response.
- Each filter group contains objects with `id` and `name` fields.
- Only active records (`is_active = 1`) are returned.
- Response follows the standardized `BaseResponse` schema.
- The endpoint requires encrypted token authentication with Jira email validation.
- The response is cacheable with a TTL of 1 hour.
- On the Overview screen, only the specialization values are used for filtering.

##### <u> 1.2.4 ZDAD-34-FR04: Query Parameter Validation </u>

##### Description:
The system shall validate all query parameters received by the Overview API endpoint. Invalid parameter values must result in a 400 Bad Request response with a descriptive error message indicating which parameter is invalid and what values are accepted.

##### Validation Rules:
- `period` must be one of: `last_week`, `last_month`, `last_3_months`. Any other value returns 400.
- `specialization` values are validated against existing specialization IDs in the database. Invalid IDs are ignored (non-strict filtering).

##### Error Response Format:
```json
{
  "status_code": 400,
  "status": "failed",
  "message": "Invalid query parameter: 'period' must be one of [last_week, last_month, last_3_months]",
  "data": []
}
```

##### Acceptance Criteria:
- Invalid `period` values return HTTP 400 with a descriptive error message.
- The error message clearly identifies the invalid parameter and accepted values.
- Valid requests with unknown specialization IDs do not fail but return filtered results (graceful handling).
- Response follows the standardized error response schema.
- Both endpoints handle errors like database unavailability and invalid requests, returning meaningful responses.

##### <u> 1.2.5 ZDAD-34-FR05: Error Logging </u>

##### Description:
The system shall log all unhandled exceptions and application errors to the `error_log` database table. This provides a persistent audit trail for debugging and incident investigation. Errors are logged with the function name, file name, error message, and full stack trace.

##### Error Log Table Fields:
- `error_id` — Auto-generated UUID primary key.
- `error_message` — The exception message text.
- `error_function` — The function name where the error occurred.
- `error_file` — The file path where the error originated.
- `stack_trace` — Full Python stack trace for debugging.
- `created_at` — Timestamp when the error was logged.
- `created_by` — System identifier (e.g., "overview_service").

##### Acceptance Criteria:
- All unhandled exceptions in the Overview API and Specializations API are captured and logged to the `error_log` table.
- The error log entry contains the function name, file name, error message, and stack trace.
- Error logging does not interfere with the error response returned to the client (non-blocking).
- HTTP 500 responses are always accompanied by an `error_log` entry.

#### <u> 1.3 Database Schema </u>

The full database schema is defined in `design/er_diagram.mmd`. The following tables are directly involved in the Overview Dashboard API:

- **kpi_history** — Pre-computed KPI counts per specialization (synced by cron). Contains `projects_count`, `completed_count`, `inactive_count`, `at_risk_count`, `not_applicable_count` with corresponding increase/decrease counts. The trend is calculated by comparing today's record with the previous day's record.
- **specializations** — Specialization lookup (filter source for the overview and the specializations dropdown endpoint).
- **statuses** — Status definitions (Active, Inactive, At Risk, Completed, Not Applicable).
- **projects** — Project records with `sn_project_id`, `onboarded_date`, `status_id`, `client`. Used for status distribution, total projects count, and at-risk calculation.
- **devsecops_tickets** — Tickets linked to projects and specializations. Used for total projects count when tickets are mapped to the default project (each unique `project_name` counts as a separate project).
- **settings** — Contains `at_risk_threshold` per specialization used to determine at-risk status.
- **error_log** — Persists unhandled exceptions for debugging.

##### Key Relationships:
- `projects.status_id` → `statuses.status_id` (each project has one status)
- `devsecops_tickets.specialization_id` → `specializations.specialization_id` (links projects to specializations)
- `devsecops_tickets.sn_project_id` → `projects.sn_project_id` (links tickets to projects)
- `kpi_history.specialization_id` → `specializations.specialization_id` (KPI data per specialization)
- `settings.specialization_id` → `specializations.specialization_id` (threshold config per specialization)


#### <u> 1.4 Project Artifacts </u>

- `api/openapi.yaml` — Full OpenAPI 3.0.3 specification defining all endpoints, request/response schemas, and error formats.
- `design/er_diagram.mmd` — Mermaid ER diagram showing all database tables and relationships.
- `design/requirements.md` — Section 1 (Overview API) contains the high-level requirements for this story.
- `diagram/ZDAD-34_overview_api_flow.mmd` — Sequence diagram showing the Overview API request flow.

#### <u> 1.5 Dependencies </u>

- **Python 3.12+** — Runtime environment
- **FastAPI** — Web framework for building the REST API
- **SQLAlchemy** — ORM for PostgreSQL database access
- **Pydantic v2** — Request/response model validation and serialization
- **PostgreSQL** — Primary database storing projects, KPI history, specializations, and error logs
- **cryptography / PyCryptodome** — Token decryption using private key
- **Jira API client (atlassian-python-api or httpx)** — Validates Jira email existence
- **Uvicorn** — ASGI server for running the FastAPI application
- **ADO Azure Sync Cron** — External dependency that computes and populates the `kpi_history` table (out of scope for this story)


### <u> Section 2: Non Functional Requirements </u>

### 2.1 Infrastructure and Deployment

#### <u> 2.1.1 Overview </u>

The Overview Dashboard API is deployed as part of the DevSecOps Jira Dashboard backend application on Azure App Service. The application is a Python FastAPI service running on Uvicorn, connected to a PostgreSQL database for persistent storage. The deployment follows a containerized approach with the application packaged as a Docker image and deployed to Azure App Service. The infrastructure leverages Azure-managed services for database hosting (Azure Database for PostgreSQL), application hosting (Azure App Service), and secret management. The deployment pipeline ensures zero-downtime deployments with health check validation before traffic routing. Environment-specific configurations are managed through Azure App Service application settings and environment variables, ensuring no secrets are hardcoded in the application code.

#### <u> 2.1.2 Requirement Details </u>

- **ZDAD-34-NFR01: Azure App Service Deployment**
- **ZDAD-34-NFR02: Environment Configuration**
- **ZDAD-34-NFR03: Health Check Endpoint**

##### <u> 2.1.2.1 ZDAD-34-NFR01: Azure App Service Deployment </u>

##### Description:
The application shall be deployed to Azure App Service as a containerized Python FastAPI application. The deployment uses a Docker image built from the project's Dockerfile and pushed to a container registry. Azure App Service is configured to pull the latest image and run the application with Uvicorn as the ASGI server.

##### Deployment Configuration:
- **Runtime:** Python 3.12+ container image
- **ASGI Server:** Uvicorn with configurable workers
- **Port:** Application listens on port 8080 (configurable via environment variable)
- **Startup Command:** `uvicorn main:app --host 0.0.0.0 --port 8080`

##### Acceptance Criteria:
- The application starts successfully on Azure App Service without errors.
- The health check endpoint responds within the configured startup timeout.
- Environment variables are correctly loaded from Azure App Service configuration.
- The application connects to PostgreSQL using connection string from environment variables.

##### <u> 2.1.2.2 ZDAD-34-NFR02: Environment Configuration </u>

##### Description:
All application configuration shall be managed through environment variables. Sensitive values such as database connection strings and the private key for token decryption are stored in Azure App Service application settings. A `.env.sample` file documents all required environment variables for local development.

##### Required Environment Variables:
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `TOKEN_PRIVATE_KEY` | Private key for token decryption (PEM format or path) | Yes |
| `JIRA_BASE_URL` | Jira instance base URL for email validation | Yes |
| `JIRA_API_TOKEN` | Jira API token for user lookup requests | Yes |
| `APP_ENV` | Environment identifier (development, staging, production) | Yes |
| `LOG_LEVEL` | Application log level (default: INFO) | No |
| `PORT` | Application port (default: 8080) | No |

##### Acceptance Criteria:
- The application fails to start with a clear error message if required environment variables are missing.
- No secrets or credentials are hardcoded in the application source code.
- A `.env.sample` file exists documenting all required variables with placeholder values.

#### <u> 2.1.3 Project Artifacts </u>

- `api/openapi.yaml` — API specification including health and readiness endpoints
- `design/er_diagram.mmd` — Database schema reference for readiness check validation

### 2.2 Architecture and System Design

#### <u> 2.2.1 Security and Compliance </u>

##### Token-Based Authentication with Jira Email Validation:
All API endpoints (except `/health` and `/ready`) require a valid encrypted token in the `Authorization` header. The authentication middleware decrypts the token using a private key to extract the Jira email ID, then validates that the email exists in Jira. Invalid or unrecognized tokens result in an HTTP 401 Unauthorized response.

##### Token Validation Flow:
1. Extract the `Authorization` header from the incoming request.
2. Verify the header contains a `Bearer` prefix followed by the encrypted token.
3. Decrypt the token using the configured private key to extract the payload (contains the Jira email ID).
4. If decryption fails (invalid token, corrupted data, wrong key), return HTTP 401.
5. Extract the Jira email ID from the decrypted payload.
6. Validate the Jira email ID by calling the Jira API to confirm the user exists and is active.
7. If the Jira email is not found or the user is inactive in Jira, return HTTP 401 with message: "User not found in Jira".
8. Attach the validated user context (email, display name) to the request for downstream use.
9. If validation fails at any step, return HTTP 401 with standardized error response.

##### Input Validation:
- All query parameters are validated using Pydantic models with strict enum constraints.
- SQL injection is prevented by using SQLAlchemy ORM with parameterized queries (no raw SQL).
- Request payloads are validated against Pydantic schemas before processing.

#### <u> 2.2.2 System Performance </u>

##### Database Query Optimization:
- The Overview API reads KPI counts and trend data directly from the `kpi_history` table (pre-populated by ADO Azure Sync cron), avoiding any on-the-fly calculations.
- Database indexes are maintained on frequently queried columns (`specialization_id`, `is_active`, `status_id`, `created_at`).
- SQLAlchemy connection pooling is configured to reuse database connections efficiently.

##### Response Efficiency:
- The API returns all overview data (KPI tiles, status distribution, attention banner) in a single response to minimize round trips.
- Status distribution is computed with a single aggregation query on the `projects` table.
- The specializations endpoint response is cacheable with a TTL of 1 hour.

#### <u> 2.2.3 Availability and Reliability </u>

##### Error Resilience:
- All unhandled exceptions are caught by a global exception handler that returns HTTP 500 and logs the error to the `error_log` table.
- Database connection failures are handled gracefully with appropriate error responses.
- The application implements connection retry logic for transient database failures.

##### Deployment Reliability:
- Azure App Service provides built-in auto-restart on application crashes.
- Health check endpoints enable Azure to detect and replace unhealthy instances.

#### <u> 2.2.4 Cost Efficiency </u>

##### Resource Optimization:
- KPI metrics and trend data in `kpi_history` (populated by ADO Azure Sync) eliminate on-the-fly computation, reducing database CPU usage.
- Azure App Service scaling is configured based on actual traffic patterns.
- PostgreSQL connection pooling minimizes the number of active database connections.
- Single consolidated response reduces network overhead and client-side complexity.

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
- Sensitive data (tokens, private keys, credentials) is never included in log output.



### <u> Section 3: In Scope and Out Scope </u>

#### <u> 3.1 Inscope Details </u>

- Implementation of `GET /api/v1/overview` endpoint returning KPI tiles (Total Projects, Adopted, Adoption Rate, At Risk, Active, Inactive), status distribution, and attention banner in one response
- Implementation of `GET /api/v1/filters` endpoint returning all filter dropdown options (specializations, clients, statuses) — only specialization is used on the Overview screen
- Encrypted token authentication middleware with Jira email validation for both endpoints
- Query parameter validation for `period` (enum) and `specialization` (CSV) filters
- Reading KPI data from the `kpi_history` table (populated by ADO Azure Sync cron — out of scope)
- Deriving trend from `increase_count` / `decrease_count` columns (increase > 0 → "increase", decrease > 0 → "decrease", both 0 → "flat")
- Computing status distribution from the `projects` and `statuses` tables
- Computing attention banner with severity levels based on at-risk project count
- Standardized response format following `BaseResponse` schema (`status_code`, `status`, `message`, `data`)
- Error handling with HTTP 400, 401, and 500 responses with meaningful messages
- Error logging to the `error_log` database table for all unhandled exceptions
- Health check (`/health`) and readiness (`/ready`) endpoints
- SQLAlchemy ORM models for `kpi_history`, `specializations`, `projects`, `statuses`, `devsecops_tickets`, `settings`, and `error_log` tables
- Pydantic v2 request/response models for validation and serialization
- Structured JSON logging with trace_id for request tracing
- Environment variable-based configuration with validation at startup
- Layered architecture: Routes → Services → Repositories → Data Store
- Unit tests covering positive and negative cases for both endpoints

#### <u> 3.2 Outscope Details </u>

- UI/Frontend implementation
- Caching layer implementation (Redis or in-memory)
- Rate limiting and throttling
- Role-based access control (RBAC) beyond token authentication

### <u> Section 4: Solution Diagrams </u>

#### <u> 4.1 UI/UX Design Diagram </u>

**Diagram Location:** Not applicable for this story (backend API only)

#### <u> 4.2 Architecture Design Diagram </u>

**Diagram Location:** `diagram/ZDAD-34_overview_api_flow.mmd`

#### <u> 4.3 Infrastructure Design Diagram </u>

**Diagram Location:** Not applicable for this story
