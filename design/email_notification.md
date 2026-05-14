## SOLDEF-ZDAD-60 - Implement Email Notification Service

### <u>Project Details</u>
- **Project ID:** ZDAD  
- **Project Name:** DevSecOps Jira Dashboard  

### <u>Story Details</u>
- **Story ID:** ZDAD-60  
- **Story Name:** Implement Email Notification Service  
- **Story Description:**  
  When there are at-risk projects or pipeline failures, stakeholders need to receive automated email notifications so that they can stay informed and take timely action. Daily digests and weekly reports are available — stakeholders want to receive automated email notifications so that users can stay informed and take timely action.
- **Scope:**  
  This issue involves implementing an email notification service. The service will support various business scenarios and provide a reliable API for integration by other components. It will handle message composition, recipient management, and interaction with the email provider, ensuring traceability and basic error handling.
- **Acceptance Criteria:**
  - Generate Story Definition (SD) for email notification scenarios.
  - Confirm functional and non-functional requirements.
  - Design and implement the Email Service API with: request/response models, validation, and integration with the email delivery mechanism.
  - Create and execute unit tests for email service components.
  - Fix defects identified during unit testing.
  - Conduct developer pre-verification of end-to-end notification flows.
  - Perform System Integration Testing (SIT 1 and SIT 2) for email notification scenarios.
  - Ensure regression testing of impacted components.
  - Review code and implementation for: adherence to coding standards, logging, and configuration management.

