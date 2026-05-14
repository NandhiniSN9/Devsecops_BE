# Requirements Document

## Introduction

The Overview Dashboard API is the primary data source for the DevSecOps Jira Dashboard landing page (ZDAD-34). It provides delivery leads and stakeholders with a consolidated view of project health across the organization, enabling quick assessment of portfolio status and timely action on at-risk projects. The API exposes two endpoints: `GET /api/v1/overview` for KPI metrics, status distribution, and attention banner data, and `GET /api/v1/filters` for filter dropdown options. The backend is built with Python FastAPI, SQLAlchemy ORM, Pydantic v2, and PostgreSQL.

## Glossary

- **Overview_API**: The FastAPI application serving the Overview Dashboard endpoints at `/api/v1/overview` and `/api/v1/filters`.
- **KPI_Tile**: A metric card displaying a count, trend direction, and change value for a project category (Total Projects, Completed, Active, Inactive, At Risk, Not Applicable).
- **Trend**: A directional indicator derived from increase/decrease counts in the kpi_history table. Values: "increase", "decrease", or "flat".
- **Status_Distribution**: A breakdown of projects grouped by status with count and percentage for each status category.
- **Attention_Banner**: A notification element displaying the number of at-risk projects with a severity level (critical, warning, info).
- **Auth_Middleware**: The encrypted token authentication middleware that decrypts a bearer token using TOKEN_PRIVATE_KEY and validates the contained Jira email against the Jira API.
- **BaseResponse**: The standardized JSON response envelope containing `status_code`, `status`, `message`, and `data` fields.
- **KPI_History_Table**: The `kpi_history` database table containing pre-computed KPI counts per specialization, populated by the ADO Azure Sync cron (out of scope).
- **Period_Filter**: A query parameter enum restricting time-based filtering to `last_week`, `last_month`, or `last_3_months`.
- **Specialization_Filter**: A comma-separated list of specialization IDs used to filter KPI data by organizational specialization.
- **Error_Logger**: The component responsible for persisting unhandled exceptions to the `error_log` database table.
- **Filter_Service**: The service layer component that retrieves active specializations, clients, and statuses for dropdown population.

## Requirements

### Requirement 1: Overview Metrics Retrieval

