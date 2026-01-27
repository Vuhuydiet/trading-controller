# Trading Controller - Project Overview

## 1. Tổng Quan

**Trading Controller** là một nền tảng giao dịch cryptocurrency với kiến trúc **Modular Monolith + Vertical Slice**. Hệ thống tích hợp AI để phân tích tin tức, dự đoán xu hướng giá, và cung cấp dữ liệu thị trường real-time từ Binance.

### Tech Stack Chính

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + Uvicorn |
| Database | SQLite + SQLModel |
| Message Queue | Apache Kafka (KRaft mode) |
| AI/ML | PyTorch, Transformers (FinBERT), Ollama |
| External API | Binance REST + WebSocket |
| Auth | JWT (python-jose) + bcrypt |
| Async Kafka | aiokafka |

---

## 2. Cấu Trúc Project

```
trading-controller/
├── app/
│   ├── main.py                    # FastAPI entry point + Kafka consumer startup
│   ├── modules/                   # Feature modules
│   │   ├── identity/              # Auth & User management
│   │   ├── market/                # Binance integration
│   │   ├── analysis/              # AI analysis (sentiment, prediction, causal, history)
│   │   ├── news/                  # News crawling & Kafka producer
│   │   └── subscription/          # Plans & tiers
│   └── shared/                    # Shared infrastructure
│       ├── core/                  # Config, logging
│       ├── domain/                # Shared enums
│       └── infrastructure/        # DB, security, AI adapters
├── scripts/
│   ├── crawl_news.py              # Standalone crawler
│   ├── test_kafka_msg.py          # Test Kafka message
│   ├── trigger_mock_news.sh       # Linux/Mac test script
│   └── trigger_mock_news.bat      # Windows test script
├── logs/                          # Log files
├── docker-compose.yml             # Kafka infrastructure
├── trading.db                     # SQLite database
└── pyproject.toml                 # Dependencies
```

### Vertical Slice Pattern

Mỗi feature được tổ chức theo cấu trúc:
```
features/
└── feature_name/
    ├── dtos.py      # Request/Response models
    ├── handler.py   # Business logic
    └── router.py    # API endpoints
```

---

## 3. Authentication & Authorization

### JWT Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│ POST /login │────▶│   Server    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌─────────────────────────┐│
                    │ Access Token (3 days)   ││
                    │ Refresh Token (7 days)  │◀┘
                    └─────────────────────────┘
```

### User Tiers

| Feature | Anonymous | FREE | VIP |
|---------|-----------|------|-----|
| Get prices | ✅ | ✅ | ✅ |
| Klines limit | 500 | 500 | 5000 |
| Order book depth | 100 | 100 | 1000 |
| Rate limit/min | 5 | 10 | 1000 |
| AI Analysis | ❌ | ❌ | ✅ |
| Sentiment API | ❌ | ❌ | ✅ |
| Prediction API | ❌ | ❌ | ✅ |
| Causal Analysis | ❌ | ❌ | ✅ |

### Endpoints

```
POST /api/v1/register        # Đăng ký user mới
POST /api/v1/login           # Đăng nhập, lấy tokens
POST /api/v1/refresh-token   # Refresh access token
POST /api/v1/forgot-password # Reset password
GET  /api/v1/me              # Lấy thông tin user hiện tại
```

---

## 4. Binance Integration

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Market Module                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ REST Client  │  │  WS Manager  │  │ Price Cache  │       │
│  │ (httpx)      │  │ (websockets) │  │ (in-memory)  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘       │
│         │                 │                                  │
│         ▼                 ▼                                  │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Binance API                          │       │
│  │  REST: https://api.binance.com                   │       │
│  │  WS: wss://stream.binance.com:9443               │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Features

| Feature | Description |
|---------|-------------|
| Rate Limiting | Sliding window, 1200 req/min |
| Retry Logic | 3 attempts, exponential backoff |
| WebSocket | Auto-reconnect, 20s ping interval |
| Caching | 3-layer: WebSocket → DB → API |

### Endpoints

```
GET /api/v1/market/klines/{symbol}   # Candlestick data
GET /api/v1/market/ticker/{symbol}   # 24h stats
GET /api/v1/market/price/{symbol}    # Current price
GET /api/v1/market/depth/{symbol}    # Order book
GET /api/v1/market/symbols           # Trading pairs
WS  /api/v1/market/stream            # Real-time prices
```

---

## 5. News Crawler & Kafka Producer

### Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    News Crawler Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ CoinDesk │  │ Reuters  │  │Bloomberg │  │ Twitter  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┘           │
│                           │                                 │
│                           ▼                                 │
│                   ┌───────────────┐                         │
│                   │ NewsArticle   │                         │
│                   │ {title, content, url, published_at}     │
│                   └───────┬───────┘                         │
│                           │                                 │
│                           ▼                                 │
│                   ┌───────────────┐                         │
│                   │ LLM Adapter   │ (Ollama)                │
│                   │ Generate      │                         │
│                   │ Insights      │                         │
│                   └───────┬───────┘                         │
│                           │                                 │
│           ┌───────────────┴───────────────┐                 │
│           ▼                               ▼                 │
│   ┌───────────────┐               ┌───────────────┐         │
│   │ news.articles │               │ news.insights │         │
│   │ (Kafka topic) │               │ (Kafka topic) │         │
│   └───────────────┘               └───────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Sources

| Source | Method | Library |
|--------|--------|---------|
| CoinDesk | RSS Feed | feedparser |
| Reuters | RSS Feed | feedparser |
| Bloomberg | RSS Feed | feedparser |
| Twitter | API | tweepy |

### Usage

```bash
# Periodic mode (every 60 min)
python scripts/crawl_news.py

