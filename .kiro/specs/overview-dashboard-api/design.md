# Design Document: Overview Dashboard API

## Overview

The Overview Dashboard API is the backend data source for the DevSecOps Jira Dashboard landing page (ZDAD-34). It provides two authenticated endpoints — `GET /api/v1/overview` for consolidated KPI metrics, status distribution, and attention banner data, and `GET /api/v1/filters` for filter dropdown options. The API is built with Python FastAPI, SQLAlchemy async ORM, Pydantic v2, and PostgreSQL. It reads pre-computed KPI data from the `kpi_history` table (populated by an external ADO Azure Sync cron), derives trends from increase/decrease columns, computes status distribution from the `projects`/`statuses` tables, and generates attention banners based on at-risk counts. All endpoints (except health checks) require encrypted token authentication with Jira email validation.

## Architecture

The application follows a layered architecture with unidirectional dependencies:

```
Client Request
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Middleware Layer (src/middleware/)              │
│  - Auth middleware: token decryption + Jira     │
│    email validation                             │
│  - Request ID (trace_id) injection              │
│  - Global exception handler                     │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Route Layer (src/routes/)                      │
│  - overview_route.py: GET /api/v1/overview      │
│  - filter_route.py: GET /api/v1/filters         │
│  - default_route.py: /health, /ready            │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Service Layer (src/services/)                  │
│  - overview_service.py: KPI aggregation, trend  │
│    derivation, status distribution, banner      │
│  - filter_service.py: specializations, clients, │
│    statuses retrieval                           │
│  - dependencies.py: DI configuration            │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Repository Layer (src/repositories/)           │
│  - kpi_history_repository.py                    │
│  - project_repository.py                        │
│  - specialization_repository.py                 │
│  - status_repository.py                         │
│  - error_log_repository.py                      │
│  - schema/ (SQLAlchemy ORM models)              │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  PostgreSQL Database                            │
└─────────────────────────────────────────────────┘
```

**Layer Communication Rules:**
- Routes → Services → Repositories → Database (never skip layers)
- Middleware intercepts all requests before reaching routes
- Dependency injection wires service/repository instances via `src/services/dependencies.py`

**Technology Stack:**
- FastAPI with async support (uvicorn ASGI server)
- Python 3.12+ with modern type hint syntax
- SQLAlchemy 2.0 async ORM with `asyncpg` driver
- Pydantic v2 for request/response validation
- httpx for async HTTP calls (Jira API)
- structlog for structured JSON logging
- uv for dependency management

**File Structure:**
```
src/
├── __init__.py
├── settings.py
├── routes/
│   ├── __init__.py
│   ├── default_route.py
│   ├── overview_route.py
│   └── filter_route.py
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py
├── services/
│   ├── __init__.py
│   ├── dependencies.py
│   ├── overview_service.py
│   └── filter_service.py
├── repositories/
│   ├── __init__.py
│   ├── kpi_history_repository.py
│   ├── project_repository.py
│   ├── specialization_repository.py
│   ├── status_repository.py
│   ├── error_log_repository.py
│   └── schema/
│       ├── __init__.py
│       ├── base.py
│       ├── kpi_history.py
│       ├── specialization.py
│       ├── project.py
│       ├── status.py
│       ├── devsecops_ticket.py
│       ├── setting.py
│       └── error_log.py
├── models/
│   ├── __init__.py
│   ├── base_response.py
│   ├── overview_models.py
│   ├── filter_models.py
│   └── query_params.py
├── client/
│   ├── __init__.py
│   └── jira_client.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── exceptions/
│       ├── __init__.py
│       ├── error_codes.py
│       ├── exceptions.py
│       └── error_responses.py
├── migrations/
│   └── create_tables.sql
└── tests/
    ├── __init__.py
    ├── routes/
    ├── services/
    ├── repositories/
    └── middleware/
main.py
```

## Components and Interfaces

### 1. Settings & Configuration (`src/settings.py`)

Pydantic Settings class loaded once at startup with `@lru_cache` singleton pattern.

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    TOKEN_PRIVATE_KEY: str
    JIRA_BASE_URL: str
    JIRA_API_TOKEN: str
    model_config = ConfigDict(env_file=".env")
```

**Startup Validation:**
- `DATABASE_URL` must match `postgresql://` or `postgresql+asyncpg://` with host, port, database
- `JIRA_BASE_URL` must start with `https://`
- `TOKEN_PRIVATE_KEY` must be at least 10 characters
- Missing/empty variables → non-zero exit with error to stderr