**User Story:** As a delivery lead, I want to retrieve consolidated KPI metrics for all projects in a single API call, so that I can quickly assess portfolio health without navigating multiple screens.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/v1/overview` with a valid encrypted bearer token that resolves to a recognized Jira email, THE Overview_API SHALL return HTTP 200 with a BaseResponse containing KPI_Tile data for Total Projects, Completed, Active, Inactive, At Risk, and Not Applicable categories.
2. WHEN no `period` query parameter is provided, THE Overview_API SHALL default to `last_week` as the period filter.
3. WHEN a `period` query parameter with a value of `last_week`, `last_month`, or `last_3_months` is provided, THE Overview_API SHALL read KPI data from the KPI_History_Table filtered by the specified period.
4. IF a `period` query parameter is provided with a value not in [`last_week`, `last_month`, `last_3_months`], THEN THE Overview_API SHALL return HTTP 400 with a BaseResponse containing a message indicating the invalid parameter and the accepted values.
5. WHEN no `specialization` query parameter is provided, THE Overview_API SHALL aggregate KPI data across all specializations where `is_active = 1` by summing the `count` values from each matching KPI_History record, summing the `change` values per category, and deriving the aggregated `trend` per category as `increase` if the summed increase_count exceeds the summed decrease_count, `decrease` if the summed decrease_count exceeds the summed increase_count, or `flat` if both sums are equal.
6. WHEN a valid `specialization` CSV query parameter is provided containing up to 50 comma-separated specialization IDs, THE Overview_API SHALL return KPI data filtered to only the matching specialization records in the KPI_History_Table where `is_active = 1`, ignoring any specialization IDs that do not match existing active records.
7. IF all specialization IDs provided in the `specialization` query parameter are invalid or do not match any active records, THEN THE Overview_API SHALL return HTTP 200 with a BaseResponse containing KPI_Tile data where all `count` values are 0, all `trend` values are `null`, and all `change` values are 0.
8. THE Overview_API SHALL return each KPI_Tile with three fields: `count` (non-negative integer), `trend` (one of `increase`, `decrease`, `flat`, or `null` when no KPI_History records exist for the requested period and specialization filter), and `change` (non-negative integer representing the absolute difference from the prior period, or 0 when `trend` is `null`).
9. IF the request does not include a valid bearer token or the token does not resolve to a recognized Jira email, THEN THE Overview_API SHALL return HTTP 401 with a BaseResponse indicating authentication failure.
10. IF no KPI_History records exist for the requested period and specialization filter, THEN THE Overview_API SHALL return HTTP 200 with a BaseResponse containing KPI_Tile data where all `count` values are 0, all `trend` values are `null`, and all `change` values are 0.
11. IF an unhandled error occurs during request processing, THEN THE Overview_API SHALL return HTTP 500 with a BaseResponse containing a generic error message and log the error details to the error_log table.

### Requirement 2: Trend Derivation

**User Story:** As a delivery lead, I want to see trend indicators on each KPI tile, so that I can understand whether metrics are improving or declining compared to the previous period.

#### Acceptance Criteria

1. WHEN the `{metric}_increase_count` column value is greater than zero and the `{metric}_decrease_count` column value is zero in the selected KPI_History_Table record, THE Overview_API SHALL set the trend to "increase" and the change value to the `{metric}_increase_count`.
2. WHEN the `{metric}_decrease_count` column value is greater than zero and the `{metric}_increase_count` column value is zero in the selected KPI_History_Table record, THE Overview_API SHALL set the trend to "decrease" and the change value to the `{metric}_decrease_count`.
3. WHEN both `{metric}_increase_count` and `{metric}_decrease_count` are zero in the selected KPI_History_Table record, THE Overview_API SHALL set the trend to "flat" and the change value to 0.
4. IF both `{metric}_increase_count` and `{metric}_decrease_count` are greater than zero in the selected KPI_History_Table record, THEN THE Overview_API SHALL set the trend to "increase" and the change value to the `{metric}_increase_count`.
5. IF no KPI_History_Table record exists for the requested specialization and period combination, THEN THE Overview_API SHALL set the trend to null and the change value to 0.
6. THE Overview_API SHALL apply the trend derivation logic defined in criteria 1 through 5 to all six KPI categories: projects, completed, active, inactive, at_risk, and not_applicable.
7. WHEN a specialization filter is provided, THE Overview_API SHALL select the most recent KPI_History_Table record (by `created_at`) for the matching specialization_id whose `created_at` falls within the requested period range and derive the trend from that single record.
8. WHEN no specialization filter is provided, THE Overview_API SHALL sum the `{metric}_increase_count` and `{metric}_decrease_count` values across the most recent KPI_History_Table record (by `created_at`) per specialization within the requested period range, and apply the trend derivation logic from criteria 1 through 4 to the summed values.
9. WHEN the period parameter is "last_week", THE Overview_API SHALL consider KPI_History_Table records with `created_at` within the last 7 days; WHEN "last_month", within the last 30 days; WHEN "last_3_months", within the last 90 days.

### Requirement 3: Status Distribution Computation

**User Story:** As a delivery lead, I want to see the distribution of projects across statuses, so that I can visualize the proportion of projects in each state.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/v1/overview` with valid authentication, THE Overview_API SHALL return a `status_distribution` object containing a `total` count (non-negative integer representing the sum of all status counts in the breakdown) and a `breakdown` array.
2. WHEN computing the status distribution, THE Overview_API SHALL join the `projects` table with the `statuses` table, grouping by status and counting active projects (`is_active = 1`).
3. THE Overview_API SHALL calculate the `percentage` field for each status as `(status_count / total_count) * 100`, rounded to one decimal place.
4. IF the total project count is zero, THEN THE Overview_API SHALL set the `percentage` to 0.0 for all statuses in the breakdown to avoid division-by-zero errors.
5. WHEN a `specialization` filter is applied, THE Overview_API SHALL compute the status distribution only for projects that have at least one associated record in the `devsecops_tickets` table where `devsecops_tickets.specialization_id` matches one of the filtered specialization IDs.
6. THE Overview_API SHALL include all statuses from the `statuses` table where `is_active = 1` in the breakdown array, even if no projects currently have that status (count of 0).
7. THE Overview_API SHALL return each object in the `breakdown` array containing three fields: `status` (string, the status name from `statuses.status_name`), `count` (non-negative integer), and `percentage` (float, rounded to one decimal place, range 0.0 to 100.0).
8. THE Overview_API SHALL return the `breakdown` array sorted alphabetically by the `status` field in ascending order.

