## SOLDEF-ZDAD-57 - Fetch Project Pipeline Data From Azure DevOps and Display in Repository Page

### <u>Project Details</u>
- **Project ID:** ZDAD  
- **Project Name:** DevSecOps Jira Dashboard  

### <u>Story Details</u>
- **Story ID:** ZDAD-57  
- **Story Name:** Fetch Project Pipeline Data From Azure DevOps and Display in Repository Page  
- **Story Description:**  
  The DevSecOps Dashboard Projects module provides the ability to sync pipeline data from Azure DevOps (ADO) for applicable projects and their repositories into the DevSecOps database, and display detailed repository information including pipeline activity, commits, pull requests, security scans, and artifacts. The sync process fetches only the last 5 records per data type per repository and maintains a rolling window of 5 records per table per repository.
- **Scope:**  
  Implement the Repository Detail API (`GET /api/v1/repositories/{repository_id}`) and the ADO Sync API (`POST /api/v1/sync/ado`). The repository detail endpoint returns comprehensive information including header metadata, pipeline metrics, adoption timeline, pipeline activity, commits, pull requests, security scans, and artifacts. The sync endpoint triggers data ingestion from Azure DevOps, creates cron job tracking records, updates pipeline data tables, and refreshes KPI history. All service errors are logged to the `error_log` table.
- **Acceptance Criteria:**
  - The `GET /api/v1/repositories/{repository_id}` endpoint returns repository header, pipeline metrics, adoption timeline, pipeline activity, commits, pull requests, security scans, and artifacts for a valid repository UUID.
  - Invalid UUID format returns HTTP 400 with descriptive error message.
  - Non-existent repository returns HTTP 404 with message "Repository not found".
  - The `POST /api/v1/sync/ado` endpoint creates a cron job record with `sync_status = "pending"` and `type = "azure"`.
  - The sync process fetches only the last 5 records per data type per repository from Azure DevOps.
  - Existing records are updated with the latest data (only 5 records maintained per table per repository).
  - KPI history is updated after successful sync completion.
  - Cron job status is updated to "success" or "fail" based on sync outcome.
  - Optional `specialization_id` filters sync to a specific specialization.
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

The Repository Detail and ADO Sync APIs are core components of the DevSecOps Jira Dashboard backend that enable delivery leads and stakeholders to view comprehensive repository-level information and trigger data synchronization from Azure DevOps. The API exposes two endpoints: `GET /api/v1/repositories/{repository_id}` which returns a complete repository detail view including header metadata (name, client, onboarding date, overdue status, project type, parent project), pipeline metrics (total runs, success rate, last run days count), adoption timeline (4-step progression from kicked_off to adopted), and tabbed data sections (pipeline activity, commits, pull requests, security scans, artifacts); and `POST /api/v1/sync/ado` which triggers the ingestion of pipeline data from Azure DevOps for applicable projects, creating cron job tracking records, fetching the last 5 records per data type per repository, maintaining a rolling window of 5 records per table, updating repository aggregate metrics, and refreshing KPI history for the relevant specialization(s). The sync process identifies applicable projects (`is_applicable = TRUE`), resolves their repositories through the `devsecops_tickets` relationship, and uses the `ado_repo_id` field to map internal repositories to Azure DevOps repositories. Both endpoints require JWT Bearer token authentication and return standardized JSON responses following the `BaseResponse` schema. All unhandled exceptions are logged to the `error_log` database table for traceability and debugging. The implementation follows the layered architecture pattern: Routes → Services → Repositories → Schema, with Pydantic models for request/response validation and an external ADO client for Azure DevOps REST API communication.

#### <u> 1.2 Requirement Details </u>

- **ZDAD-57-FR01: Repository Detail — Header and Pipeline Metrics**
- **ZDAD-57-FR02: Repository Detail — Adoption Timeline**
- **ZDAD-57-FR03: Repository Detail — Pipeline Activity Tab**
- **ZDAD-57-FR04: Repository Detail — Commits Tab**
- **ZDAD-57-FR05: Repository Detail — Pull Requests Tab**
- **ZDAD-57-FR06: Repository Detail — Security Scans Tab**
- **ZDAD-57-FR07: Repository Detail — Artifacts Tab**
- **ZDAD-57-FR08: ADO Sync — Trigger and Cron Job Management**
- **ZDAD-57-FR09: ADO Sync — Data Ingestion and Record Management**
- **ZDAD-57-FR10: ADO Sync — KPI History Update**
- **ZDAD-57-FR11: Input Validation**
- **ZDAD-57-FR12: Error Logging**


##### <u> 1.2.1 ZDAD-57-FR01: Repository Detail — Header and Pipeline Metrics </u>

##### Description:
The system shall expose a `GET /api/v1/repositories/{repository_id}` endpoint that returns comprehensive detail information for a specific repository. The response includes a header section with repository metadata and a pipeline metrics section with aggregate run statistics.

##### Path Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_id` | UUID | Yes | Unique identifier of the repository |

##### Processing Logic — Header:
1. Validate `repository_id` is a valid UUID format. Return HTTP 400 if invalid.
2. Query the `repositories` table for the record with matching `repository_id` and `is_active = 1`. Return HTTP 404 if not found.
3. Resolve the parent project by joining `repositories` → `devsecops_tickets` (via `ticket_id`) → `projects` (via `project_id` or `sn_project_id`).
4. Determine `client` from the parent project's `client` field.
5. Determine `onboarding_date` from the `devsecops_tickets.requested_at` or `repositories.created_at` field.
6. Determine `closed_by` from the parent project's `completed_at` field (null if not completed).
7. Determine `project_type` by combining the specialization name and project type (format: "{specialization_name} · {project_type}").
8. Calculate `overdue` as the number of days since onboarding without reaching "adopted" status. Set to null if not overdue (within the at-risk threshold from settings).
9. Compose the `project` object with parent project `id` and `name`.

##### Processing Logic — Pipeline Metrics:
1. Count all active `pipeline_runs` records for the repository to get `total_runs`.
2. Calculate `success_rate` as the percentage of successful runs from the last 30 pipeline runs.
3. Determine `last_pipeline_run_at` from the most recent `pipeline_runs.triggered_at` value.
4. Calculate `last_pipeline_run` as the number of days since the last pipeline run (integer value, e.g., 5).

