# DevSecOps Jira Dashboard - Requirements

## 1. Overview API

### 1.1 Description

The Overview API provides dashboard-level KPI metrics and status distribution for all onboarded projects. It serves as the landing page data source, giving stakeholders a quick snapshot of project health across the organization.

### 1.2 Endpoint

`GET /api/v1/overview`

### 1.3 Filters

| Filter | Parameter | Type | Required | Default | Description |
|--------|-----------|------|----------|---------|-------------|
| Period | `period` | string (enum) | No | `last_month` | Time period for metric calculations |
| Specialization | `specialization` | string (CSV) | No | All | Comma-separated specialization IDs to filter by |

#### Period Options
- `last_3_months` — Last 90 days
- `last_6_months` — Last 180 days

#### Specialization Filter

- Accepts a comma-separated list of specialization IDs (e.g., `devsecops,devops`)
- When empty or omitted, returns metrics across all specializations
- Valid IDs are retrieved from `GET /api/v1/specializations`

### 1.4 Response — KPI Metrics

The API returns the following KPI cards:

| KPI | Field | Description |
|-----|-------|-------------|
| Total Projects | `metrics.totalProjects` | Total number of projects in the system |
| Completed | `metrics.completed` | Projects that are fully onboarded |
| Active | `metrics.active` | Projects with pipeline activity within the last 10 days |
| Inactive | `metrics.inactive` | Projects with no pipeline activity for 10+ days |
| At Risk | `metrics.atRisk` | Projects with overdue onboarding |
| Not Applicable | `metrics.notApplicable` | Projects marked as exceptions |

Each KPI includes:

- `count` — Current value for the selected period
- `trend` — Direction compared to previous period (`increase`, `decrease`, `flat`, or `null`)
- `change` — Numeric difference from the previous period

### 1.5 Response — Status Distribution

The API also returns a status distribution breakdown:

- `statusDistribution.total` — Total project count
- `statusDistribution.breakdown[]` — Array of status groups, each with:
  - `status` — Status name (Completed, Active, Inactive, At Risk, Not Applicable)
  - `count` — Number of projects in that status
  - `percentage` — Percentage of total projects

### 1.6 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid query parameter value (e.g., unsupported period) |
| 401 | Missing or invalid authentication token |
| 500 | Unexpected server error |

### 1.7 Authentication

- Requires a valid JWT Bearer token in the `Authorization` header
- Returns 401 if the token is missing, expired, or invalid

---

## 2. ServiceNow Sync

### 2.1 Description

The ServiceNow Sync module handles the ingestion of project and DevSecOps ticket data from ServiceNow into the dashboard database. ServiceNow acts as the source of truth for project onboarding and ticket creation. The sync is initiated by ServiceNow itself — a script on the ServiceNow side calls our API endpoints to push data into the system.

### 2.2 How the Sync Works

```
┌──────────────┐         ┌──────────────────────┐         ┌────────────┐
│  ServiceNow  │──POST──▶│  DevSecOps Dashboard │──────▶  │  Database  │
│   (Script)   │         │       API            │         │  (Upsert)  │
└──────────────┘         └──────────────────────┘         └────────────┘
```

1. A scheduled or event-driven script in ServiceNow triggers the sync.
2. The script sends an HTTP POST request to the dashboard API with project or ticket data.
3. The API authenticates the request using a dedicated ServiceNow service account.
4. Upon successful authentication, the API processes the payload and upserts the data into the database.
5. The API returns a success or error response back to ServiceNow.

### 2.3 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sync/servicenow/projects` | POST | Sync a project from ServiceNow |
| `/api/v1/sync/servicenow/devsecops-tickets` | POST | Sync DevSecOps tickets from ServiceNow |

### 2.4 Authentication