### Requirement 4: Attention Banner

**User Story:** As a delivery lead, I want to see a prominent banner when projects are at risk, so that I can prioritize immediate action on critical items.

#### Acceptance Criteria

1. WHEN the Overview_API retrieves the `at_risk_count` from the KPI_History_Table and the value is greater than zero, THE Overview_API SHALL include an `attention_banner` object in the response containing `message` (string of no more than 200 characters that includes the numeric `at_risk_count` value), `at_risk_count` (integer matching the retrieved value), and `severity` (one of "critical", "warning", or "info").
2. IF the `at_risk_count` is 5 or more, THEN THE Overview_API SHALL set the `severity` field to "critical".
3. IF the `at_risk_count` is between 1 and 4 inclusive, THEN THE Overview_API SHALL set the `severity` field to "warning".
4. WHEN the Overview_API retrieves the `at_risk_count` from the KPI_History_Table and the value is zero, THE Overview_API SHALL include an `attention_banner` object in the response with `severity` set to "info", `at_risk_count` set to 0, and `message` indicating that no projects are currently at risk.
5. WHEN a `specialization` filter is applied to the Overview_API request, THE Overview_API SHALL derive the `attention_banner` fields from the filtered `at_risk_count` corresponding to the specified specialization(s) in the KPI_History_Table by summing the `at_risk_count` values across all matching specializations.
6. IF the `at_risk_count` is greater than zero, THEN THE Overview_API SHALL populate the `message` field with a string that includes the numeric `at_risk_count` value and a statement that projects require attention.
7. IF the Overview_API fails to retrieve the `at_risk_count` from the KPI_History_Table due to a database error, THEN THE Overview_API SHALL return an HTTP 500 response following the standardized error response schema and log the error to the `error_log` table.

### Requirement 5: Filters Endpoint

