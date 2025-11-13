#!/bin/bash

# Script to start all Synapse services
# Usage: ./start_all_services.sh [options]
# Options:
#   --api-port PORT        Port for API service (default: 8000)
#   --worker               Start worker service
#   --stt-port PORT        Port for STT service (default: 5000)
#   --mobile               Start mobile frontend development server
#   --console              Start the backend console (Vite dev server)
#   --all                  Start all services (default)
#   --stop                 Stop all running services
#   --help                 Show this help message

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Change to the project root directory
cd "$SCRIPT_DIR/.."
PROJECT_ROOT="$(pwd)"

# Load environment variables from .env if present
if [ -f ".env" ]; then
    # shellcheck disable=SC2046,SC1091
    set -a
    source .env
    set +a
fi

# Track whether user pre-set dependency hosts/ports
USER_SET_POSTGRES_HOST=false
USER_SET_POSTGRES_PORT=false
USER_SET_REDIS_HOST=false
USER_SET_REDIS_PORT=false
USER_SET_MINIO_HOST=false
USER_SET_MINIO_PORT=false
USER_SET_MINIO_CONSOLE=false
if [ -n "${POSTGRES_HOST:-}" ]; then USER_SET_POSTGRES_HOST=true; fi
if [ -n "${POSTGRES_PORT:-}" ]; then USER_SET_POSTGRES_PORT=true; fi
if [ -n "${REDIS_HOST:-}" ]; then USER_SET_REDIS_HOST=true; fi
if [ -n "${REDIS_PORT:-}" ]; then USER_SET_REDIS_PORT=true; fi
if [ -n "${MINIO_HOST:-}" ]; then USER_SET_MINIO_HOST=true; fi
if [ -n "${MINIO_API_PORT:-}" ]; then USER_SET_MINIO_PORT=true; fi
if [ -n "${MINIO_CONSOLE_PORT:-}" ]; then USER_SET_MINIO_CONSOLE=true; fi

# Default dependency values (overridable via env)
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
MINIO_HOST=${MINIO_HOST:-localhost}
MINIO_API_PORT=${MINIO_API_PORT:-9000}
MINIO_CONSOLE_PORT=${MINIO_CONSOLE_PORT:-9001}
MINIO_DATA_DIR=${MINIO_DATA_DIR:-$HOME/minio-data}
MINIO_LOG_FILE=${MINIO_LOG_FILE:-$PROJECT_ROOT/logs/minio.log}
MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-minioadmin}

# Track dependency stop commands to clean up if we started them
DEPENDENCY_STOP_COMMANDS=()
MINIO_PID=""

# Parse connection details from URLs when available so we do not try to manage remote hosts
parse_url_components() {
    local url=$1
    local prefix=$2
    python - "$url" "$prefix" <<'PY'
import sys, urllib.parse
url = sys.argv[1]
prefix = sys.argv[2]
if not url:
    sys.exit(0)
parsed = urllib.parse.urlparse(url)
if parsed.hostname:
    print(f"{prefix}_HOST_FROM_URL={parsed.hostname}")
if parsed.port:
    print(f"{prefix}_PORT_FROM_URL={parsed.port}")
PY
}

if [ -n "$DATABASE_URL" ]; then
    eval "$(parse_url_components "$DATABASE_URL" "POSTGRES")"
    if [ -n "${POSTGRES_HOST_FROM_URL:-}" ] && [ "$USER_SET_POSTGRES_HOST" = false ]; then
        POSTGRES_HOST="$POSTGRES_HOST_FROM_URL"
    fi
    if [ -n "${POSTGRES_PORT_FROM_URL:-}" ] && [ "$USER_SET_POSTGRES_PORT" = false ]; then
        POSTGRES_PORT="$POSTGRES_PORT_FROM_URL"
    fi
fi
if [ -n "$CELERY_BROKER_URL" ]; then
    eval "$(parse_url_components "$CELERY_BROKER_URL" "REDIS")"
    if [ -n "${REDIS_HOST_FROM_URL:-}" ] && [ "$USER_SET_REDIS_HOST" = false ]; then
        REDIS_HOST="$REDIS_HOST_FROM_URL"
    fi
    if [ -n "${REDIS_PORT_FROM_URL:-}" ] && [ "$USER_SET_REDIS_PORT" = false ]; then
        REDIS_PORT="$REDIS_PORT_FROM_URL"
    fi