##### Response Structure — Header and Metrics:
```json
{
  "header": {
    "id": "880e8400-e29b-41d4-a716-446655440030",
    "name": "xenon-infra-core",
    "overdue": 3,
    "client": "Internal",
    "onboarding_date": "2026-02-27",
    "closed_by": "2026-04-13",
    "project_type": "Internal · Infrastructure",
    "project": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Project Xenon"
    }
  },
  "pipeline_metrics": {
    "total_runs": 142,
    "success_rate": 85.5,
    "last_pipeline_run": 5,
    "last_pipeline_run_at": "2026-05-07T10:30:00Z"
  }
}
```

##### Error Responses:
| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid UUID format for `repository_id` |
| 401 | Missing or invalid JWT Bearer token |
| 404 | Repository not found or inactive |
| 500 | Unexpected server error (logged to `error_log`) |

##### Acceptance Criteria:
- A valid `repository_id` returns the header with all fields populated (id, name, overdue, client, onboarding_date, closed_by, project_type, project).
- `overdue` is null when the repository is within the acceptable onboarding timeline.
- `overdue` is a positive integer representing days overdue when the repository exceeds the at-risk threshold.
- `closed_by` is null when the parent project has not been completed.
- `pipeline_metrics.total_runs` reflects the count of all active pipeline run records for the repository.
- `pipeline_metrics.success_rate` reflects the percentage of successful runs from the last 30 pipeline runs.
- `last_pipeline_run` is an integer representing the number of days since the last pipeline run; `last_pipeline_run_at` is an ISO 8601 timestamp.
- Both `last_pipeline_run` and `last_pipeline_run_at` are null when no pipeline runs exist.


##### <u> 1.2.2 ZDAD-57-FR02: Repository Detail — Adoption Timeline </u>

##### Description:
The system shall return an ordered list of adoption timeline steps for the repository. The timeline tracks the progression from initial onboarding to full adoption, with each step having a status (completed, in_progress, pending) and an optional completion date.

##### Timeline Steps:
| Step | Label | Completion Criteria |
|------|-------|---------------------|
| `kicked_off` | Kicked Off | Project onboarding date is set (always completed for existing repositories) |
| `pipeline_detected` | Pipeline Detected | A pipeline YAML file is detected in the repository (first pipeline run exists) |
| `first_run` | First Run | The first successful pipeline run is recorded |
| `adopted` | Adopted | Consistent pipeline usage is established (multiple successful runs over time) |

##### Processing Logic:
1. `kicked_off`: Always "completed" for existing repositories. `completed_at` = project's `onboarded_date`.
2. `pipeline_detected`: "completed" if at least one `pipeline_runs` record exists for the repository. `completed_at` = earliest `pipeline_runs.triggered_at`.
3. `first_run`: "completed" if at least one `pipeline_runs` record with `status = "passed"` exists. `completed_at` = earliest successful run's `triggered_at`. If pipeline runs exist but none passed, status is "in_progress".
4. `adopted`: "completed" if the repository has consistent usage (e.g., multiple successful runs). `completed_at` = date when adoption criteria were met. Otherwise "pending".
5. Steps are returned in order. A step can only be "in_progress" if all previous steps are "completed". A step is "pending" if any previous step is not "completed".

##### Response Structure:
```json
{
  "adoption_timeline": [
    { "step": "kicked_off", "label": "Kicked Off", "status": "completed", "completed_at": "2026-02-20" },
    { "step": "pipeline_detected", "label": "Pipeline Detected", "status": "completed", "completed_at": "2026-03-10" },
    { "step": "first_run", "label": "First Run", "status": "in_progress", "completed_at": null },
    { "step": "adopted", "label": "Adopted", "status": "pending", "completed_at": null }
  ]
}
```

##### Acceptance Criteria:
- The timeline always contains exactly 4 steps in the defined order.
- `completed_at` is an ISO 8601 date string for completed steps and null for non-completed steps.
- Steps follow sequential progression — no step can be "completed" if a prior step is not "completed".
- A repository with no pipeline runs returns: kicked_off=completed, pipeline_detected=in_progress, first_run=pending, adopted=pending.


##### <u> 1.2.3 ZDAD-57-FR03: Repository Detail — Pipeline Activity Tab </u>

##### Description:
The system shall return the active pipeline run records for the repository. Pipeline runs represent individual CI/CD pipeline executions fetched from Azure DevOps and stored in the `pipeline_runs` table. Only active records (`is_active = 1`) are returned, sorted by `triggered_at` descending (most recent first).

##### Processing Logic:
1. Query `pipeline_runs` table where `repository_id` matches and `is_active = 1`.
2. Sort results by `triggered_at` descending.
3. For each record, compute `duration` as a human-readable string from `duration_seconds` (e.g., "2m 14s", "45s", "1h 3m").
4. Map `triggered_at` to ISO 8601 format.

##### Response Structure:
```json
{
  "pipeline_activity": {
    "runs": [
      {
        "run_number": 142,
        "status": "passed",
        "branch": "main",
        "duration": "2m 14s",
        "triggered_at": "2026-05-07T10:30:00Z"
      }
    ]
  }
}
```

##### Field Definitions:
| Field | Type | Description |
|-------|------|-------------|
| `run_number` | Integer | Pipeline run number |
| `status` | String (enum) | Run status: `passed`, `failed`, `running`, `cancelled` |
| `branch` | String | Branch name the pipeline ran on |
| `duration` | String | Human-readable duration (computed from `duration_seconds`) |
| `triggered_at` | String (ISO 8601) | Timestamp when the pipeline run was triggered |

##### Acceptance Criteria:
- Only active pipeline run records are returned (`is_active = 1`).
- Records are sorted by `triggered_at` descending.
- `duration` is formatted as human-readable (e.g., "2m 14s" for 134 seconds).
- An empty `runs` array is returned when no pipeline runs exist for the repository.


##### <u> 1.2.4 ZDAD-57-FR04: Repository Detail — Commits Tab </u>

