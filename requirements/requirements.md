# DevSecOps Jira Dashboard - Requirements

## 1. Overview API (ZDAD-34)

### 1.1 Description

The Overview API provides dashboard-level KPI metrics, status distribution, and attention banner for all onboarded projects. It serves as the landing page data source, giving delivery leads and stakeholders a consolidated view of project health across the organization. The KPI data is read directly from the `kpi_history` table which is populated by the ADO Azure Sync cron, ensuring the Overview API performs efficient read operations without any on-the-fly calculations.

### 1.2 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/overview` | GET | Get overview dashboard metrics, status distribution, and attention banner |
| `/api/v1/filters` | GET | Get all filter dropdown options (specializations, clients, statuses) |

### 1.3 Filters — Overview Endpoint

| Filter | Parameter | Type | Required | Default | Description |
|--------|-----------|------|----------|---------|-------------|
| Period | `period` | string (enum) | No | `last_week` | Time period for metric calculations |
| Specialization | `specialization` | string (CSV) | No | All | Comma-separated specialization IDs to filter by |

#### Period Options
- `last_week` — Last 7 days
- `last_month` — Last 30 days
- `last_3_months` — Last 90 days

#### Specialization Filter
- Accepts a comma-separated list of specialization IDs (e.g., `devsecops,devops`)
- When empty or omitted, returns metrics aggregated across all specializations
- Invalid IDs are ignored (non-strict filtering)
- Valid IDs are retrieved from `GET /api/v1/filters`

### 1.4 Response — KPI Metrics

The API returns the following KPI tiles read directly from the `kpi_history` table:

| KPI | Field | Description |
|-----|-------|-------------|
| Total Projects | `metrics.total_projects` | Total number of onboarded projects |
| Completed | `metrics.completed` | Projects with a `completed_at` date set |
| Active | `metrics.active` | Projects with pipeline activity within the last 10 days |
| Inactive | `metrics.inactive` | Projects with no pipeline activity for 10+ days |
| At Risk | `metrics.at_risk` | Projects where days since onboarding exceeds `at_risk_threshold` and not yet completed |
| Not Applicable | `metrics.not_applicable` | Projects marked as not applicable (exception raised) |

Each KPI includes:
- `count` — Current value from `kpi_history`
- `trend` — Direction: `increase`, `decrease`, `flat`, or `null`
- `change` — Numeric difference (whichever of increase/decrease count is non-zero)

### 1.4.1 Response — Sync Detail

The response `data.sync_detail` object provides synchronization status information:

| Field | Type | Description |
|-------|------|-------------|
| `last_sync_datetime` | string (nullable) | Most recent sync timestamp in "DD Mon YYYY, HH:MM" format, or null if never synced |
| `is_sync_in_progress` | boolean | Whether an ADO sync operation is currently in progress |

- `last_sync_datetime` is derived from the `last_synced` column in the `settings` table (max value across matching specializations).
- `is_sync_in_progress` is determined by checking the `cron_jobs` table for any active record with `type = "azure"` and `sync_status = "pending"`.

#### Trend Logic (applies to all tiles):
- If `{metric}_increase_count > 0` → trend = `"increase"`, change = `{metric}_increase_count`
- If `{metric}_decrease_count > 0` → trend = `"decrease"`, change = `{metric}_decrease_count`
- If both are 0 → trend = `"flat"`, change = 0

### 1.5 Response — Status Distribution

- `status_distribution.total` — Total project count
- `status_distribution.breakdown[]` — Array of status groups, each with:
  - `status` — Status name (Completed, Active, Inactive, At Risk, Not Applicable)
  - `count` — Number of projects in that status
  - `percentage` — Percentage of total projects (float)

Status distribution is computed from the `projects` table joined with `statuses` table.

### 1.6 Response — Attention Banner

- `attention_banner.message` — Alert message (e.g., "6 projects are at risk and require immediate attention")
- `attention_banner.at_risk_count` — Number of at-risk projects
- `attention_banner.severity` — Severity level: `critical`, `warning`, or `info`

