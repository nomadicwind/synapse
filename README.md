# Synapse - AI-Powered Knowledge Capture System

![Synapse Architecture](https://via.placeholder.com/800x400?text=Synapse+Architecture+Diagram)

Synapse is an AI-powered knowledge capture system that helps users collect, process, and organize information from various sources including webpages, videos, audio, and voice memos. The system processes captured content using AI services and prepares it for distillation into structured knowledge.

## Key Features

- **Multi-source Capture**: Capture content from webpages, YouTube videos, audio files, and voice memos
- **AI Processing**: Automatically extract and process content using AI services
- **Knowledge Organization**: Store and organize processed content for easy retrieval
- **Mobile-First Design**: Native mobile application for on-the-go knowledge capture
- **Extensible Architecture**: Modular design that can be extended with additional processing capabilities

## Architecture Overview

Synapse follows a microservices architecture with the following components:

1. **Frontend Mobile App**: React Native application for capturing and viewing content
2. **FastAPI Backend**: REST API for handling capture requests and serving processed content
3. **Celery Worker**: Background task processor for content extraction and AI processing
4. **STT Service**: Speech-to-text service for processing audio content
5. **PostgreSQL Database**: Stores metadata and processed content
6. **MinIO Storage**: Object storage for images and media files
7. **Redis**: Message broker for Celery tasks

For detailed architecture information, see [Technical Design Document](doc/tech_design.md).

## Prerequisites

Before setting up Synapse, ensure you have the following installed:

- Docker and Docker Compose
- Python 3.9+
- Node.js 16+
- React Native development environment (for mobile app development)

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/nomadicwind/synapse.git
cd synapse
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Update the `.env` file with your configuration values.

### 3. Start the services

```bash
docker-compose up -d
```

This will start all the required services including:
- PostgreSQL database
- Redis message broker
- MinIO storage
- FastAPI backend
- Celery worker
- STT service

### 4. Set up the database

```bash
docker-compose exec api python setup_database.py
```

### 5. Run the mobile app

```bash
cd frontend/mobile
npm install
npx react-native run-ios  # or run-android
```

## Configuration

### Environment Variables

Key environment variables that can be configured:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string for Celery
- `MINIO_ENDPOINT`: MinIO storage endpoint
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `STT_SERVICE_URL`: URL for the STT service

See [docker-compose.yml](docker-compose.yml) for default values and service configurations.

## Running the Application

Once all services are running:

1. The FastAPI backend will be available at `http://localhost:8000`
2. The API documentation can be accessed at `http://localhost:8000/docs`
3. The mobile app can be run on iOS or Android simulators/devices
4. MinIO dashboard is available at `http://localhost:9001` (credentials: minioadmin/minioadmin)

## Testing

Run all tests:

```bash
npm test
```

Run backend API tests:

```bash
cd backend/api && python -m pytest test_main.py -v
```

Run worker tests:

```bash
cd backend/worker && python -m pytest test_app.py -v
```

Run STT service tests:

```bash
cd infrastructure/stt_service && python -m pytest test_app.py -v
```

## Documentation

For detailed information about the project:

- [Product Design Document](doc/product_design.md) - User stories, requirements, and product vision
- [Technical Design Document](doc/tech_design.md) - System architecture, data models, and technical specifications
- [API Documentation](http://localhost:8000/docs) - Interactive API documentation (when server is running)

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

Please ensure your code follows the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, bug reports, or feature requests, please open an issue on the [GitHub repository](https://github.com/nomadicwind/synapse/issues).
