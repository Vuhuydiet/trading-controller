#!/bin/bash
# Start the news crawler in periodic mode

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "========================================="
echo "Starting News Crawler (Periodic Mode)"
echo "========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Kafka Servers: ${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
echo "LLM Provider: ${LLM_PROVIDER:-ollama}"
echo "Crawl Interval: ${NEWS_CRAWL_INTERVAL_MINUTES:-60} minutes"
echo "========================================="
echo ""

# Run the crawler
python scripts/crawl_news.py
