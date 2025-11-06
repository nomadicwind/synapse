# Capability: Content Processing Worker

## Purpose
The Celery worker consumes capture jobs, enriches knowledge items with extracted content, and maintains item lifecycle state. Handlers are specialised for webpages, online media, and voice memos while sharing common persistence and error-handling patterns.

## Requirements
### Requirement: Process webpage captures into structured content
Webpage jobs MUST extract readable text, HTML, metadata, and referenced images before marking the item ready.

#### Scenario: Webpage handler persists parsed content
- **GIVEN** `tasks.process_webpage` receives an `item_id` for a stored knowledge item
- **WHEN** the worker fetches the source URL successfully
- **THEN** it sets `status` to `"processing"`, sets `processed_at` to the current timestamp, uses Readability to derive clean HTML, rewrites `<img>` `src` attributes to point at internal storage keys, stores the plain-text version, updates `title`, `author`, `published_date`, creates corresponding `image_assets` rows for downloaded images under `storage/images/{item_id}/`, and finally commits the transaction with `status` set to `"ready_for_distillation"`

#### Scenario: Webpage handler flags failures
- **GIVEN** the upstream site returns an error or raises during parsing
- **WHEN** the handler catches the exception
- **THEN** it updates the knowledge item `status` to `"error"`, preserves the last `processed_at` timestamp for auditing, commits, and returns a payload with `"status": "error"` describing the failure

### Requirement: Transcribe media captures via STT
Media jobs (video or audio URLs) MUST extract audio, send it to the STT service, and persist the transcript.

#### Scenario: Media handler stores transcription
- **GIVEN** `tasks.process_media` receives a queued media item
- **WHEN** yt-dlp downloads the audio stream and the STT service returns JSON containing `transcript`
- **THEN** the worker writes the transcript into `processed_text_content`, records any metadata returned by the STT service (e.g., `language`, `duration`) on the knowledge item, moves the item to `"ready_for_distillation"`, and deletes the temporary audio file before returning success

#### Scenario: Media handler records processing errors
- **GIVEN** yt-dlp returns a non-zero exit code or the STT request fails
- **WHEN** the exception propagates
- **THEN** the worker marks the knowledge item `status` as `"error"`, commits the change, removes any temporary files, and returns an error payload

### Requirement: Handle voice memo captures
Voice memo jobs SHALL transition items through processing even though full transcription is not yet implemented.

#### Scenario: Voice memo handler stores placeholder transcription
- **GIVEN** `tasks.process_voicememo` receives an existing item
- **WHEN** the handler runs
- **THEN** it sets `status` to `"processing"`, stores `"Voice memo transcription placeholder"` in `processed_text_content`, marks the item `"ready_for_distillation"`, and commits the update

### Requirement: Maintain knowledge item lifecycle invariants
Handlers MUST manage state transitions and timestamps consistently so downstream services can rely on item status.

#### Scenario: Successful processing updates timestamps
- **GIVEN** any handler begins work on a `knowledge_items` row whose `status` is `"pending"`
- **WHEN** it sets the status to `"processing"`
- **THEN** it MUST update `processed_at` to the current timestamp and, upon success, commit the row with status `"ready_for_distillation"`

#### Scenario: Failures mark items as error
- **GIVEN** a handler raises an exception before completion
- **WHEN** the exception is caught
- **THEN** the worker MUST set the item `status` to `"error"`, leave a meaningful error message in the task logs, commit the change, and exit without retrying automatically

### Requirement: Guard against missing knowledge items
All handlers MUST fail fast when the referenced item no longer exists.

#### Scenario: Missing knowledge item returns error response
- **GIVEN** a Celery task executes with an `item_id` that is absent from PostgreSQL
- **WHEN** the handler checks the database
- **THEN** it logs the problem and returns a payload with `"status": "error"` and `"message": "Item not found"` without attempting downstream processing