- ServiceNow authenticates using a dedicated service account with a JWT Bearer token.
- The token is issued to a specific ServiceNow integration user (e.g., `svc_servicenow@zeb.co`).
- The API validates the token and checks that the caller has the `servicenow_sync` role/permission.
- If the token is missing, expired, or the user does not have the required permission, the API returns a `401 Unauthorized` response.

### 2.5 Project Sync — `POST /api/v1/sync/servicenow/projects`

#### 2.5.1 Description

Receives project data from ServiceNow and creates or updates a project record in the database. The `sn_project_id` field is used as the unique identifier to determine whether to insert a new project or update an existing one.

#### 2.5.2 Request Payload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sn_project_id` | string | Yes | ServiceNow project identifier (unique key for upsert) |
| `project_name` | string | Yes | Name of the project |
| `onboarded_date` | date | Yes | Date when the project was onboarded |
| `project_type` | string | Yes | Type/category of the project (e.g., Infrastructure) |
| `is_applicable` | boolean | No | Whether the project is applicable for DevSecOps (default: true) |
| `client` | string | No | Client name associated with the project |
| `approver` | string | No | Name or email of the approver for the project |

#### 2.5.3 Processing Logic

1. Validate the request payload (required fields, data types).
2. Look up the project by `sn_project_id`.
   - If found → update the existing record with the new values.
   - If not found → create a new project record with a generated UUID and default status (Active).
3. Set `created_by` / `modified_by` to the authenticated service account.
4. Return success response.

#### 2.5.4 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid or missing required fields |
| 401 | Missing/invalid token or insufficient permissions |
| 409 | Sync already in progress (concurrent request protection) |
| 500 | Unexpected server error |

### 2.6 DevSecOps Tickets Sync — `POST /api/v1/sync/servicenow/devsecops-tickets`

#### 2.6.1 Description

Receives DevSecOps ticket data from ServiceNow and inserts or updates records in the `devsecops_tickets` table. Each ticket is linked to a project (via `sn_project_id`) and a specialization (via `specialization_name`). Repositories associated with the ticket are also created or updated.

#### 2.6.2 Request Payload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tickets` | array | Yes | List of ticket objects to sync |

**Each ticket object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sn_project_id` | string | Yes | ServiceNow project identifier (FK to projects) |
| `project_name` | string | Yes | Name of the project the ticket belongs to |
| `client` | string | No | Client name associated with the ticket |
| `specialization_name` | string | Yes | Specialization name (must match an existing specialization) |
| `repositories` | array | No | List of repositories associated with the ticket |
| `requested_by` | string | No | Name or email of the person who raised the request |
| `approver` | string | No | Name or email of the approver for the ticket |
| `requested_at` | datetime | No | Timestamp when the ticket was requested in ServiceNow |

**Each repository object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repo_name` | string | Yes | Repository name |
| `ado_repo_id` | string | No | Azure DevOps repository identifier |

#### 2.6.3 Processing Logic

1. Validate the request payload.
2. For each ticket in the array:
   a. Resolve `specialization_name` to a `specialization_id` (return 400 if not found).
   b. Resolve `sn_project_id` to a `project_id` (return 400 if project does not exist).
   c. Upsert the ticket record in `devsecops_tickets`.
   d. For each repository in the ticket, upsert into the `repositories` table linked to the ticket.
3. Set `created_by` / `modified_by` to the authenticated service account.
4. Return success response.

#### 2.6.4 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid payload, unknown specialization, or project not found |
| 401 | Missing/invalid token or insufficient permissions |
| 409 | Sync already in progress (concurrent request protection) |
| 500 | Unexpected server error |

### 2.7 Security Considerations

- The ServiceNow service account must be provisioned with minimal permissions (only sync-related endpoints).
- All sync requests are logged for audit purposes (caller identity, timestamp, payload summary).
- Rate limiting should be applied to prevent abuse or accidental flooding from misconfigured scripts.
- The API should validate that the authenticated user belongs to the ServiceNow integration role before processing any sync request.

---