**User Story:** As a delivery lead, I want to retrieve all available filter options in a single call, so that I can populate dropdown menus on the dashboard without multiple requests.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/v1/filters` with valid authentication, THE Filter_Service SHALL return HTTP 200 with a BaseResponse containing `specializations`, `clients`, and `statuses` arrays sorted alphabetically by `name` in ascending order (case-insensitive).
2. WHEN processing the filters request, THE Filter_Service SHALL read specializations from the `specializations` table where `is_active = 1`, returning objects with `id` (mapped from `specialization_id`) and `name` (mapped from `specialization_name`) fields.
3. WHEN processing the filters request, THE Filter_Service SHALL derive clients from distinct non-null and non-empty-string `client` values in the `projects` table where `is_active = 1`, returning objects with `id` (a deterministic UUID v5 generated using a fixed application namespace and the `client` value as input) and `name` (the `client` value) fields.
4. WHEN processing the filters request, THE Filter_Service SHALL read statuses from the `statuses` table where `is_active = 1`, returning objects with `id` (mapped from `status_id`) and `name` (mapped from `status_name`) fields.
5. THE Filter_Service SHALL set a `Cache-Control` header with a `max-age` of 3600 seconds on the filters response.
6. IF no active records exist for a filter category, THEN THE Filter_Service SHALL return an empty array `[]` for that category within the response.
7. IF the database is unavailable when processing the filters request, THEN THE Filter_Service SHALL return HTTP 500 with a BaseResponse containing status `"error"` and a message indicating a server error occurred.
8. IF the authentication token is missing or invalid, THEN THE Filter_Service SHALL return HTTP 401 with a BaseResponse containing status `"failed"` and a message indicating authentication failure.
9. WHEN processing the filters request, THE Filter_Service SHALL return the response within 2 seconds under normal operating conditions.

### Requirement 6: Encrypted Token Authentication

**User Story:** As a system administrator, I want all API endpoints to require encrypted token authentication with Jira email validation, so that only authorized users can access dashboard data.

#### Acceptance Criteria

1. WHEN a request is received without a Bearer token in the Authorization header, THE Auth_Middleware SHALL return HTTP 401 with a BaseResponse containing status "failed" and message "Authentication token is missing or expired".
2. IF a request contains a Bearer token that cannot be decrypted using the TOKEN_PRIVATE_KEY environment variable, THEN THE Auth_Middleware SHALL return HTTP 401 with a BaseResponse containing status "failed" and message "Authentication failed or user not found in Jira".
3. WHEN a request contains a Bearer token that is successfully decrypted using the TOKEN_PRIVATE_KEY environment variable, THE Auth_Middleware SHALL extract the Jira email from the decrypted payload and validate it by calling the Jira REST API at JIRA_BASE_URL using JIRA_API_TOKEN to confirm the email corresponds to an existing Jira user.
4. IF the decrypted token payload does not contain a non-empty email field, THEN THE Auth_Middleware SHALL return HTTP 401 with a BaseResponse containing status "failed" and message "Authentication failed or user not found in Jira".
5. IF the Jira email validation fails because the user is not found in Jira, THEN THE Auth_Middleware SHALL return HTTP 401 with a BaseResponse containing status "failed" and message "Authentication failed or user not found in Jira".
6. IF the Jira API is unreachable or returns an HTTP status code outside the 200–299 range due to a network or server error, THEN THE Auth_Middleware SHALL return HTTP 401 with a BaseResponse containing status "failed" and message "Authentication failed or user not found in Jira".
7. WHEN the Jira email validation succeeds, THE Auth_Middleware SHALL allow the request to proceed to the target endpoint handler with the validated email available in the request context.
8. THE Auth_Middleware SHALL enforce a maximum timeout of 10 seconds for the Jira API validation call.

### Requirement 7: Query Parameter Validation

**User Story:** As a developer consuming the API, I want clear error messages when I provide invalid query parameters, so that I can quickly correct my requests.

#### Acceptance Criteria

1. WHEN the `period` query parameter contains a value not matching one of [last_week, last_month, last_3_months] using case-sensitive comparison, THE Overview_API SHALL return HTTP 400 with a BaseResponse containing status "failed" and a message indicating the parameter name "period" and the list of accepted values.
2. WHEN the `specialization` query parameter contains IDs where some match active specialization records and some do not, THE Overview_API SHALL ignore the non-matching IDs and return results filtered to the valid IDs only.
3. WHEN the `specialization` query parameter is an empty string or all provided IDs do not match any active specialization records, THE Overview_API SHALL treat it as no filter applied and return data for all specializations.
4. WHEN the `period` query parameter is provided as an empty string, THE Overview_API SHALL return HTTP 400 with a BaseResponse containing status "failed" and a message indicating the parameter name "period" and the list of accepted values.
5. WHEN the `period` query parameter is omitted from the request, THE Overview_API SHALL default to "last_week" and proceed with normal processing.
6. WHEN both `period` and `specialization` query parameters are invalid, THE Overview_API SHALL validate `period` first and return the HTTP 400 error for the `period` parameter without evaluating the `specialization` parameter.

### Requirement 8: Error Handling and Logging

**User Story:** As a system administrator, I want all unhandled exceptions to be logged to the database with full context, so that I can investigate and resolve issues efficiently.

#### Acceptance Criteria

1. WHEN an unhandled exception occurs during request processing, THE Error_Logger SHALL insert a record into the `error_log` table with `error_message` (exception message text, maximum 65,535 characters, truncated if exceeded), `error_function` (function name where the error occurred), `error_file` (file path where the error originated), `stack_trace` (full Python stack trace, maximum 65,535 characters, truncated if exceeded), and `created_by` set to the originating service identifier (one of: "overview_service", "servicenow_sync_service", "report_service").
2. WHEN an unhandled exception occurs, THE Overview_API SHALL return HTTP 500 with a BaseResponse containing `status_code` 500, `status` "error", `message` "An unexpected error occurred. Please try again later", and `data` as an empty array.
3. WHEN an unhandled exception occurs, THE Error_Logger SHALL execute the database insert asynchronously so that error logging does not block the error response to the client.
4. WHEN an unhandled exception occurs, THE Overview_API SHALL return the HTTP 500 response to the client within 500 milliseconds regardless of whether the error log insert has completed.
5. IF the Error_Logger fails to insert a record into the `error_log` table (e.g., database unavailable), THEN THE Error_Logger SHALL log the failure to the application's structured JSON log output including the original exception details and the `trace_id`, without raising an additional exception or affecting the client response.
6. THE Overview_API SHALL include a `trace_id` (UUID v4 format) in structured JSON logs for every request, and SHALL include the same `trace_id` as a prefix in the format `[trace_id:{uuid}]` at the beginning of the `error_message` field value when logging unhandled exceptions to the `error_log` table, to enable correlation between application logs and database error records.
7. WHEN an unhandled exception occurs and the database connection is available (responds to queries within 2 seconds), THE Error_Logger SHALL persist the error_log record within 5 seconds of the exception occurrence.
8. IF the Error_Logger does not receive a database write acknowledgment within 10 seconds of attempting to persist an error_log record, THEN THE Error_Logger SHALL abandon the insert attempt and log the timeout failure to the application's structured JSON log output including the original exception details.

### Requirement 9: Health and Readiness Endpoints

**User Story:** As a platform engineer, I want health check and readiness endpoints, so that the container orchestrator can determine if the service is alive and ready to serve traffic.

#### Acceptance Criteria

1. WHEN a GET request is made to `/health`, THE Overview_API SHALL return HTTP 200 with a JSON body containing a status field set to "healthy", without requiring authentication, within 500 milliseconds.
2. WHEN a GET request is made to `/ready`, THE Overview_API SHALL execute a database connectivity check query within a timeout of 5 seconds and return HTTP 200 with a JSON body containing a status field set to "ready", without requiring authentication, within 6 seconds total response time.
3. IF the database connectivity check fails or does not respond within 5 seconds during a readiness check, THEN THE Overview_API SHALL return HTTP 503 with a JSON body containing a status field set to "unavailable".
4. THE Overview_API SHALL expose the `/health` and `/ready` endpoints without requiring Bearer token authentication so that container orchestrator probes can access them without credentials.
5. IF an unexpected error occurs while processing the `/health` endpoint, THEN THE Overview_API SHALL return HTTP 503 with a JSON body containing a status field set to "unhealthy".

### Requirement 10: Standardized Response Format

**User Story:** As a frontend developer, I want all API responses to follow a consistent structure, so that I can implement a single response parser for all endpoints.

#### Acceptance Criteria

1. THE Overview_API SHALL return all responses (success and error) using the BaseResponse schema with fields: `status_code` (integer matching the HTTP response status code), `status` (enum: success, failed, error), `message` (non-empty string, maximum 256 characters), and `data` (non-null object or array, never omitted).
2. WHEN a request succeeds, THE Overview_API SHALL set `status_code` to the HTTP status code, set `status` to "success", and populate the `data` field with the endpoint-specific response payload as a non-null object.
3. IF a request fails due to a client error (4xx status codes including 400, 401, 403, 404), THEN THE Overview_API SHALL set `status_code` to the corresponding HTTP status code, set `status` to "failed", set `message` to a non-empty description indicating the failure reason, and set `data` to an empty array.
4. IF a request fails due to a server error (5xx status codes), THEN THE Overview_API SHALL set `status_code` to the corresponding HTTP status code, set `status` to "error", set `message` to a non-empty description indicating a server-side failure occurred, and set `data` to an empty array.
5. THE Overview_API SHALL include the `Content-Type: application/json` header in all responses regardless of success or failure status.
6. THE Overview_API SHALL always include all four BaseResponse fields (`status_code`, `status`, `message`, `data`) in every response — none of these fields shall be omitted or set to null.

### Requirement 11: Application Configuration

**User Story:** As a DevOps engineer, I want all sensitive configuration managed through environment variables, so that secrets are never committed to source control and can be rotated without code changes.

#### Acceptance Criteria

1. THE Overview_API SHALL read DATABASE_URL, TOKEN_PRIVATE_KEY, JIRA_BASE_URL, and JIRA_API_TOKEN from environment variables at startup.
2. IF any required environment variable is missing or set to an empty string at startup, THEN THE Overview_API SHALL exit with a non-zero exit code and log an error message to standard error that includes the name of each missing or empty variable.
3. THE Overview_API SHALL validate the DATABASE_URL format as a valid PostgreSQL connection string matching the pattern `postgresql://` or `postgresql+asyncpg://` with host, port, and database name components during startup.
4. IF DATABASE_URL is present but does not match the expected PostgreSQL connection string pattern, THEN THE Overview_API SHALL exit with a non-zero exit code and log an error message to standard error indicating the invalid format.
5. IF JIRA_BASE_URL is present but is not a valid URL starting with `https://`, THEN THE Overview_API SHALL exit with a non-zero exit code and log an error message to standard error indicating the invalid JIRA_BASE_URL value.
6. IF TOKEN_PRIVATE_KEY is present but contains fewer than 10 characters, THEN THE Overview_API SHALL exit with a non-zero exit code and log an error message to standard error indicating the invalid TOKEN_PRIVATE_KEY value.
7. THE Overview_API SHALL load all environment variable values once at startup and retain them in memory for the lifetime of the process without re-reading from the environment.