##### Description:
The system shall return the active commit records for the repository. Commits represent source code changes fetched from Azure DevOps and stored in the `commits` table. Only active records (`is_active = 1`) are returned, sorted by `committed_at` descending.

##### Processing Logic:
1. Query `commits` table where `repository_id` matches and `is_active = 1`.
2. Sort results by `committed_at` descending.
3. Abbreviate the commit `hash` to the first 6 characters for display.
4. Map `committed_at` to ISO 8601 format.

##### Response Structure:
```json
{
  "commits": {
    "commit_details": [
      {
        "hash": "478b98",
        "message": "feat: update pipeline configuration",
        "author": "Tom Walsh",
        "committed_at": "2026-05-07T09:15:00Z"
      }
    ]
  }
}
```

##### Field Definitions:
| Field | Type | Description |
|-------|------|-------------|
| `hash` | String | Abbreviated commit hash (first 6 characters) |
| `message` | String | Full commit message |
| `author` | String | Author name |
| `committed_at` | String (ISO 8601) | Timestamp of the commit |

##### Acceptance Criteria:
- Only active commit records are returned (`is_active = 1`).
- Records are sorted by `committed_at` descending.
- Commit hash is abbreviated to 6 characters.
- An empty `commit_details` array is returned when no commits exist for the repository.


##### <u> 1.2.5 ZDAD-57-FR05: Repository Detail — Pull Requests Tab </u>

##### Description:
The system shall return pull request data for the repository, including a summary of counts grouped by status (open, merged, declined) and a detailed list of active pull request records sorted by `updated_at` descending.

##### Processing Logic:
1. Query `pull_requests` table where `repository_id` matches and `is_active = 1`.
2. Compute summary counts by grouping records by `status` field.
3. Sort the detail records by `updated_at` descending.
4. Map `updated_at` to ISO 8601 format.

##### Response Structure:
```json
{
  "pull_requests": {
    "summary": {
      "open": 5,
      "merged": 12,
      "declined": 1
    },
    "pull_requests_details": [
      {
        "title": "Add DevSecOps pipeline template",
        "author": "Tom Walsh",
        "status": "open",
        "updated_at": "2026-05-11T14:20:00Z"
      }
    ]
  }
}
```

##### Field Definitions:
| Field | Type | Description |
|-------|------|-------------|
| `summary.open` | Integer | Count of pull requests with status "open" |
| `summary.merged` | Integer | Count of pull requests with status "merged" |
| `summary.declined` | Integer | Count of pull requests with status "declined" |
| `title` | String | Pull request title |
| `author` | String | Author name |
| `status` | String (enum) | PR status: `open`, `merged`, `declined` |
| `updated_at` | String (ISO 8601) | Timestamp of the last update |

##### Acceptance Criteria:
- Summary counts accurately reflect the number of active pull requests per status.
- Only active pull request records are returned in `pull_requests_details` (`is_active = 1`).
- Records are sorted by `updated_at` descending.
- Summary counts default to 0 when no pull requests exist for a given status.


##### <u> 1.2.6 ZDAD-57-FR06: Repository Detail — Security Scans Tab </u>

##### Description:
The system shall return security scan findings for the repository, grouped by scan type (SCA, SAST, DAST) with individual counts and a total findings count across all types.

##### Processing Logic:
1. Query `security_scans` table where `repository_id` matches and `is_active = 1`.
2. Group findings by `scan_type` and sum `findings_count` for each type.
3. Calculate `total_findings` as the sum of all findings across all scan types.
4. Map scan types to response keys: "SCA" → `sca`, "SAST" → `sast`, "DAST" → `dast`.

##### Response Structure:
```json
{
  "security_scans": {
    "total_findings": 21,
    "sca": { "count": 12 },
    "sast": { "count": 6 },
    "dast": { "count": 3 }
  }
}
```

##### Field Definitions:
| Field | Type | Description |
|-------|------|-------------|
| `total_findings` | Integer | Sum of all findings across all scan types |
| `sca.count` | Integer | Number of SCA (dependency vulnerability) findings |
| `sast.count` | Integer | Number of SAST (static analysis) findings |
| `dast.count` | Integer | Number of DAST (dynamic scan) findings |

##### Acceptance Criteria:
- `total_findings` equals the sum of `sca.count + sast.count + dast.count`.
- Only active security scan records are included (`is_active = 1`).
- Counts default to 0 when no findings exist for a scan type.
- The response always includes all three scan type keys (sca, sast, dast) even if counts are 0.


##### <u> 1.2.7 ZDAD-57-FR07: Repository Detail — Artifacts Tab </u>

##### Description:
The system shall return build artifact records associated with the repository's pipeline runs. Artifacts are linked to pipeline runs and include file metadata and download URLs.

##### Processing Logic:
1. Query `artifacts` table joined with `pipeline_runs` where `pipeline_runs.repository_id` matches and both `artifacts.is_active = 1` and `pipeline_runs.is_active = 1`.
2. Sort results by `artifacts.uploaded_at` descending.
3. Compute `size_label` as a human-readable file size from `size_bytes` (e.g., "4.2 MB", "512 KB").
4. Map `pipeline_runs.run_number` to `build_number`.
5. Map `uploaded_at` to ISO 8601 format as `created_at`.

##### Response Structure:
```json
{
  "artifacts": {
    "artifacts_details": [
      {
        "filename": "build-output.zip",
        "size_bytes": 4404019,
        "size_label": "4.2 MB",
        "build_number": 142,
        "created_at": "2026-05-07T10:32:00Z",
        "download_url": "https://storage.zeb.co/artifacts/880e8400/build-output.zip"
      }
    ]
  }
}
```

##### Field Definitions:
| Field | Type | Description |
|-------|------|-------------|
| `filename` | String | Name of the artifact file |
| `size_bytes` | Integer | File size in bytes |
| `size_label` | String | Human-readable file size (e.g., "4.2 MB") |
| `build_number` | Integer | Associated pipeline run number |
| `created_at` | String (ISO 8601) | Timestamp when the artifact was uploaded |
| `download_url` | String (URI) | Pre-signed URL to download the artifact |