Derived from the `at_risk_count` in `kpi_history`.

### 1.7 Filters Endpoint — `GET /api/v1/filters`

Returns all filter dropdown options in a single response. On the Overview screen, only the specialization value is used to populate the query param for the overview API.

#### Response Structure:
- `specializations[]` — Array of `{id, name}` from `specializations` table where `is_active = 1`
- `clients[]` — Array of `{id, name}` from distinct `client` values in `projects` table where `is_active = 1`
- `statuses[]` — Array of `{id, name}` from `statuses` table where `is_active = 1`

Cacheable with TTL of 1 hour.

### 1.8 Authentication

- Requires encrypted token authentication with Jira email validation
- Token is decrypted with private key, containing Jira email for validation
- Returns 401 if the token is missing, expired, or invalid

### 1.9 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid query parameter value (e.g., unsupported period) |
| 401 | Missing or invalid authentication token |
| 500 | Unexpected server error |

### 1.10 Error Logging

All unhandled exceptions are logged to the `error_log` database table with:
- `error_message` — Exception message text
- `error_function` — Function name where the error occurred
- `error_file` — File path where the error originated
- `stack_trace` — Full Python stack trace
- `created_by` — "overview_service"

### 1.11 Data Sources

| Table | Role |
|-------|------|
| `kpi_history` | Pre-computed KPI counts per specialization (synced by ADO cron) |
| `specializations` | Specialization lookup for filters and KPI queries |
| `statuses` | Status definitions for filters and distribution |
| `projects` | Project records for status distribution and client filter |
| `settings` | Contains `at_risk_threshold` per specialization and `last_synced` timestamp |
| `cron_jobs` | Tracks sync operations; used to determine if sync is in progress |
| `error_log` | Persists unhandled exceptions |

### 1.12 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `TOKEN_PRIVATE_KEY` | Private key for token decryption (PEM format or path) | Yes |
| `JIRA_BASE_URL` | Jira instance base URL for email validation | Yes |
| `JIRA_API_TOKEN` | Jira API token for user lookup requests | Yes |

---

## 2. ServiceNow Sync (ZDAD-58)

### 2.1 Description

The ServiceNow Sync module handles the ingestion of project and DevSecOps ticket data from ServiceNow into the dashboard database. ServiceNow acts as the source of truth for project onboarding and ticket creation. A webhook configured in ServiceNow triggers the project sync endpoint when a new project is created, ensuring real-time ingestion without manual data entry. A separate endpoint receives DevSecOps ticket data pushed by ServiceNow when a ticket is completed.

### 2.2 How the Sync Works

```
┌──────────────┐         ┌──────────────────────┐         ┌────────────┐
│  ServiceNow  │──POST──▶│  DevSecOps Dashboard │──────▶  │  Database  │
│  (Webhook)   │         │       API            │         │  (Insert)  │
└──────────────┘         └──────────────────────┘         └────────────┘
```

1. A webhook or event-driven script in ServiceNow triggers the sync.
2. The script sends an HTTP POST request to the dashboard API with project or ticket data.
3. The API authenticates by decrypting the token and validating the ServiceNow email against `SERVICENOW_ALLOWED_EMAIL` env var.
4. Upon successful authentication, the API processes the payload and inserts data into the database.
5. The API returns a success or error response back to ServiceNow.

### 2.3 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sync/servicenow/projects` | POST | Ingest projects from ServiceNow (insert-only, skip duplicates) |
| `/api/v1/sync/servicenow/devsecops-tickets` | POST | Ingest DevSecOps tickets with repositories from ServiceNow |

### 2.4 Authentication

- Encrypted token authentication: token is decrypted with private key to extract ServiceNow email ID.
- The extracted email is validated against the `SERVICENOW_ALLOWED_EMAIL` environment variable.
- If the email does not match, the request is rejected with HTTP 401.
- No role-based access control — authentication is purely email-based validation.

### 2.5 Project Sync — `POST /api/v1/sync/servicenow/projects`