fi
if [ -n "$MINIO_ENDPOINT" ]; then
    eval "$(parse_url_components "$MINIO_ENDPOINT" "MINIO")"
    if [ -n "${MINIO_HOST_FROM_URL:-}" ] && [ "$USER_SET_MINIO_HOST" = false ]; then
        MINIO_HOST="$MINIO_HOST_FROM_URL"
    fi
    if [ -n "${MINIO_PORT_FROM_URL:-}" ] && [ "$USER_SET_MINIO_PORT" = false ]; then
        MINIO_API_PORT="$MINIO_PORT_FROM_URL"
    fi
fi

register_dependency_stop() {
    local cmd=$1
    if [ -n "$cmd" ]; then
        DEPENDENCY_STOP_COMMANDS+=("$cmd")
    fi
}

# Default values
API_PORT=8000
STT_PORT=5000
START_API=true
START_WORKER=true
START_STT=true
START_MOBILE=false
START_CONSOLE=false
STOP_SERVICES=false

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
        --console)
            START_CONSOLE=true
            shift
            ;;
        --all)
            START_API=true
            START_WORKER=true
            START_STT=true
            START_MOBILE=true
            START_CONSOLE=true
            shift
            ;;
        --help)
            grep '^#' "$0" | cut -c4-
            exit 0
            ;;
        --stop)
            STOP_SERVICES=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to check if a port is in use
is_port_in_use() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Network utility helpers
is_service_up() {
    local host=$1
    local port=$2
    if command -v nc > /dev/null 2>&1; then
        nc -z "$host" "$port" >/dev/null 2>&1
    else
        (echo > /dev/tcp/"$host"/"$port") >/dev/null 2>&1
    fi
}

wait_for_service() {
    local host=$1
    local port=$2
    local name=$3
    local attempts=${4:-20}
    local delay=${5:-1}

    for ((i=1; i<=attempts; i++)); do
        if is_service_up "$host" "$port"; then
            echo "$name is available on $host:$port"
            return 0
        fi
        sleep "$delay"
    done

    echo "ERROR: Timed out waiting for $name on $host:$port"
    return 1
}

start_postgres_service() {
    if [ -n "$POSTGRES_START_CMD" ]; then
        if eval "$POSTGRES_START_CMD"; then
            register_dependency_stop "${POSTGRES_STOP_CMD:-}"
            return 0
        fi
        return 1
    fi

    if command -v brew >/dev/null 2>&1; then
        local brew_service
        brew_service=$(brew services list 2>/dev/null | awk 'NR>1 && $1 ~ /^postgresql/ {print $1; exit}')
        if [ -n "$brew_service" ]; then
            if brew services start "$brew_service"; then
                register_dependency_stop "brew services stop $brew_service"
                return 0
            fi
        fi
    fi

    if command -v pg_ctl >/dev/null 2>&1 && [ -n "$POSTGRES_DATA_DIR" ]; then
        if pg_ctl -D "$POSTGRES_DATA_DIR" -l "$POSTGRES_DATA_DIR/server.log" start; then
            register_dependency_stop "pg_ctl -D \"$POSTGRES_DATA_DIR\" stop"
            return 0
        fi
    fi

    if command -v systemctl >/dev/null 2>&1; then
        local candidates=("postgresql.service" "postgresql" "postgresql@15-main.service")
        for svc in "${candidates[@]}"; do
            if systemctl list-unit-files 2>/dev/null | grep -q "$svc"; then
                if sudo systemctl start "$svc"; then
                    register_dependency_stop "sudo systemctl stop $svc"
                    return 0
                fi
            fi
        done
    fi

    return 1
}