##### Acceptance Criteria:
- Only active artifacts linked to active pipeline runs are returned.
- Records are sorted by `uploaded_at` descending.
- `size_label` is correctly formatted (bytes → KB → MB → GB as appropriate).
- `build_number` correctly maps to the parent pipeline run's `run_number`.
- An empty `artifacts_details` array is returned when no artifacts exist.


##### <u> 1.2.8 ZDAD-57-FR08: ADO Sync — Trigger and Cron Job Management </u>

##### Description:
The system shall expose a `POST /api/v1/sync/ado` endpoint that triggers the synchronization of pipeline data from Azure DevOps. Each sync operation is tracked via the `cron_jobs` table with status progression from "pending" to "success" or "fail".

##### Request Body (optional):
```json
{
  "specialization_id": "uuid or null"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `specialization_id` | UUID | No | UUID of the specialization to sync. Null or omitted syncs all specializations. |

##### Processing Logic:
1. Validate `specialization_id` is a valid UUID format if provided. Return HTTP 400 if invalid.
2. Create a new record in `cron_jobs` table:
   - `cron_id`: Auto-generated UUID
   - `specialization_id`: From request (or "all" if not provided)
   - `type`: "azure"
   - `sync_status`: "pending"
   - `created_at`: Current timestamp
   - `created_by`: "sync_ado_service"
3. Identify applicable projects by querying `projects` where `is_applicable = TRUE` and `is_active = 1`.
4. If `specialization_id` is provided, further filter by joining with `devsecops_tickets` where `specialization_id` matches.
5. Resolve repositories for each applicable project through `devsecops_tickets` → `repositories` relationship.
6. For each repository with a valid `ado_repo_id`, trigger data ingestion (FR09).
7. After all repositories are processed:
   - If no errors occurred: Update `cron_jobs.sync_status = "success"`.
   - If any errors occurred: Update `cron_jobs.sync_status = "fail"`.
8. Update `cron_jobs.modified_at` with current timestamp.
9. Return HTTP 200 with success response.

##### Response Structure (200):
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
| 400 | Invalid `specialization_id` UUID format |
| 401 | Missing or invalid JWT Bearer token |
| 500 | Unexpected server error (logged to `error_log`) |

##### Acceptance Criteria:
- A cron job record is created with `sync_status = "pending"` before sync begins.
- Only applicable projects (`is_applicable = TRUE`) are processed.
- When `specialization_id` is provided, only repositories linked to that specialization are synced.
- When `specialization_id` is null or omitted, all applicable repositories are synced.
- Cron job status is updated to "success" on successful completion.
- Cron job status is updated to "fail" if any errors occur during sync.
- The endpoint returns HTTP 200 regardless of individual repository sync failures (overall status tracked in cron_jobs).


##### <u> 1.2.9 ZDAD-57-FR09: ADO Sync — Data Ingestion and Record Management </u>

##### Description:
The system shall fetch the last 5 records per data type (pipeline runs, commits, pull requests, security scans, artifacts) from Azure DevOps for each repository and maintain a rolling window of exactly 5 records per table per repository. Existing records are soft-deleted and replaced with fresh data on each sync.

##### Processing Logic (per repository):
1. Use the `ado_repo_id` from the `repositories` table to identify the Azure DevOps repository.
2. Call the Azure DevOps REST API to fetch:
   - Last 5 pipeline runs (builds)
   - Last 5 commits
   - Last 5 pull requests
   - Latest security scan results (SCA, SAST, DAST)
   - Last 5 artifacts from the most recent pipeline run
3. For each data type:
   - Soft-delete existing active records for the repository by setting `is_active = 0` and `modified_at = NOW()`.
   - Insert the newly fetched records with `is_active = 1`.
4. Update the `repositories` table:
   - `pipeline_runs_count`: Total count of all pipeline runs (historical, not just last 5).
   - `success_rate`: Percentage of successful runs from the last 30 pipeline runs.
   - `last_run_at`: Timestamp of the most recent pipeline run.
   - `modified_at`: Current timestamp.

##### Azure DevOps API Calls:
| Data Type | ADO API Endpoint | Records Fetched |
|-----------|------------------|-----------------|
| Pipeline Runs | `GET /{org}/{project}/_apis/build/builds?definitions={pipelineId}&$top=5` | Last 5 builds |
| Commits | `GET /{org}/{project}/_apis/git/repositories/{repoId}/commits?$top=5` | Last 5 commits |
| Pull Requests | `GET /{org}/{project}/_apis/git/repositories/{repoId}/pullrequests?$top=5&status=all` | Last 5 PRs |
| Security Scans | Derived from pipeline run extensions or external scan tool API | Latest findings |
| Artifacts | `GET /{org}/{project}/_apis/build/builds/{buildId}/artifacts` | Artifacts from last run |

##### Data Mapping:
| ADO Field | Database Field | Table |
|-----------|---------------|-------|
| `build.buildNumber` | `run_number` | pipeline_runs |
| `build.result` | `status` (mapped: succeeded→passed, failed→failed, canceled→cancelled) | pipeline_runs |
| `build.sourceBranch` | `branch` (strip "refs/heads/" prefix) | pipeline_runs |
| `build.startTime` to `build.finishTime` | `duration_seconds` (computed difference) | pipeline_runs |
| `build.queueTime` | `triggered_at` | pipeline_runs |
| `commit.commitId` | `hash` | commits |
| `commit.comment` | `message` | commits |
| `commit.author.name` | `author` | commits |
| `commit.author.date` | `committed_at` | commits |
| `pr.title` | `title` | pull_requests |
| `pr.createdBy.displayName` | `author` | pull_requests |
| `pr.status` | `status` (mapped: active→open, completed→merged, abandoned→declined) | pull_requests |
| `pr.closedDate` or `pr.creationDate` | `updated_at` | pull_requests |

##### Acceptance Criteria:
- Only the last 5 records per data type are fetched from Azure DevOps.
- Existing active records are soft-deleted (`is_active = 0`) before inserting new records.
- After sync, exactly 5 (or fewer if ADO has fewer) active records exist per data type per repository.
- Repository aggregate fields (`pipeline_runs_count`, `success_rate`, `last_run_at`) are updated after sync.
- Repositories without a valid `ado_repo_id` are skipped (not an error).
- ADO API failures for individual repositories do not halt the entire sync process — errors are logged and the sync continues with remaining repositories.


##### <u> 1.2.10 ZDAD-57-FR10: ADO Sync — KPI History Update </u>

##### Description:
After successful data sync, the system shall create a new KPI history snapshot for each affected specialization. The KPI history tracks project counts by status and their changes compared to the previous snapshot.

##### Processing Logic:
1. After all repositories for a specialization are synced, query current project counts by status.
2. Retrieve the most recent `kpi_history` record for the specialization.
3. Calculate increase/decrease counts by comparing current counts with the previous snapshot.
4. Insert a new `kpi_history` record with:
   - `specialization_id`: The specialization being synced
   - `projects_count`: Total applicable projects
   - `projects_increase_count` / `projects_decrease_count`: Change from previous snapshot
   - `completed_count`, `inactive_count`, `at_risk_count`, `not_applicable_count`: Current counts per status
   - Corresponding increase/decrease fields for each status
   - `created_at`: Current timestamp
   - `created_by`: "sync_ado_service"

##### Acceptance Criteria:
- A new `kpi_history` record is created for each specialization after successful sync.
- Increase/decrease counts accurately reflect changes from the previous KPI snapshot.
- If no previous snapshot exists, increase/decrease counts are set to 0.
- KPI history is only updated when the sync completes successfully (not on failure).


##### <u> 1.2.11 ZDAD-57-FR11: Input Validation </u>

##### Description:
The system shall validate all incoming request data for both endpoints. Invalid inputs result in an HTTP 400 response with a descriptive error message.

##### Validation Rules — GET `/api/v1/repositories/{repository_id}`:
| Parameter | Rule | Error Message |
|-----------|------|---------------|
| `repository_id` | Must be a valid UUID format | "Invalid parameter: 'repository_id' must be a valid UUID" |

##### Validation Rules — POST `/api/v1/sync/ado`:
| Field | Rule | Error Message |
|-------|------|---------------|
| `specialization_id` | If provided, must be a valid UUID format | "Invalid parameter: 'specialization_id' must be a valid UUID" |

##### Error Response Format:
```json
{
  "status_code": 400,
  "status": "failed",
  "message": "Invalid parameter: 'repository_id' must be a valid UUID",
  "data": []
}
```

##### Acceptance Criteria:
- Invalid UUID format for `repository_id` returns HTTP 400 before any database query.
- Invalid UUID format for `specialization_id` returns HTTP 400 before sync begins.
- Valid requests with optional fields omitted are processed successfully.
- Pydantic validation errors are caught and transformed into the standardized error response format.


##### <u> 1.2.12 ZDAD-57-FR12: Error Logging </u>

##### Description:
The system shall log all unhandled exceptions occurring during repository detail retrieval or ADO sync operations to the `error_log` database table. This provides a persistent audit trail for debugging and incident investigation.

##### Error Log Table Fields:
- `error_id` — Auto-generated UUID primary key.
- `error_message` — The exception message text.
- `error_function` — The function name where the error occurred (e.g., "get_repository_detail", "sync_ado_data").
- `error_file` — The file path where the error originated (e.g., "src/services/repositories_service.py", "src/services/sync_ado_service.py").
- `stack_trace` — Full Python stack trace for debugging.
- `created_at` — Timestamp when the error was logged.
- `created_by` — "repositories_service" or "sync_ado_service".

##### Acceptance Criteria:
- All unhandled exceptions in both endpoints are captured and logged to `error_log`.
- The error log entry contains the function name, file name, error message, and stack trace.
- Error logging does not interfere with the error response returned to the client (non-blocking).
- HTTP 500 responses are always accompanied by an `error_log` entry.
- Validation errors (HTTP 400) and not-found errors (HTTP 404) are NOT logged to `error_log`.
- ADO API call failures during sync are logged individually without stopping the overall sync process.


#### <u> 1.3 Database Schema </u>

The following tables are directly involved in the Repository Detail and ADO Sync APIs (as defined in `design/er_diagram.mmd`):

##### repositories
| Column | Type | Constraints |
|--------|------|-------------|
| repository_id | UUID | PK |
| ticket_id | UUID | FK → devsecops_tickets.ticket_id |
| repository_name | VARCHAR | NOT NULL |
| ado_repo_id | VARCHAR | Azure DevOps repository identifier |
| pipeline_runs_count | INTEGER | DEFAULT 0 |
| success_rate | FLOAT | DEFAULT 0 |
| last_run_at | DATETIME | |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### pipeline_runs
| Column | Type | Constraints |
|--------|------|-------------|
| pipeline_run_id | UUID | PK |
| repository_id | UUID | FK → repositories.repository_id |
| run_number | INTEGER | NOT NULL |
| status | VARCHAR | NOT NULL (passed, failed, running, cancelled) |
| branch | VARCHAR | NOT NULL |
| duration_seconds | INTEGER | |
| triggered_at | DATETIME | NOT NULL |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### commits
| Column | Type | Constraints |
|--------|------|-------------|
| commit_id | UUID | PK |
| repository_id | UUID | FK → repositories.repository_id |
| hash | VARCHAR | NOT NULL |
| message | TEXT | NOT NULL |
| author | VARCHAR | NOT NULL |
| committed_at | DATETIME | NOT NULL |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### pull_requests
| Column | Type | Constraints |
|--------|------|-------------|
| pull_request_id | UUID | PK |
| repository_id | UUID | FK → repositories.repository_id |
| title | VARCHAR | NOT NULL |
| author | VARCHAR | NOT NULL |
| status | VARCHAR | NOT NULL (open, merged, declined) |
| updated_at | DATETIME | |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### security_scans
| Column | Type | Constraints |
|--------|------|-------------|
| security_scan_id | UUID | PK |
| repository_id | UUID | FK → repositories.repository_id |
| scan_type | VARCHAR | NOT NULL (SCA, SAST, DAST) |
| findings_count | INTEGER | DEFAULT 0 |
| description | VARCHAR | |
| scanned_at | DATETIME | NOT NULL |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

##### artifacts
| Column | Type | Constraints |
|--------|------|-------------|
| artifact_id | UUID | PK |
| pipeline_run_id | UUID | FK → pipeline_runs.pipeline_run_id |
| artifact_name | VARCHAR | NOT NULL |
| size_bytes | BIGINT | NOT NULL |
| url | TEXT | NOT NULL |
| uploaded_at | DATETIME | NOT NULL |
| created_at | DATETIME | |
| created_by | VARCHAR | |
| modified_at | DATETIME | |
| modified_by | VARCHAR | |
| is_active | INT | DEFAULT 1 |

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

##### kpi_history
| Column | Type | Constraints |
|--------|------|-------------|
| kpi_history_id | UUID | PK |
| specialization_id | UUID | FK → specializations.specialization_id |
| projects_count | INTEGER | DEFAULT 0 |
| projects_increase_count | INTEGER | DEFAULT 0 |
| projects_decrease_count | INTEGER | DEFAULT 0 |
| completed_count | INTEGER | DEFAULT 0 |
| completed_increase_count | INTEGER | DEFAULT 0 |
| completed_decrease_count | INTEGER | DEFAULT 0 |
| inactive_count | INTEGER | DEFAULT 0 |
| inactive_increase_count | INTEGER | DEFAULT 0 |
| inactive_decrease_count | INTEGER | DEFAULT 0 |
| at_risk_count | INTEGER | DEFAULT 0 |
| at_risk_increase_count | INTEGER | DEFAULT 0 |
| at_risk_decrease_count | INTEGER | DEFAULT 0 |
| not_applicable_count | INTEGER | DEFAULT 0 |
| not_applicable_increase_count | INTEGER | DEFAULT 0 |
| not_applicable_decrease_count | INTEGER | DEFAULT 0 |
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
- `repositories.ticket_id` → `devsecops_tickets.ticket_id` (repositories belong to tickets)
- `devsecops_tickets.specialization_id` → `specializations.specialization_id` (links tickets to specializations)
- `devsecops_tickets.project_id` → `projects.project_id` (direct project link, nullable)
- `devsecops_tickets.sn_project_id` → `projects.sn_project_id` (links tickets to projects via ServiceNow ID)
- `pipeline_runs.repository_id` → `repositories.repository_id` (pipeline runs belong to repositories)
- `commits.repository_id` → `repositories.repository_id` (commits belong to repositories)
- `pull_requests.repository_id` → `repositories.repository_id` (PRs belong to repositories)
- `security_scans.repository_id` → `repositories.repository_id` (scans belong to repositories)
- `artifacts.pipeline_run_id` → `pipeline_runs.pipeline_run_id` (artifacts belong to pipeline runs)
- `kpi_history.specialization_id` → `specializations.specialization_id` (KPI tracked per specialization)


#### <u> 1.4 Project Artifacts </u>

- `api/openapi.yaml` — Full OpenAPI 3.0.3 specification defining the `GET /api/v1/repositories/{repository_id}` and `POST /api/v1/sync/ado` endpoints, request/response schemas (`RepositoryDetailSuccessResponse`, `RepositoryDetailData`, `RepositoryHeader`, `PipelineMetrics`, `AdoptionTimeline`, `PipelineActivitySection`, `CommitsSection`, `PullRequestsSection`, `SecurityScansSection`, `ArtifactsSection`, `SyncSuccessResponse`), and error response formats.
- `design/er_diagram.mmd` — Mermaid ER diagram showing all database tables and relationships including `repositories`, `pipeline_runs`, `commits`, `pull_requests`, `security_scans`, `artifacts`, `projects`, `devsecops_tickets`, `kpi_history`, `cron_jobs`, and `error_log`.
- `design/requirements.md` — Detailed requirements document for ZDAD-57 with acceptance criteria, technical details, and affected components.

#### <u> 1.5 Dependencies </u>

- **Python 3.12+** — Runtime environment
- **FastAPI** — Web framework for building the REST API
- **SQLAlchemy** — ORM for PostgreSQL database access (queries on `repositories`, `pipeline_runs`, `commits`, `pull_requests`, `security_scans`, `artifacts`, `kpi_history`, `cron_jobs`, `error_log`)
- **Pydantic v2** — Request/response model validation and serialization
- **PostgreSQL** — Primary database storing all repository and pipeline data
- **python-jose / PyJWT** — JWT token decoding and validation (shared with existing auth middleware)
- **Uvicorn** — ASGI server for running the FastAPI application
- **httpx** — Async HTTP client for Azure DevOps REST API calls
- **Azure DevOps REST API** — External data source for pipeline runs, commits, pull requests, security scans, and artifacts (authenticated via PAT or OAuth)
- **humanize** — Library for generating human-readable time strings (e.g., "5 days ago") and file sizes (e.g., "4.2 MB")



### <u> Section 2: Non Functional Requirements </u>

### 2.1 Infrastructure and Deployment

#### <u> 2.1.1 Overview </u>

The Repository Detail and ADO Sync APIs are deployed as part of the existing DevSecOps Jira Dashboard backend application on Azure App Service. No separate service or infrastructure is required — the repository and sync routes are registered within the existing FastAPI application alongside the Overview API, Projects API, Settings API, and ServiceNow Sync routes. The application is a Python FastAPI service running on Uvicorn, packaged as a Docker container image and deployed to Azure App Service. The service connects to the same Azure Database for PostgreSQL instance and shares the same JWT middleware, error handling, and logging infrastructure established in ZDAD-34. The ADO Sync endpoint requires outbound HTTPS connectivity to Azure DevOps REST APIs, authenticated via Personal Access Token (PAT) stored securely in environment variables. Environment-specific configurations are managed through Azure App Service application settings and environment variables, ensuring no secrets are hardcoded in the application code. The sync operation may be long-running depending on the number of repositories; it executes synchronously within the request lifecycle but is designed to handle partial failures gracefully without blocking the response.

#### <u> 2.1.2 Requirement Details </u>

- **ZDAD-57-NFR01: Shared Deployment with Existing Application**
- **ZDAD-57-NFR02: Environment Configuration**
- **ZDAD-57-NFR03: Health Check Compatibility**

##### <u> 2.1.2.1 ZDAD-57-NFR01: Shared Deployment with Existing Application </u>

##### Description:
The Repository Detail and ADO Sync API endpoints shall be deployed as additional routes within the existing FastAPI application. No separate service or deployment is required. The routes are registered via dedicated `APIRouter` instances with appropriate prefixes and share the same database connection pool, JWT middleware, and error handling infrastructure.

##### Deployment Configuration:
- **Runtime:** Python 3.12+ container image
- **ASGI Server:** Uvicorn with configurable workers
- **Port:** Application listens on port 8080 (configurable via `PORT` environment variable)
- **Route Registration:** Repository routes added via `APIRouter` with prefix `/api/v1`. Sync routes added via existing sync `APIRouter`.
- **Database:** Uses the same SQLAlchemy engine and session factory.
- **Authentication:** Uses the same JWT middleware.
- **Error Handling:** Uses the same global exception handler that logs to `error_log`.
- **External Connectivity:** Requires outbound HTTPS access to `dev.azure.com` for ADO API calls.

##### Acceptance Criteria:
- The repository detail and sync/ado endpoints are accessible after deployment without additional infrastructure changes.
- Existing endpoints (Overview, Projects, Filters, Settings, ServiceNow Sync) continue to function without disruption.
- The application starts successfully with the new routes registered.
- Health check and readiness endpoints remain unaffected.
- Outbound connectivity to Azure DevOps APIs is available from the deployment environment.

##### <u> 2.1.2.2 ZDAD-57-NFR02: Environment Configuration </u>

##### Description:
All application configuration shall be managed through environment variables. The Repository Detail and ADO Sync APIs use the same environment variables as the existing application, with additional variables required for Azure DevOps API authentication.

##### Required Environment Variables:
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT token validation | Yes |
| `JWT_ALGORITHM` | Algorithm used for JWT (default: HS256) | No |
| `APP_ENV` | Environment identifier (development, staging, production) | Yes |
| `LOG_LEVEL` | Application log level (default: INFO) | No |
| `PORT` | Application port (default: 8080) | No |
| `ADO_ORG_URL` | Azure DevOps organization URL (e.g., https://dev.azure.com/{org}) | Yes |
| `ADO_PAT` | Azure DevOps Personal Access Token for API authentication | Yes |
| `ADO_PROJECT` | Default Azure DevOps project name | Yes |

##### Acceptance Criteria:
- The application fails to start with a clear error message if `ADO_ORG_URL` or `ADO_PAT` are not configured.
- The existing `DATABASE_URL` is reused for all repository and sync-related database operations.
- The existing JWT configuration is reused for endpoint authentication.
- ADO credentials are never logged or exposed in error responses.

##### <u> 2.1.2.3 ZDAD-57-NFR03: Health Check Compatibility </u>

##### Description:
The addition of Repository Detail and ADO Sync routes shall not affect the existing health check (`/health`) and readiness (`/ready`) endpoints. The readiness endpoint continues to validate database connectivity, which implicitly covers the repository-related tables.

##### Acceptance Criteria:
- `GET /health` continues to return HTTP 200 with `{"status": "healthy"}`.
- `GET /ready` continues to validate database connectivity.
- Adding new routes does not increase application startup time significantly.
- ADO API connectivity is NOT checked in the readiness probe (external dependency, may be temporarily unavailable).

#### <u> 2.1.3 Project Artifacts </u>

- `api/openapi.yaml` — API specification including repository detail and sync endpoints
- `design/er_diagram.mmd` — Database schema reference for repository-related tables



### 2.2 Architecture and System Design

#### <u> 2.2.1 Security and Compliance </u>

##### JWT Authentication:
All Repository Detail and ADO Sync API endpoints require a valid JWT Bearer token in the `Authorization` header. The middleware validates the token signature, expiration, and required claims before allowing the request to proceed to the route handler. Invalid or expired tokens result in an HTTP 401 Unauthorized response.

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

##### Azure DevOps API Security:
- ADO Personal Access Token (PAT) is stored as an environment variable, never hardcoded.
- PAT is transmitted only over HTTPS to Azure DevOps endpoints.
- PAT is never logged, included in error responses, or exposed in any output.
- API calls use the minimum required scope (read-only access to builds, code, and work items).

#### <u> 2.2.2 System Performance </u>

##### Database Query Optimization:
- The repository detail endpoint uses efficient JOINs between `repositories`, `devsecops_tickets`, `projects`, and `specializations` tables for header resolution.
- Database indexes are maintained on frequently queried columns: `repositories.repository_id`, `repositories.ticket_id`, `pipeline_runs.repository_id`, `commits.repository_id`, `pull_requests.repository_id`, `security_scans.repository_id`, `artifacts.pipeline_run_id`.
- Each tab section (pipeline activity, commits, PRs, scans, artifacts) is queried independently, allowing parallel execution if needed.
- Only active records (`is_active = 1`) are queried, reducing result set size.
- SQLAlchemy connection pooling is configured to reuse database connections efficiently.

##### ADO Sync Performance:
- The sync process fetches only the last 5 records per data type, minimizing API call payload.
- Repositories without a valid `ado_repo_id` are skipped immediately, avoiding unnecessary API calls.
- Bulk insert operations are used where possible to minimize database round-trips during sync.
- The `httpx` async client enables concurrent ADO API calls for different data types within the same repository.

##### Response Efficiency:
- The repository detail endpoint returns all sections in a single response, eliminating multiple round-trips.
- Human-readable fields (duration, file size labels) are computed server-side to reduce client processing.

#### <u> 2.2.3 Availability and Reliability </u>

##### Error Resilience:
- All unhandled exceptions are caught by the global exception handler that returns HTTP 500 and logs the error to the `error_log` table.
- Database connection failures are handled gracefully with appropriate error responses.
- The ADO sync process handles individual repository failures without halting the entire sync — errors are logged per repository and the process continues.
- If the Azure DevOps API is temporarily unavailable, the sync fails gracefully with appropriate error logging and cron job status update.

##### Data Consistency:
- The sync process uses database transactions for each repository's data update — if inserting new records fails, the soft-delete of old records is rolled back.
- The cron job status is updated as the final step, ensuring it accurately reflects the sync outcome.
- KPI history is only updated after all repository syncs complete successfully.

##### Deployment Reliability:
- Azure App Service provides built-in auto-restart on application crashes.
- Health check endpoints enable Azure to detect and replace unhealthy instances.
- Both APIs are stateless — any instance can serve any request.

#### <u> 2.2.4 Cost Efficiency </u>

##### Resource Optimization:
- The Repository Detail and ADO Sync APIs add minimal overhead to the existing application — no additional infrastructure or services are required.
- Database queries use indexed columns for efficient lookups.
- The sync process fetches only 5 records per data type, minimizing Azure DevOps API usage and associated rate limit consumption.
- Soft-delete approach avoids expensive DELETE operations and maintains audit trail without additional storage overhead.
- SQLAlchemy connection pooling minimizes the number of active database connections.
- The sync endpoint is designed to be triggered on-demand or via scheduled cron, not continuously polling.

#### <u> 2.2.5 Traceability and Observability </u>

##### Structured Logging:
- All application logs use JSON-formatted structured logging with fields: `timestamp`, `level`, `logger`, `filename`, `line_number`, `message`.
- Each request is assigned a `trace_id` for end-to-end request tracing.
- Log levels: DEBUG for development, INFO for production request/response logging, ERROR for exceptions.

##### Error Persistence:
- All application errors are persisted to the `error_log` database table with full context (function name, file name, stack trace).
- Error log entries include `created_at` timestamp and `created_by` identifier for audit purposes.

##### Sync Operation Logging:
- Each sync operation is tracked in the `cron_jobs` table with status progression (pending → success/fail).
- Individual repository sync outcomes are logged at INFO level with repository_id and data counts.
- ADO API call failures are logged at ERROR level with the repository_id, API endpoint, and error details.
- Sync start and completion times are logged for performance monitoring.

##### Request Logging:
- Incoming requests are logged at INFO level with method, path, and parameters.
- Response status codes and latency are logged for monitoring purposes.
- Sensitive data (JWT tokens, ADO PAT) is never included in log output.



### <u> Section 3: In Scope and Out Scope </u>

#### <u> 3.1 Inscope Details </u>

- Implementation of `GET /api/v1/repositories/{repository_id}` endpoint returning comprehensive repository details
- Repository header metadata: id, name, overdue days, client, onboarding date, closed by date, project type, parent project reference
- Pipeline metrics calculation: total runs count, success rate, last pipeline run days count, last pipeline run timestamp
- Adoption timeline with 4 sequential steps (kicked_off, pipeline_detected, first_run, adopted) with status and completion dates
- Pipeline activity tab: active pipeline run records with run_number, status, branch, duration, triggered_at
- Commits tab: active commit records with abbreviated hash, message, author, committed_at
- Pull requests tab: summary counts (open, merged, declined) and active PR records with title, author, status, updated_at
- Security scans tab: total findings count and breakdown by scan type (SCA, SAST, DAST)
- Artifacts tab: active artifact records with filename, size_bytes, size_label, build_number, created_at, download_url
- Implementation of `POST /api/v1/sync/ado` endpoint for triggering Azure DevOps data synchronization
- Cron job creation and status management (pending → success/fail) in `cron_jobs` table
- Fetching last 5 records per data type (pipeline runs, commits, pull requests, security scans, artifacts) from Azure DevOps REST API
- Soft-delete and re-insert strategy for maintaining rolling window of 5 records per table per repository
- Repository aggregate field updates (pipeline_runs_count, success_rate, last_run_at)
- KPI history snapshot creation after successful sync
- Optional specialization-based filtering for targeted sync operations
- Azure DevOps REST API client implementation (`src/client/ado_client.py`) with PAT authentication
- Data mapping from Azure DevOps API response formats to internal database schema
- JWT Bearer token authentication for both endpoints (shared middleware)
- UUID format validation with descriptive HTTP 400 error messages
- Repository existence validation with HTTP 404 for non-existent repositories
- Standardized response format following `BaseResponse` schema
- Error handling with HTTP 400, 401, 404, and 500 responses
- Error logging to the `error_log` database table for all unhandled exceptions
- Layered architecture implementation: Route → Service → Repository → Schema → Client
- Pydantic v2 models for request/response validation and serialization
- SQLAlchemy ORM for all database operations (no raw SQL)
- Unit tests covering positive and negative cases for both endpoints

#### <u> 3.2 Outscope Details </u>

- Azure DevOps API credential setup and PAT provisioning (assumes credentials are pre-configured)
- Azure DevOps webhook integration for real-time push notifications
- ServiceNow project sync operations (covered in ZDAD-58)
- Settings and notification configuration (covered in ZDAD-59)
- Overview dashboard metrics and KPI calculations (covered in ZDAD-34)
- Projects list and project actions (covered in ZDAD-48)
- Email notification delivery and report generation
- Scheduled/automated cron job execution (only manual trigger via API is in scope)
- User management and role-based access control beyond JWT validation
- Frontend/UI implementation
- Database migration scripts (tables are assumed to be pre-provisioned)
- Load testing and performance benchmarking
- CI/CD pipeline configuration
- Azure DevOps OAuth flow implementation (PAT-based auth is used)
- Historical data backfill beyond the last 5 records per data type
- Real-time pipeline status streaming or WebSocket notifications


### <u> Section 4: Solution Diagrams </u>

#### <u> 4.1 UI/UX Design Diagram </u>

**Diagram Location:** Refer to the Repository Detail Page UI mockups (provided separately)

#### <u> 4.2 Architecture Design Diagram </u>

**Diagram Location:** `design/er_diagram.mmd`

#### <u> 4.3 Infrastructure Design Diagram </u>

**Diagram Location:** N/A (shared infrastructure with existing ZDAD-34 deployment)
