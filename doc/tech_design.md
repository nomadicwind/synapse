### **Technical Design Document: Synapse**

**Component: 1.0 - Source (Capture & Textualization)**  
**Version:** 1.0  
**Based on PDD Version:** Final 1.0

### 1. Introduction

This document provides a detailed technical design for the **Source (Capture & Textualization)** component of the Synapse knowledge management system. It outlines the system architecture, module-level design, data schemas, and implementation details necessary to build the functionality described in the corresponding PDD. The target audience for this document is the software engineer responsible for implementation.

### 2. System Architecture

The system is designed as a set of containerized, decoupled services that communicate asynchronously. This architecture ensures resilience, scalability, and a smooth local development experience.

#### 2.1. High-Level Component Diagram

codeCode

```
+---------------------------------+      +--------------------------------+      +--------------------------------+
|         Frontend Layer          |      |         Application Layer      |      |       Persistence Layer        |
|---------------------------------|      |--------------------------------|      |--------------------------------|
|                                 |      |                                |      |                                |
|  +---------------------------+  |      |  +--------------------------+  |      |  +--------------------------+  |
|  | React Native App (Expo)   |  | HTTP |  |   API Service (FastAPI)  |  |      |  | PostgreSQL Database      |  |
|  | - Mobile (Android)        | =====> |   - /api/v1/capture      | ------> |  - knowledge_items table  |  |
|  | - Web                     |  |      |   - Enqueues jobs to Redis |  |      |  - image_assets table     |  |
|  +---------------------------+  |      |  +--------------------------+  |      |  +--------------------------+  |
|                                 |      |               |                |      |               ^                |
+---------------------------------+      |               |                |      |               |                |
                                         |               V                |      |               | (Read/Write)   |
                                         |  +--------------------------+  |      |               |                |
                                         |  | Message Broker (Redis)   | <---+  +--------------------------+  |
                                         |  +--------------------------+  |  |  | Object Storage (MinIO)   |  |
                                         |               |                |  |  | - Stored images          |  |
                                         |               | (Job Queue)    |  |  +--------------------------+  |
                                         |               V                |  +--------------^----------------+
                                         |  +--------------------------+  |                 | (Write)
                                         |  | Worker Service (Celery)  | ------------------+
                                         |  | - Dispatches to handlers |  |
                                         |  | - Calls STT Service      |  |
                                         |  +--------------------------+  |
                                         |               |                |
                                         |               V (Internal RPC) |
                                         |  +--------------------------+  |
                                         |  | STT Service (Whisper)    |  |
                                         |  +--------------------------+  |
                                         |                                |
                                         +--------------------------------+
```

#### 2.2. Local Development Environment

The entire stack will be run as separate local services without Docker. Each service will be installed and configured individually:

- api: The FastAPI application will run directly using Python.
    
- worker: The Celery worker will run as a separate Python process.
    
- db: The PostgreSQL database will be installed locally or use a cloud-based PostgreSQL instance.
    
- broker: The Redis instance will be installed locally or use a cloud-based Redis service.
    
- storage: MinIO object storage will be installed locally or use a cloud-based S3-compatible storage.
    
- stt_service: The Whisper model will run as a local Python service or use a cloud-based STT API.
    

### 3. Detailed Module Design

#### 3.1. API Service (FastAPI)

- **Responsibilities:**
    
    - Expose a public API for the frontend client.
        
    - Handle user authentication and request validation.
        
    - Create an initial knowledge_items record.
        
    - Enqueue processing jobs to the Celery/Redis queue.
        
- **Key Endpoint:** POST /api/v1/capture
    
    - **Authentication:** JWT-based (bearer token in Authorization header).
        
    - **Request Validation (Pydantic Model):**
        
        codePython
        
        ```
        class CaptureRequest(BaseModel):
            source_type: Literal["webpage", "video", "audio"]
            url: HttpUrl
        ```
        
    - **Logic:**
        
        1. Validate the incoming request body.
            
        2. Create a new KnowledgeItem in the PostgreSQL database with status='pending'.
            
        3. Publish a task to the Celery queue. The task name will correspond to the handler (e.g., 'tasks.process_webpage') and the payload will be the id of the newly created item.
            
        4. Return an immediate 202 Accepted response with the itemId.
            
- **Key Considerations:**
    
    - Use FastAPI's dependency injection to manage database connections and the Celery producer instance.
        
    - Implement structured logging to track all incoming requests.
        

#### 3.2. Worker Service (Celery)

- **Responsibilities:**
    
    - Consume tasks from the Redis queue.
        
    - Execute the appropriate processing handler based on the task type.
        
    - Interact with external resources (web pages, STT service).
        
    - Update the PostgreSQL database and write to MinIO storage.
        
- **Task Definitions:**
    
    - @celery_app.task(name='tasks.process_webpage'):
        
        1. Sets item status to 'processing'.
            
        2. Uses libraries like httpx and beautifulsoup4/readability-lxml.
            
        3. Iterates through <img> tags, downloads images, and uploads them to MinIO using the boto3 S3 client.
            
        4. Updates the knowledge_items table with processed_text_content, processed_html_content, metadata, and sets status to 'ready_for_distillation'.
            
    - @celery_app.task(name='tasks.process_media'): (Handles both video and audio)
        
        1. Sets item status to 'processing'.
            
        2. Uses yt-dlp as a subprocess to download the audio to a temporary file.
            
        3. Makes an HTTP request to the internal stt_service with the audio file.
            
        4. Updates the knowledge_items table with the transcript and metadata.
            
        5. Cleans up the temporary audio file.
            