start_redis_service() {
    if [ -n "$REDIS_START_CMD" ]; then
        if eval "$REDIS_START_CMD"; then
            register_dependency_stop "${REDIS_STOP_CMD:-}"
            return 0
        fi
        return 1
    fi

    if command -v brew >/dev/null 2>&1; then
        if brew services list 2>/dev/null | awk 'NR>1 {print $1}' | grep -q "^redis"; then
            if brew services start redis >/dev/null 2>&1; then
                register_dependency_stop "brew services stop redis"
                return 0
            fi
        fi
    fi

    if command -v systemctl >/dev/null 2>&1; then
        local redis_units=("redis-server.service" "redis.service" "redis")
        for svc in "${redis_units[@]}"; do
            if systemctl list-unit-files 2>/dev/null | grep -q "$svc"; then
                if sudo systemctl start "$svc"; then
                    register_dependency_stop "sudo systemctl stop $svc"
                    return 0
                fi
            fi
        done
    fi

    if command -v redis-server >/dev/null 2>&1; then
        if redis-server --daemonize yes >/dev/null 2>&1; then
            register_dependency_stop "redis-cli shutdown"
            return 0
        fi
    fi

    return 1
}

start_minio_service() {
    mkdir -p "$MINIO_DATA_DIR"
    mkdir -p "$(dirname "$MINIO_LOG_FILE")"
    echo "Starting MinIO (logs: $MINIO_LOG_FILE)..."
    MINIO_ROOT_USER="$MINIO_ROOT_USER" MINIO_ROOT_PASSWORD="$MINIO_ROOT_PASSWORD" \
        minio server "$MINIO_DATA_DIR" --address ":$MINIO_API_PORT" --console-address ":$MINIO_CONSOLE_PORT" \
        > "$MINIO_LOG_FILE" 2>&1 &
    MINIO_PID=$!
    register_dependency_stop "kill $MINIO_PID"
    sleep 2
    if ps -p "$MINIO_PID" >/dev/null 2>&1; then
        echo "MinIO started with PID $MINIO_PID"
        return 0
    fi
    echo "Failed to start MinIO (see $MINIO_LOG_FILE)"
    return 1
}

ensure_postgres() {
    if [[ "$POSTGRES_HOST" != "localhost" && "$POSTGRES_HOST" != "127.0.0.1" ]]; then
        echo "Skipping PostgreSQL management (host set to $POSTGRES_HOST)"
        return
    fi

    echo "Checking PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
    if is_service_up "$POSTGRES_HOST" "$POSTGRES_PORT"; then
        echo "PostgreSQL is already running."
        return
    fi

    echo "PostgreSQL not detected, attempting to start..."
    if start_postgres_service && wait_for_service "$POSTGRES_HOST" "$POSTGRES_PORT" "PostgreSQL"; then
        echo "PostgreSQL started successfully."
    else
        echo "ERROR: Unable to start PostgreSQL automatically. Please start it manually and rerun the script."
        exit 1
    fi
}

ensure_redis() {
    if [[ "$REDIS_HOST" != "localhost" && "$REDIS_HOST" != "127.0.0.1" ]]; then
        echo "Skipping Redis management (host set to $REDIS_HOST)"
        return
    fi

    echo "Checking Redis at $REDIS_HOST:$REDIS_PORT..."
    if is_service_up "$REDIS_HOST" "$REDIS_PORT"; then
        echo "Redis is already running."
        return
    fi

    echo "Redis not detected, attempting to start..."
    if start_redis_service && wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"; then
        echo "Redis started successfully."
    else
        echo "ERROR: Unable to start Redis automatically. Please start it manually and rerun the script."
        exit 1
    fi
}

ensure_minio() {
    if [[ "$MINIO_HOST" != "localhost" && "$MINIO_HOST" != "127.0.0.1" ]]; then
        echo "Skipping MinIO management (endpoint host is $MINIO_HOST)"
        return
    fi

    echo "Checking MinIO at $MINIO_HOST:$MINIO_API_PORT..."
    if is_service_up "$MINIO_HOST" "$MINIO_API_PORT"; then
        echo "MinIO is already running."
        return
    fi

    if ! command -v minio >/dev/null 2>&1; then
        echo "ERROR: MinIO binary not found on PATH. Install MinIO or adjust MINIO_ENDPOINT."
        exit 1
    fi

    echo "MinIO not detected, attempting to start..."
    if start_minio_service && wait_for_service "$MINIO_HOST" "$MINIO_API_PORT" "MinIO"; then
        echo "MinIO started successfully. Console available on port $MINIO_CONSOLE_PORT."
    else
        echo "ERROR: Unable to start MinIO automatically. Check $MINIO_LOG_FILE for details."
        exit 1
    fi
}