#### 2.5.1 Description

Receives project data from ServiceNow and inserts new project records. The `sn_project_id` field serves as the unique identifier — if a project with the same `sn_project_id` already exists, the record is skipped (no duplicate created, no update performed). This is insert-only behavior.

#### 2.5.2 Request Payload

**Root object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `projects` | array | Yes | List of project objects to sync (must be non-empty) |

**Each project object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sn_project_id` | string | Yes | ServiceNow project identifier (unique key for deduplication) |
| `project_name` | string | Yes | Name of the project |
| `onboarded_date` | date (ISO 8601) | Yes | Date when the project was onboarded (YYYY-MM-DD) |
| `project_type` | string | Yes | Type/category of the project (e.g., "Infrastructure") |
| `is_applicable` | boolean | No | Whether the project is applicable for DevSecOps (default: true) |
| `client` | string | No | Client name associated with the project |
| `approver` | string | No | Name or email of the approver for the project |

#### 2.5.3 Processing Logic

1. Authenticate: decrypt token, extract ServiceNow email, validate against `SERVICENOW_ALLOWED_EMAIL`. Return 401 if mismatch.
2. Validate payload: must contain a non-empty `projects` array with required fields and correct data types.
3. For each project in the array:
   a. Look up by `sn_project_id` in the `projects` table.
   b. **If found** → Skip (project already exists, no duplicate created).
   c. **If not found** → Create new project with:
      - Generated UUID as `project_id`
      - `status_id` set to "Inactive" status (resolved from `statuses` table by name)
      - `is_active` set to 1
      - `created_at` set to current timestamp
      - `created_by` set to authenticated service account identifier
4. Return HTTP 200 success response.

#### 2.5.4 Success Response

```json
{
  "status_code": 200,
  "status": "success",
  "message": "Sync completed successfully"
}
```

#### 2.5.5 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid or missing required fields (e.g., missing `sn_project_id`, invalid date format) |
| 401 | Missing/invalid token or email does not match allowed ServiceNow account |
| 500 | Unexpected server error (logged to `error_log` table) |

#### 2.5.6 Key Behaviors

- Insert-only: existing projects are skipped, never updated.
- New projects default to "Inactive" status.
- Endpoint is idempotent — calling multiple times with same data produces same result.

### 2.6 DevSecOps Tickets Sync — `POST /api/v1/sync/servicenow/devsecops-tickets`

#### 2.6.1 Description

Receives a batch of DevSecOps ticket data from ServiceNow and performs insert operations in the `devsecops_tickets` and `repositories` tables. Each ticket is always created (one project can have multiple tickets). Supports partial success — valid tickets are processed while invalid ones are logged and skipped.

#### 2.6.2 Request Payload

**Root object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tickets` | array | Yes | List of ticket objects to sync (must be non-empty) |

