# Capability: Source Capture API

## Purpose
The FastAPI service accepts capture requests from clients, persists an initial knowledge item record, and brokers long-running processing through Celery. It also exposes read endpoints so clients can inspect knowledge items along with a lightweight service health check.

## Requirements
### Requirement: Authenticate capture requests
The API MUST require a valid bearer token on every capture and knowledge item request.

#### Scenario: Missing token returns 401
- **GIVEN** a client omits the `Authorization: Bearer <token>` header
- **WHEN** it POSTs to `/api/v1/capture` or GETs `/api/v1/knowledge-items/{item_id}`
- **THEN** the service responds with HTTP 401 and does not touch the database or enqueue a task

### Requirement: Accept capture requests asynchronously
The API MUST validate capture submissions, persist them, and return immediately while background processing occurs in Celery.

#### Scenario: Supported capture enqueues task
- **GIVEN** a JSON payload containing `source_type` in `["webpage","video","audio","voicememo"]` and an `https://` URL
- **WHEN** the client POSTs it to `/api/v1/capture`
- **THEN** the service responds with HTTP 202 and a body containing a generated `item_id`, `status` set to `"processing"`, the echoed `source_type`, and the submitted `source_url`

### Requirement: Reject malformed capture input
Invalid submissions MUST be rejected before any database or queue operations occur.

#### Scenario: Missing or invalid URL is rejected
- **GIVEN** a payload with an empty string or a URL that lacks an `http` or `https` scheme
- **WHEN** the client POSTs to `/api/v1/capture`
- **THEN** FastAPI validation fails with HTTP 422 and no Celery task is sent

#### Scenario: Unsupported source type returns 400
- **GIVEN** a payload with `source_type` set to `"note"`
- **WHEN** the client POSTs to `/api/v1/capture`
- **THEN** the service responds with HTTP 400 and an error message explaining the supported source types

### Requirement: Persist initial knowledge item record
Each accepted capture MUST create a `knowledge_items` row with canonical metadata ready for downstream processing.

#### Scenario: Knowledge item stored with pending status
- **GIVEN** a supported capture request for a new URL
- **WHEN** the service handles the request
- **THEN** it creates a `knowledge_items` record with the generated UUID primary key, random `user_id`, the request `source_url` and `source_type`, `status` set to `"pending"`, and timestamps `created_at` populated via `func.now()`

### Requirement: Enforce unique captures per URL
The API MUST prevent duplicate knowledge items for the same `source_url`.

#### Scenario: Duplicate capture surfaces conflict
- **GIVEN** a URL that already exists in `knowledge_items.source_url`
- **WHEN** the client attempts another POST `/api/v1/capture` with the same URL
- **THEN** the service responds with HTTP 409, reports that the URL is already captured, and does not enqueue a new Celery task

### Requirement: Enqueue the correct Celery task
The API MUST dispatch the capture to the matching Celery task name so workers execute the right handler.

#### Scenario: Webpage capture routes to webpage task
- **GIVEN** a `source_type` of `"webpage"`
- **WHEN** the request succeeds
- **THEN** the API calls `celery_app.send_task("tasks.process_webpage", args=[item_id])`

#### Scenario: Media capture routes to media task
- **GIVEN** a `source_type` of `"video"` or `"audio"`
- **WHEN** the request succeeds
- **THEN** the API calls `celery_app.send_task("tasks.process_media", args=[item_id])`

#### Scenario: Voice memo capture routes to voicememo task
- **GIVEN** a `source_type` of `"voicememo"`
- **WHEN** the request succeeds
- **THEN** the API calls `celery_app.send_task("tasks.process_voicememo", args=[item_id])`

### Requirement: Retrieve knowledge items by ID
Clients MUST be able to fetch processed records and receive accurate errors for missing identifiers.

#### Scenario: Existing knowledge item returned
- **GIVEN** a knowledge item exists in PostgreSQL
- **WHEN** the client performs GET `/api/v1/knowledge-items/{item_id}`
- **THEN** the service responds with HTTP 200 and a JSON body that includes stored metadata plus `processed_text_content` and `processed_html_content` fields when available

#### Scenario: Missing knowledge item returns 404
- **GIVEN** the requested `item_id` is absent
- **WHEN** the lookup runs
- **THEN** the service raises an HTTP 404 error with `"Knowledge item not found"`

### Requirement: Expose a health endpoint
Operational tooling SHALL provide a simple health probe for the service.

#### Scenario: Health probe succeeds
- **GIVEN** the API process is running
- **WHEN** a client calls GET `/health`
- **THEN** the service responds with HTTP 200 and JSON containing `"status": "healthy"` plus an ISO8601 `"timestamp"`