## 3. Report Generation & Email Delivery

### 3.1 Description

The Report Generation module generates PDF reports for a given specialization and delivers them via email to configured recipients. Reports are triggered either by a cron job (scheduled) or manually via the API. The system fetches an HTML email template from the database, populates it with report data, converts it to a PDF using BeautifulSoup for HTML processing, uploads the PDF to cloud storage (Azure Blob Storage / AWS S3), and sends the email with the report link via Amazon SES. The report generation history is tracked in the `email_history` table for audit and status tracking.

### 3.2 How Report Generation Works

```
┌───────────┐       ┌──────────────────┐       ┌─────────────────┐       ┌─────────────┐       ┌─────────────┐
│ Cron Job  │──────▶│ GenerateReport   │──────▶│ PDF Generation  │──────▶│ Upload to   │──────▶│ Amazon SES  │
│ (trigger) │       │ API              │       │ (BeautifulSoup) │       │ S3/Blob     │       │ (send email)│
└───────────┘       └──────────────────┘       └─────────────────┘       └─────────────┘       └─────────────┘
                          │                                                                           │
                          │ Fetch:                                                                    │
                          │ • Email template                                                          ▼
                          │ • Report data                                                    ┌─────────────────┐
                          │ • Recipient emails                                               │ Update          │
                          └──────────────────────────────────────────────────────────────────▶│ email_history   │
                                                                                             └─────────────────┘
```

1. A cron job (or manual API call) triggers `POST /api/v1/reports/generate` with the report type and specialization.
2. The API fetches the email template from the `email_templates` table.
3. The API fetches the report data (projects, KPIs, status distribution) relevant to the specialization.
4. The API fetches the recipient email addresses from the `email_recipient` table for the given specialization.
5. The HTML template is populated with the report data using BeautifulSoup for HTML processing.
6. The populated HTML is converted to a PDF document.
7. The PDF is uploaded to cloud storage (S3 or Azure Blob Storage) and a URL is generated.
8. The email is sent via Amazon SES to all configured recipients, with the report URL or PDF attachment.
9. On success, the `email_history` table is updated with the report status, URL, and timestamp.
10. On failure, the error is logged and the `email_history` record is updated with a failed status.

### 3.3 Endpoint

`POST /api/v1/reports/generate`

### 3.4 Request Payload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string (enum) | Yes | Type of report to generate: `At-risk` or `Summary report` |
| `specialization_id` | string (UUID) | Yes | UUID of the specialization to generate the report for |

#### Report Types

- **At-risk** — Generates a report listing all projects in "At Risk" status for the given specialization, including project details, overdue duration, and risk indicators.
- **Summary report** — Generates a comprehensive summary report with KPI metrics, status distribution, and project health overview for the given specialization.

### 3.5 Processing Logic

1. Validate the request payload (required fields, valid enum value, valid UUID format).
2. Resolve `specialization_id` — verify it exists in the `specializations` table and is active. Return 404 if not found.
3. Fetch the email template from `email_templates` table based on the report type (`template_name` matches the report type).
4. Fetch report data based on the report type:
   - **At-risk**: Query projects with "At Risk" status linked to the specialization (via `devsecops_tickets` → `specialization_id`).
   - **Summary report**: Query KPI metrics from `kpi_history` and status distribution from `projects` for the specialization.
5. Fetch recipient email addresses from `email_recipient` table where `specialization_id` matches and `is_active = 1`.
6. If no recipients are configured, return 400 with a descriptive error message.
7. Populate the HTML template with the fetched report data (inject values into template placeholders).
8. Convert the populated HTML to PDF using BeautifulSoup for HTML parsing and a PDF generation library.
9. Upload the generated PDF to cloud storage (S3 or Azure Blob Storage).
10. Send the email via Amazon SES to all recipients with the report URL.
11. Create/update a record in `email_history` with:
    - `setting_id` — Resolved from the `settings` table for the specialization.
    - `report_frequency` — Based on the cron schedule or "manual" for API-triggered reports.
    - `email_status` — "sent" on success, "failed" on error.
    - `email_type` — The report type ("At-risk" or "Summary report").
    - `report_url` — URL of the uploaded PDF in cloud storage.
    - `last_synced` — Current timestamp.