**Each ticket object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sn_project_id` | string | Yes | ServiceNow project identifier (used for project resolution) |
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

#### 2.6.3 Processing Logic

1. Authenticate: decrypt token, extract ServiceNow email, validate against `SERVICENOW_ALLOWED_EMAIL`. Return 401 if mismatch.
2. Validate root payload: must contain a non-empty `tickets` array.
3. For each ticket in the array:
   a. **Resolve specialization**: Query `specializations` table where `specialization_name` matches (case-insensitive) and `is_active = 1`. If not found → skip ticket, log WARNING.
   b. **Resolve project (4-step fallback)**:
      1. Match by `sn_project_id` → Query `projects` where `sn_project_id` matches and `is_active = 1`.
      2. Match by `project_name` → Query `projects` where `project_name` matches and `is_active = 1`.
      3. Match by `client` → Query `projects` where `client` matches and `is_active = 1`.
      4. Use default project → Map to pre-existing default project record.
   c. **Insert ticket**: Create new `devsecops_tickets` record with generated UUID, resolved `specialization_id` and `project_id`, `is_active = 1`.
   d. **Process repositories**: For each repository:
      - Look up by `repo_name` + `ticket_id` combination.
      - If found → Skip (already exists).
      - If not found → Create new repository record with generated UUID, linked via `ticket_id`.
4. Return HTTP 200 success response.

#### 2.6.4 Partial Success Behavior

- Valid tickets are processed; invalid ones (unknown specialization) are skipped and logged at WARNING level.
- Response returns HTTP 200 with "Sync completed successfully" as long as processing completes.
- If ALL tickets fail, response still returns HTTP 200 but failures are logged.
- Failed tickets are logged with sufficient detail for debugging.

#### 2.6.5 Success Response

```json
{
  "status_code": 200,
  "status": "success",
  "message": "Sync completed successfully"
}
```

#### 2.6.6 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid payload structure (missing `tickets` array, empty array, or missing required fields) |
| 401 | Missing/invalid token or email does not match allowed ServiceNow account |
| 500 | Unexpected server error (logged to `error_log` table) |

### 2.7 Payload Validation

- Pydantic v2 models validate all incoming payloads.
- Validation errors return HTTP 400 before any database operations.
- Error response identifies which field failed and why.
- Error format follows standardized `BaseResponse` schema.

### 2.8 Error Logging

- All unhandled exceptions are logged to the `error_log` database table.
- Error entries include: `error_function`, `error_file`, `error_message`, `stack_trace`.
- `created_by` = "servicenow_sync_service".
- Partial failures (individual ticket validation) are logged at application WARNING level, not in `error_log`.
- HTTP 500 responses are always accompanied by an `error_log` entry.

### 2.9 Data Sources

| Table | Role |
|-------|------|
| `projects` | Project records with `sn_project_id` for deduplication |
| `devsecops_tickets` | Tickets linked to projects and specializations |
| `repositories` | Repositories linked to tickets via `ticket_id` |
| `specializations` | Read-only reference for resolving specialization names |
| `statuses` | Read-only reference for default "Inactive" status assignment |
| `error_log` | Persists unhandled exceptions |

### 2.10 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `TOKEN_PRIVATE_KEY` | Private key for token decryption (PEM format or path) | Yes |
| `SERVICENOW_ALLOWED_EMAIL` | Allowed ServiceNow service account email for validation | Yes |

---

## 3. Report Generation & Email Delivery (ZDAD-60)

### 3.1 Description

The Email Notification Service automates the generation and delivery of PDF reports for the DevSecOps Jira Dashboard. The service exposes a `POST /api/v1/reports/generate` endpoint that is triggered by an external daily cron job with no request body. Upon invocation, the service internally fetches all active specializations and evaluates each one's configured report frequencies from the `settings` table. It checks the `email_history` table to determine whether a report has already been sent within the current frequency window. If a report is due, the service generates a PDF, uploads it to AWS S3, sends the email via Microsoft Graph API, and records the delivery status.

### 3.2 How Report Generation Works

```
┌───────────┐       ┌──────────────────┐       ┌─────────────────┐       ┌─────────────┐       ┌──────────────────┐
│ External  │──────▶│ POST /reports/   │──────▶│ PDF Generation  │──────▶│ Upload to   │──────▶│ Microsoft Graph  │
│ Cron Job  │       │ generate         │       │ (WeasyPrint)    │       │ AWS S3      │       │ API (send email) │
└───────────┘       └──────────────────┘       └─────────────────┘       └─────────────┘       └──────────────────┘
                          │                                                                           │
                          │ Internal:                                                                  │
                          │ • Iterate specializations                                                  ▼
                          │ • Evaluate frequency                                             ┌─────────────────┐
                          │ • Fetch template & data                                          │ Track in        │
                          │ • Fetch recipients                                               │ email_history   │
                          └──────────────────────────────────────────────────────────────────▶│ & cron_jobs     │
                                                                                             └─────────────────┘
