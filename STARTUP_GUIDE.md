# Synapse Service Startup Guide

This guide provides step-by-step instructions for starting all services required for textualizing sources in the Synapse project.

## Prerequisites

Before starting the services, ensure you have the following installed:

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 1.29 or later (included with Docker Desktop)
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

### 2. Start All Services
The Synapse system uses Docker Compose to manage all services. Run the following command to start all services:

```bash
docker-compose up -d
```

This will start the following services in the background:
- **PostgreSQL Database** (db) - Port 5432
- **Redis Message Broker** (redis) - Port 6379
- **MinIO Object Storage** (minio) - Ports 9000 (API) and 9001 (Console)
- **API Service** (api) - Port 8000
- **Worker Service** (worker) - No exposed port (runs in background)
- **STT Service** (stt_service) - Port 5000

### 3. Verify Services Are Running
Check that all services are running successfully:

```bash
docker-compose ps
```

You should see all services with a status of "Up" or "healthy".

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
If this is your first time starting the services, you may need to initialize the database:

```bash
docker-compose exec api python setup_database.py
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
docker-compose exec db psql -U synapse -d synapse -c "SELECT 1;"
```
Expected response: Should return "1" indicating successful connection.

### 3. Test Redis Connection
```bash
docker-compose exec redis redis-cli ping
```
Expected response: `PONG`

### 4. Test MinIO Connection
```bash
docker-compose exec api curl -f http://minio:9000/minio/health/live
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
- Modify the port mappings in docker-compose.yml to use different host ports

#### 2. Services Not Starting
If services fail to start or show unhealthy status:
```bash
# Check logs for a specific service
docker-compose logs <service_name>

# Example: Check API service logs
docker-compose logs api
```

#### 3. Database Initialization Issues
If you encounter database errors:
```bash
# Restart the database service
docker-compose restart db

# Re-run database initialization
docker-compose exec api python setup_database.py
```

#### 4. MinIO Access Issues
If you can't access the MinIO console:
- Ensure you're using the correct credentials (username: synapse, password: synapse123)
- Check that the MinIO service is running: `docker-compose ps minio`

#### 5. Worker Service Not Processing Tasks
If the worker service appears to be running but not processing tasks:
- Check the worker logs: `docker-compose logs worker`
- Ensure Redis is running and accessible
- Restart the worker service: `docker-compose restart worker`

## Stopping Services

To stop all services, run:
```bash
docker-compose down
```

To stop services but keep data volumes (database and MinIO data):
```bash
docker-compose down --volumes
```

## Updating Services

If you've made changes to the code and need to rebuild and restart services:

```bash
# Rebuild and restart specific service
docker-compose up -d --build <service_name>

# Rebuild and restart all services
docker-compose up -d --build
```

## Additional Notes

- The system is designed to be resilient. If a service goes down, you can restart it individually without affecting others.
- Data is persisted in Docker volumes, so your database and MinIO data will survive container restarts.
- For development, the API and Worker services mount local code directories, so code changes will be reflected without rebuilding containers.
