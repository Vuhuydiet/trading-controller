#!/bin/bash
set -e

echo "🚀 Trading Controller - Deployment Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Warning: Not running as root. Some commands may fail.${NC}"
fi

# Navigate to project directory
cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)
echo "📁 Project directory: $PROJECT_DIR"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.production...${NC}"
    cp .env.production .env
    echo -e "${YELLOW}⚠️  Please edit .env file and set SECRET_KEY!${NC}"
fi

# Create data directories
echo "📂 Creating data directories..."
mkdir -p data logs
chmod 755 data logs

# Pull latest code (if git repo)
if [ -d ".git" ]; then
    echo "📥 Pulling latest code..."
    git pull origin main 2>/dev/null || echo "Skipping git pull"
fi

# Build Docker images
echo "🔨 Building Docker images..."
docker compose build

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Start services
echo "🚀 Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start (60 seconds)..."
sleep 60

# Check service status
echo "📊 Service Status:"
docker compose ps

# Pull Ollama model
echo "🤖 Checking Ollama model..."
if docker exec ollama ollama list | grep -q "llama3.2"; then
    echo -e "${GREEN}✅ llama3.2 model already exists${NC}"
else
    echo "📥 Pulling llama3.2 model (this may take a few minutes)..."
    docker exec ollama ollama pull llama3.2
fi

# Health check
echo "🏥 Running health check..."
for i in {1..5}; do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ API is healthy!${NC}"
        break
    else
        echo "Attempt $i/5: API not ready yet..."
        sleep 10
    fi
done

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "📌 API Endpoints:"
echo "   - Health:  http://$SERVER_IP:8000/health"
echo "   - Swagger: http://$SERVER_IP:8000/docs"
echo "   - News:    http://$SERVER_IP:8000/api/v1/news"
echo ""
echo "📝 Useful commands:"
echo "   - View logs:    docker compose logs -f"
echo "   - Stop:         docker compose down"
echo "   - Restart:      docker compose restart"
echo ""
