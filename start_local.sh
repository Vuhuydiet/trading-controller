#!/bin/bash

# Local Development Start Script for Trading Controller API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${APP_DIR}/.venv"
ENV_FILE="${APP_DIR}/.env"

echo "========================================="
echo "Trading Controller - Local Development"
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

# Check if .env exists, create if not
if [ ! -f "$ENV_FILE" ]; then
    print_warn ".env file not found. Creating template..."
    cat > "$ENV_FILE" << 'EOF'
# Development Settings
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./trading_controller.db

# Binance API (optional for public endpoints)
BINANCE_API_BASE_URL=https://api.binance.com
BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Development
DEBUG=True
EOF

    print_info "Template .env created!"
    echo ""
fi

# Check if database exists
if [ ! -f "trading_controller.db" ]; then
    print_info "Database not found. Initializing..."
    python -c "from app.shared.infrastructure.db import create_db_and_tables; create_db_and_tables(); print('[OK] Database initialized!')" || {
        print_error "Failed to initialize database"
        exit 1
    }
    echo ""
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    print_warn "Uvicorn not found, installing..."
    pip install "uvicorn[standard]"
fi

echo ""
print_info "Starting development server..."
echo ""
echo "Configuration:"
echo "  - Environment: Development"
echo "  - Hot reload: Enabled"
echo "  - Host: localhost"
echo "  - Port: 8000"
echo ""
echo "Access your application at:"
echo -e "  - API:   ${BLUE}http://localhost:8000${NC}"
echo -e "  - Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  - ReDoc: ${BLUE}http://localhost:8000/redoc${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start development server with auto-reload
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 || {
    print_error "Failed to start server"
    exit 1
}
