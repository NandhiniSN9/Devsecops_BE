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
        - [1.2.1 ZDAD-34-FR01: Overview Dashboard Metrics and Data Retrieval](#1.2.1-ZDAD-34-FR01:-Overview-Dashboard-Metrics-and-Data-Retrieval)
        - [1.2.2 ZDAD-34-FR02: Filters Endpoint](#1.2.2-ZDAD-34-FR02:-Filters-Endpoint)
        - [1.2.3 ZDAD-34-FR03: Attention Banner](#1.2.3-ZDAD-34-FR03:-Attention-Banner)
        - [1.2.4 ZDAD-34-FR04: Query Parameter Validation](#1.2.4-ZDAD-34-FR04:-Query-Parameter-Validation)
        - [1.2.5 ZDAD-34-FR05: Error Logging](#1.2.5-ZDAD-34-FR05:-Error-Logging)
    - [1.3 Database Schema](#1.3-Database-Schema)
    - [1.4 Project Artifacts](#1.4-Project-Artifacts)
    - [1.5 Environment Variables](#1.5-Environment-Variables)
- [Section 2: In Scope and Out Scope](#Section-2:-In-Scope-and-Out-Scope)
    - [2.1 In Scope Details](#2.1-In-Scope-Details)
    - [2.2 Out Scope Details](#2.2-Out-Scope-Details)
- [Section 3: Solution Diagrams](#Section-3:-Solution-Diagrams)

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

#### <u> 1.5 Environment Variables </u>

##### Description:
All application configuration shall be managed through environment variables. Sensitive values such as database connection strings and the private key for token decryption are stored in Azure App Service application settings. A `.env.sample` file documents all required environment variables for local development.

##### Required Environment Variables:
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `TOKEN_PRIVATE_KEY` | Private key for token decryption (PEM format or path) | Yes |
| `JIRA_BASE_URL` | Jira instance base URL for email validation | Yes |
| `JIRA_API_TOKEN` | Jira API token for user lookup requests | Yes |

### <u> Section 2: In Scope and Out Scope </u>

#### <u> 2.1 Inscope Details </u>

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

#### <u> 2.2 Outscope Details </u>

- UI/Frontend implementation
- Caching layer implementation (Redis or in-memory)
- Rate limiting and throttling
- Role-based access control (RBAC) beyond token authentication


### <u> Section 3: Solution Diagrams </u>

#### <u> 3.1 Architecture Diagram </u>

**Diagram Location:** `diagram/email_notification.mmd`
