# Synapse Service Startup Guide

This guide provides step-by-step instructions for starting all services required for textualizing sources in the Synapse project without using Docker.

## Prerequisites

Before starting the services, ensure you have the following installed:

- **Python**: Version 3.9 or later
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

**On macOS:**
```bash
brew install minio/stable/minio
mkdir -p ~/minio-data
minio server ~/minio-data --console-address ":9001"
```

**On Linux:**
```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
mkdir -p ~/minio-data
./minio server ~/minio-data --console-address ":9001"
```

> **Note**: If you encounter "file access denied" errors, it means you don't have write permissions to the specified directory. Using `~/minio-data` (in your home directory) ensures you have the necessary permissions.

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
celery -A app worker --loglevel=info
```

> **Note**: If you encounter "Unable to load celery application" errors, ensure you're using the correct module path. The Celery application is defined in `app.py`, so use `celery -A app worker` (not `app.worker`).

#### 3.3. Start STT Service
```bash
cd infrastructure/stt_service
python app.py
```

#### 3.4. Start Web Interface
```bash
cd frontend/mobile
npm install
npm run web
```

#### 3.5. Start Backend Service Console (Operators)
The console provides a dashboard for monitoring health, queue depth, and retrying failed captures.

```bash
cd console
npm install   # first run only
npm run dev
```

- Default URL: `http://localhost:5173`
- Configure the API origin via `VITE_CONSOLE_API_BASE_URL`
- Ensure the FastAPI service allows the console origin by setting `CONSOLE_ALLOWED_ORIGINS` (default includes `http://localhost:5173`)
- Optional security: set `CONSOLE_API_TOKEN` on the API and `VITE_CONSOLE_API_TOKEN` on the console to require an `X-Console-Token` header for every console request

> **Note**: The web interface is built using React Native with Expo, which supports web deployment. This will start the web interface at http://localhost:19006.

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

- **Web Interface**: http://localhost:19006
  - The main user interface for capturing and managing knowledge items

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

#### 6. Pillow Dependency Conflict
If you encounter an error like "mineru 2.1.5 requires pillow>=11.0.0, but you have pillow 10.4.0 which is incompatible":
- Reinstall dependencies with the updated requirements.txt files:
```bash
# API Service
cd backend/api
pip install -r requirements.txt --upgrade

# Worker Service
cd ../worker
pip install -r requirements.txt --upgrade

# STT Service
cd ../../infrastructure/stt_service
pip install -r requirements.txt --upgrade
```
- This will upgrade Pillow to version 11.0.0 or higher, resolving the conflict.

#### 3. Database Initialization Issues
If you encounter database errors:
- Ensure PostgreSQL is running
- Verify the database user and permissions
- Re-run database initialization: `python setup_database.py`

#### 4. MinIO Access Issues
If you can't access the MinIO console:
- Ensure you're using the correct credentials (username: synapse, password: synapse123)
- Check that the MinIO service is running
- Verify you have write permissions to the data directory (use `~/minio-data` to avoid permission issues)

#### 5. Worker Service Not Processing Tasks
If the worker service appears to be running but not processing tasks:
- Check the worker terminal logs
- Ensure Redis is running and accessible
- Restart the worker service
- Verify you're using the correct command: `celery -A app worker --loglevel=info`

#### 6. npm Dependency Installation Issues
If you encounter errors like "No matching version found for react-native-reanimated@^4.11.0" when running `npm install`:
- This is typically due to version compatibility issues between React Native and its dependencies
- Check the React Native version in package.json (currently 0.81.4)
- Update incompatible dependencies to compatible versions:
  ```bash
  # For React Native 0.81.x, use react-native-reanimated v3.x
  # Edit package.json to change:
  # "react-native-reanimated": "^3.10.1"
  ```
- Delete node_modules and package-lock.json, then reinstall:
  ```bash
  rm -rf node_modules package-lock.json
  npm install
  ```

### Useful PostgreSQL Commands

When working with the Synapse database, these PostgreSQL commands can be helpful:

```bash
# Connect to the synapse database
psql -U synapse -d synapse

# List all tables in the database
\dt

# Describe a specific table (show column names, types, constraints)
\d table_name

# Describe the knowledge_items table
\d knowledge_items

# Describe the image_assets table
\d image_assets

# View first 10 rows from a table
SELECT * FROM table_name LIMIT 10;

# Count rows in a table
SELECT COUNT(*) FROM table_name;

# View database schema (list all tables with their columns)
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;

# Exit psql
\q
```

### Cleaning Up Database Data

If you need to clean up existing data (trash) in the PostgreSQL database, you have several options:

#### Option 1: Delete All Records (Keep Database Structure)
```bash
# Connect to the database
psql -U synapse -d synapse

# Delete all records from knowledge_items (this will also delete related image_assets due to CASCADE)
DELETE FROM knowledge_items;

# Verify deletion
SELECT COUNT(*) FROM knowledge_items;
SELECT COUNT(*) FROM image_assets;
```

#### Option 2: Reset Database to Initial State
```bash
# Drop and recreate the database
psql -U postgres -c "DROP DATABASE IF EXISTS synapse;"
psql -U postgres -c "CREATE DATABASE synapse OWNER synapse;"

# Re-run database initialization
cd backend/api
python setup_database.py
```

#### Option 3: Complete Database Reset (Drop and Recreate Everything)
```bash
# Drop the database and user
psql -U postgres -c "DROP DATABASE IF EXISTS synapse;"
psql -U postgres -c "DROP USER IF EXISTS synapse;"

# Re-run the complete setup
cd backend/api
python setup_database.py
```

> **Note**: Be very careful when running these commands as they will permanently delete data. Always ensure you have backups if needed.

## Stopping Services

To stop all services, simply close the terminal windows where each service is running, or use Ctrl+C in each terminal.

## Updating Services

If you've made changes to the code:
- For Python services, restart the service to pick up changes
- For services with auto-reload (like the API with --reload flag), changes will be picked up automatically

## Additional Notes

- The system is designed to be resilient. If a service goes down, you can restart it individually without affecting others.
- Data is persisted in local storage, so your database and MinIO data will survive service restarts.
- For development, the API and Worker services use local code directories, so code changes will be reflected without rebuilding containers.