**Constants (defined outside Settings class):**
- `PERIOD_DAYS_MAP`: Maps period enum values to day counts (7, 30, 90)
- `SEVERITY_CRITICAL_THRESHOLD = 5`
- `FILTER_CACHE_MAX_AGE = 3600`
- `JIRA_VALIDATION_TIMEOUT = 10`
- `OVERVIEW_SERVICE_IDENTIFIER = "overview_service"`
- `MAX_SPECIALIZATION_FILTER_COUNT = 50`
- `CLIENT_UUID_NAMESPACE`: Fixed UUID namespace for deterministic client ID generation

### 2. Authentication Middleware (`src/middleware/auth_middleware.py`)

**Interface:**
- Intercepts all requests except `/health`, `/ready`, `/docs`, `/openapi.json`
- Extracts `Authorization: Bearer <token>` header
- Decrypts token using `TOKEN_PRIVATE_KEY`
- Extracts email from decrypted payload
- Validates email via Jira REST API (10s timeout)
- On success: attaches email to `request.state.user_email`
- On failure: returns 401 BaseResponse

**Error Messages (all return 401):**
- Missing token: "Authentication token is missing or expired"
- Decryption failure: "Authentication failed or user not found in Jira"
- Empty email: "Authentication failed or user not found in Jira"
- Jira validation failure: "Authentication failed or user not found in Jira"

### 3. Jira Client (`src/client/jira_client.py`)

**Interface:**
```python
class JiraClient:
    async def validate_email(self, email: str) -> bool
```
- Calls `GET {JIRA_BASE_URL}/rest/api/2/user/search?username={email}`
- Uses `JIRA_API_TOKEN` for authentication
- 10-second timeout
- Returns `True` if user found, `False` otherwise

### 4. Overview Route (`src/routes/overview_route.py`)

**Interface:**
```python
@router.get("/overview")
async def get_overview(
    period: str | None = Query(default=None),
    specialization: str | None = Query(default=None),
    overview_service: OverviewService = Depends(get_overview_service),
) -> BaseResponse
```

### 5. Filter Route (`src/routes/filter_route.py`)

**Interface:**
```python
@router.get("/filters")
async def get_filters(
    filter_service: FilterService = Depends(get_filter_service),
) -> BaseResponse
```
- Sets `Cache-Control: max-age=3600` response header

### 6. Overview Service (`src/services/overview_service.py`)

**Interface:**
```python
class OverviewService:
    def __init__(self, kpi_repo: KpiHistoryRepository, project_repo: ProjectRepository,
                 specialization_repo: SpecializationRepository)

    async def get_overview(self, period: str | None, specialization: str | None) -> OverviewData
```

**Internal Logic:**

*Period Validation:*
- `None` → defaults to `"last_week"`
- Valid enum value → accepted
- Invalid value → raises `InvalidParameterError` (HTTP 400)
- Empty string → raises `InvalidParameterError` (HTTP 400)
- Period validated BEFORE specialization (fail fast)

*Specialization Parsing:*
- `None` or empty string → no filter (all specializations)
- CSV string → split by comma, trim whitespace, limit to 50 IDs
- All invalid IDs → treated as no filter (return all)
- Mix of valid/invalid → ignore invalid, use valid only

*Trend Derivation (per metric):*
```python
def _derive_trend(increase_count: int, decrease_count: int) -> tuple[str | None, int]:
    if increase_count > 0:
        return ("increase", increase_count)
    elif decrease_count > 0:
        return ("decrease", decrease_count)
    else:
        return ("flat", 0)
```

*KPI Aggregation (no filter):*
- Get most recent `kpi_history` record per active specialization within period window
- Sum all `{metric}_count` values across records
- Sum all `{metric}_increase_count` and `{metric}_decrease_count` values
- Apply trend derivation to summed increase/decrease

*KPI Aggregation (with filter):*
- Get most recent `kpi_history` record per matching specialization within period
- If no records found → all counts = 0, all trends = null, all changes = 0
- Otherwise sum and derive trends as above

*Status Distribution:*
- Join `projects` with `statuses`, group by status, count active projects
- When specialization filter applied: only count projects with matching `devsecops_tickets`
- Calculate percentage: `(count / total) * 100` rounded to 1 decimal
- If total = 0: all percentages = 0.0
- Include all active statuses (even with count 0)
- Sort alphabetically by status name (ascending)

*Attention Banner:*
- `at_risk_count >= 5` → severity = "critical"
- `1 <= at_risk_count <= 4` → severity = "warning"
- `at_risk_count == 0` → severity = "info"
- Message includes numeric count when > 0

