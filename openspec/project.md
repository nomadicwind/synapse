# Project Context

## Purpose
Synapse captures knowledge from web articles, online media, and voice notes, then prepares the material for downstream distillation and consumption workflows. The current focus is the “Source” component: gathering user-submitted content, extracting structured text, and preserving supporting media so knowledge workers can review and enrich it later.

## Tech Stack
- Backend API: Python 3.11, FastAPI, Pydantic, SQLAlchemy
- Background processing: Celery, Redis, requests, readability-lxml, BeautifulSoup4, yt-dlp
- Data stores: PostgreSQL (metadata), local filesystem or MinIO/S3 (media assets)
- AI services: OpenAI Whisper via local FastAPI service
- Frontend: React Native (Expo) with TypeScript
- Tooling: pytest, Jest/React Testing Library, Uvicorn, dotenv

## Project Conventions

### Code Style
- Python services follow FastAPI conventions with dependency-injected DB sessions, SQLAlchemy ORM models, and structured logging.
- React Native code prefers functional components with hooks, TypeScript typing, and inline StyleSheet definitions.
- Keep environment-specific values in `.env` files loaded by `python-dotenv`.

### Architecture Patterns
- Service-oriented layout with independent processes for API, worker, and STT service communicating over Redis and HTTP.
- Asynchronous capture pipeline: API accepts work quickly, Celery workers perform long-running extraction, and data persists in PostgreSQL plus object storage.
- Clear separation between capture (Source) responsibilities and future distillation/consumption stages.

### Testing Strategy
- FastAPI routes covered by pytest-based HTTP client tests (`backend/api/test_main.py`).
- Worker logic validated with mocked dependencies in `backend/worker/test_app.py`.
- STT service behavior exercised through FastAPI TestClient in `infrastructure/stt_service/test_app.py`.
- React Native UI pieces use Jest with Expo presets (`frontend/mobile/__tests__`).

### Git Workflow
- Feature work happens on topic branches forked from the main branch, following the flow described in `README.md`.
- Pull requests should include relevant tests and respect existing formatting conventions; linting is handled by tooling in each subproject.

## Domain Context
Synapse targets knowledge professionals who need to capture multi-modal inputs (articles, videos, voice memos) into a single repository. Captured items progress from `pending` to `ready_for_distillation` as automated processing completes, enabling later summarisation, tagging, and retrieval experiences.

## Important Constraints
- Capture requests must return quickly; all heavy lifting runs in Celery tasks to keep the mobile client responsive.
- URLs must be unique per knowledge item to avoid duplicate indexing.
- Long-running media processing relies on external binaries (`yt-dlp`, Whisper); deployments must provision GPU/CPU resources accordingly.
- Failure handling must mark items with an `error` status so downstream systems can surface retries.

## External Dependencies
- PostgreSQL 15+ for metadata persistence.
- Redis 7+ as the Celery broker/result backend.
- MinIO/S3-compatible object storage for extracted images (local filesystem fallback during development).
- Whisper model weights (downloaded on service start) for speech-to-text.
- FFmpeg and yt-dlp binaries for audio extraction from media sources.
