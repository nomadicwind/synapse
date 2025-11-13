## ADDED Requirements
### Requirement: Console access MUST be authenticated and role-restricted
The Backend Service Console SHALL only be reachable to operators possessing an `admin` (or higher) scope, enforced on every HTTP request.

#### Scenario: Unauthorized user is redirected/denied
- **GIVEN** a user without the `admin` scope tries to load `/internal/console`
- **WHEN** the request is processed
- **THEN** the API responds with HTTP 401/403 and does not return console data or HTML

#### Scenario: Console token guard is configurable
- **GIVEN** `CONSOLE_API_TOKEN` is set on the API
- **WHEN** the console frontend includes the matching `X-Console-Token` header (via `VITE_CONSOLE_API_TOKEN`)
- **THEN** requests succeed; otherwise, they are rejected with HTTP 401

### Requirement: Console MUST display real-time service health
The console SHALL surface a combined health view for API, Worker, STT, PostgreSQL, Redis, and MinIO so operators can see platform readiness at a glance.

#### Scenario: Health panel aggregates dependencies
- **GIVEN** all services expose their health probes (`/health`, DB ping, Redis `PING`, MinIO bucket check)
- **WHEN** the console dashboard loads
- **THEN** it calls the aggregated console API and renders each dependency as `healthy`, `degraded`, or `down` with last-checked timestamps and error reasons

### Requirement: Console MUST surface queue and worker metrics
The console MUST expose Celery queue depth metrics and worker heartbeat status to help operators detect backlogs or stalled workers.

#### Scenario: Queue card shows backlog and workers
- **GIVEN** Celery exposes queue statistics and worker heartbeats
- **WHEN** the console metrics endpoint is queried
- **THEN** it returns per-task pending counts, average wait time, and worker heartbeat metadata (hostname, last seen), which the UI renders as charts/cards

### Requirement: Console MUST list knowledge items with operational filters
Operators SHALL be able to inspect paginated knowledge items filtered by operational status to diagnose problematic captures.

#### Scenario: Knowledge table filters by status
- **GIVEN** the operator selects `status=error`
- **WHEN** the console loads the knowledge-item list endpoint
- **THEN** it returns a paginated table containing id, source_type, source_url, status, processed_at, last error message, and the UI renders it with sort/filter controls

#### Scenario: Dedicated knowledge page provides detail view
- **GIVEN** the operator navigates to the knowledge-items page
- **WHEN** they click on an item row
- **THEN** the console presents a detail panel/page showing full metadata (timestamps, transcript availability, last error) plus the retry action without leaving the page

#### Scenario: Table-style panel renders existing attributes
- **GIVEN** the knowledge-items page loads existing captures
- **WHEN** the UI renders the table panel
- **THEN** each row displays key attributes (ID prefix, status badge, source type, last error summary, last update time) with row-hover/selection states so operators can quickly scan and focus on a specific record

### Requirement: Console MUST allow safe capture retries
The console MUST provide a retry action that safely resets knowledge items and re-dispatches their Celery tasks without manual SQL.

#### Scenario: Retry action re-enqueues item
- **GIVEN** a knowledge item is in `error` or `pending` status
- **WHEN** an operator clicks “Retry” in the console
- **THEN** the backend resets the item to `pending`, logs the action, dispatches the proper Celery task (`process_webpage`, `process_media`, or `process_voicememo`), and returns confirmation to the UI

### Requirement: Knowledge page MUST support in-place edits
Operators SHALL be able to modify approved fields (title, status, last_error) for a knowledge item directly from the console with server-side validation and immediate feedback.

#### Scenario: Operator edits metadata inline
- **GIVEN** the operator selects a knowledge item
- **WHEN** they update the title or status via the console UI and confirm the change
- **THEN** the console calls a secured PATCH endpoint, persists the new values, and visibly updates the table/detail panel without requiring a page refresh

#### Scenario: Edit form enforces validation
- **GIVEN** an operator attempts to set an unsupported status or clears a required field
- **WHEN** the request reaches the API
- **THEN** the backend rejects it with a descriptive error that the console surfaces inline, leaving the original value untouched

### Requirement: Console MUST surface recent logs and alerts
The console SHALL make recent API/worker logs and alert banners visible so operators can triage failures without shell access.

#### Scenario: Log viewer streams tail output
- **GIVEN** the API and worker write to structured log files
- **WHEN** the operator opens the Logs panel
- **THEN** the console API streams the last N lines tagged with timestamps and severity, and highlights entries referenced by current alerts (e.g., unhealthy services, queue thresholds)