# One-time execution
python scripts/crawl_news.py --once

# Test Kafka message (mock news)
python scripts/test_kafka_msg.py
```

---

## 6. Kafka Message Queue

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kafka Flow                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │   Crawler   │─────▶│    Kafka    │─────▶│  Consumer   │ │
│  │  (Producer) │      │   Broker    │      │ (Analysis)  │ │
│  └─────────────┘      │  :9092      │      └──────┬──────┘ │
│                       └─────────────┘             │        │
│                                                   ▼        │
│                                            ┌─────────────┐ │
│                                            │ AI Analysis │ │
│                                            │ FinBERT +   │ │
│                                            │ Ollama LLM  │ │
│                                            └──────┬──────┘ │
│                                                   │        │
│                                                   ▼        │
│                                            ┌─────────────┐ │
│                                            │   SQLite    │ │
│                                            │  Database   │ │
│                                            └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Topics

| Topic | Description | Key |
|-------|-------------|-----|
| `news.articles` | Raw news articles | article.url |
| `news.insights` | AI-generated insights | article.url |

### Message Formats

**news.articles:**
```json
{
  "source": "coindesk",
  "title": "Bitcoin ETF Approval",
  "url": "https://...",
  "content": "Full article text...",
  "published_at": "2026-01-11T14:30:00Z"
}
```

**news.insights:**
```json
{
  "article_url": "https://...",
  "summary": "Brief summary",
  "sentiment": "bullish",
  "key_points": ["Point 1", "Point 2"],
  "market_impact": "Positive for adoption",
  "affected_symbols": ["BTC", "ETH"],
  "confidence_score": 0.92
}
```

### Docker Compose (Kafka KRaft Mode)

```yaml
services:
  kafka:
    image: confluentinc/cp-kafka:7.6.1
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      # ... KRaft configuration
```

```bash
# Start Kafka
docker-compose up -d
```

---

## 7. Kafka Consumer (Background AI Processing)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Consumer                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 App Startup                          │   │
│  │  1. Pre-load FinBERT model                          │   │
│  │  2. Pre-load Ollama LLM                             │   │
│  │  3. Start async consumer task                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Kafka Consumer Loop                     │   │
│  │  - Listen to 'news.articles' topic                  │   │
│  │  - Deserialize JSON messages                        │   │
│  │  - Validate payload                                 │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            For Each Message                          │   │
│  │                                                      │   │
│  │  1. Create AnalyzeNewsRequest                       │   │
│  │     - news_id = payload.url                         │   │
│  │     - news_content = payload.content/title          │   │
│  │     - published_at = payload.published_at           │   │
│  │                                                      │   │
│  │  2. Execute AnalyzeNewsHandler                      │   │
│  │     - NewsPriceAligner: align news + market data    │   │
│  │     - FinBERT: sentiment analysis                   │   │
│  │     - Ollama: market reasoning                      │   │
│  │                                                      │   │
│  │  3. Save to analysis_results table                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Code

```python
# app/modules/analysis/infrastructure/kafka_consumer.py