```

1. External daily cron job calls `POST /api/v1/reports/generate` (no request body, no authentication).
2. Service fetches all active specializations.
3. For each specialization, evaluates frequency settings against `email_history`.
4. If a report is due: fetches template, retrieves data, processes HTML with BeautifulSoup, generates PDF with WeasyPrint.
5. Uploads PDF to AWS S3, generates pre-signed URL.
6. Sends email to all active recipients via Microsoft Graph API.
7. Records delivery status in `email_history` and cron execution in `cron_jobs`.

### 3.3 Endpoint

`POST /api/v1/reports/generate`

- **No request body required** — the cron simply calls it.
- **No authentication required** — triggered by external cron.
- The service internally iterates over all active specializations.

### 3.4 Report Types

| Type | Setting Field | Description |
|------|---------------|-------------|
| Summary report | `settings.email_digest` | KPI metrics, status distribution, project health overview |
| At-risk | `settings.at_risk_alert` | Projects exceeding `at_risk_threshold` days since onboarding |

Report settings are controlled at the specialization/domain level, NOT per user. Each specialization maintains its own independent configuration.

### 3.5 Frequency Evaluation Logic

The service evaluates whether a report should be sent based on the configured frequency:

#### Frequency Options:
- `daily` — Send every day (check if sent in the last 24 hours)
- `weekly` — Send once per week (check if sent in the last 7 days)
- `bi-weekly` — Send once every two weeks (check if sent in the last 14 days)
- `monthly` — Send once per month (check if sent in the last 30 days)
- `not_required` — Do not send this report type

#### Evaluation Steps:
1. Read `settings` record for the specialization to get `email_digest` and `at_risk_alert` frequency values.
2. For each report type:
   a. If frequency is `not_required` → skip.
   b. Query `email_history` for most recent record where `email_type` matches, `setting_id` matches, and `email_status = "sent"`.
   c. Calculate if time elapsed since `last_synced` exceeds the frequency window.
   d. If window elapsed (or no history exists) → trigger report generation.
   e. If already sent within window → skip, log at DEBUG level.

### 3.6 Processing Logic (Per Specialization)

1. Create `cron_jobs` record with `type = "email"`, `sync_status = "pending"`.
2. Evaluate frequency for both report types (Summary and At-risk).
3. For each report type that is due:
   a. Fetch email template from `email_templates` where `template_name` matches report type.
   b. Fetch report data:
      - **Summary report**: KPI metrics from `kpi_history` for the specialization.
      - **At-risk**: Projects where days since onboarding exceeds threshold.
   c. Fetch active recipients from `email_recipient` where `specialization_id` matches and `is_active = 1`.
   d. If no active recipients → skip specialization, log WARNING.
   e. Parse HTML with BeautifulSoup, inject dynamic data into placeholders.
   f. Convert populated HTML to PDF with WeasyPrint (in-memory, no temp files).
   g. Upload PDF to AWS S3 with path: `reports/{specialization_name}/{report_type}/{YYYY}/{MM}/{filename}.pdf`.
   h. Generate pre-signed URL (default expiry: 7 days).
   i. Send email to each recipient via Microsoft Graph API (skip-and-continue on individual failures).
   j. Record in `email_history`: status "sent" if at least one email succeeded, "failed" if all failed.
4. Update `cron_jobs` record: `sync_status = "success"` or `"fail"`.

### 3.7 Email Delivery

- **Provider**: Microsoft Graph API
- **From**: Configured sender email (`GRAPH_SENDER_EMAIL`)
- **To**: Each active recipient's `alert_recipient` email
- **Subject**: `[DevSecOps Dashboard] {Report Type} Report - {Specialization Name} - {Date}`
- **Body**: HTML containing report type, specialization name, generation date, and download link
- **Pattern**: Skip-and-continue — individual recipient failures do not block others
- **Status determination**:
  - At least one email sent successfully → status = "sent"
  - All emails failed → status = "failed"

### 3.8 PDF Generation & Storage

- HTML template processed with BeautifulSoup for data injection.
- PDF generated in-memory using WeasyPrint (no temporary files written to disk).
- Uploaded to AWS S3 bucket (`S3_BUCKET_NAME` env var).
- File path: `reports/{specialization_name}/{report_type}/{YYYY}/{MM}/{filename}.pdf`
- Filename: `{report_type}_{specialization_name}_{YYYYMMDD_HHmmss}.pdf`
- Pre-signed URL generated with configurable expiration (default: 7 days via `S3_URL_EXPIRY_DAYS`).

### 3.9 Email History Tracking

After each report generation attempt, a record is created in `email_history`:

| Field | Value |
|-------|-------|
| `email_history_id` | Auto-generated UUID |
| `setting_id` | FK to the `settings` record for the specialization |
| `email_status` | "sent" (at least one recipient succeeded) or "failed" (all failed) |
| `email_type` | Report type: "At-risk" or "Summary report" |
| `report_url` | URL of uploaded PDF (null if generation failed before upload) |
| `last_synced` | Timestamp of the generation attempt |
| `created_at` | Current timestamp |
| `created_by` | "report_service" |
| `is_active` | 1 |

History records are never deleted — they serve as a permanent audit trail and are used by frequency evaluation logic.

### 3.10 Cron Job Status Tracking

Each cron execution is tracked in the `cron_jobs` table:

| Field | Value |
|-------|-------|
| `cron_id` | Auto-generated UUID |
| `specialization_id` | The specialization being processed |
| `type` | "email" (distinguishes from "azure" sync cron jobs) |
| `sync_status` | "pending" → "success" or "pending" → "fail" |
| `created_at` | Timestamp when execution started |
| `created_by` | "report_service" |

### 3.11 Success Response

```json
{
  "status_code": 200,
  "status": "success",
  "message": "Email sent successfully"
}
```

### 3.12 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 500 | Unexpected server error (PDF generation failure, email delivery failure, storage upload failure) |

### 3.13 Error Logging

- All unhandled exceptions are logged to the `error_log` database table.
- Error entries include: `error_function`, `error_file`, `error_message`, `stack_trace`.
- `created_by` = "report_service".
- Individual recipient email failures are logged at application WARNING level, not in `error_log`.
- HTTP 500 responses are always accompanied by an `error_log` entry.

### 3.14 Data Sources

| Table | Role |
|-------|------|
| `email_templates` | HTML templates for report generation (selected by `template_name`) |
| `email_recipient` | Recipient email addresses per specialization (`is_active = 1`) |
| `email_history` | Tracks report generation attempts, delivery status, and frequency evaluation |
| `settings` | Configuration for report frequency (`email_digest`, `at_risk_alert`) and `at_risk_threshold` |
| `specializations` | Iteration list for active specializations |
| `kpi_history` | Source data for Summary reports |
| `projects` | Source data for At-risk reports |
| `cron_jobs` | Tracks scheduled report generation executions |
| `error_log` | Persists unhandled exceptions |

### 3.15 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `S3_BUCKET_NAME` | AWS S3 bucket name for PDF uploads | Yes |
| `S3_URL_EXPIRY_DAYS` | Pre-signed URL expiration in days (default: 7) | No |
| `AWS_REGION` | AWS region for S3 | Yes |
| `GRAPH_CLIENT_ID` | Microsoft Graph API client ID | Yes |
| `GRAPH_CLIENT_SECRET` | Microsoft Graph API client secret | Yes |
| `GRAPH_TENANT_ID` | Microsoft Graph API tenant ID | Yes |
| `GRAPH_SENDER_EMAIL` | Sender email for Graph API | Yes |

---

## 4. Settings Management (ZDAD-34)

### 4.1 Description

The Settings module provides CRUD operations for managing specialization-level settings including report frequency configuration and email recipient management.

### 4.2 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/settings/{specializationId}` | GET | Get settings for a specialization |
| `/api/v1/settings/manage` | PUT | Update settings for a specialization |

