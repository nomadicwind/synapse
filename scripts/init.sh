#!/bin/bash

# Initialization script for Synapse application
# Usage: ./scripts/init.sh

set -e  # Exit on any error

echo "🔧 Starting Synapse initialization..."

# Create required directories
echo "📁 Creating required directories..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/minio

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please review and update the .env file with your actual configuration values"
fi

# Initialize Git submodules if any
if [ -f ".gitmodules" ]; then
    echo "🔄 Initializing Git submodules..."
    git submodule init
    git submodule update
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r backend/api/requirements.txt
pip install -r backend/worker/requirements.txt
pip install -r infrastructure/stt_service/requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend/mobile && npm install && cd ../..

# Initialize database
echo "🗄️  Setting up database..."
python backend/api/setup_database.py

# Run migrations
echo "🔄 Running database migrations..."
cd backend && alembic upgrade head && cd ..

# Build Docker images
echo "🏗️  Building Docker images..."
docker-compose build

# Create test data (optional)
if [ "$1" = "--with-test-data" ]; then
    echo "🧪 Creating test data..."
    python scripts/create_test_data.py
fi

echo "✅ Initialization completed successfully!"
echo "   To start the application: docker-compose up"
echo "   To run tests: pytest backend/api/test_main.py"