class AnalysisConsumer:
    async def start(self):
        # Pre-load AI models
        finbert_bot = FinBertAdapter()
        ollama_bot = OllamaLlamaAdapter(model_name=settings.AI_REASONING_MODEL)

        consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id="analysis_group",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        async for msg in consumer:
            # Process each news article
            handler = AnalyzeNewsHandler(...)
            await handler.execute(request)

# Started in app/main.py lifespan
def start_analysis_consumer():
    consumer = AnalysisConsumer()
    asyncio.create_task(consumer.start())
```

---

## 8. AI Features

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Model Factory                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Config (.env)                       │  │
│  │  AI_SENTIMENT_MODEL=finbert                          │  │
│  │  AI_REASONING_PROVIDER=ollama                        │  │
│  │  AI_REASONING_MODEL=llama3.2                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│              ┌────────────┴────────────┐                   │
│              ▼                         ▼                   │
│  ┌─────────────────────┐   ┌─────────────────────┐        │
│  │ SentimentAnalyzer   │   │  MarketReasoner     │        │
│  │ - FinBERT (local)   │   │  - Ollama (local)   │        │
│  │ - OpenAI (cloud)    │   │  - OpenAI (cloud)   │        │
│  │ - Ensemble          │   │  - Gemini (cloud)   │        │
│  └─────────────────────┘   └─────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### AI Models

| Model | Purpose | Provider |
|-------|---------|----------|
| FinBERT | Sentiment analysis | Local (PyTorch) |
| Llama 3.2 | Market reasoning | Ollama (local) |
| GPT-4 | Alternative reasoning | OpenAI (cloud) |
| Claude | Alternative reasoning | Anthropic (cloud) |

### Analysis Features

#### 1. Sentiment Analysis (`/api/v1/analysis/sentiment`)

Phân tích sentiment của symbol hoặc tin tức.

```
GET  /sentiment/{symbol}?period=24h   # Symbol sentiment
GET  /sentiment/market?period=24h     # Market sentiment tổng quan
POST /sentiment/news                   # Phân tích tin tức cụ thể
```

**Response Example:**
```json
{
  "symbol": "BTCUSDT",
  "period": "24h",
  "sentiment": {
    "score": 0.72,
    "label": "BULLISH",
    "confidence": 0.85
  },
  "breakdown": {
    "positive": 55,
    "neutral": 30,
    "negative": 15
  },
  "top_factors": [
    {"factor": "ETF-related news", "impact": "POSITIVE", "weight": 0.35}
  ]
}
```

**Features:**
- AI-powered sentiment scoring (-1 to 1)
- Sentiment breakdown (positive/neutral/negative)
- Key factors extraction
- Database caching với TTL (15min - 12h tùy period)

#### 2. Prediction (`/api/v1/analysis/prediction`)

Dự đoán xu hướng giá.

```
GET /prediction/{symbol}?timeframe=24h       # Single prediction
GET /prediction?symbols=BTC,ETH&timeframe=24h  # Batch predictions
```

**Response Example:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "24h",
  "current_price": "97500.00",
  "prediction": {
    "direction": "UP",
    "confidence": 0.78,
    "target_price": {
      "low": "98000.00",
      "mid": "99500.00",
      "high": "101000.00"
    },
    "support_levels": ["94575.00", "91380.00", "87750.00"],
    "resistance_levels": ["100425.00", "103350.00", "107250.00"]
  },
  "model_version": "v1.0.0"
}
```

**Features:**
- Direction prediction: UP / DOWN / NEUTRAL
- Target prices: low, mid, high
- Support & resistance levels
- Lưu vào `prediction_history` để track accuracy

#### 3. Causal Analysis (`/api/v1/analysis/causal`)

Phân tích nguyên nhân biến động giá.

```
GET  /causal/{symbol}?from=...&to=...   # Auto period analysis
POST /causal/explain                     # Explain specific movement
```

