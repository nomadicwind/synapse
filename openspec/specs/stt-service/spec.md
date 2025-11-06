# Capability: STT Service

## Purpose
The speech-to-text service wraps the Whisper model behind a FastAPI interface so workers can obtain transcripts for captured audio. It exposes lightweight health reporting and handles temporary file management for each transcription request.

## Requirements
### Requirement: Expose service health status
Operational checks MUST have a quick way to confirm the STT process and model are ready.

#### Scenario: Health endpoint reports readiness
- **GIVEN** the FastAPI app is running and Whisper has loaded
- **WHEN** a client sends GET `/health`
- **THEN** the service responds with HTTP 200 and JSON including `"status": "healthy"` and the configured `"model"` name

### Requirement: Transcribe uploaded audio
The service MUST accept an uploaded audio file, run Whisper, and return the transcription metadata.

#### Scenario: Successful transcription returns transcript payload
- **GIVEN** a multipart/form-data request with field `file` containing audio bytes (e.g., `audio/mpeg`)
- **WHEN** the client POSTs to `/transcribe`
- **THEN** the service writes the upload to a temporary file, invokes `model.transcribe`, deletes the temp file, and responds with HTTP 200 and JSON including `"status": "success"`, `"transcript"`, `"language"`, and `"duration"`

### Requirement: Validate presence of audio data
Requests without an attached file MUST be rejected.

#### Scenario: Missing file generates validation error
- **GIVEN** a POST `/transcribe` request without the `file` field
- **WHEN** FastAPI processes the request
- **THEN** it returns HTTP 422 signalling the missing required upload

### Requirement: Surface transcription failures cleanly
Runtime errors from Whisper MUST translate into informative HTTP errors.

#### Scenario: Transcription failure returns 500
- **GIVEN** Whisper raises an exception while processing audio
- **WHEN** the handler catches the error
- **THEN** it logs the issue, cleans up the temporary file, and responds with HTTP 500 containing `{"detail": "Error transcribing audio: ..."}` in the body