### Requirement 12: Layered Architecture

**User Story:** As a developer, I want the codebase organized in a layered architecture, so that business logic, data access, and routing concerns are separated for maintainability and testability.

#### Acceptance Criteria

1. THE Overview_API SHALL organize code into four layers: Routes (FastAPI routers handling HTTP interface in `src/routes/`), Middleware (cross-cutting concerns such as authentication in `src/middleware/`), Services (business logic and orchestration in `src/services/`), and Repositories (SQLAlchemy ORM data access in `src/repositories/`).
2. THE Overview_API SHALL enforce unidirectional layer communication where Routes depend on Services and Services depend on Repositories, and no layer shall bypass the layer directly below it (route handlers shall not import or invoke repository functions directly).
3. THE Overview_API SHALL use dependency injection to provide service and repository instances to route handlers, such that each layer can be independently tested by substituting mock implementations of its dependencies.
4. THE Overview_API SHALL define SQLAlchemy ORM models in `src/repositories/schema/` for `kpi_history`, `specializations`, `projects`, `statuses`, `devsecops_tickets`, `settings`, and `error_log` tables, where each model maps column names and types to the schema defined in the ER diagram.
5. THE Overview_API SHALL define Pydantic v2 models in `src/models/` for all request query parameters and response payloads across the overview and filters endpoints, where each model specifies field types, required/optional status, default values, and constrained values (enums, min/max bounds) matching the API specification.
6. THE Overview_API SHALL place dependency injection configuration in `src/services/dependencies.py` to centralize the wiring of service and repository instances.