### <u> Table of Contents </u>
- [Section 1: Functional Requirements](#Section-1:-Functional-Requirements)
    - [1.1 Overview](#1.1-Overview)
    - [1.2 Requirement Details](#1.2-Requirement-Details)
        - [1.2.1 ZDAD-60-FR01: Report Generation Endpoint](#1.2.1-ZDAD-60-FR01:-Report-Generation-Endpoint)
        - [1.2.2 ZDAD-60-FR02: Cron Job Frequency Evaluation](#1.2.2-ZDAD-60-FR02:-Cron-Job-Frequency-Evaluation)
        - [1.2.3 ZDAD-60-FR03: HTML Template Processing and PDF Generation](#1.2.3-ZDAD-60-FR03:-HTML-Template-Processing-and-PDF-Generation)
        - [1.2.4 ZDAD-60-FR04: Cloud Storage Upload](#1.2.4-ZDAD-60-FR04:-Cloud-Storage-Upload)
        - [1.2.5 ZDAD-60-FR05: Email Delivery](#1.2.5-ZDAD-60-FR05:-Email-Delivery)
        - [1.2.6 ZDAD-60-FR06: Email History Tracking](#1.2.6-ZDAD-60-FR06:-Email-History-Tracking)
        - [1.2.7 ZDAD-60-FR07: Cron Job Status Tracking](#1.2.7-ZDAD-60-FR07:-Cron-Job-Status-Tracking)
        - [1.2.8 ZDAD-60-FR08: Error Logging](#1.2.8-ZDAD-60-FR08:-Error-Logging)
    - [1.3 Database Schema](#1.3-Database-Schema)
    - [1.4 Project Artifacts](#1.4-Project-Artifacts)
    - [1.5 Environment Variables](#1.5-Environment-Variables)
- [Section 2: In Scope and Out Scope](#Section-2:-In-Scope-and-Out-Scope)
    - [2.1 In Scope Details](#2.1-In-Scope-Details)
    - [2.2 Out Scope Details](#2.2-Out-Scope-Details)
- [Section 3: Solution Diagrams](#Section-3:-Solution-Diagrams)

### <u> Section 1: Functional Requirements </u>

#### <u> 1.1 Overview </u>

The Email Notification Service automates the generation and delivery of PDF reports for the DevSecOps Jira Dashboard. The service exposes a `POST /api/v1/reports/generate` endpoint that is triggered by an external daily cron job with no request body. Upon invocation, the service internally fetches all active specializations and evaluates each one's configured report frequencies (`email_digest` for Summary reports and `at_risk_alert` for At-risk reports) from the `settings` table. It checks the `email_history` table to determine whether a report has already been sent within the current frequency window (e.g., weekly, monthly). If a report is due, the service fetches the corresponding HTML email template from the `email_templates` table, retrieves the relevant report data (KPI metrics for Summary reports or at-risk project details for At-risk reports), processes the HTML using BeautifulSoup to inject dynamic data, converts the populated HTML to a PDF document using WeasyPrint, uploads the PDF to AWS S3, sends the email with the report link to all active recipients configured for that specialization via Microsoft Graph API, and finally records the delivery status in the `email_history` table. The cron job execution status is tracked in the `cron_jobs` table. All errors are logged to the `error_log` table for traceability.

#### <u> 1.2 Requirement Details </u>

- **ZDAD-60-FR01: Report Generation Endpoint**
- **ZDAD-60-FR02: Cron Job Frequency Evaluation**
- **ZDAD-60-FR03: HTML Template Processing and PDF Generation**
- **ZDAD-60-FR04: Cloud Storage Upload**
- **ZDAD-60-FR05: Email Delivery**
- **ZDAD-60-FR06: Email History Tracking**
- **ZDAD-60-FR07: Cron Job Status Tracking**
- **ZDAD-60-FR08: Error Logging**

##### <u> 1.2.1 ZDAD-60-FR01: Report Generation Endpoint </u>

##### Description:
The system shall expose a `POST /api/v1/reports/generate` endpoint that triggers report generation and email delivery for all active specializations. This endpoint requires no request body — the cron simply calls it, and the service internally iterates over all active specializations, evaluates frequency windows, and generates/sends reports as needed. When invoked, it orchestrates the full pipeline: specialization iteration, frequency evaluation, data retrieval, template processing, PDF generation, cloud upload, email delivery, and history tracking.

##### Request:
No request body required. The endpoint is called without any payload.

##### Processing Logic:
1. Fetch all active specializations from the `specializations` table.
3. For each active specialization:
   a. Read the `settings` record to get `email_digest` and `at_risk_alert` frequency values.
   b. For each report type (Summary and At-risk), evaluate whether the report is due (see FR02).
   c. If due, fetch the email template from `email_templates` table where `template_name` matches the report type.
   d. Fetch report data based on the report type:
      - **At-risk**: Query projects where days since onboarding exceeds the threshold, linked to the specialization.
      - **Summary report**: Query KPI metrics from `kpi_history` for the specialization.
   e. Fetch active recipient email addresses from `email_recipient` table where `specialization_id` matches and `is_active = 1`.
   f. If no active recipients are configured, skip this specialization and log a warning.
   g. Process the HTML template with BeautifulSoup, injecting report data into placeholders.
   h. Convert the populated HTML to PDF using WeasyPrint (in-memory).
   i. Upload the PDF to cloud storage with filename: `{report_type}_{specialization_name}_{YYYYMMDD_HHmmss}.pdf`.
   j. Send the email to all active recipients with the report download link.
   k. Create a record in `email_history` with delivery status.
4. Return success response.

##### Success Response:
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Email sent successfully"
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 500 | Unexpected server error (PDF generation failure, email delivery failure, storage upload failure) |

##### Acceptance Criteria:
- The endpoint requires no request body — it processes all active specializations internally.
- For each specialization, the service evaluates frequency and only generates reports that are due.
- Specializations with no active recipients are skipped (logged as warning, not an error).
- Successful execution returns HTTP 200 and creates `email_history` records for each report sent.
- Failed execution logs the error and creates `email_history` records with status "failed".

##### <u> 1.2.2 ZDAD-60-FR02: Cron Job Frequency Evaluation </u>

##### Description:
The system shall implement frequency-based evaluation logic that determines whether a report should be sent for a given specialization. The daily cron job (external trigger) calls the report generation endpoint for each specialization. Before generating and sending a report, the service checks the `email_history` table to determine if a report of the same type has already been sent within the current frequency window. The frequency is configured per specialization in the `settings` table via `email_digest` (for Summary reports) and `at_risk_alert` (for At-risk reports).

**Important:** Report settings are controlled at the specialization/domain level, NOT per user. Each specialization (e.g., DevSecOps, Platform Engineering, Frontend, SRE) maintains its own independent configuration. If one specialization head updates the settings for a domain, the settings apply to ALL specialization heads/users within that same domain. For example, if DevSecOps is configured with Risk Report = Daily and Summary Report = Weekly, then all DevSecOps specialization heads receive daily Risk Reports and weekly Summary Reports — but these settings do NOT affect other domains like Platform Engineering or SRE.

##### Frequency Options:
- `daily` — Send every day (check if sent in the last 24 hours)
- `weekly` — Send once per week (check if sent in the last 7 days)
- `bi-weekly` — Send once every two weeks (check if sent in the last 14 days)
- `monthly` — Send once per month (check if sent in the last 30 days)
- `not_required` — Do not send this report type

##### Evaluation Logic:
1. For each active specialization, read the `settings` record to get `email_digest` and `at_risk_alert` frequency values.
2. For each report type (Summary and At-risk):
   a. If the frequency is `not_required`, skip this report type.
   b. Query `email_history` for the most recent record where `email_type` matches the report type, `setting_id` matches, and `email_status = "sent"`.
   c. Calculate whether the time elapsed since `last_synced` exceeds the frequency window:
      - `daily`: 24 hours
      - `weekly`: 7 days
      - `bi-weekly`: 14 days
      - `monthly`: 30 days
   d. If the frequency window has elapsed (or no history exists), trigger report generation.
   e. If a report was already sent within the window, skip and log at DEBUG level.

##### Acceptance Criteria:
- Reports are not sent if one was already delivered within the configured frequency window.
- A specialization with `email_digest = "weekly"` receives a Summary report only once per 7 days.
- A specialization with `at_risk_alert = "not_required"` never receives At-risk reports.
- First-time execution (no history) triggers report generation immediately.
- The evaluation logic correctly handles all frequency options (daily, weekly, bi-weekly, monthly, not_required).
- Skipped reports are logged at DEBUG level with the reason.

##### <u> 1.2.3 ZDAD-60-FR03: HTML Template Processing and PDF Generation </u>

##### Description:
The system shall fetch the HTML email template from the `email_templates` table, parse it using BeautifulSoup, inject dynamic report data into the template placeholders, and convert the final HTML to a PDF document using WeasyPrint. The template contains HTML elements with identifiable attributes (IDs or classes) that serve as injection points for dynamic data.

##### Template Selection:
- Template is selected from `email_templates` table where `template_name` matches the report type:
  - `At-risk` → Template named "At-risk"
  - `Summary report` → Template named "Summary report"
- The `template_content` field contains the full HTML string.

##### Data Injection (BeautifulSoup Processing):
- Parse the HTML string using `BeautifulSoup(template_content, "html.parser")`.
- Locate placeholder elements by their IDs or CSS classes.
- Inject dynamic data into the appropriate elements:
  - **Summary report data**: Specialization name, report date range, total projects count, completed count, active count, inactive count, at-risk count, not-applicable count, percentage breakdown, trend indicators.
  - **At-risk report data**: Specialization name, report generation date, list of at-risk projects with project name, client, onboarded date, days overdue, and risk indicators.
- Convert the modified BeautifulSoup object back to an HTML string using `.prettify()` or `str()`.

##### PDF Conversion:
- Use WeasyPrint to convert the populated HTML string to a PDF document.
- The PDF is generated in memory (bytes buffer) without writing to disk.
- WeasyPrint handles CSS styling embedded in the HTML template for proper PDF formatting.

##### Acceptance Criteria:
- The correct template is fetched based on the report type.
- Dynamic data is correctly injected into the HTML template placeholders.
- The generated PDF contains all injected data in a readable format.
- PDF generation does not write temporary files to disk (in-memory processing).
- If the template is not found in the database, the service returns HTTP 500 and logs the error.
- Malformed HTML templates are handled gracefully with appropriate error logging.

##### <u> 1.2.4 ZDAD-60-FR04: Cloud Storage Upload </u>

##### Description:
The system shall upload the generated PDF document to AWS S3 and return a pre-signed URL for download.

##### Upload Configuration:
- **Bucket name**: Configured via `S3_BUCKET_NAME` environment variable.
- **File path pattern**: `reports/{specialization_name}/{report_type}/{YYYY}/{MM}/{filename}.pdf`
- **Filename format**: `{report_type}_{specialization_name}_{YYYYMMDD_HHmmss}.pdf`

##### Processing Logic:
1. Generate the file path and filename based on the report metadata.
2. Upload the PDF bytes to the configured storage provider.
3. Generate a pre-signed URL with configurable expiration (default: 7 days).
4. Return the URL for inclusion in the email body and `email_history.report_url`.

##### Acceptance Criteria:
- The PDF is uploaded successfully to S3.
- The generated URL is accessible and allows PDF download.
- The URL has a configurable expiration period (default 7 days).
- Upload failures are caught, logged to `error_log`, and result in HTTP 500 response.
- The file path follows the organized folder structure for easy management.

##### <u> 1.2.5 ZDAD-60-FR05: Email Delivery </u>

##### Description:
The system shall send emails to all active recipients configured for the target specialization. The email contains the report download link (URL to the uploaded PDF in cloud storage). The email is sent via Microsoft Graph API. If sending fails for a specific recipient, the service skips that recipient and continues to the next one without failing the entire batch.

##### Email Service Configuration:
- **Email provider**: Microsoft Graph API.
- **Microsoft Graph API**: Requires `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, `GRAPH_TENANT_ID`, and `GRAPH_SENDER_EMAIL` environment variables.

##### Email Content:
- **From**: Configured sender email address.
- **To**: Each active recipient's `alert_recipient` email from the `email_recipient` table.
- **Subject**: `[DevSecOps Dashboard] {Report Type} Report - {Specialization Name} - {Date}`
- **Body**: HTML email body containing:
  - Report type and specialization name
  - Report generation date
  - Download link to the PDF in cloud storage
  - Brief summary of key metrics (optional, based on template)

##### Processing Logic:
1. Fetch all active recipients from `email_recipient` where `specialization_id` matches and `is_active = 1`.
2. For each recipient:
   a. Compose the email with subject, body, and report link.
   b. Send via the configured email provider.
   c. If sending fails, log the failure at WARNING level with recipient email and error details.
   d. Continue to the next recipient regardless of individual failures.
3. Track overall delivery status:
   - If at least one email was sent successfully → status is "sent".
   - If all emails failed → status is "failed".

##### Acceptance Criteria:
- Emails are sent to all active recipients for the given specialization.
- Individual recipient failures do not block delivery to other recipients.
- Failed deliveries are logged at WARNING level with the recipient and error details.
- The email contains a valid download link to the PDF report.
- The email subject includes the report type, specialization name, and date.

##### <u> 1.2.6 ZDAD-60-FR06: Email History Tracking </u>

##### Description:
The system shall create a record in the `email_history` table after each report generation attempt (success or failure). This record serves as the audit trail for delivery tracking and is used by the frequency evaluation logic (FR02) to determine whether a report has already been sent within the current window.

##### Email History Record Fields:
| Field | Value |
|-------|-------|
| `email_history_id` | Auto-generated UUID |
| `setting_id` | FK to the `settings` record for the specialization |
| `email_status` | "sent" (at least one recipient succeeded) or "failed" (all recipients failed) |
| `email_type` | Report type: "At-risk" or "Summary report" |
| `report_url` | URL of the uploaded PDF in cloud storage (null if generation failed before upload) |
| `last_synced` | Timestamp of the generation attempt |
| `created_at` | Current timestamp |
| `created_by` | "report_service" |
| `is_active` | 1 |

##### Acceptance Criteria:
- A record is created in `email_history` for every report generation attempt.
- Successful deliveries have `email_status = "sent"` and a valid `report_url`.
- Failed deliveries have `email_status = "failed"` and `report_url` may be null.
- The `setting_id` correctly references the specialization's settings record.
- History records are never deleted — they serve as a permanent audit trail.

##### <u> 1.2.7 ZDAD-60-FR07: Cron Job Status Tracking </u>

##### Description:
The system shall track each cron job execution in the `cron_jobs` table. When the external cron trigger invokes the report generation endpoint, a record is created (or updated) in `cron_jobs` with the execution status. This provides visibility into cron execution history and helps diagnose scheduling issues.

##### Cron Job Record Fields:
| Field | Value |
|-------|-------|
| `cron_id` | Auto-generated UUID |
| `specialization_id` | The specialization being processed |
| `type` | "email" (distinguishes from "azure" sync cron jobs) |
| `sync_status` | "pending" (started), "success" (completed), or "fail" (error occurred) |
| `created_at` | Timestamp when the cron execution started |
| `created_by` | "report_service" |
| `modified_at` | Timestamp when the status was last updated |
| `modified_by` | "report_service" |

##### Processing Logic:
1. When the cron trigger invokes the endpoint, create a `cron_jobs` record with `sync_status = "pending"`.
2. After successful report generation and email delivery, update `sync_status` to "success".
3. If an unhandled error occurs during processing, update `sync_status` to "fail".

##### Acceptance Criteria:
- A `cron_jobs` record is created for each cron-triggered execution.
- The record transitions from "pending" → "success" or "pending" → "fail".
- The `type` field is always "email" for report generation cron jobs.
- Manual API-triggered reports do not create `cron_jobs` records (only cron-triggered ones do).

##### <u> 1.2.8 ZDAD-60-FR08: Error Logging </u>

##### Description:
The system shall log all unhandled exceptions occurring during report generation to the `error_log` database table. This provides a persistent audit trail for debugging report generation failures. The error logging mechanism is the same global exception handler used across the application (as established in ZDAD-34-FR04).

##### Error Log Table Fields:
- `error_id` — Auto-generated UUID primary key.
- `error_message` — The exception message text.
- `error_function` — The function name where the error occurred (e.g., "generate_report", "upload_pdf", "send_email").
- `error_file` — The file path where the error originated.
- `stack_trace` — Full Python stack trace for debugging.
- `created_at` — Timestamp when the error was logged.
- `created_by` — "report_service".

##### Acceptance Criteria:
- All unhandled exceptions in the report generation pipeline are captured and logged to `error_log`.
- The error log entry contains the function name, file name, error message, and stack trace.
- Error logging does not interfere with the error response returned to the caller (non-blocking).
- HTTP 500 responses are always accompanied by an `error_log` entry.
- Individual recipient email failures are logged at application WARNING level, not in `error_log`.


#### <u> 1.3 Database Schema </u>

The full database schema is defined in `design/er_diagram.mmd`. The following tables are directly involved in the Email Notification Service:

- **email_templates** — HTML templates for report generation. Selected by `template_name` matching the report type.
- **email_recipient** — Recipient email addresses per specialization. Filtered by `specialization_id` and `is_active = 1`.
- **email_history** — Tracks report generation attempts and delivery status (`email_status`, `email_type`, `report_url`, `last_synced`).
- **settings** — Configuration for report frequency (`email_digest`, `at_risk_alert`) and `at_risk_threshold` per specialization.
- **specializations** — Validates the target specialization and provides iteration list.
- **kpi_history** — Source data for Summary reports (KPI counts per specialization).
- **projects** — Source data for At-risk reports (projects exceeding threshold).
- **cron_jobs** — Tracks scheduled report generation executions (`type="email"`, `sync_status`).
- **error_log** — Persists unhandled exceptions during report generation.

##### Key Relationships:
- `email_recipient.specialization_id` → `specializations.specialization_id` (recipients per specialization)
- `email_history.setting_id` → `settings.setting_id` (history tracks per settings record)
- `settings.specialization_id` → `specializations.specialization_id` (settings per specialization)
- `kpi_history.specialization_id` → `specializations.specialization_id` (KPI data per specialization)

#### <u> 1.4 Project Artifacts </u>

- `api/email-notification-openapi.yaml` — OpenAPI 3.0.3 specification for the report generation endpoint.
- `design/er_diagram.mmd` — Mermaid ER diagram showing all database tables and relationships.
- `design/requirements.md` — Section 3 (Report Generation & Email Delivery) contains the high-level requirements.
- `diagram/email_notification.mmd` — Sequence diagram showing the email notification flow.

#### <u> 1.5 Environment Variables </u>

##### Description:
All application configuration shall be managed through environment variables. The Email Notification Service requires the following variables beyond the base application config.

##### Required Environment Variables:
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

### <u> Section 2: In Scope and Out Scope </u>

#### <u> 2.1 Inscope Details </u>

- Implementation of `POST /api/v1/reports/generate` endpoint (no request body) for triggering report generation
- Internal iteration over all active specializations
- Frequency evaluation logic checking `settings.email_digest` and `settings.at_risk_alert` against `email_history`
- Fetching HTML email templates from the `email_templates` table based on report type
- Fetching report data: KPI metrics from `kpi_history` for Summary reports, at-risk projects from `projects` for At-risk reports
- Fetching active email recipients from `email_recipient` table filtered by `specialization_id`
- HTML template processing using BeautifulSoup to inject dynamic report data
- PDF generation from populated HTML using WeasyPrint (in-memory, no temp files)
- PDF upload to AWS S3 with pre-signed URL generation
- Email delivery to all active recipients via Microsoft Graph API
- Skip-and-continue pattern for individual recipient email failures
- Email history tracking in `email_history` table (status, URL, timestamp)
- Cron job status tracking in `cron_jobs` table (pending → success/fail)
- Error logging to `error_log` table for all unhandled exceptions
- Pydantic v2 response models for serialization
- SQLAlchemy ORM models for `email_templates`, `email_recipient`, `email_history`, `settings`, `cron_jobs`, `kpi_history`, and `projects` tables
- Environment variable-based configuration for email provider, storage provider, and credentials
- Standardized response format following `BaseResponse` schema
- Structured JSON logging with trace_id for all report generation operations
- Layered architecture: Routes → Services → Repositories → Database

#### <u> 2.2 Outscope Details </u>

- Implementation of the external cron trigger (Azure Function Timer Trigger or AWS EventBridge) — only the API endpoint is in scope
- Email template CRUD management (templates are pre-seeded in the database)
- Email recipient CRUD management (managed via the Settings endpoints in a separate story)
- Settings CRUD management (managed via a separate Settings story)
- Report scheduling UI or configuration UI
- Custom report types beyond "At-risk" and "Summary report"
- Email attachment (PDF is delivered via download link, not as an attachment)
- Retry logic for failed email deliveries within the same request
- Cloud storage lifecycle management (cleanup of expired PDFs)
- Real-time report generation (reports are batch-processed via cron)
- Dashboard UI for viewing email history or report status
- ADO Sync API that populates `kpi_history` (separate story)
- ServiceNow Sync endpoints (covered in ZDAD-58)
- Overview API and Filters API (covered in ZDAD-34)

### <u> Section 3: Solution Diagrams </u>

#### <u> 3.1 Architecture Diagram </u>

**Diagram Location:** `diagram/email_notification.mmd`
