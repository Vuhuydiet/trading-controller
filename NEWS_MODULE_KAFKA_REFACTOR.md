# News Module Refactoring: MongoDB to Kafka

**Date:** January 15, 2026

## Overview

Refactored the news module from a database-backed API to a Kafka-based message streaming architecture with standalone script execution.

## Changes Summary

### Architecture Changes

**Before:**
- News articles and insights stored in MongoDB
- Served via FastAPI endpoints (`/api/v1/news/*`)
- Integrated into main application lifecycle
- APScheduler pipeline running inside main app

**After:**
- News articles and insights published to Kafka topics
- Standalone script for periodic execution (`scripts/crawl_news.py`)
- Completely decoupled from main API application
- Independent deployment and scaling

### New Files Created

1. **`app/modules/news/infrastructure/kafka_producer.py`**
   - `KafkaNewsProducer` class
   - Handles connection to Kafka
   - Publishes articles to `news.articles` topic
   - Publishes insights to `news.insights` topic
   - Implements retry logic and error handling

2. **`app/modules/news/domain/kafka_service.py`**
   - `NewsKafkaService` class
   - Replaces `NewsService` for Kafka-based workflow
   - Crawls news from multiple sources
   - Processes with LLM
   - Publishes to Kafka instead of storing in DB
   - In-memory deduplication using URL cache

3. **`scripts/crawl_news.py`**
   - Standalone entry point for news crawler
   - Supports two modes:
     - Periodic: Runs continuously with APScheduler
     - One-time: `--once` flag for single execution
   - Signal handlers for graceful shutdown
   - Comprehensive logging
   - Independent of main FastAPI application

4. **`scripts/README.md`**
   - Complete documentation for news crawler
   - Usage examples
   - Docker/systemd deployment guides
   - Troubleshooting section
   - Performance metrics

5. **`scripts/start_crawler.sh`** & **`scripts/start_crawler.bat`**
   - Convenience scripts for starting the crawler
   - Load environment variables
   - Activate virtual environment
   - Cross-platform support

### Modified Files

1. **`app/main.py`**
   - ✅ Removed all news module imports
   - ✅ Removed news pipeline initialization from lifespan
   - ✅ Removed news API routers
   - ✅ Removed MongoDB connection/disconnection

2. **`app/shared/core/config.py`**
   - ✅ Removed `NEWS_COLLECTION` and `INSIGHTS_COLLECTION`
   - ✅ Added `KAFKA_BOOTSTRAP_SERVERS`
   - ✅ Added `KAFKA_NEWS_ARTICLES_TOPIC`
   - ✅ Added `KAFKA_NEWS_INSIGHTS_TOPIC`
   - ⚠️ Kept `MONGODB_URI` for potential other modules

3. **`pyproject.toml`**
   - ✅ Added dependency: `aiokafka>=0.11.0`
   - ✅ Added mypy override for `aiokafka.*`

4. **`.env.example`**
   - ✅ Replaced MongoDB collection variables with Kafka configuration
   - ✅ Documented new Kafka environment variables

5. **`README.md`**
   - ✅ Updated Features section (Kafka instead of MongoDB)
   - ✅ Updated Tech Stack section
   - ✅ Added "Run News Crawler" section
   - ✅ Updated environment variables table
   - ✅ Added reference to scripts/README.md

### Files No Longer Used by Main App

These files still exist but are only used by the standalone crawler script:

- `app/modules/news/infrastructure/repository.py` (MongoDB repositories)
- `app/modules/news/infrastructure/mongo_connection.py`
- `app/modules/news/infrastructure/pipeline.py`
- `app/modules/news/domain/services.py`
- `app/modules/news/features/*` (API endpoints)
- `app/modules/news/public_api.py`

**Note:** These can be removed if you don't plan to use MongoDB for news anymore.

## Kafka Topics

### Topic: `news.articles`

Raw news articles published as they are crawled.

**Message Schema:**
```json
{
  "source": "coindesk",
  "title": "Bitcoin Reaches New All-Time High",
  "url": "https://www.coindesk.com/...",
  "published_at": "2026-01-15T10:30:00Z",
  "content": "Full article content...",
  "author": "Jane Doe"
}
```