# Function to stop all running services
stop_services() {
    echo "Stopping all services..."
    if [ "$START_API" = true ] && [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null && echo "API service stopped" || echo "API service was not running"
    fi
    if [ "$START_WORKER" = true ] && [ ! -z "$WORKER_PID" ]; then
        kill $WORKER_PID 2>/dev/null && echo "Worker service stopped" || echo "Worker service was not running"
    fi
    if [ "$START_STT" = true ] && [ ! -z "$STT_PID" ]; then
        kill $STT_PID 2>/dev/null && echo "STT service stopped" || echo "STT service was not running"
    fi
    if [ "$START_MOBILE" = true ] && [ ! -z "$MOBILE_PID" ]; then
        kill $MOBILE_PID 2>/dev/null && echo "Mobile frontend stopped" || echo "Mobile frontend was not running"
    fi
    if [ "$START_CONSOLE" = true ] && [ ! -z "$CONSOLE_PID" ]; then
        kill $CONSOLE_PID 2>/dev/null && echo "Console app stopped" || echo "Console app was not running"
    fi
    if [ -n "$MINIO_PID" ] && ps -p "$MINIO_PID" >/dev/null 2>&1; then
        kill "$MINIO_PID" 2>/dev/null && echo "MinIO stopped" || echo "MinIO was not running"
    fi
    if [ "${#DEPENDENCY_STOP_COMMANDS[@]}" -gt 0 ]; then
        for cmd in "${DEPENDENCY_STOP_COMMANDS[@]}"; do
            if [ -n "$cmd" ]; then
                eval "$cmd" >/dev/null 2>&1 || true
            fi
        done
        echo "Dependency services stopped (where applicable)."
    fi
    echo "All services stopped."
}

# If --stop is specified, stop services and exit
if [ "$STOP_SERVICES" = true ]; then
    stop_services
    exit 0
fi

echo "Ensuring dependent services..."
ensure_postgres
ensure_redis
ensure_minio

echo "Starting Synapse services..."

# Function to start API service
start_api() {
    echo "Starting API service on port $API_PORT..."
    
    # Check if port is already in use
    if is_port_in_use $API_PORT; then
        echo "ERROR: Port $API_PORT is already in use!"
        echo "Please either:"
        echo "1. Stop the process using port $API_PORT (run 'lsof -i :$API_PORT' to find it)"
        echo "2. Use a different port with --api-port PORT"
        exit 1
    fi
    
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
    source ../../backend/api/.venv-py39/bin/activate
    celery -A app:celery_app worker --loglevel=info &
    WORKER_PID=$!
    cd ../..
    echo "Worker service started with PID $WORKER_PID"
}

# Function to start STT service
start_stt() {
    echo "Starting STT service on port $STT_PORT..."
    
    # Check if port is already in use
    if is_port_in_use $STT_PORT; then
        echo "ERROR: Port $STT_PORT is already in use!"
        echo "Please either:"
        echo "1. Stop the process using port $STT_PORT (run 'lsof -i :$STT_PORT' to find it)"
        echo "2. Use a different port with --stt-port PORT"
        exit 1
    fi
    
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

start_console() {
    echo "Starting Backend Console app..."
    cd console
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev &
    CONSOLE_PID=$!
    cd ..
    echo "Backend console started with PID $CONSOLE_PID"
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

if [ "$START_CONSOLE" = true ]; then
    start_console
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
if [ "$START_CONSOLE" = true ]; then
    echo "- Backend Console (PID: $CONSOLE_PID)"
fi

echo ""
echo "To stop all services, press Ctrl+C"


# Wait for Ctrl+C
trap 'stop_services; exit 0' INT

wait
