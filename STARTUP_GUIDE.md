# Synapse Service Startup Guide

This guide provides step-by-step instructions for starting all services required for textualizing sources in the Synapse project without using Docker.

## Prerequisites

Before starting the services, ensure you have the following installed:

- **Python**: Version 3.11 or later
- **Node.js**: Version 16 or later (for frontend)
- **PostgreSQL**: Version 15 or later
- **Redis**: Version 7 or later
- **MinIO**: Latest version
- **FFmpeg**: For audio/video processing (required for STT service)
- **Git**: For cloning the repository (if not already cloned)
- **Minimum System Requirements**:
  - 4GB RAM (8GB recommended)
  - 2 CPU cores
  - 5GB free disk space

## Step-by-Step Startup Process

### 1. Clone the Repository (if not already done)
```bash
git clone https://github.com/nomadicwind/synapse.git
cd synapse
```

### 2. Install and Configure Services

#### 2.1. PostgreSQL Setup
Install PostgreSQL locally and create a database:
```bash
# Create database and user (adjust for your PostgreSQL installation)
createdb synapse
createuser synapse
psql -c "ALTER USER synapse WITH PASSWORD 'synapse';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE synapse TO synapse;"
```

#### 2.2. Redis Setup
Install Redis and start the service:
```bash
# On macOS with Homebrew
brew install redis
brew services start redis

# On Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
```

#### 2.3. MinIO Setup
Install MinIO and start the service:
```bash
# Download and install MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /data --console-address ":9001"
```

#### 2.4. Install Python Dependencies
Install dependencies for API, Worker, and STT services:
```bash
# API Service
cd backend/api
pip install -r requirements.txt

# Worker Service
cd ../worker
pip install -r requirements.txt
pip install yt-dlp

# STT Service
cd ../../infrastructure/stt_service
pip install -r requirements.txt
```

### 3. Start All Services

Start each service in a separate terminal:

#### 3.1. Start API Service
```bash
cd backend/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3.2. Start Worker Service
```bash
cd backend/worker
celery -A app.worker worker --loglevel=info
```

#### 3.3. Start STT Service
```bash
cd infrastructure/stt_service
python app.py
```

### 3. Verify Services Are Running
Check that all services are running successfully by accessing their health endpoints:

```bash
# Test API Service
curl -X GET http://localhost:8000/health

# Test STT Service
curl -X GET http://localhost:5000/health

# Test Redis
redis-cli ping

# Test PostgreSQL
psql -U synapse -d synapse -c "SELECT 1;"
```

### 4. Access Service Interfaces
Once all services are running, you can access them at the following URLs:

- **API Service**: http://localhost:8000
  - API documentation: http://localhost:8000/docs
  - Health check: http://localhost:8000/health

- **MinIO Console**: http://localhost:9001
  - Username: synapse
  - Password: synapse123

- **STT Service**: http://localhost:5000
  - Health check: http://localhost:5000/health

### 5. Initialize Database (First Time Only)
If this is your first time starting the services, initialize the database:

```bash
cd backend/api
python setup_database.py
```

## Verification Steps

To ensure all services are working correctly, follow these verification steps:

### 1. Test API Service
```bash
curl -X GET http://localhost:8000/health
```
Expected response: `{"status":"healthy"}`

### 2. Test Database Connection
```bash
psql -U synapse -d synapse -c "SELECT 1;"
```
Expected response: Should return "1" indicating successful connection.

### 3. Test Redis Connection
```bash
redis-cli ping
```
Expected response: `PONG`

### 4. Test MinIO Connection
```bash
curl -f http://localhost:9000/minio/health/live
```
Expected response: Should return a 200 status code.

### 5. Test STT Service
```bash
curl -X GET http://localhost:5000/health
```
Expected response: `{"status":"healthy"}`

## Troubleshooting Tips

### Common Issues and Solutions

#### 1. Port Conflicts
If you get errors about ports being in use, you can either:
- Stop the conflicting services on your host machine, or
- Modify the port configurations in the respective service files

#### 2. Services Not Starting
If services fail to start:
- Check the terminal logs for each service
- Ensure all dependencies are installed
- Verify environment variables are set correctly

#### 3. Database Initialization Issues
If you encounter database errors:
- Ensure PostgreSQL is running
- Verify the database user and permissions
- Re-run database initialization: `python setup_database.py`

#### 4. MinIO Access Issues
If you can't access the MinIO console:
- Ensure you're using the correct credentials (username: synapse, password: synapse123)
- Check that the MinIO service is running

#### 5. Worker Service Not Processing Tasks
If the worker service appears to be running but not processing tasks:
- Check the worker terminal logs
- Ensure Redis is running and accessible
- Restart the worker service

## Stopping Services

To stop all services, simply close the terminal windows where each service is running, or use Ctrl+C in each terminal.

## Updating Services

If you've made changes to the code:
- For Python services, restart the service to pick up changes
- For services with auto-reload (like the API with --reload flag), changes will be picked up automatically

## Additional Notes

- The system is designed to be resilient. If a service goes down, you can restart it individually without affecting others.
- Data is persisted in Docker volumes, so your database and MinIO data will survive container restarts.
- For development, the API and Worker services mount local code directories, so code changes will be reflected without rebuilding containers.