**Key:** Article URL (for partitioning and deduplication)

### Topic: `news.insights`

LLM-generated insights for each article.

**Message Schema:**
```json
{
  "article_url": "https://www.coindesk.com/...",
  "article_title": "Bitcoin Reaches New All-Time High",
  "summary": "Bitcoin price surges past previous records...",
  "sentiment": "bullish",
  "key_points": [
    "New ATH reached",
    "Strong institutional demand",
    "Technical breakout confirmed"
  ],
  "market_impact": "Significant positive impact on crypto market sentiment",
  "affected_symbols": ["BTC", "ETH", "COIN"],
  "confidence_score": 0.87,
  "generated_at": "2026-01-15T10:31:00Z"
}
```

**Key:** Article URL (maintains ordering with articles)

## Usage

### Running the Crawler

```bash
# Start Kafka (Docker example)
docker run -d --name kafka \
  -p 9092:9092 \
  apache/kafka:latest

# Configure environment
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export LLM_PROVIDER=ollama
export NEWS_CRAWL_INTERVAL_MINUTES=60

# Run crawler
python scripts/crawl_news.py

# Or run once
python scripts/crawl_news.py --once
```

### Consuming Messages

```python
from aiokafka import AIOKafkaConsumer
import json

consumer = AIOKafkaConsumer(
    'news.articles',
    'news.insights',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

await consumer.start()
async for message in consumer:
    print(f"Topic: {message.topic}")
    print(f"Data: {message.value}")
```

## Deployment Options

### 1. Docker Compose

```yaml
services:
  kafka:
    image: apache/kafka:latest
    ports:
      - "9092:9092"

  news-crawler:
    build: .
    command: python scripts/crawl_news.py
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - kafka
```

### 2. Systemd Service (Linux)

```ini
[Unit]
Description=News Crawler
After=kafka.service

[Service]
ExecStart=/path/to/.venv/bin/python /path/to/scripts/crawl_news.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 3. Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: news-crawler
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: crawler
            image: trading-controller:latest
            command: ["python", "scripts/crawl_news.py", "--once"]
            env:
            - name: KAFKA_BOOTSTRAP_SERVERS
              value: "kafka:9092"
```

## Benefits of New Architecture

1. **Decoupling:** News crawler can be deployed, scaled, and updated independently
2. **Scalability:** Multiple consumers can process the same news stream
3. **Reliability:** Kafka provides message persistence and replay capabilities
4. **Flexibility:** Consumers can be written in any language that supports Kafka
5. **Real-time:** Lower latency between news crawling and consumption
6. **Simplicity:** Main API doesn't need to manage news pipeline

## Migration Path

If you have existing data in MongoDB:

1. Keep MongoDB repositories for historical data access
2. Create a separate consumer to write Kafka messages to MongoDB
3. Gradually transition existing consumers to Kafka-based system

## Testing

```bash
# Terminal 1: Start Kafka
docker run -p 9092:9092 apache/kafka:latest

# Terminal 2: Run crawler once
python scripts/crawl_news.py --once

# Terminal 3: Consume messages
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic news.articles --from-beginning
```

## Dependencies

**New:**
- `aiokafka>=0.11.0` - Async Kafka client for Python

**Still Required:**
- `apscheduler>=3.10.4` - Job scheduling
- `beautifulsoup4>=4.12.0` - HTML parsing
- `feedparser>=6.0.10` - RSS feed parsing
- `tweepy>=4.14.0` - Twitter API
- `openai>=1.3.0` - OpenAI LLM
- `anthropic>=0.7.0` - Anthropic LLM
- `ollama>=0.6.1` - Ollama local LLM

**No Longer Required by Main App:**
- `motor` - Async MongoDB driver (only needed by standalone script if you keep MongoDB)
- `pymongo` - MongoDB driver (only needed by standalone script if you keep MongoDB)

## Future Enhancements

1. **Multiple Crawler Instances:** Use consumer groups for parallel processing
2. **Dead Letter Queue:** Failed messages go to DLQ for manual review
3. **Schema Registry:** Add Avro schemas for message validation
4. **Monitoring:** Add Prometheus metrics for crawler performance
5. **Backpressure:** Implement rate limiting based on downstream capacity
