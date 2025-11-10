# Synapse Implementation Overview

## System Architecture

Synapse is a knowledge management system with the following components:

1. **Mobile Frontend**: React Native application for capturing content
2. **Backend API**: FastAPI service that receives capture requests and manages knowledge items
3. **Content Processing Worker**: Celery worker that processes captured content asynchronously
4. **STT Service**: FastAPI service using Whisper model for speech-to-text transcription
5. **Database**: PostgreSQL for storing knowledge items and metadata
6. **Message Queue**: Redis for task queuing between API and Worker
7. **File Storage**: Local filesystem storage for images and processed content

## Component Interactions

1. User captures content via Mobile Frontend
2. Mobile Frontend sends request to Backend API
3. Backend API creates knowledge item record with "pending" status
4. Backend API enqueues processing task in Redis queue
5. Content Processing Worker picks up task and processes content
6. For media content, Worker calls STT Service for transcription
7. Worker updates knowledge item with processed content and "ready_for_distillation" status
8. Mobile Frontend can poll Backend API to check processing status

## Implementation Details

### Backend API (backend/api/main.py)

- FastAPI application with structured logging
- Health check endpoint at `/health`
- Capture endpoint at `/api/v1/capture` that accepts webpage, video, audio, and voicememo sources
- Knowledge item retrieval endpoint at `/api/v1/knowledge-items/{item_id}`
- Uses SQLAlchemy for database operations
- Integrates with Celery for task queuing
- Returns 202 Accepted immediately while processing happens asynchronously

### Content Processing Worker (backend/worker/app.py)

Implements three main tasks:

1. **process_webpage**: 
   - Fetches webpage content
   - Uses Readability to extract main content
   - Processes and stores images locally
   - Updates knowledge item with extracted content and metadata

2. **process_media**:
   - Uses yt-dlp to download audio from video/audio URLs
   - Sends audio to STT Service for transcription
   - Updates knowledge item with transcript

3. **process_voicememo**:
   - Currently a placeholder that sets processed_text_content to "Voice memo transcription placeholder"
   - TODO: Implement actual voice memo processing

### STT Service (infrastructure/stt_service/app.py)

- FastAPI application using Whisper model for speech-to-text
- Health check endpoint at `/health`
- Transcription endpoint at `/transcribe` that accepts audio file uploads
- Configurable model size via WHISPER_MODEL_SIZE environment variable
- Returns transcript, detected language, and duration

### Mobile Frontend (frontend/mobile/App.tsx)

- React Native application with React Navigation
- Bottom tab navigator with Home and Explore screens
- Stack navigator for modal screens (Capture and Modal)
- Communicates with Backend API for capture requests and status checks

## Discrepancies Between Spec and Implementation

1. The process_media task in implementation includes a source_type parameter not mentioned in spec
2. Implementation includes additional error handling and logging beyond what's specified
3. Voice memo processing is still a placeholder as noted in spec

## Current Limitations and TODOs

1. Voice memo processing needs to be fully implemented
2. Error handling could be improved with more specific error codes/messages
3. No retry mechanism for failed processing tasks
4. Limited monitoring and metrics collection
5. Authentication and user management not yet implemented
6. File storage is currently local filesystem, should consider cloud storage options
7. No rate limiting or request throttling implemented
