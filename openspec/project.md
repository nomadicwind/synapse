# Project Context

## Purpose
Synapse captures knowledge from web articles, online media, local recordings, and voice notes, then prepares the material for downstream distillation and consumption workflows. The current focus is the “Source” component: gathering user-submitted content (via mobile share sheet, manual URL entry, or in-app voice memos), extracting structured text, and preserving supporting media so knowledge workers can review and enrich it later.

## Tech Stack
- Backend API: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy ORM, UUID-backed PostgreSQL models
- Background processing: Celery 5, Redis broker/result backend, requests/httpx, readability-lxml, BeautifulSoup4, yt-dlp, boto3 (MinIO/S3 uploads)
- Data stores: PostgreSQL (metadata), MinIO/S3 or local filesystem (media assets), temporary filesystem for worker scratch space
- AI services: OpenAI Whisper (via `infrastructure/stt_service` FastAPI wrapper), FFmpeg for audio conversions
- Frontend: React Native (Expo) with TypeScript, React Navigation, Native Stack/Bottom Tabs
- Tooling: pytest, FastAPI TestClient, Jest/React Testing Library, ESLint/TypeScript, dotenv, start scripts in `scripts/`

## Project Conventions

### Code Style
- Python services follow FastAPI conventions with dependency-injected DB sessions, SQLAlchemy ORM models, structured logging, and type-annotated Pydantic models. Avoid inline SQL; use declarative models in `backend/api/models.py`.
- Background workers prefer explicit task names (`tasks.process_webpage`, etc.) and wrap every handler in `try/except` blocks, mutating `status` and `processed_at` consistently.
- React Native code uses functional components with hooks, TypeScript typing, React Navigation, and inline StyleSheet definitions (NativeWind planned but not yet wired).
- Keep environment-specific values in `.env` files loaded by `python-dotenv`; do not hardcode secrets inside code.

### Architecture Patterns
- Service-oriented layout with independent processes for API, worker, STT service, and mobile client; Redis mediates asynchronous communication.
- Asynchronous capture pipeline: API accepts work quickly, Celery workers perform long-running extraction, STT service transcribes audio, and data persists in PostgreSQL plus object storage.
- Local-first development: each service is run directly (no docker-compose) using the instructions in `README.md` / `STARTUP_GUIDE.md`.
- Capability separation: Source handles capture/textualisation now; Knowledge Distillation/Consumption will be separate specs and services later.

### Testing Strategy
- FastAPI routes covered by pytest-based HTTP client tests (`backend/api/test_main.py`) including validation, Celery dispatch, and error cases.
- Worker logic validated with mocked dependencies in `backend/worker/test_app.py`; Celery tasks rely on MagicMock’d network/storage calls.
- STT service behavior exercised through FastAPI TestClient in `infrastructure/stt_service/test_app.py`.
- React Native UI components use Jest w/ React Testing Library under `frontend/mobile/__tests__`, focusing on navigation and validation.
- Future integration/e2e tests will live under `tests/` folders (placeholders exist today).

### Git Workflow
- Feature work happens on topic branches (`feature/<slug>` or `chore/<slug>`) forked from `main`.
- Each PR must include relevant unit tests and, when applicable, updates to OpenSpec specs plus `doc/` references.
- Keep commits focused (spec vs implementation) and run `npm test` / targeted pytest suites locally before opening PRs.
- Avoid reformatting unrelated files; rely on subproject formatters (e.g., `eslint`, `black/isort` if added later).

## Domain Context
Synapse targets knowledge professionals who need to capture multi-modal inputs (articles, videos, voice memos, shared text) into a single repository. The Source pipeline turns raw captures into normalized `knowledge_items` plus related `image_assets`, progressing through `pending → processing → ready_for_distillation` or `error`. Downstream phases (Distillation, Consumption) will add summarisation, tagging, retrieval, and bidirectional linking once specs land.

## Important Constraints
- Capture requests must return quickly; all heavy lifting runs in Celery tasks to keep the mobile client responsive.
- URLs must be unique per knowledge item to avoid duplicate indexing; database enforces a unique index on `knowledge_items.source_url`.
- Long-running media processing relies on external binaries (`yt-dlp`, Whisper, FFmpeg); deployments must provision CPU/GPU resources and configure binary paths.
- Worker tasks must download and re-host media (images/audio) into internal storage to avoid hot-linking and to guarantee availability; MinIO credentials required.
- Failure handling must mark items with an `error` status so downstream systems can surface retries; logs should capture URLs and exception traces for debugging.
- Authentication is required on API endpoints (JWT bearer tokens) even during capture to isolate users’ data scopes.

## External Dependencies
- PostgreSQL 15+ for metadata persistence (`DATABASE_URL` configured via env).
- Redis 7+ as the Celery broker/result backend.
- MinIO/S3-compatible object storage for extracted images (local filesystem fallback during development via `STORAGE_ROOT`).
- Whisper model weights (downloaded on STT service start) for speech-to-text.
- FFmpeg and yt-dlp binaries for audio extraction from media sources; ensure they’re available on PATH.
- Expo/React Native tooling (Metro, Android/iOS simulators) for the mobile client.
