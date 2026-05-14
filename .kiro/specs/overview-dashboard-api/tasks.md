# Implementation Plan: Overview Dashboard API

## Overview

Implement the Overview Dashboard API backend using Python FastAPI with SQLAlchemy async ORM, Pydantic v2, and PostgreSQL. The implementation follows a layered architecture (Routes → Services → Repositories) with encrypted token authentication middleware, two main endpoints (`GET /api/v1/overview` and `GET /api/v1/filters`), health/readiness checks, and structured error handling with async database logging.

## Tasks

- [x] 1. Set up project structure, configuration, and core models
  - [x] 1.1 Create project skeleton with settings and dependency management
    - Create `pyproject.toml` with FastAPI, SQLAlchemy[asyncio], asyncpg, Pydantic v2, httpx, structlog, pytest, pytest-asyncio, hypothesis dependencies
    - Create `Makefile` with setup, run, test, lint, format, clean targets
    - Create `src/__init__.py`, `src/settings.py` with `Settings(BaseSettings)` class using `@lru_cache` singleton
    - Define constants: `PERIOD_DAYS_MAP`, `SEVERITY_CRITICAL_THRESHOLD`, `FILTER_CACHE_MAX_AGE`, `JIRA_VALIDATION_TIMEOUT`, `OVERVIEW_SERVICE_IDENTIFIER`, `MAX_SPECIALIZATION_FILTER_COUNT`, `CLIENT_UUID_NAMESPACE`
    - Implement startup validation for `DATABASE_URL`, `TOKEN_PRIVATE_KEY`, `JIRA_BASE_URL`, `JIRA_API_TOKEN`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [x] 1.2 Create SQLAlchemy ORM schema models
    - Create `src/repositories/__init__.py` and `src/repositories/schema/__init__.py`
    - Create `src/repositories/schema/base.py` with declarative Base
    - Create ORM models: `kpi_history.py`, `specialization.py`, `project.py`, `status.py`, `devsecops_ticket.py`, `setting.py`, `error_log.py`
    - Map all columns and types from `create_tables.sql` to SQLAlchemy models
    - Define relationships and foreign keys
    - _Requirements: 12.4_

  - [x] 1.3 Create Pydantic response and query parameter models
    - Create `src/models/__init__.py`
    - Create `src/models/base_response.py` with `BaseResponse` model (status_code, status, message, data)
    - Create `src/models/overview_models.py` with `KpiTile`, `OverviewMetrics`, `StatusBreakdownItem`, `StatusDistribution`, `AttentionBanner`, `OverviewData`
    - Create `src/models/filter_models.py` with `FilterItem`, `FiltersData`
    - Create `src/models/query_params.py` with period enum validation
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 12.5_

  - [x] 1.4 Create utility modules (logger, exceptions)
    - Create `src/utils/__init__.py`, `src/utils/logger.py` with structlog JSON configuration
    - Create `src/utils/exceptions/__init__.py`, `src/utils/exceptions/error_codes.py`
    - Create `src/utils/exceptions/exceptions.py` with `InvalidParameterError`, `AuthenticationError`
    - Create `src/utils/exceptions/error_responses.py` with error response builders
    - _Requirements: 8.2, 8.6_

- [x] 2. Checkpoint - Verify project structure
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement repository layer
  - [x] 3.1 Implement KPI History Repository
    - Create `src/repositories/kpi_history_repository.py`
    - Implement `get_latest_by_specializations(specialization_ids, period_days)` method
    - Use `ROW_NUMBER() OVER (PARTITION BY specialization_id ORDER BY created_at DESC)` window function
    - Filter by `created_at >= NOW() - interval`, `is_active = 1`, join with active specializations
    - When `specialization_ids` provided: add `WHERE specialization_id IN (...)` filter
    - Return only `row_number = 1` records (most recent per specialization)
    - _Requirements: 1.3, 1.5, 1.6, 2.7, 2.8, 2.9_

  - [x] 3.2 Implement Project Repository
    - Create `src/repositories/project_repository.py`
    - Implement `get_status_distribution(specialization_ids)` with LEFT JOIN statuses → projects
    - When specialization filter: additionally JOIN `devsecops_tickets` with matching `specialization_id`
    - Group by `status_name`, count distinct `project_id`, order by `status_name ASC`
    - Implement `get_distinct_clients()` for non-null, non-empty active project clients
    - _Requirements: 3.1, 3.2, 3.5, 3.6, 3.8, 5.3_

  - [x] 3.3 Implement Specialization and Status Repositories
    - Create `src/repositories/specialization_repository.py` with `get_active_specializations()` method
    - Create `src/repositories/status_repository.py` with `get_active_statuses()` method
    - Both filter by `is_active = 1`
    - _Requirements: 5.2, 5.4_

  - [x] 3.4 Implement Error Log Repository
    - Create `src/repositories/error_log_repository.py`
    - Implement `log_error(error_message, error_function, error_file, stack_trace, created_by)` method
    - Truncate `error_message` and `stack_trace` to 65,535 characters
    - Non-blocking execution via `asyncio.create_task` with 10-second timeout
    - _Requirements: 8.1, 8.3, 8.4, 8.7, 8.8_

  - [x] 3.5 Write unit tests for repositories
    - Test KPI history window function returns latest per specialization
    - Test period filtering respects day boundaries
    - Test status distribution includes all active statuses (even with 0 count)
    - Test distinct clients excludes null/empty values
    - Test error log truncation at 65,535 characters
    - _Requirements: 1.3, 1.5, 3.2, 3.6, 8.1_

