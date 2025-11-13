# Proposal: Backend Service Console

## Why
- Operators currently lack observability into the health of Synapse services. Start-up scripts (`scripts/start_all_services.sh`) only report initial PIDs; there is no persistent dashboard to confirm API/Worker/STT availability or backing services such as Redis, PostgreSQL, and MinIO.
- `openspec/changes/implementation-overview.md` and the Technical Design document both call out missing monitoring, retry tooling, and task visibility. When captures fail, engineers must SSH into each process, tail logs, and manually poke the database to retry items.
- As we ramp more capture sources, we need a secured console to inspect service health, queue depth, recent knowledge items, and trigger safe remediation actions (e.g., retry failed captures) without running ad-hoc SQL.

## What Changes
- Build an authenticated Backend Service Console (web UI served from the FastAPI app) that aggregates health signals from API/Worker/STT along with connectivity checks for PostgreSQL, Redis, and storage.
- Expose internal Console APIs that surface Celery queue metrics (per-task backlog, worker heartbeat) and stream recent log lines so operators can diagnose issues quickly.
- Provide operational tooling inside the console to list knowledge items filtered by `status`, view processing history, edit key database fields (title, status, last_error) directly in-place, and re-queue failed captures via a dedicated “Knowledge Items” page with one-click “Retry”. The page should render a table-style panel with better visual cues (row selection, detail pane) so attributes are easy to scan.
- Add alert banners and notification hooks when any service health check fails or queue depth exceeds thresholds so engineers can act before end users notice.

## Impact
- **Security:** Introduces a privileged admin surface. Requires JWT scopes/roles (e.g., `admin`) plus CSRF protection for console actions.
- **Backend:** Adds new FastAPI routes under `/internal/console/*`, Celery inspection utilities, and DB queries for status dashboards. Worker must expose lightweight heartbeat metadata (timestamp, hostname).
- **Frontend:** A small React (or FastAPI Jinja) single-page UI bundled with the API service for now. Needs shared component library decisions, but scope is limited to dashboards/tables.
- **Operations:** Gives on-call engineers concrete tooling for monitoring and manual retries, reducing reliance on direct DB access and bespoke shell scripts.