**Response Example:**
```json
{
  "symbol": "BTCUSDT",
  "period": {
    "period_from": "2026-01-24T00:00:00Z",
    "period_to": "2026-01-25T00:00:00Z"
  },
  "price_change": {
    "price_from": "95000.00",
    "price_to": "97500.00",
    "percent": "+2.6%"
  },
  "causal_factors": [
    {
      "factor": "Regulatory developments",
      "category": "REGULATORY",
      "impact_score": 0.35,
      "explanation": "ETF approval news..."
    },
    {
      "factor": "Market dynamics",
      "category": "MARKET",
      "impact_score": 0.30,
      "explanation": "Strong trading volume..."
    }
  ],
  "summary": "BTCUSDT price change of +2.6% primarily driven by regulatory developments..."
}
```

**Factor Categories:**
- `REGULATORY` - ETF, SEC, regulations
- `ON_CHAIN` - Whale activity, wallets
- `MARKET` - Sentiment, volume, liquidity
- `NEWS` - Announcements, partnerships
- `TECHNICAL` - Support, resistance, breakouts

#### 4. History (`/api/v1/analysis/history`)

Lịch sử dự đoán và độ chính xác.

```
GET /history/{symbol}?period=30d
```

**Response Example:**
```json
{
  "symbol": "BTCUSDT",
  "period": "30d",
  "accuracy": {
    "total_predictions": 45,
    "verified_predictions": 30,
    "correct_predictions": 22,
    "accuracy_rate": 0.73,
    "up_predictions": 25,
    "down_predictions": 15,
    "neutral_predictions": 5
  },
  "recent_predictions": [
    {
      "id": 123,
      "predicted_direction": "UP",
      "predicted_at": "2026-01-24T10:00:00Z",
      "target_price": "98000.00",
      "actual_price": "97800.00",
      "is_correct": true
    }
  ]
}
```

---

## 9. Database Schema

### Entity Relationship