12. Return success or error response.

### 3.6 Response

#### Success Response

```json
{
  "status_code": 200,
  "status": "success",
  "message": "Email sent successfully"
}
```

### 3.7 Error Responses

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid request body (missing fields, invalid report type, no recipients configured) |
| 401 | Missing or invalid authentication token |
| 404 | Specialization not found or inactive |
| 500 | Unexpected server error (PDF generation failure, email delivery failure, storage upload failure) |

### 3.8 Email Recipients

- Recipients are fetched from the `email_recipient` table filtered by `specialization_id` and `is_active = 1`.
- Each recipient record contains an `alert_recipient` field with the email address.
- Recipients are configured via the Settings management endpoints (out of scope for this module).
- The email is sent to all active recipients for the given specialization — there is no per-report-type recipient filtering.

### 3.9 Email Templates

- Templates are stored in the `email_templates` table with `template_name` and `template_content` (HTML).
- The `template_content` contains HTML with placeholders for dynamic data injection.
- BeautifulSoup is used to parse the HTML template and inject report data into the appropriate elements.
- Template selection is based on the report type:
  - `At-risk` → Template named "At-risk" or similar identifier.
  - `Summary report` → Template named "Summary report" or similar identifier.

### 3.10 PDF Generation & Storage

- The populated HTML template is converted to a PDF document.
- The PDF is uploaded to cloud storage with a unique filename (e.g., `{report_type}_{specialization_name}_{timestamp}.pdf`).
- The storage URL is persisted in the `email_history.report_url` field for future reference.
- The URL can be included in the email body for recipients to download the report.

### 3.11 Email History Tracking

After each report generation attempt (success or failure), a record is created in the `email_history` table:

| Field | Value |
|-------|-------|
| `email_history_id` | Auto-generated UUID |
| `setting_id` | FK to the settings record for the specialization |
| `report_frequency` | Cron schedule identifier or "manual" |
| `email_status` | "sent" (success) or "failed" (error) |
| `email_type` | Report type ("At-risk" or "Summary report") |
| `report_url` | URL of the uploaded PDF (null if generation failed) |
| `last_synced` | Timestamp of the generation attempt |
| `created_at` | Current timestamp |
| `created_by` | System identifier (e.g., "report_service") |

### 3.12 Cron Job Integration

- The cron job is tracked in the `cron_jobs` table with `type = "email"`.
- When the cron triggers, it calls `POST /api/v1/reports/generate` internally for each specialization that has email digest or at-risk alert configured in the `settings` table.
- The `settings.email_digest` field determines the frequency for summary reports.
- The `settings.at_risk_alert` field determines the frequency for at-risk reports.
- After execution, the `cron_jobs` record is updated with `sync_status` ("success" or "fail").

### 3.13 Authentication

- Requires a valid JWT Bearer token in the `Authorization` header.
- Returns 401 if the token is missing, expired, or invalid.
- No additional role check is required (any authenticated user can trigger report generation).

### 3.14 Database Tables Involved

| Table | Role |
|-------|------|
| `email_templates` | Source of HTML templates for report generation |
| `email_recipient` | Source of recipient email addresses per specialization |
| `email_history` | Tracks report generation attempts and delivery status |
| `settings` | Configuration for report frequency and alert thresholds |
| `specializations` | Validates the target specialization |
| `kpi_history` | Source data for summary reports |
| `projects` | Source data for at-risk reports and status distribution |
| `cron_jobs` | Tracks scheduled report generation executions |
| `error_log` | Persists unhandled exceptions during report generation |