### 4.3 Get Settings — `GET /api/v1/settings/{specializationId}`

Returns the settings record for the given specialization, including specialization name and email recipients.

#### Response includes:
- `setting_id` — UUID of the settings record
- `specialization_id` — UUID of the specialization
- `specialization_name` — Name of the specialization
- `at_risk_threshold` — Days threshold for at-risk determination
- `email_digest` — Frequency for summary reports (daily/weekly/bi-weekly/monthly/not_required)
- `at_risk_alert` — Frequency for at-risk reports (daily/weekly/bi-weekly/monthly/not_required)
- `email_recipients[]` — List of configured email recipients

#### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 404 | Specialization not found |
| 500 | Server error |

### 4.4 Update Settings — `PUT /api/v1/settings/manage`

Partially updates the settings record. Only send the fields that changed. Email recipients are managed via action-based approach (add/remove).

#### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Validation error |
| 404 | Specialization not found |
| 500 | Server error |

---

## 5. ADO Sync (ZDAD-34)

### 5.1 Description

Triggers a sync of data from Azure DevOps. Populates `kpi_history` and updates repository pipeline data.

### 5.2 Endpoint

`POST /api/v1/sync/ado`

### 5.3 Request Payload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `specialization_id` | string (UUID) | No | UUID of the specialization to sync. Null or omitted syncs all. |