### 7. Filter Service (`src/services/filter_service.py`)

**Interface:**
```python
class FilterService:
    def __init__(self, specialization_repo: SpecializationRepository,
                 project_repo: ProjectRepository, status_repo: StatusRepository)

    async def get_filters(self) -> FiltersData
```

**Internal Logic:**
- Specializations: query `specializations` where `is_active = 1`, map to `{id, name}`
- Clients: query distinct non-null, non-empty `client` from `projects` where `is_active = 1`, generate UUID v5 per client name using fixed namespace
- Statuses: query `statuses` where `is_active = 1`, map to `{id, name}`
- All arrays sorted alphabetically by `name` (case-insensitive)
- Empty categories return `[]`

### 8. KPI History Repository (`src/repositories/kpi_history_repository.py`)

**Interface:**
```python
class KpiHistoryRepository:
    async def get_latest_by_specializations(
        self, specialization_ids: list[UUID] | None, period_days: int
    ) -> list[KpiHistory]
```

**Query Strategy:**
- Uses `ROW_NUMBER() OVER (PARTITION BY specialization_id ORDER BY created_at DESC)` window function
- Filters to `created_at >= NOW() - interval '{period_days} days'`
- Filters to `is_active = 1`
- Joins with `specializations` where `is_active = 1`
- When `specialization_ids` provided: adds `WHERE specialization_id IN (...)`
- Returns only `row_number = 1` records (most recent per specialization)

### 9. Project Repository (`src/repositories/project_repository.py`)

**Interface:**
```python
class ProjectRepository:
    async def get_status_distribution(self, specialization_ids: list[UUID] | None) -> list[dict]
    async def get_distinct_clients(self) -> list[str]
```

**Status Distribution Query:**
- LEFT JOIN `statuses` → `projects` (to include statuses with 0 projects)
- When specialization filter: additionally JOIN `devsecops_tickets` with matching `specialization_id`
- Group by `status_name`, count distinct `project_id`
- Order by `status_name ASC`

### 10. Error Log Repository (`src/repositories/error_log_repository.py`)

**Interface:**
```python
class ErrorLogRepository:
    async def log_error(
        self, error_message: str, error_function: str,
        error_file: str, stack_trace: str, created_by: str
    ) -> None
```
- Truncates `error_message` and `stack_trace` to 65,535 characters
- Non-blocking (called via `asyncio.create_task`)
- 10-second timeout; abandoned if exceeded

### 11. Dependency Injection (`src/services/dependencies.py`)

```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]
def get_kpi_history_repository(session) -> KpiHistoryRepository
def get_project_repository(session) -> ProjectRepository
def get_specialization_repository(session) -> SpecializationRepository
def get_status_repository(session) -> StatusRepository
def get_overview_service(...) -> OverviewService
def get_filter_service(...) -> FilterService
```

### 12. Pydantic Response Models (`src/models/`)

**BaseResponse:**
```python
class BaseResponse(BaseModel):
    status_code: int
    status: Literal["success", "failed", "error"]
    message: str = Field(max_length=256)
    data: Any
```

**KpiTile:**
```python
class KpiTile(BaseModel):
    count: int = Field(ge=0)
    trend: Literal["increase", "decrease", "flat"] | None
    change: int = Field(ge=0)
```

**OverviewMetrics:**
```python
class OverviewMetrics(BaseModel):
    total_projects: KpiTile
    completed: KpiTile
    active: KpiTile
    inactive: KpiTile
    at_risk: KpiTile
    not_applicable: KpiTile
```

**StatusDistribution:**
```python
class StatusBreakdownItem(BaseModel):
    status: str
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)

class StatusDistribution(BaseModel):
    total: int = Field(ge=0)
    breakdown: list[StatusBreakdownItem]
```

**AttentionBanner:**
```python
class AttentionBanner(BaseModel):
    message: str = Field(max_length=200)
    at_risk_count: int = Field(ge=0)
    severity: Literal["critical", "warning", "info"]
```

**FilterItem / FiltersData:**
```python
class FilterItem(BaseModel):
    id: str
    name: str

class FiltersData(BaseModel):
    specializations: list[FilterItem]
    clients: list[FilterItem]
    statuses: list[FilterItem]
```

## Data Models

### Database Tables (SQLAlchemy ORM in `src/repositories/schema/`)

