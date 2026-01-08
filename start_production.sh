#!/bin/bash

# Production Start Script for Trading Controller API
# This script helps you start the application in production mode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${APP_DIR}/.env.production"
LOG_DIR="${APP_DIR}/logs"
VENV_DIR="${APP_DIR}/.venv"

echo "========================================="
echo "Trading Controller - Production Startup"
echo "========================================="
echo ""

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warn "Running as root is not recommended for production"
fi

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env.production not found!"
    echo ""
    echo "Creating template .env.production file..."
    cat > "$ENV_FILE" << 'EOF'
# Application Settings
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Security - CHANGE THESE!
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_STRING
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./trading_controller_prod.db

# Binance API Configuration
BINANCE_API_BASE_URL=https://api.binance.com
BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=4
EOF

    print_warn "Template .env.production created. Please edit it with your configuration!"
    echo ""
    echo "To generate a secure SECRET_KEY, run:"
    echo "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo ""
    exit 1
fi

# Check if SECRET_KEY is still default
if grep -q "CHANGE_THIS_TO_A_SECURE_RANDOM_STRING" "$ENV_FILE"; then
    print_error "SECRET_KEY is still set to default value!"
    echo ""
    echo "Generate a secure key with:"
    echo "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo ""
    echo "Then update SECRET_KEY in .env.production"
    exit 1
fi

# Create logs directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    print_info "Creating logs directory..."
    mkdir -p "$LOG_DIR"
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at $VENV_DIR"
    echo ""
    echo "Please install dependencies first:"
    echo "  uv sync"
    echo "  # or"
    echo "  python -m venv .venv && source .venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Load environment variables
print_info "Loading environment variables from .env.production..."
export $(cat "$ENV_FILE" | grep -v '^#' | xargs)

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    print_warn "Gunicorn not found, installing..."
    pip install gunicorn
fi

# Initialize database if it doesn't exist
if [ ! -f "trading_controller_prod.db" ]; then
    print_info "Initializing database..."
    python -c "
from app.shared.infrastructure.db import create_db_and_tables
create_db_and_tables()
print('Database initialized successfully!')
" || {
        print_error "Failed to initialize database"
        exit 1
    }
fi

# Determine number of workers
if [ -z "$WORKERS" ]; then
    WORKERS=$(python -c "import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)")
    print_info "Auto-detected $WORKERS workers"
fi

# Check if port is available
PORT=${PORT:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_error "Port $PORT is already in use!"
    echo ""
    echo "To find the process using the port:"
    echo "  lsof -i :$PORT"
    echo ""
    echo "To kill the process:"
    echo "  kill -9 \$(lsof -t -i:$PORT)"
    exit 1
fi

echo ""
print_info "Starting Trading Controller API in production mode..."
echo ""
echo "Configuration:"
echo "  - Host: ${HOST:-0.0.0.0}"
echo "  - Port: $PORT"
echo "  - Workers: $WORKERS"
echo "  - Log Directory: $LOG_DIR"
echo "  - Environment: production"
echo ""

# Create gunicorn config if it doesn't exist
if [ ! -f "gunicorn_config.py" ]; then
    print_info "Creating gunicorn_config.py..."
    cat > gunicorn_config.py << 'EOF'
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "trading-controller"

# Server mechanics
daemon = False
pidfile = "gunicorn.pid"
EOF
fi

# Start the application
print_info "Launching application with Gunicorn..."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start gunicorn
gunicorn app.main:app \
    --workers "$WORKERS" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "${HOST:-0.0.0.0}:${PORT}" \
    --timeout 120 \
    --access-logfile "${LOG_DIR}/access.log" \
    --error-logfile "${LOG_DIR}/error.log" \
    --log-level info \
    --pid gunicorn.pid \
    || {
        print_error "Failed to start application"
        exit 1
    }
