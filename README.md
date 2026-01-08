# Trading Controller

A FastAPI-based cryptocurrency trading platform integrating with Binance API, built with Modular Monolith Architecture and Vertical Slice pattern.

## Overview

Trading Controller provides a backend API for cryptocurrency market data and trading operations. It serves as a proxy layer between frontend applications and Binance, offering real-time market data, authentication, and comprehensive market analysis features.

## Features

**Market Data**
- Real-time price updates via WebSocket
- 24-hour ticker statistics
- Candlestick (OHLCV) data with multiple timeframes
- Order book depth analysis
- Trading symbols information
- Multi-layer caching for optimal performance

**Authentication & Authorization**
- JWT-based authentication
- User registration and login
- Tiered access control (free, premium, vip)

**Technical Highlights**
- Modular Monolith Architecture
- Vertical Slice pattern for feature organization
- SQLite database with SQLModel ORM
- WebSocket integration with auto-reconnection
- Rate limiting (1200 requests/minute)
- Comprehensive logging
- OpenAPI documentation

## Tech Stack

- **Framework:** FastAPI 0.128.0+
- **Database:** SQLite with SQLModel
- **Authentication:** JWT with python-jose
- **External APIs:** Binance REST & WebSocket
- **Validation:** Pydantic 2.12+
- **Server:** Uvicorn/Gunicorn

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Installation

```bash
# Clone repository
git clone <repository-url>
cd trading-controller

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Configuration

Create `.env` file in project root:

```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./trading_controller.db

# Binance API
BINANCE_API_BASE_URL=https://api.binance.com
BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-secret-key

# Development
DEBUG=True
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Run Application

**Development:**
```bash
uvicorn app.main:app --reload
```

**Using start script (Windows):**
```bash
.\start_local.bat
```

**Using start script (Linux/Mac):**
```bash
./start_local.sh
```

The application will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc


## Project Structure

```
trading-controller/
├── app/
│   ├── main.py                      # Application entry point
│   ├── modules/
│   │   ├── identity/                # Authentication module
│   │   │   ├── domain/
│   │   │   ├── features/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   └── public_api.py
│   │   └── market/                  # Market data module
│   │       ├── domain/              # Domain models
│   │       ├── infrastructure/      # External integrations
│   │       └── features/            # Feature slices
│   └── shared/
│       ├── core/                    # Core configuration
│       └── infrastructure/          # Shared infrastructure
├── logs/                            # Application logs
├── .env                             # Environment configuration
├── pyproject.toml                   # Dependencies
└── README.md
```

## Development

### Testing API

1. Start the server
2. Open http://localhost:8000/docs
3. Register a user via POST /api/v1/register
4. Login via POST /api/v1/login to get access token
5. Click "Authorize" button and enter: `Bearer <your-token>`
6. Test any endpoint

### Adding New Features

Follow the Vertical Slice pattern:

1. Create feature folder in `app/modules/<module>/features/<feature-name>/`
2. Add files:
   - `dtos.py` - Request/Response models
   - `handler.py` - Business logic
   - `router.py` - FastAPI routes
3. Register router in `app/main.py`

## Production Deployment

See detailed guides:
- Local development: README_LOCAL.md
- Production deployment: README_PRODUCTION.md
- API documentation: API_ENDPOINTS_VERIFICATION.md
- Implementation details: IMPLEMENTATION_SUMMARY.md

**Quick production start:**

```bash
# Install dependencies
pip install -e .
pip install gunicorn

# Configure .env.production
cp .env .env.production
# Edit .env.production with production values

# Run with Gunicorn (Linux/Mac)
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000

# Or use start script
.\start_production.bat  # Windows
./start_production.sh   # Linux/Mac
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| SECRET_KEY | JWT secret key | Yes | - |
| DATABASE_URL | Database connection string | Yes | sqlite:///./trading_controller.db |
| BINANCE_API_KEY | Binance API key | No | - |
| BINANCE_API_SECRET | Binance API secret | No | - |
| BINANCE_API_BASE_URL | Binance API URL | No | https://api.binance.com |
| BINANCE_WS_BASE_URL | Binance WebSocket URL | No | wss://stream.binance.com:9443 |
| DEBUG | Enable debug mode | No | False |

Note: BINANCE_API_KEY and BINANCE_API_SECRET are optional for public endpoints.

## Architecture

**Modular Monolith:**
- Self-contained modules (identity, market)
- Clear module boundaries
- Shared infrastructure for common concerns

**Vertical Slice:**
- Each feature is self-contained
- Feature folders include all layers (DTOs, handlers, routers)
- Reduces coupling between features

**Clean Architecture Layers:**
1. Presentation - FastAPI routers and DTOs
2. Application - Business logic handlers
3. Domain - Core business models
4. Infrastructure - External integrations (Binance, Database)

## Logging

Logs are written to:
- Console (stdout)
- File: logs/app.log

Log levels: DEBUG, INFO, WARNING, ERROR

## Rate Limiting

- Binance API: 1200 requests/minute (handled automatically)
- Sliding window algorithm
- Automatic retry with exponential backoff

## WebSocket

- Persistent connection to Binance
- Auto-reconnection on disconnect
- Real-time price updates for BTC, ETH, BNB, SOL, ADA
- Configure streams in: app/modules/market/infrastructure/ws_config.py

## Error Handling

- HTTP 400: Bad Request (invalid parameters)
- HTTP 401: Unauthorized (invalid/missing token)
- HTTP 404: Not Found (invalid symbol)
- HTTP 500: Internal Server Error (Binance API issues)

All errors return JSON with detail message.

## Security

- JWT token-based authentication
- API keys stored in environment variables
- Never expose Binance credentials in responses
- Input validation on all endpoints
- SQL injection protection via SQLModel

## Performance

**Caching Strategy:**
1. WebSocket cache - Real-time data (instant)
2. Database cache - Recent data with TTL (< 50ms)
3. Binance API - Fresh data on cache miss (100-500ms)

**Optimization:**
- Connection pooling
- Async/await throughout
- Database indexing on frequently queried fields

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow existing code patterns
4. Write tests for new features
5. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

- Documentation: See docs/ folder
- Issues: GitHub Issues
- API Docs: http://localhost:8000/docs (when running)

## Changelog

See CHANGELOG.md for version history and updates.

## Authors

- Your Name - Initial work

## Acknowledgments

- FastAPI framework
- Binance API documentation
- SQLModel library
- Python community