| Model | Table | Primary Key | Key Relationships |
|-------|-------|-------------|-------------------|
| KpiHistory | `kpi_history` | `kpi_history_id` (UUID) | FK → `specializations.specialization_id` |
| Specialization | `specializations` | `specialization_id` (UUID) | — |
| Project | `projects` | `project_id` (UUID) | FK → `statuses.status_id` |
| Status | `statuses` | `status_id` (UUID) | — |
| DevsecopsTicket | `devsecops_tickets` | `ticket_id` (UUID) | FK → `specializations.specialization_id`, FK → `projects.sn_project_id` |
| Setting | `settings` | `setting_id` (UUID) | FK → `specializations.specialization_id` |
| ErrorLog | `error_log` | `error_id` (UUID) | — |

### KpiHistory Fields (core data source)

| Column | Type | Description |
|--------|------|-------------|
| `projects_count` | INTEGER | Total project count for specialization |
| `projects_increase_count` | INTEGER | Increase from prior period |
| `projects_decrease_count` | INTEGER | Decrease from prior period |
| `completed_count` | INTEGER | Completed projects count |
| `completed_increase_count` / `completed_decrease_count` | INTEGER | Trend data |
| `active_count` | INTEGER | Active projects count |
| `active_increase_count` / `active_decrease_count` | INTEGER | Trend data |
| `inactive_count` | INTEGER | Inactive projects count |
| `inactive_increase_count` / `inactive_decrease_count` | INTEGER | Trend data |
| `at_risk_count` | INTEGER | At-risk projects count |
| `at_risk_increase_count` / `at_risk_decrease_count` | INTEGER | Trend data |
| `not_applicable_count` | INTEGER | Not applicable projects count |
| `not_applicable_increase_count` / `not_applicable_decrease_count` | INTEGER | Trend data |
| `specialization_id` | UUID | FK to specializations |
| `created_at` | TIMESTAMP | Record creation time (used for period filtering) |
| `is_active` | INT | Soft delete flag |

### Pydantic Response Models (`src/models/`)

**BaseResponse** — Standard envelope for all API responses:
- `status_code: int` — HTTP status code
- `status: Literal["success", "failed", "error"]` — Response category
- `message: str` (max 256 chars) — Human-readable message
- `data: Any` — Payload (object for success, empty array for errors)

**KpiTile** — Single KPI metric card:
- `count: int` (≥0) — Current metric value
- `trend: Literal["increase", "decrease", "flat"] | None` — Direction indicator
- `change: int` (≥0) — Absolute change value

**OverviewMetrics** — All six KPI tiles:
- `total_projects`, `completed`, `active`, `inactive`, `at_risk`, `not_applicable`: KpiTile

**StatusDistribution** — Project status breakdown:
- `total: int` (≥0) — Sum of all status counts
- `breakdown: list[StatusBreakdownItem]` — Per-status details (status, count, percentage)

**AttentionBanner** — Risk notification:
- `message: str` (max 200 chars) — Alert text
- `at_risk_count: int` (≥0) — Number of at-risk projects
- `severity: Literal["critical", "warning", "info"]` — Severity level

**FiltersData** — Dropdown options:
- `specializations: list[FilterItem]` — Active specializations
- `clients: list[FilterItem]` — Distinct active clients
- `statuses: list[FilterItem]` — Active statuses

**FilterItem** — Generic id/name pair:
- `id: str` — UUID string
- `name: str` — Display name

## Correctness Properties

### Property 1: Trend Derivation Determinism
Given the same `increase_count` and `decrease_count` values, the trend output is always the same. Priority order: increase > decrease > flat. When both increase and decrease are > 0, "increase" wins with `increase_count` as the change value.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Period Default Behavior
When `period` is `None` or omitted from the request, the system always defaults to `"last_week"` (7 days). This is applied before any database queries.

**Validates: Requirements 1.2**

### Property 3: Status Distribution Percentage Integrity
The sum of all `percentage` values in the breakdown equals 100.0 (within floating-point rounding tolerance), or all are 0.0 when total is 0. Division by zero is prevented by checking total before calculation.

**Validates: Requirements 3.3, 3.4**

### Property 4: Complete Status Representation
The breakdown array always contains every status from the `statuses` table where `is_active = 1`, even if no projects currently have that status (count of 0, percentage of 0.0).

**Validates: Requirements 3.6**

### Property 5: Attention Banner Severity Exclusivity
Exactly one severity is assigned based on `at_risk_count`: count ≥ 5 → "critical", 1 ≤ count ≤ 4 → "warning", count = 0 → "info". These ranges are mutually exclusive and exhaustive.

**Validates: Requirements 4.2, 4.3, 4.4**

### Property 6: Client ID Determinism
UUID v5 generation with a fixed application namespace produces the same ID for the same client name across all requests and server restarts.

