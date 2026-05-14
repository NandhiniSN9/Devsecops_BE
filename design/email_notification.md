## SOLDEF-ZDAD-60 - Implement Email Notification Service

### <u>Project Details</u>
- **Project ID:** ZDAD  
- **Project Name:** DevSecOps Jira Dashboard  

### <u>Story Details</u>
- **Story ID:** ZDAD-60  
- **Story Name:** Implement Email Notification Service  
- **Story Description:**  
  Implement an automated email notification service that generates PDF reports (At-risk and Summary) for each specialization and delivers them to configured recipients. The service is triggered by a daily cron job that evaluates each specialization's configured email digest and at-risk alert frequencies, generates HTML-to-PDF reports using stored templates, uploads them to cloud storage, sends emails via Microsoft Graph API or Amazon SES, and tracks delivery history to prevent duplicate sends within the configured frequency window.

### <u> Table of Contents </u>
- [Section 1: Functional Requirements](#Section-1:-Functional-Requirements)
    - [1.1 Overview](#1.1-Overview)
    - [1.2 Requirement Details](#1.2-Requirement-Details)
    - [1.3 Project Artifacts](#1.3-Project-Artifacts)
    - [1.4 Dependencies](#1.4-Dependencies)
- [Section 2: Non Functional Requirements](#Section-2:-Non-Functional-Requirements)
- [2.1 Infrastructure and Deployment](#2.1-Infrastructure-and-Deployment)
    - [2.1.1 Overview](#2.1-Overview)
    - [2.1.2 Requirement Details](#2.2-Requirement-Details)
    - [2.1.3 Project Artifacts](#2.3-Project-Artifacts)
    - [2.1.4 Dependencies](#2.4-Dependencies)
- [2.2 Architecture and System Design](#2.2-Architecture-and-System-Design)
    - [2.2.1 Security and Compliance](#2.2.1-Security-and-Compliance)
    - [2.2.2 System Performance](#2.2.2-System-Performance)
    - [2.2.3 Availability and Reliability](#2.2.3-Availability-and-Reliability)
    - [2.2.4 Cost Efficiency](#2.2.4-Cost-Efficiency)
    - [2.2.5 Traceability and Observability](#2.2.5-Traceability-and-Observability)
- [Section 3: In Scope and Out Scope](#Section-3:-In-Scope-and-Out-Scope)
    - [3.1 In Scope Details](#1.1-In-Scope-Details)
    - [3.2 Out Scope Details](#1.2-Out-Scope-Details)
- [Section 4: Solution Diagrams](#Section-4:-Solution-Diagrams)
    - [4.1 UI/UX Design Diagram](#4.1-UI/UX-Design-Diagram)
    - [4.2 Architecture Design Diagram](#4.2-Architecture-Design-Diagram)
    - [4.3 Infrastructure Design Diagram](#4.3-Infrastructure-Design-Diagram)

### <u> Section 1: Functional Requirements </u>

#### <u> 1.1 Overview </u>

The Email Notification Service automates the generation and delivery of PDF reports for the DevSecOps Jira Dashboard. The service exposes a `POST /api/v1/reports/generate` endpoint that is triggered by an external daily cron job with no request body. Upon invocation, the service internally fetches all active specializations and evaluates each one's configured report frequencies (`email_digest` for Summary reports and `at_risk_alert` for At-risk reports) from the `settings` table. It checks the `email_history` table to determine whether a report has already been sent within the current frequency window (e.g., weekly, monthly). If a report is due, the service fetches the corresponding HTML email template from the `email_templates` table, retrieves the relevant report data (KPI metrics for Summary reports or at-risk project details for At-risk reports), processes the HTML using BeautifulSoup to inject dynamic data, converts the populated HTML to a PDF document using WeasyPrint, uploads the PDF to cloud storage (AWS S3 or Azure Blob Storage), sends the email with the report link to all active recipients configured for that specialization via Microsoft Graph API or Amazon SES, and finally records the delivery status in the `email_history` table. The cron job execution status is tracked in the `cron_jobs` table. All errors are logged to the `error_log` table for traceability.

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
1. Authenticate the request (encrypted token validation).
2. Fetch all active specializations from the `specializations` table.
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
| 401 | Missing or invalid authentication token |
| 500 | Unexpected server error (PDF generation failure, email delivery failure, storage upload failure) |

##### Acceptance Criteria:
- The endpoint requires no request body — it processes all active specializations internally.
- For each specialization, the service evaluates frequency and only generates reports that are due.
- Specializations with no active recipients are skipped (logged as warning, not an error).
- Successful execution returns HTTP 200 and creates `email_history` records for each report sent.
- Failed execution logs the error and creates `email_history` records with status "failed".
- The endpoint requires encrypted token authentication (shared middleware).

##### <u> 1.2.2 ZDAD-60-FR02: Cron Job Frequency Evaluation </u>

##### Description:
The system shall implement frequency-based evaluation logic that determines whether a report should be sent for a given specialization. The daily cron job (external trigger) calls the report generation endpoint for each specialization. Before generating and sending a report, the service checks the `email_history` table to determine if a report of the same type has already been sent within the current frequency window. The frequency is configured per specialization in the `settings` table via `email_digest` (for Summary reports) and `at_risk_alert` (for At-risk reports).

##### Frequency Options:
- `daily` — Send every day
- `weekly` — Send once per week (check if sent in the last 7 days)
- `monthly` — Send once per month (check if sent in the last 30 days)
- `disabled` or `null` — Do not send this report type

##### Evaluation Logic:
1. For each active specialization, read the `settings` record to get `email_digest` and `at_risk_alert` frequency values.
2. For each report type (Summary and At-risk):
   a. If the frequency is `disabled` or `null`, skip this report type.
   b. Query `email_history` for the most recent record where `email_type` matches the report type, `setting_id` matches, and `email_status = "sent"`.
   c. Calculate whether the time elapsed since `last_synced` exceeds the frequency window:
      - `daily`: 24 hours
      - `weekly`: 7 days
      - `monthly`: 30 days
   d. If the frequency window has elapsed (or no history exists), trigger report generation.
   e. If a report was already sent within the window, skip and log at DEBUG level.

##### Acceptance Criteria:
- Reports are not sent if one was already delivered within the configured frequency window.
- A specialization with `email_digest = "weekly"` receives a Summary report only once per 7 days.
- A specialization with `at_risk_alert = "disabled"` never receives At-risk reports.
- First-time execution (no history) triggers report generation immediately.
- The evaluation logic correctly handles all frequency options (daily, weekly, monthly, disabled).
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
The system shall upload the generated PDF document to cloud storage (AWS S3 or Azure Blob Storage) and return a publicly accessible or pre-signed URL for download. The storage provider is configurable via environment variables, allowing deployment flexibility between AWS and Azure environments.

##### Upload Configuration:
- **Storage provider**: Determined by `STORAGE_PROVIDER` environment variable (`s3` or `azure_blob`).
- **Bucket/Container name**: Configured via `STORAGE_BUCKET_NAME` environment variable.
- **File path pattern**: `reports/{specialization_name}/{report_type}/{YYYY}/{MM}/{filename}.pdf`
- **Filename format**: `{report_type}_{specialization_name}_{YYYYMMDD_HHmmss}.pdf`

##### Processing Logic:
1. Generate the file path and filename based on the report metadata.
2. Upload the PDF bytes to the configured storage provider.
3. Generate a download URL:
   - **S3**: Generate a pre-signed URL with configurable expiration (default: 7 days).
   - **Azure Blob**: Generate a SAS token URL with configurable expiration (default: 7 days).
4. Return the URL for inclusion in the email body and `email_history.report_url`.

##### Acceptance Criteria:
- The PDF is uploaded successfully to the configured cloud storage.
- The generated URL is accessible and allows PDF download.
- The URL has a configurable expiration period (default 7 days).
- Upload failures are caught, logged to `error_log`, and result in HTTP 500 response.
- The file path follows the organized folder structure for easy management.
- Both S3 and Azure Blob Storage are supported based on configuration.

##### <u> 1.2.5 ZDAD-60-FR05: Email Delivery </u>

##### Description:
The system shall send emails to all active recipients configured for the target specialization. The email contains the report download link (URL to the uploaded PDF in cloud storage). The email delivery service is configurable — supporting either Microsoft Graph API or Amazon SES based on the deployment environment. If sending fails for a specific recipient, the service skips that recipient and continues to the next one without failing the entire batch.

##### Email Service Configuration:
- **Email provider**: Determined by `EMAIL_PROVIDER` environment variable (`graph_api` or `ses`).
- **Microsoft Graph API**: Requires `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, `GRAPH_TENANT_ID`, and `GRAPH_SENDER_EMAIL` environment variables.
- **Amazon SES**: Requires `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `SES_SENDER_EMAIL` environment variables.

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
- Both Microsoft Graph API and Amazon SES are supported based on configuration.
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

The following tables are directly involved in the Email Notification Service (as defined in `design/er_diagram.mmd`):

##### email_templates
| Column | Type | Constraints |
|--------|------|-------------|
| email_template_id | UUID | PK |
| template_name | VARCHAR | NOT NULL |
| template_content | TEXT | NOT NULL (HTML string) |
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

##### email_history
| Column | Type | Constraints |
|--------|------|-------------|
| email_history_id | UUID | PK |
| setting_id | UUID | FK → settings.setting_id |
| email_status | VARCHAR | NOT NULL ("sent" or "failed") |
| email_type | VARCHAR | NOT NULL ("At-risk" or "Summary report") |
| report_url | TEXT | URL to uploaded PDF (nullable) |
| last_synced | DATETIME | Timestamp of generation attempt |
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
| email_digest | VARCHAR | Frequency for Summary reports (daily/weekly/monthly/disabled) |
| at_risk_alert | VARCHAR | Frequency for At-risk reports (daily/weekly/monthly/disabled) |
| last_synced | DATETIME | |
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

##### kpi_history (read-only reference for Summary reports)
| Column | Type | Constraints |
|--------|------|-------------|
| kpi_history_id | UUID | PK |
| specialization_id | UUID | FK → specializations.specialization_id |
| projects_count | INTEGER | DEFAULT 0 |
| projects_increase_count | INTEGER | DEFAULT 0 |
| completed_count | INTEGER | DEFAULT 0 |
| completed_increase_count | INTEGER | DEFAULT 0 |
| inactive_count | INTEGER | DEFAULT 0 |
| inactive_increase_count | INTEGER | DEFAULT 0 |
| at_risk_count | INTEGER | DEFAULT 0 |
| at_risk_increase_count | INTEGER | DEFAULT 0 |
| not_applicable_count | INTEGER | DEFAULT 0 |
| not_applicable_increase_count | INTEGER | DEFAULT 0 |
| created_at | DATETIME | |
| is_active | INT | DEFAULT 1 |

##### projects (read-only reference for At-risk reports)
| Column | Type | Constraints |
|--------|------|-------------|
| project_id | UUID | PK |
| status_id | UUID | FK → statuses.status_id |
| project_name | VARCHAR | NOT NULL |
| onboarded_date | DATE | NOT NULL |
| client | VARCHAR | |
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
| is_active | INT | DEFAULT 1 |

##### Key Relationships:
- `email_recipient.setting_id` → `settings.setting_id` (recipients belong to a settings record)
- `email_recipient.specialization_id` → `specializations.specialization_id` (recipients are per specialization)
- `email_history.setting_id` → `settings.setting_id` (history tracks per settings record)
- `settings.specialization_id` → `specializations.specialization_id` (settings are per specialization)
- `kpi_history.specialization_id` → `specializations.specialization_id` (KPI data per specialization)

#### <u> 1.4 Project Artifacts </u>

- `api/openapi.yaml` — Full OpenAPI 3.0.3 specification defining the `POST /api/v1/reports/generate` endpoint, request schema (`GenerateReportRequest`), and response schemas.
- `design/er_diagram.mmd` — Mermaid ER diagram showing all database tables and relationships including `email_templates`, `email_recipient`, `email_history`, `settings`, `cron_jobs`, and `kpi_history`.
- `design/requirements.md` — Section 3 (Report Generation & Email Delivery) contains the high-level requirements for this story.

#### <u> 1.5 Dependencies </u>

- **Python 3.12+** — Runtime environment
- **FastAPI** — Web framework for building the REST API
- **SQLAlchemy** — ORM for PostgreSQL database access (queries on email_templates, email_recipient, email_history, settings, kpi_history, projects)
- **Pydantic v2** — Response model serialization
- **PostgreSQL** — Primary database storing templates, recipients, history, settings, and report data
- **BeautifulSoup4 (bs4)** — HTML template parsing and dynamic data injection
- **WeasyPrint** — HTML-to-PDF conversion library
- **boto3** — AWS SDK for S3 upload and SES email delivery (when using AWS)
- **azure-storage-blob** — Azure Blob Storage SDK for PDF upload (when using Azure)
- **msal / microsoft-graph-core** — Microsoft Graph API client for email delivery (when using Graph API)
- **cryptography / PyCryptodome** — Token decryption using private key (shared with existing auth middleware)
- **Jira API client (atlassian-python-api or httpx)** — Validates Jira email existence (shared with existing auth middleware)
- **Uvicorn** — ASGI server for running the FastAPI application


### <u> Section 2: Non Functional Requirements </u>

### 2.1 Infrastructure and Deployment

#### <u> 2.1.1 Overview </u>

The Email Notification Service is deployed as part of the existing DevSecOps Jira Dashboard backend application on Azure App Service. No separate service or infrastructure is required — the report generation route is registered within the existing FastAPI application alongside the Overview API and ServiceNow Sync routes. The service connects to the same PostgreSQL database instance and shares the same authentication middleware, error handling, and logging infrastructure. The external cron trigger (Azure Function Timer Trigger or AWS EventBridge) invokes the API endpoint on a daily schedule. Cloud storage credentials (S3 or Azure Blob) and email service credentials (Graph API or SES) are managed through Azure App Service application settings as environment variables.

#### <u> 2.1.2 Requirement Details </u>

- **ZDAD-60-NFR01: Shared Deployment with Existing Application**
- **ZDAD-60-NFR02: Environment Configuration for Email Service**
- **ZDAD-60-NFR03: External Cron Trigger Configuration**

##### <u> 2.1.2.1 ZDAD-60-NFR01: Shared Deployment with Existing Application </u>

##### Description:
The Email Notification Service endpoints shall be deployed as additional routes within the existing FastAPI application. No separate service or deployment is required. The report generation route is registered via a dedicated `APIRouter` with prefix `/api/v1/reports` and shares the same database connection pool, authentication middleware, and error handling infrastructure established in ZDAD-34.

##### Deployment Configuration:
- **Route Registration:** Report routes are added via `APIRouter` with prefix `/api/v1/reports`.
- **Database:** Uses the same SQLAlchemy engine and session factory.
- **Authentication:** Uses the same encrypted token middleware.
- **Error Handling:** Uses the same global exception handler that logs to `error_log`.

##### Acceptance Criteria:
- The report generation endpoint is accessible after deployment without additional infrastructure changes.
- Existing endpoints (Overview, Filters, ServiceNow Sync) continue to function without disruption.
- The application starts successfully with the new routes registered.
- Health check and readiness endpoints remain unaffected.

##### <u> 2.1.2.2 ZDAD-60-NFR02: Environment Configuration for Email Service </u>

##### Description:
All email service and cloud storage configuration shall be managed through environment variables. No credentials are hardcoded in the application source code.

##### Required Environment Variables:
| Variable | Description | Required |
|----------|-------------|----------|
| `EMAIL_PROVIDER` | Email service provider: `graph_api` or `ses` | Yes |
| `STORAGE_PROVIDER` | Cloud storage provider: `s3` or `azure_blob` | Yes |
| `STORAGE_BUCKET_NAME` | S3 bucket or Azure Blob container name | Yes |
| `STORAGE_URL_EXPIRY_DAYS` | Pre-signed URL expiration in days (default: 7) | No |
| `GRAPH_CLIENT_ID` | Microsoft Graph API client ID | If EMAIL_PROVIDER=graph_api |
| `GRAPH_CLIENT_SECRET` | Microsoft Graph API client secret | If EMAIL_PROVIDER=graph_api |
| `GRAPH_TENANT_ID` | Microsoft Graph API tenant ID | If EMAIL_PROVIDER=graph_api |
| `GRAPH_SENDER_EMAIL` | Sender email for Graph API | If EMAIL_PROVIDER=graph_api |
| `AWS_REGION` | AWS region for SES and S3 | If using AWS services |
| `AWS_ACCESS_KEY_ID` | AWS access key | If using AWS services |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | If using AWS services |
| `SES_SENDER_EMAIL` | Verified sender email for SES | If EMAIL_PROVIDER=ses |

##### Acceptance Criteria:
- The application validates required environment variables at startup based on the configured providers.
- Missing required variables result in a clear startup error message.
- No secrets or credentials are hardcoded in the application source code.
- A `.env.sample` file documents all email-service-related variables with placeholder values.

##### <u> 2.1.2.3 ZDAD-60-NFR03: External Cron Trigger Configuration </u>

##### Description:
The report generation is triggered by an external scheduler (Azure Function Timer Trigger or AWS EventBridge Rule) that calls `POST /api/v1/reports/generate` on a daily schedule. No request body is sent — the API internally iterates over all active specializations and evaluates frequency windows.

##### Trigger Flow:
1. External cron fires daily (e.g., 06:00 UTC).
2. The cron calls `POST /api/v1/reports/generate` with no request body (only the authentication token in the header).
3. The API internally fetches all active specializations and processes each one.
4. The API handles frequency evaluation internally (FR02) to determine if the report should actually be sent.

##### Acceptance Criteria:
- The external cron trigger is documented with the expected schedule and invocation pattern.
- The API endpoint requires no request body — it processes all specializations internally.
- The API endpoint handles being called daily without sending duplicate reports (frequency evaluation).
- The trigger uses a service account encrypted token for authentication.

#### <u> 2.1.3 Project Artifacts </u>

- `api/openapi.yaml` — API specification including the report generation endpoint
- `design/er_diagram.mmd` — Database schema reference for email-related tables

### 2.2 Architecture and System Design

#### <u> 2.2.1 Security and Compliance </u>

##### Encrypted Token Authentication:
The report generation endpoint requires a valid encrypted token in the `Authorization` header. The existing authentication middleware decrypts the token using a private key and validates the Jira email ID against the Jira API. No additional role check is required — any authenticated user (including the cron service account) can trigger report generation.

##### Credential Management:
- Cloud storage credentials (AWS keys, Azure connection strings) are stored exclusively in environment variables.
- Email service credentials (Graph API secrets, SES keys) are stored exclusively in environment variables.
- No credentials are logged, included in error messages, or exposed in API responses.
- Pre-signed URLs have configurable expiration to limit access window.

##### Data Protection:
- Email recipient addresses are stored in the database and only used for sending — never exposed in API responses to non-admin users.
- Report PDFs may contain sensitive project data — access is controlled via pre-signed URLs with expiration.
- All communication with cloud storage and email services uses HTTPS/TLS.

#### <u> 2.2.2 System Performance </u>

##### Processing Efficiency:
- PDF generation is performed in-memory using WeasyPrint without writing temporary files to disk.
- Email sending is performed sequentially per recipient to avoid rate limiting from email providers.
- Database queries for report data use indexed columns (`specialization_id`, `is_active`, `status_id`).
- The frequency evaluation query on `email_history` uses indexed `setting_id` and `email_type` columns.

##### Resource Considerations:
- WeasyPrint PDF generation is CPU-intensive — reports are generated one at a time per request.
- Cloud storage uploads use streaming to minimize memory usage for large PDFs.
- SQLAlchemy connection pooling is shared with the existing application.

#### <u> 2.2.3 Availability and Reliability </u>

##### Failure Isolation:
- Individual recipient email failures do not block delivery to other recipients (skip and continue pattern).
- Cloud storage upload failures are caught and result in a "failed" email history record.
- PDF generation failures are caught and logged without crashing the application.
- The global exception handler ensures all unhandled errors return HTTP 500 and are logged.

##### Idempotency:
- The frequency evaluation logic (FR02) ensures that duplicate cron triggers within the same window do not result in duplicate emails.
- Re-running the endpoint for the same specialization and report type within the frequency window is a no-op.

##### Retry Strategy:
- No automatic retry is implemented for failed email deliveries — the next cron cycle will re-evaluate and attempt again if the frequency window has elapsed.
- Cloud storage upload failures are not retried within the same request — they are logged and the report is marked as "failed".

#### <u> 2.2.4 Cost Efficiency </u>

##### Resource Optimization:
- No additional infrastructure is required — the service shares the existing App Service and database.
- PDF generation is on-demand (only when frequency window has elapsed), minimizing compute usage.
- Cloud storage costs are controlled by the URL expiration policy (old reports can be cleaned up via lifecycle rules).
- Email sending costs are minimized by the frequency evaluation logic (no unnecessary sends).

#### <u> 2.2.5 Traceability and Observability </u>

##### Structured Logging:
- All report generation operations use the same JSON-formatted structured logging as the rest of the application.
- Each report generation request is assigned a `trace_id` for end-to-end tracing.
- Key log events:
  - INFO: Report generation started (specialization, report type)
  - INFO: PDF generated successfully (file size, generation time)
  - INFO: PDF uploaded to cloud storage (URL, storage provider)
  - INFO: Email sent successfully (recipient count)
  - WARNING: Individual recipient email delivery failed (recipient, error)
  - WARNING: Report skipped due to frequency window (specialization, last sent date)
  - ERROR: Unhandled exception (logged to `error_log` table)

##### Audit Trail:
- `email_history` table provides a complete audit trail of all report generation attempts.
- `cron_jobs` table tracks cron execution status for scheduling visibility.
- `error_log` table captures all unhandled exceptions with full stack traces.


### <u> Section 3: In Scope and Out Scope </u>

#### <u> 3.1 Inscope Details </u>

- Implementation of `POST /api/v1/reports/generate` endpoint for triggering report generation
- Frequency evaluation logic checking `settings.email_digest` and `settings.at_risk_alert` against `email_history` to prevent duplicate sends
- Fetching HTML email templates from the `email_templates` table based on report type
- Fetching report data: KPI metrics from `kpi_history` for Summary reports, at-risk projects from `projects` for At-risk reports
- Fetching active email recipients from `email_recipient` table filtered by `specialization_id`
- HTML template processing using BeautifulSoup to inject dynamic report data into placeholders
- PDF generation from populated HTML using WeasyPrint (in-memory, no temp files)
- PDF upload to cloud storage (AWS S3 or Azure Blob Storage) with pre-signed/SAS URL generation
- Email delivery to all active recipients via configurable provider (Microsoft Graph API or Amazon SES)
- Skip-and-continue pattern for individual recipient email failures
- Email history tracking in `email_history` table (status, URL, frequency, timestamp)
- Cron job status tracking in `cron_jobs` table (pending → success/fail)
- Error logging to `error_log` table for all unhandled exceptions
- Encrypted token authentication (shared middleware)
- Pydantic v2 response models for serialization
- SQLAlchemy ORM models for `email_templates`, `email_recipient`, `email_history`, `settings`, `cron_jobs`, `kpi_history`, and `projects` tables
- Environment variable-based configuration for email provider, storage provider, and credentials
- Standardized response format following `BaseResponse` schema
- Structured JSON logging with trace_id for all report generation operations
- Layered architecture: Routes → Services → Repositories → Data Store

#### <u> 3.2 Outscope Details </u>

- Implementation of the external cron trigger (Azure Function Timer Trigger or AWS EventBridge) — only the API endpoint is in scope
- Email template CRUD management (templates are pre-seeded in the database)
- Email recipient CRUD management (managed via the Settings endpoints in a separate story)
- Settings CRUD management (managed via ZDAD-34 or a separate Settings story)
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

### <u> Section 4: Solution Diagrams </u>

#### <u> 4.1 UI/UX Design Diagram </u>

**Diagram Location:** N/A — This is a backend service with no UI component.

#### <u> 4.2 Architecture Design Diagram </u>

**Diagram Location:** `diagram/ZDAD-60_email_notification_service_flow.mmd`

#### <u> 4.3 Infrastructure Design Diagram </u>

**Diagram Location:** 
