### **Product Design Document: Synapse**

**Component: 1.0 - Source (Capture & Textualization)**  
**Version:** Final 1.0  
**Date:** 2025-10-9  
**Status:** Approved for Implementation

### 1. Overview

This document details the design of the **Source** component for **Synapse**, a personal knowledge management system. The primary goal of this component is to provide a low-friction, reliable, and standardized method for capturing information from various inputs and converting it into a persistent, text-based format. This "textualization" process is the foundational first step in the Synapse pipeline. Its output—a clean, structured record—will serve as the input for the subsequent **Knowledge Distillation** and **Knowledge Consumption** components.

### 2. Guiding Principles

- **Zero-Friction Capture:** The user experience for capturing information must be near-instantaneous and require minimal cognitive load.
    
- **Asynchronous by Design:** The user-facing action of "capturing" should be decoupled from the backend processing to ensure a responsive UI.
    
- **Standardized Output:** Regardless of the input's origin (web page, video, voice), the output of this component is a consistent data structure: textual content, associated metadata, and linked media assets.
    
- **Content over Container:** The system prioritizes extracting the core knowledge (text, images) over preserving the original container (e.g., the raw HTML file or audio stream).
    

### 3. User Stories & Scenarios

- **US1: Capturing an Article:** As a user browsing a technical blog, I want to save the article with one click, preserving its text and embedded code/images, so I can read and analyze it later within Synapse.
    
- **US2: Capturing a Video's Content:** As a user watching a conference talk on YouTube, I want to capture the spoken content as text, so I can search and reference the key ideas without re-watching the video.
    
- **US3: Capturing a Fleeting Thought:** As a user on the go, I want to quickly record a voice memo on my phone, have it automatically transcribed, and saved to my Synapse inbox for later processing.
    
- **US4: Specifying Content Type:** As a user capturing a URL, I want to specify if it's an article, video, or audio clip, so the system can use the most effective method to process it.
    

### 4. High-Level Architecture

The capture process is designed as an asynchronous pipeline, enabling a responsive user experience.

codeCode

```
+-----------+    1. Capture Req.     +---------------+    2. Enqueue Job    +---------------+
| User      | -------------------> | API Gateway   | -----------------> | Message Queue |
| (React    |    (URL, type, data)   | (FastAPI)     |                    | (Redis/Celery)  |
| Native)   | <------------------- |               |                    +---------------+
+-----------+    (202 Accepted)      +---------------+                            | 3. Dequeue Job
                                                                                    |
                                                                                    V
                                                                    +---------------------------------+
                                                                    | Background Worker (Python/Celery) |
                                                                    |---------------------------------|
                                                                    | -> Dispatcher (reads source_type) |
                                                                    | -> Webpage Handler              |
                                                                    | -> Video/Audio Handler          |
                                                                    | -> Voice Memo Handler           |
                                                                    +---------------------------------+
                                                                                    | 4. Persist Data
                                                                                    |
                                                      +-----------------------------+-----------------------------+
                                                      V                                                           V
                                          +----------------------+                            +--------------------------+
                                          | Relational Database  |                            | Object Storage           |
                                          | (PostgreSQL)         |                            | (MinIO / S3)             |
                                          | - Text, Metadata     |                            | - Extracted Images       |
                                          +----------------------+                            +--------------------------+
```

### 5. Detailed Feature Breakdown

#### 5.1. Capture Interfaces (Client-Side)

- **Browser Extension:** Provides a pop-up to specify source_type: [Article/Page], [Video], [Audio].
    
- **Web Interface:** Provides a web page where users can manually paste URLs or local file paths and specify the source type for information capture.
    
- **Mobile App (Android):** Integrates with the native Android Share Sheet for URLs and text, including a dialog to select source_type. Provides an in-app feature for recording voice memos.
    

#### 5.2. Background Worker: Specialized Handlers

The Celery worker dispatches each job based on the source_type.

- **webpage Handler:** Fetches the page, extracts the main content using Readability.js, downloads and re-hosts all embedded images to internal object storage, rewrites image links in the clean HTML, and extracts a pure text version.
    
- **video/audio Handler:** Uses a tool like yt-dlp to download the audio stream, transcribes it using the STT service, and extracts relevant metadata (title, creator). The temporary audio file is discarded.
    
- **voicememo Handler:** Transcribes the provided raw audio data using the STT service.
    

### 6. Technology Stack

This stack is selected to prioritize **developer velocity, ease of expansion for AI features, and a seamless local-first development workflow.**

- **Backend Services (Python with FastAPI):** Chosen for its unparalleled AI/ML ecosystem, which is critical for future Knowledge Distillation features. FastAPI provides high productivity for API development.
    
- **Asynchronous Task Processing (Celery with Redis):** The standard in the Python ecosystem. Redis is lightweight for local development and serves as a simple, effective message broker.
    
- **Primary Database (PostgreSQL):** A robust, reliable relational database. Its feature set, including the pgvector extension, makes it a powerful and expandable foundation for both structured data and future semantic search capabilities.
    
- **Media/Asset Storage (Object Storage - MinIO/S3):** MinIO will be used for local development, providing a fully S3-compatible API. This ensures that a future transition to a cloud provider like AWS S3 requires only configuration changes, not code changes.
    
- **Speech-to-Text Engine (Whisper):** The self-hosted Whisper model provides state-of-the-art transcription quality while ensuring user privacy and cost-effectiveness.
    
- **Frontend Strategy (React Native, Expo, and Tailwind CSS):**
    
    - **Core Framework:** **React Native** is chosen to leverage existing web development skills (JavaScript/TypeScript) and a vast component ecosystem.
        
    - **Build Toolchain:** **Expo** will manage the build process and enable a single codebase to be deployed to mobile (Android) and the web.
        
    - **Styling:** **Tailwind CSS** (via **NativeWind**) will be used for rapid, consistent, and maintainable UI development.
        
- **Clarification on Related Technologies:**
    
    - **Node.js (Backend Alternative):** Intentionally not chosen in favor of Python's superior AI/ML libraries.
        
    - **Next.js (Future Web Evolution):** While our initial web app will be built with Expo for Web, Next.js represents the evolutionary path for a more powerful, dedicated web client in the future, with the ability to share logic with the React Native app.
        

### 7. Data Models and Schema

- **Core Entity: KnowledgeItem**
    
    - **Description:** Represents a single piece of captured information.
        
    - **Attributes:** ID, UserID, Title, SourceURL, ProcessedTextContent, ProcessedHTMLContent, Author, PublishedDate, Status (e.g., 'pending', 'processing', 'ready_for_distillation'), SourceType, CreatedAt, ProcessedAt.
        
- **Supporting Entity: ImageAsset**
    
    - **Description:** Tracks image assets extracted from webpage items.
        
    - **Attributes:** ID, KnowledgeItemID (links to parent item), StorageURL (internal URL in object storage), OriginalURL, MIMEType.
        
- **Relationships:**
    
    - A User has many KnowledgeItems.
        
    - A KnowledgeItem can have many ImageAssets.
        

---

### 8. Placeholder: Component 2.0 - Knowledge Distillation

**(To be defined)** This component will operate on knowledge_items with a status of ready_for_distillation. Responsibilities will include AI-powered summarization, automated tagging, entity recognition, and vector embedding generation.

### 9. Placeholder: Component 3.0 - Knowledge Consumption

**(To be defined)** This component will provide the user-facing interfaces for interacting with the processed knowledge, including an omni-search interface, a rich content viewer, a note-taking editor with bi-directional linking, and knowledge visualization tools.