**Validates: Requirements 5.3**

### Property 7: Specialization Filter Isolation
When a specialization filter is applied, only KPI data and status distribution data matching those specialization IDs is included. No cross-specialization data leakage occurs.

**Validates: Requirements 1.6**

### Property 8: Authentication Opacity
All authentication failures return the same generic error message regardless of the specific failure reason (missing token, decryption failure, invalid email, Jira timeout). Internal state is never exposed.

**Validates: Requirements 6.2, 6.4, 6.5, 6.6**

## Error Handling

### Error Categories

| Category | HTTP Code | Status | Handling |
|----------|-----------|--------|----------|
| Missing/invalid token | 401 | "failed" | Auth middleware returns immediately |
| Invalid period parameter | 400 | "failed" | Service validates, raises custom exception |
| Invalid specialization (all invalid) | 200 | "success" | Treated as no filter, returns all data |
| Database unavailable | 500 | "error" | Global handler catches, logs to error_log |
| Jira API timeout | 401 | "failed" | Auth middleware returns auth failure |
| Unhandled exception | 500 | "error" | Global handler catches, logs asynchronously |

### Global Exception Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = request.state.trace_id
    error_message = f"[trace_id:{trace_id}] {str(exc)}"

    # Non-blocking async error logging
    asyncio.create_task(_log_error_to_db(
        error_message=error_message,
        error_function=_get_function_name(exc),
        error_file=_get_file_name(exc),
        stack_trace=traceback.format_exc(),
        created_by=OVERVIEW_SERVICE_IDENTIFIER,
    ))

    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "status": "error",
            "message": "An unexpected error occurred. Please try again later",
            "data": [],
        },
    )
```

### Error Logging Guarantees
- Error response returned to client within 500ms regardless of DB write status
- DB insert has 10-second timeout; abandoned if exceeded
- If DB insert fails, error details logged to structured JSON application logs (fallback)
- `trace_id` included in both application logs and `error_log.error_message` for correlation
- `error_message` and `stack_trace` truncated to 65,535 characters

### Custom Exceptions

```python
class InvalidParameterError(Exception):
    """Raised when query parameter validation fails. Returns 400."""

class AuthenticationError(Exception):
    """Raised when token decryption or Jira validation fails. Returns 401."""
```

## Testing Strategy

### Unit Tests (`src/tests/`)

**Coverage Target:** >80% code coverage

**Test Structure mirrors source:**
- `src/tests/services/test_overview_service.py`
- `src/tests/services/test_filter_service.py`
- `src/tests/repositories/test_kpi_history_repository.py`
- `src/tests/repositories/test_project_repository.py`
- `src/tests/middleware/test_auth_middleware.py`
- `src/tests/routes/test_overview_route.py`
- `src/tests/routes/test_filter_route.py`

**Key Test Scenarios:**

*Overview Service:*
- Valid request with default period → returns metrics with last_week data
- Valid request with explicit period → filters by correct day range
- Valid specialization filter → returns filtered data
- Invalid period → raises InvalidParameterError
- Empty period string → raises InvalidParameterError
- All invalid specialization IDs → returns all data (treated as no filter)
- No KPI history records → returns all zeros with null trends
- Trend derivation: increase > 0 → "increase"
- Trend derivation: decrease > 0 → "decrease"
- Trend derivation: both 0 → "flat"
- Trend derivation: both > 0 → "increase" (increase takes priority)
- Attention banner: count >= 5 → critical
- Attention banner: count 1-4 → warning
- Attention banner: count 0 → info
- Status distribution percentage calculation
- Status distribution with zero total → all percentages 0.0

*Filter Service:*
- Returns all active specializations, clients, statuses
- Empty categories return empty arrays
- Client UUID v5 generation is deterministic
- Results sorted alphabetically (case-insensitive)
- Null/empty client values excluded

*Auth Middleware:*
- Missing Authorization header → 401
- Invalid token format → 401
- Decryption failure → 401
- Empty email in payload → 401
- Jira validation failure → 401
- Jira API timeout → 401
- Valid token + valid email → request proceeds
- Health/ready endpoints bypass auth

*Repositories:*
- KPI history window function returns latest per specialization
- Period filtering respects day boundaries
- Status distribution includes all active statuses
- Distinct clients excludes null/empty values

**Testing Tools:**
- pytest + pytest-asyncio for async tests
- unittest.mock for mocking external dependencies
- pytest fixtures for DB session and service setup
- pytest.raises for exception path testing
- parametrize for multiple input scenarios