```
┌─────────────────────────────────────────────────────────────┐
│                      Database Schema                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌──────────────────────┐         │
│  │    User      │         │  SubscriptionPlan    │         │
│  ├──────────────┤         ├──────────────────────┤         │
│  │ id (PK)      │         │ id (PK)              │         │
│  │ username     │         │ name                 │         │
│  │ email        │         │ price                │         │
│  │ tier (enum)  │◀────────│ granted_tier         │         │
│  │ is_active    │         │ features (1:N)       │         │
│  └──────────────┘         └──────────────────────┘         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Market Data                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Ticker    │  Kline     │  OrderBook  │  SymbolInfo  │  │
│  │  (24h)     │  (OHLCV)   │  (Depth)    │  (Metadata)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Analysis Results                    │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ AnalysisResult   │ SymbolSentiment  │ TrendPrediction│  │
│  │ CausalAnalysis   │ PredictionHistory                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Analysis Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| `analysis_results` | News analysis từ Kafka consumer | news_id, sentiment, confidence, trend, reasoning |
| `symbol_sentiments` | Sentiment theo symbol/period | symbol, period, sentiment_score, sentiment_label |
| `trend_predictions` | Dự đoán giá | symbol, timeframe, direction, target_low/mid/high |
| `causal_analyses` | Phân tích nguyên nhân | symbol, price_change_percent, causal_factors (JSON) |
| `prediction_history` | Track accuracy | symbol, predicted_direction, is_correct |

### Enums

```python
class SentimentLabel(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class TrendDirection(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"
```

---

## 10. System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRADING CONTROLLER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐                              ┌─────────────────────────┐  │
│   │   Frontend  │◀────────REST API────────────▶│    FastAPI Server       │  │
│   │   (React)   │◀────────WebSocket───────────▶│    (Uvicorn)            │  │
│   └─────────────┘                              └───────────┬─────────────┘  │
│                                                            │                │
│                              ┌─────────────────────────────┼────────────┐   │
│                              │                             │            │   │
│                              ▼                             ▼            ▼   │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  ┌──────────┐     │
│   │  Identity   │    │   Market    │    │  Analysis   │  │   News   │     │
│   │  Module     │    │   Module    │    │   Module    │  │  Module  │     │
│   │             │    │             │    │             │  │          │     │
│   │ - Register  │    │ - Klines    │    │ - Sentiment │  │ - Crawl  │     │
│   │ - Login     │    │ - Ticker    │    │ - Prediction│  │ - Parse  │     │
│   │ - JWT       │    │ - Depth     │    │ - Causal    │  │ - Kafka  │     │
│   │             │    │ - WebSocket │    │ - History   │  │          │     │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  └────┬─────┘     │
│          │                  │                  │               │           │
│          └──────────────────┴──────────────────┴───────────────┘           │
│                                      │                                      │
│                                      ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         Shared Infrastructure                        │  │
│   │                                                                      │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │  │
│   │  │  SQLite  │  │ Security │  │  Config  │  │    AI Adapters       │ │  │
│   │  │    DB    │  │  (JWT)   │  │ (pydantic│  │ (FinBERT, Ollama)    │ │  │
│   │  └──────────┘  └──────────┘  │ settings)│  └──────────────────────┘ │  │
│   │                              └──────────┘                            │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         External Services                            │  │
│   │                                                                      │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │  │
│   │  │ Binance  │  │  Kafka   │  │  Ollama  │  │   News Sources       │ │  │
│   │  │   API    │  │  Broker  │  │  (LLM)   │  │ (CoinDesk, Reuters)  │ │  │
│   │  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            COMPLETE DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [News Sources]                          [User Request]                     │
│       │                                        │                            │
│       ▼                                        ▼                            │
│  ┌─────────────┐                        ┌─────────────┐                    │
│  │   Crawler   │                        │  REST API   │                    │
│  │  (Script)   │                        │  Endpoints  │                    │
│  └──────┬──────┘                        └──────┬──────┘                    │
│         │                                      │                            │
│         ▼                                      │                            │
│  ┌─────────────┐                              │                            │
│  │   Kafka     │                              │                            │
│  │   Broker    │                              │                            │
│  └──────┬──────┘                              │                            │
│         │                                      │                            │
│         ▼                                      │                            │
│  ┌─────────────┐      ┌─────────────┐         │                            │
│  │  Kafka      │─────▶│ AI Analysis │◀────────┘                            │
│  │  Consumer   │      │ - FinBERT   │                                      │
│  │ (Background)│      │ - Ollama    │                                      │
│  └─────────────┘      └──────┬──────┘                                      │
│                              │                                              │
│                              ▼                                              │
│  [Binance API]        ┌─────────────┐        ┌─────────────┐               │
│       │               │   SQLite    │        │  Response   │               │
│       ▼               │  Database   │───────▶│   JSON      │               │
│  ┌─────────────┐      └─────────────┘        └──────┬──────┘               │
│  │ Market Data │──────────────┘                     │                      │
│  │ - Klines    │                                    ▼                      │
│  │ - Prices    │                             ┌─────────────┐               │
│  └─────────────┘                             │  Frontend   │               │
│                                              └─────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. API Endpoints Summary

### Authentication (`/api/v1`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register` | Đăng ký user | - |
| POST | `/login` | Đăng nhập | - |
| POST | `/refresh-token` | Refresh token | - |
| GET | `/me` | User profile | Required |

### Market (`/api/v1/market`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/klines/{symbol}` | Candlestick data | Optional |
| GET | `/ticker/{symbol}` | 24h statistics | Optional |
| GET | `/price/{symbol}` | Current price | Optional |
| GET | `/depth/{symbol}` | Order book | Optional |
| GET | `/symbols` | Trading pairs | - |
| WS | `/stream` | Real-time prices | - |

### Analysis (`/api/v1/analysis`) - VIP Only

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze-news` | Analyze news content |
| GET | `/sentiment/{symbol}` | Symbol sentiment |
| GET | `/sentiment/market` | Market sentiment |
| POST | `/sentiment/news` | News sentiment |
| GET | `/prediction/{symbol}` | Price prediction |
| GET | `/prediction` | Batch predictions |
| GET | `/causal/{symbol}` | Causal analysis |
| POST | `/causal/explain` | Explain price movement |
| GET | `/history/{symbol}` | Prediction history |

### Subscription (`/api/v1`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/plans` | List plans | - |
| POST | `/buy-subscription` | Purchase plan | Required |

---

## 12. Configuration

### Environment Variables

```env
# === Core ===
PROJECT_NAME=Crypto Trading Platform
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
DATABASE_URL=sqlite:///./trading.db
DEBUG=True

# === Auth ===
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=4320
REFRESH_TOKEN_EXPIRE_DAYS=7

# === Binance ===
BINANCE_API_BASE_URL=https://api.binance.com
BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
BINANCE_API_KEY=<optional>
BINANCE_API_SECRET=<optional>

# === AI ===
AI_SENTIMENT_MODEL=finbert
AI_REASONING_PROVIDER=ollama
AI_REASONING_MODEL=llama3.2
OPENAI_API_KEY=<optional>
GEMINI_API_KEY=<optional>

# === Kafka ===
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_NEWS_ARTICLES_TOPIC=news.articles
KAFKA_NEWS_INSIGHTS_TOPIC=news.insights

# === Crawler ===
LLM_PROVIDER=ollama
LLM_MODEL=llama2
NEWS_CRAWL_INTERVAL_MINUTES=60
NEWS_SOURCES=["coindesk", "reuters", "bloomberg", "twitter"]
TWITTER_BEARER_TOKEN=<optional>
```

### CORS

```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
```

---

## 13. Running the Project

### Prerequisites

- Python 3.11+
- Docker (for Kafka)
- Ollama (for local LLM)
- (Optional) GPU for faster AI inference

### Development

```bash
# 1. Start Kafka
docker-compose up -d

# 2. Install dependencies
pip install -e .

# 3. Copy environment
cp .env.example .env
# Edit .env with your secrets

# 4. Start Ollama (if using local LLM)
ollama pull llama3.2
ollama serve

# 5. Start server (Kafka consumer auto-starts)
uvicorn app.main:app --reload

# 6. (Optional) Start crawler in separate terminal
python scripts/crawl_news.py

# 7. (Optional) Test with mock news
python scripts/test_kafka_msg.py
```

### Production

```bash
# With Gunicorn
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

---

## 14. Key Design Decisions

### Why Modular Monolith?

| Benefit | Description |
|---------|-------------|
| Simplicity | Single deployment, easy debugging |
| Performance | In-process communication, no network latency |
| Flexibility | Can split into microservices later |
| Clear boundaries | Modules communicate via `public_api.py` |

### Why Kafka for News Processing?

| Benefit | Description |
|---------|-------------|
| Decoupling | Crawler & Analysis run independently |
| Reliability | Messages persisted, can replay |
| Scalability | Can add more consumers |
| Async | Non-blocking background processing |

### Why aiokafka?

| Benefit | Description |
|---------|-------------|
| Async native | Works with FastAPI async |
| Non-blocking | Consumer runs in background task |
| Efficient | Single event loop |

### Why Pre-load AI Models?

| Benefit | Description |
|---------|-------------|
| Fast inference | Models already in memory |
| Consistent latency | No cold start per message |
| Resource efficient | Load once, use many times |

---

## 15. File References

| File | Description |
|------|-------------|
| [main.py](app/main.py) | FastAPI entry + Kafka consumer startup |
| [kafka_consumer.py](app/modules/analysis/infrastructure/kafka_consumer.py) | Async Kafka consumer |
| [sentiment/handler.py](app/modules/analysis/features/sentiment/handler.py) | Sentiment analysis logic |
| [prediction/handler.py](app/modules/analysis/features/prediction/handler.py) | Price prediction logic |
| [causal/handler.py](app/modules/analysis/features/causal/handler.py) | Causal analysis logic |
| [history/handler.py](app/modules/analysis/features/history/handler.py) | Prediction history & accuracy |
| [entities.py](app/modules/analysis/domain/entities.py) | Analysis database models |
| [docker-compose.yml](docker-compose.yml) | Kafka KRaft setup |
| [test_kafka_msg.py](scripts/test_kafka_msg.py) | Test Kafka with mock news |

---

## 16. Future Improvements

- [x] ~~Docker Compose~~ - Kafka infrastructure added
- [x] ~~Kafka Consumer~~ - Background AI processing
- [x] ~~Sentiment API~~ - Symbol & market sentiment
- [x] ~~Prediction API~~ - Price trend prediction
- [x] ~~Causal Analysis~~ - Price movement reasoning
- [x] ~~History API~~ - Prediction accuracy tracking
- [ ] **get_market_insight** - Aggregate insights từ nhiều news
- [ ] **PostgreSQL** - Upgrade DB cho production
- [ ] **Redis** - Caching layer
- [ ] **Prediction verification** - Auto-verify predictions
- [ ] **More news sources** - CryptoSlate, Decrypt, etc.
- [ ] **WebSocket auth** - Secure real-time streams

---

*Updated: 2026-01-25*