- [x] 4. Implement service layer
  - [x] 4.1 Implement Overview Service
    - Create `src/services/__init__.py` and `src/services/overview_service.py`
    - Implement `get_overview(period, specialization)` method
    - Implement period validation: None → "last_week", invalid → `InvalidParameterError`, empty string → `InvalidParameterError`
    - Validate period BEFORE specialization (fail fast)
    - Implement specialization parsing: CSV split, trim, limit to 50 IDs, all invalid → no filter
    - Implement `_derive_trend(increase_count, decrease_count)` helper
    - Implement KPI aggregation: sum counts across latest records per specialization
    - Implement status distribution computation with percentage calculation (rounded to 1 decimal)
    - Implement attention banner logic: ≥5 → critical, 1-4 → warning, 0 → info
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 1.10, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.3, 3.4, 3.6, 3.7, 3.8, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 4.2 Write property test for trend derivation determinism
    - **Property 1: Trend Derivation Determinism**
    - Given the same increase_count and decrease_count values, the trend output is always the same. Priority: increase > decrease > flat. When both > 0, "increase" wins.
    - Use Hypothesis to generate arbitrary non-negative integer pairs
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [x] 4.3 Write property test for period default behavior
    - **Property 2: Period Default Behavior**
    - When period is None or omitted, the system always defaults to "last_week" (7 days)
    - **Validates: Requirements 1.2**

  - [ ]* 4.4 Write property test for status distribution percentage integrity
    - **Property 3: Status Distribution Percentage Integrity**
    - Sum of all percentage values equals 100.0 (within floating-point tolerance), or all are 0.0 when total is 0
    - Use Hypothesis to generate lists of non-negative counts
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 4.5 Write property test for attention banner severity exclusivity
    - **Property 5: Attention Banner Severity Exclusivity**
    - Exactly one severity assigned: count ≥ 5 → "critical", 1 ≤ count ≤ 4 → "warning", count = 0 → "info". Ranges are mutually exclusive and exhaustive.
    - Use Hypothesis to generate arbitrary non-negative integers
    - **Validates: Requirements 4.2, 4.3, 4.4**

  - [x] 4.6 Implement Filter Service
    - Create `src/services/filter_service.py`
    - Implement `get_filters()` method
    - Query active specializations, map to `{id, name}`
    - Query distinct non-null, non-empty clients from active projects, generate UUID v5 per client name
    - Query active statuses, map to `{id, name}`
    - Sort all arrays alphabetically by name (case-insensitive)
    - Return empty `[]` for categories with no records
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 5.9_

  - [ ]* 4.7 Write property test for client ID determinism
    - **Property 6: Client ID Determinism**
    - UUID v5 generation with fixed namespace produces the same ID for the same client name across all invocations
    - Use Hypothesis to generate arbitrary strings as client names
    - **Validates: Requirements 5.3**

  - [x] 4.8 Write unit tests for Overview Service
    - Test valid request with default period returns last_week data
    - Test explicit period filters by correct day range
    - Test valid specialization filter returns filtered data
    - Test invalid period raises InvalidParameterError
    - Test empty period string raises InvalidParameterError
    - Test all invalid specialization IDs returns all data
    - Test no KPI history records returns zeros with null trends
    - Test trend derivation all scenarios (increase, decrease, flat, both > 0)
    - Test attention banner severity thresholds
    - Test status distribution percentage calculation and zero total
    - _Requirements: 1.2, 1.4, 1.7, 1.10, 2.1, 2.2, 2.3, 2.4, 3.3, 3.4, 4.2, 4.3, 4.4_

  - [x] 4.9 Write unit tests for Filter Service
    - Test returns all active specializations, clients, statuses
    - Test empty categories return empty arrays
    - Test client UUID v5 generation is deterministic
    - Test results sorted alphabetically (case-insensitive)
    - Test null/empty client values excluded
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

