#!/bin/bash

# Script to start all Synapse services
# Usage: ./start_all_services.sh [options]
# Options:
#   --api-port PORT        Port for API service (default: 8000)
#   --worker               Start worker service
#   --stt-port PORT        Port for STT service (default: 5000)
#   --mobile               Start mobile frontend development server
#   --all                  Start all services (default)
#   --help                 Show this help message

set -e

# Default values
API_PORT=8000
STT_PORT=5000
START_API=true
START_WORKER=true
START_STT=true
START_MOBILE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-port)
            API_PORT="$2"
            shift 2
            ;;
        --worker)
            START_WORKER=true
            shift
            ;;
        --stt-port)
            STT_PORT="$2"
            shift 2
            ;;
        --mobile)
            START_MOBILE=true
            shift
            ;;
        --all)
            START_API=true
            START_WORKER=true
            START_STT=true
            START_MOBILE=true
            shift
            ;;
        --help)
            grep '^#' "$0" | cut -c4-
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Starting Synapse services..."

# Function to start API service
start_api() {
    echo "Starting API service on port $API_PORT..."
    cd backend/api
    source .venv-py39/bin/activate
    uvicorn main:app --host 0.0.0.0 --port $API_PORT &
    API_PID=$!
    cd ../..
    echo "API service started with PID $API_PID"
}

# Function to start Worker service
start_worker() {
    echo "Starting Worker service..."
    cd backend/worker
    source .venv-py39/bin/activate
    python app.py &
    WORKER_PID=$!
    cd ../..
    echo "Worker service started with PID $WORKER_PID"
}

# Function to start STT service
start_stt() {
    echo "Starting STT service on port $STT_PORT..."
    cd infrastructure/stt_service
    source ../../backend/api/.venv-py39/bin/activate
    uvicorn app:app --host 0.0.0.0 --port $STT_PORT &
    STT_PID=$!
    cd ../..
    echo "STT service started with PID $STT_PID"
}

# Function to start Mobile frontend
start_mobile() {
    echo "Starting Mobile frontend development server..."
    cd frontend/mobile
    npm start &
    MOBILE_PID=$!
    cd ../..
    echo "Mobile frontend started with PID $MOBILE_PID"
}

# Start services based on flags
if [ "$START_API" = true ]; then
    start_api
fi

if [ "$START_WORKER" = true ]; then
    start_worker
fi

if [ "$START_STT" = true ]; then
    start_stt
fi

if [ "$START_MOBILE" = true ]; then
    start_mobile
fi

echo "All selected services have been started."

# Display running services
echo ""
echo "Running services:"
if [ "$START_API" = true ]; then
    echo "- API Service (PID: $API_PID, Port: $API_PORT)"
fi
if [ "$START_WORKER" = true ]; then
    echo "- Worker Service (PID: $WORKER_PID)"
fi
if [ "$START_STT" = true ]; then
    echo "- STT Service (PID: $STT_PID, Port: $STT_PORT)"
fi
if [ "$START_MOBILE" = true ]; then
    echo "- Mobile Frontend (PID: $MOBILE_PID)"
fi

echo ""
echo "To stop all services, press Ctrl+C"

# Wait for Ctrl+C
trap 'echo "Stopping all services..."; 
      if [ "$START_API" = true ]; then kill $API_PID 2>/dev/null; fi;
      if [ "$START_WORKER" = true ]; then kill $WORKER_PID 2>/dev/null; fi;
      if [ "$START_STT" = true ]; then kill $STT_PID 2>/dev/null; fi;
      if [ "$START_MOBILE" = true ]; then kill $MOBILE_PID 2>/dev/null; fi;
      echo "All services stopped."; exit 0' INT

wait
