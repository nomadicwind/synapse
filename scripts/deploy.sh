#!/bin/bash

# Deployment script for Synapse application
# Usage: ./scripts/deploy.sh [environment]
# Environment: dev, staging, prod (default: dev)

set -e  # Exit on any error

# Default environment
ENVIRONMENT=${1:-dev}

echo "🚀 Starting Synapse deployment for $ENVIRONMENT environment..."

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    echo "Loading environment variables from .env.$ENVIRONMENT"
    export $(grep -v '^#' .env.$ENVIRONMENT | xargs)
fi

# Check if required environment variables are set
REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "MINIO_ENDPOINT"
    "STT_SERVICE_URL"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Build Docker images
echo "🏗️  Building Docker images..."
docker-compose build --pull

# Stop existing containers if running
echo "⏹️  Stopping existing containers..."
docker-compose down

# Start services
echo "▶️  Starting services..."
if [ "$ENVIRONMENT" = "prod" ]; then
    docker-compose up -d --remove-orphans
else
    docker-compose up -d --remove-orphans
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "🔧 Initializing database..."
docker-compose exec api python setup_database.py

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec api alembic upgrade head

# Test health endpoints
echo "✅ Testing health endpoints..."
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
STT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)

if [ "$API_HEALTH" = "200" ] && [ "$STT_HEALTH" = "200" ]; then
    echo "✅ All services are healthy!"
else
    echo "❌ Some services are not healthy:"
    echo "   API Health: $API_HEALTH"
    echo "   STT Health: $STT_HEALTH"
    exit 1
fi

echo "🎉 Deployment completed successfully for $ENVIRONMENT environment!"
echo "   API available at: http://localhost:8000"
echo "   STT Service available at: http://localhost:5000"