### 5.4 Response

```json
{
  "status_code": 200,
  "status": "success",
  "message": "Sync completed successfully"
}
```

### 5.5 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 500 | Server error |

---

## 6. Projects Module

### 6.1 Description

The Projects module provides paginated project listing with filtering, sorting, and project actions (mark as not applicable, mark as complete).

### 6.2 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/projects` | GET | Get paginated projects list with filters |
| `/api/v1/projects/action` | POST | Perform action on a project |

### 6.3 Projects List — `GET /api/v1/projects`

#### Query Parameters:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `period` | string (enum) | No | `last_month` | Time period filter |
| `search` | string | No | — | Free text search on project name |
| `status` | string (CSV) | No | All | Comma-separated status IDs |
| `client` | string (CSV) | No | All | Comma-separated client IDs |
| `specialization` | string (CSV) | No | All | Comma-separated specialization IDs |
| `offset` | integer | No | 0 | Pagination offset |
| `limit` | integer | No | 10 | Items per page |
| `sort_by` | string (enum) | No | `project` | Sort field: `project` or `onboarded_date` |
| `sort_order` | string (enum) | No | `asc` | Sort direction: `asc` or `desc` |

### 6.4 Project Action — `POST /api/v1/projects/action`

Supports `multipart/form-data` with actions:
- `mark_not_applicable` — Raises a Jira ticket
- `mark_complete` — Updates project status to Completed

---

## 7. Repository Detail

### 7.1 Description

Returns comprehensive detail information for a specific repository including header metadata, pipeline metrics, adoption timeline, pipeline activity, commits, pull requests, security scan findings, and build artifacts.

### 7.2 Endpoint

`GET /api/v1/repositories/{repository_id}`

### 7.3 Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_id` | string (UUID) | Yes | UUID of the repository |

### 7.4 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid UUID format |
| 401 | Unauthorized |
| 404 | Repository not found |
| 500 | Server error |

---

## 8. Cross-Cutting Concerns

### 8.1 Response Format

All endpoints follow the standardized `BaseResponse` schema:

```json
{
  "status_code": 200,
  "status": "success",
  "message": "Description of result",
  "data": {}
}
```

Status values: `success`, `failed`, `error`

### 8.2 Health & Readiness Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Liveness probe — returns 200 if application is running |
| `/ready` | Readiness probe — checks database connectivity and dependencies |

### 8.3 Architecture

Layered architecture: Routes → Middleware → Services → Repositories → Database

### 8.4 Technology Stack

- **Framework**: FastAPI (Python)
- **ORM**: SQLAlchemy
- **Validation**: Pydantic v2
- **Database**: PostgreSQL
- **PDF Generation**: WeasyPrint + BeautifulSoup
- **Cloud Storage**: AWS S3
- **Email Provider**: Microsoft Graph API
- **Logging**: Structured JSON with trace_id