- [x] 5. Checkpoint - Verify service layer
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement authentication middleware and Jira client
  - [x] 6.1 Implement Jira Client
    - Create `src/client/__init__.py` and `src/client/jira_client.py`
    - Implement `validate_email(email)` method using httpx async client
    - Call `GET {JIRA_BASE_URL}/rest/api/2/user/search?username={email}` with `JIRA_API_TOKEN`
    - 10-second timeout, return `True` if user found, `False` otherwise
    - _Requirements: 6.3, 6.5, 6.6, 6.8_

  - [x] 6.2 Implement Auth Middleware
    - Create `src/middleware/__init__.py` and `src/middleware/auth_middleware.py`
    - Exclude `/health`, `/ready`, `/docs`, `/openapi.json` from auth
    - Extract `Authorization: Bearer <token>` header
    - Decrypt token using `TOKEN_PRIVATE_KEY`
    - Extract email from decrypted payload
    - Validate email via Jira client
    - On success: attach email to `request.state.user_email`
    - On failure: return 401 BaseResponse with appropriate message
    - Inject `trace_id` (UUID v4) into `request.state.trace_id`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 9.4_

  - [ ]* 6.3 Write property test for authentication opacity
    - **Property 8: Authentication Opacity**
    - All authentication failures return the same generic error message regardless of failure reason (missing token, decryption failure, invalid email, Jira timeout)
    - Use Hypothesis to generate different failure scenarios
    - **Validates: Requirements 6.2, 6.4, 6.5, 6.6**

  - [ ]* 6.4 Write unit tests for Auth Middleware
    - Test missing Authorization header → 401
    - Test invalid token format → 401
    - Test decryption failure → 401
    - Test empty email in payload → 401
    - Test Jira validation failure → 401
    - Test Jira API timeout → 401
    - Test valid token + valid email → request proceeds
    - Test health/ready endpoints bypass auth
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] 7. Implement route layer and application wiring
  - [x] 7.1 Implement dependency injection configuration
    - Create `src/services/dependencies.py`
    - Implement `get_db_session()` async generator
    - Implement factory functions for all repositories and services
    - Wire service → repository dependencies using FastAPI `Depends()`
    - _Requirements: 12.2, 12.3, 12.6_

  - [x] 7.2 Implement Overview Route
    - Create `src/routes/__init__.py` and `src/routes/overview_route.py`
    - Implement `GET /api/v1/overview` with `period` and `specialization` query params
    - Inject `OverviewService` via dependency injection
    - Return `BaseResponse` with overview data on success
    - _Requirements: 1.1, 1.9, 1.11, 10.1, 10.2, 12.1_

  - [x] 7.3 Implement Filter Route
    - Create `src/routes/filter_route.py`
    - Implement `GET /api/v1/filters`
    - Inject `FilterService` via dependency injection
    - Set `Cache-Control: max-age=3600` response header
    - Return `BaseResponse` with filters data on success
    - _Requirements: 5.1, 5.5, 5.7, 5.8, 10.1, 10.2, 12.1_

  - [x] 7.4 Implement Health and Readiness Routes
    - Create `src/routes/default_route.py`
    - Implement `GET /health` returning `{"status": "healthy"}` (no auth required)
    - Implement `GET /ready` with database connectivity check (5s timeout)
    - Return 503 with `{"status": "unavailable"}` if DB check fails
    - Return 503 with `{"status": "unhealthy"}` if unexpected error on /health
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 7.5 Create main application entry point
    - Create `main.py` with FastAPI app instance
    - Register auth middleware
    - Register global exception handler with async error logging
    - Include all route routers with `/api/v1` prefix (except health/ready)
    - Configure CORS if needed
    - Implement lifespan context manager for startup/shutdown
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6, 10.5, 12.1_

  - [ ]* 7.6 Write property test for specialization filter isolation
    - **Property 7: Specialization Filter Isolation**
    - When a specialization filter is applied, only KPI data and status distribution data matching those specialization IDs is included. No cross-specialization data leakage.
    - Use Hypothesis to generate sets of specialization IDs and verify isolation
    - **Validates: Requirements 1.6**

  - [ ]* 7.7 Write property test for complete status representation
    - **Property 4: Complete Status Representation**
    - The breakdown array always contains every status from the statuses table where is_active = 1, even if no projects have that status (count 0, percentage 0.0)
    - **Validates: Requirements 3.6**

  - [ ]* 7.8 Write integration tests for routes
    - Test overview endpoint returns correct BaseResponse structure
    - Test filters endpoint returns correct BaseResponse with Cache-Control header
    - Test health endpoint returns 200 without auth
    - Test ready endpoint returns 200 when DB available
    - Test 401 response for missing token on protected endpoints
    - Test 400 response for invalid period parameter
    - Test 500 response triggers error logging
    - _Requirements: 1.1, 5.1, 5.5, 9.1, 9.2, 9.4, 10.1, 10.2, 10.3, 10.4_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The design uses Python (FastAPI) explicitly — no language selection needed
- All code follows the layered architecture: Routes → Services → Repositories → Database
- Authentication middleware intercepts all requests except health/ready endpoints
- Error logging is non-blocking with 10-second timeout to avoid impacting response times

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.4"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3", "3.4"] },
    { "id": 3, "tasks": ["3.5", "4.1", "4.6"] },
    { "id": 4, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.7", "4.8", "4.9"] },
    { "id": 5, "tasks": ["6.1"] },
    { "id": 6, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 7, "tasks": ["7.1"] },
    { "id": 8, "tasks": ["7.2", "7.3", "7.4"] },
    { "id": 9, "tasks": ["7.5"] },
    { "id": 10, "tasks": ["7.6", "7.7", "7.8"] }
  ]
}
```