- **Key Considerations:**
    
    - **Error Handling:** Each task must be wrapped in a try...except block. On failure, the task should log the exception and update the item's status to 'error' in the database.
        
    - **Idempotency:** While not strictly required for this workflow, tasks should be designed to fail gracefully if run twice (e.g., by checking the item's status at the start).
        
    - **Configuration:** The worker will be configured via environment variables for database connections, Redis URL, MinIO credentials, and the STT service URL.
        

#### 3.3. Database Schema (PostgreSQL)

The following SQL provides the concrete implementation of the data model.

codeSQL

```
-- Main table for all captured knowledge
CREATE TABLE knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- Will eventually link to a users table

    -- Core Content
    processed_text_content TEXT, -- For AI and search
    processed_html_content TEXT, -- For rich display of webpages

    -- Metadata
    title TEXT,
    source_url TEXT UNIQUE, -- Ensure each URL is only captured once
    author TEXT,
    published_date TIMESTAMPTZ,

    -- System Internals
    status VARCHAR(30) NOT NULL CHECK (status IN ('pending', 'processing', 'ready_for_distillation', 'error')),
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('webpage', 'video', 'audio', 'voicememo', 'note')),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ
);

-- Index for efficient user-specific lookups
CREATE INDEX idx_knowledge_items_user_id ON knowledge_items(user_id);
CREATE INDEX idx_knowledge_items_status ON knowledge_items(status);
-- Unique index for source_url to enforce uniqueness constraint
CREATE UNIQUE INDEX idx_knowledge_items_source_url ON knowledge_items(source_url);

-- Table for tracking extracted images
CREATE TABLE image_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_item_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    storage_key TEXT NOT NULL, -- The key/path to the object in MinIO/S3
    original_url TEXT,
    mime_type VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_image_assets_knowledge_item_id ON image_assets(knowledge_item_id);
```

#### 3.4. Frontend Application (React Native / Expo)

- **Responsibilities:**
    
    - Provide the UI for capture actions.
        
    - Integrate with native device features (Share Sheet).
        
    - Communicate with the backend API service.
        
    - Manage application state.
        
- **Core Components:**
    
    - APIClient: A dedicated module (e.g., using axios) to handle all HTTP requests to the backend, including attaching auth tokens.
        
    - State Management: A lightweight state management library like **Zustand** or **Redux Toolkit** to manage global state (e.g., user auth status, list of items).
        
    - ShareSheetHandler: A component that handles incoming share intents on Android, opens the capture UI, and calls the APIClient.
        
    - CaptureForm: The UI component that allows the user to confirm the capture and select the source_type.
        
    - WebCapturePage: A web-specific page that allows users to manually paste URLs or local file paths and specify the source type for information capture. This page will be accessible via the web route `/capture` and will include form validation and error handling.
        
- **Styling:**
    
    - **NativeWind** will be configured to use Tailwind CSS utility classes directly in JSX components for rapid and consistent styling.
        
- **Key Considerations:**
    
    - **Secure Token Storage:** JWTs received from the authentication service must be stored securely on the device using a library like **Expo SecureStore**.
        
    - **Environment Configuration:** Use .env files to manage the backend API URL for different environments (local, staging, production).
        

### 4. Development and Test Plan

This project will be developed in an iterative, milestone-based approach.

#### 4.1. Development Plan

- **Milestone 1: Backend & Infrastructure Setup (The "Spine")**
    
    1. Install and configure PostgreSQL, Redis, and MinIO as local services or cloud instances.
        
    2. Initialize the FastAPI and Celery applications.
        
    3. Implement the PostgreSQL schema using a migration tool like **Alembic**.
        
    4. Implement the /api/v1/capture endpoint to create a pending record and enqueue a dummy task.
        
    5. **Goal:** A request to the API successfully creates a DB record and a job in Redis.
        
- **Milestone 2: End-to-End Webpage Pipeline**
    
    1. Implement the full logic for the process_webpage Celery task.
        
    2. Configure the boto3 client to connect to the local MinIO container.
        
    3. Develop a minimal, temporary web interface (or use a tool like Postman) to trigger the endpoint and verify the entire flow.
        
    4. **Goal:** Capturing a URL correctly populates the database with text/HTML and stores images in MinIO.
        
- **Milestone 3: Media & Voice Pipelines**
    
    1. Implement the process_media and process_voicememo tasks.
        
    2. Containerize the Whisper STT model and create an internal API for it.
        
    3. **Goal:** Capturing a YouTube URL or uploading an audio file results in a correct transcript in the database.
        
- **Milestone 4: Frontend Implementation**
    
    1. Set up the React Native project using Expo.
        
    2. Implement user authentication screens and secure token storage.
        
    3. Build the core capture UIs and integrate with the Android Share Sheet.
        
    4. Connect the UI to the backend API.
        
    5. **Goal:** A fully functional client that can trigger and display the results of all capture pipelines.
        

#### 4.2. Testing Strategy

- **Unit Tests:**
    
    - **Backend (Pytest):** Test individual functions in isolation. Examples: Test the HTML parsing logic, test metadata extraction functions, test Pydantic validation models.
        
    - **Frontend (Jest / React Testing Library):** Test individual React components and utility functions. Example: Test the rendering of the CaptureForm, test the logic of the APIClient.
        
- **Integration Tests:**
    
    - **Backend:** Test the interaction between the API service and Celery. Verify that calling the API correctly enqueues a task, and that a worker can consume it and write to the database.
        
- **End-to-End (E2E) Tests:**
    
    - Use a framework like **Appium** (for mobile) or **Playwright** (for the Expo web client) to script full user scenarios.
        
    - **Example Scenario:**
        
        1. Launch the app and log in.
            
        2. Share a URL to the app.
            
        3. Confirm the capture.
            
        4. Poll the backend API or wait for a notification.
            
        5. Verify that the item appears in the user's list with the correct, processed content.
