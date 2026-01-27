# Local Development - Quick Start

This guide shows you how to run the Trading Controller API locally for development and testing.

---

## 🚀 Quick Start (3 Minutes)

### Step 1: Install Dependencies

**Using UV (Recommended - Faster):**
```bash
# Install UV if you don't have it
pip install uv

# Install all dependencies
uv sync
```

**Using pip (Traditional):**
```bash
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

### Step 2: Configure Environment

**Option A: Use existing .env file (if you have one)**

No action needed! The app will use your existing `.env` file.

**Option B: Create new .env file**

```bash
# Copy the example or create new
cp .env.example .env  # if you have .env.example

# Or create from scratch
```

Add to `.env`:
```bash
# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (SQLite - no setup needed)
DATABASE_URL=sqlite:///./trading_controller.db

# Binance API (optional - works without for public endpoints)
BINANCE_API_BASE_URL=https://api.binance.com
BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Development
DEBUG=True
```

**Note:** You can leave `BINANCE_API_KEY` and `BINANCE_API_SECRET` empty for testing with public endpoints.

### Step 3: Initialize Database

```bash
# Activate virtual environment first (if not already activated)
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# Initialize database
python -c "from app.shared.infrastructure.db import create_db_and_tables; create_db_and_tables(); print('✓ Database initialized!')"
```

### Step 4: Start Development Server

**Simple start:**
```bash
uvicorn app.main:app --reload
```

**With custom host/port:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**With detailed logging:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

That's it! Your server is now running at `http://localhost:8000`

---

## 🎯 Access Your Application

### Interactive API Documentation (Swagger UI)
```
http://localhost:8000/docs
```
- Test all endpoints interactively
- See request/response schemas
- Try out authentication

### Alternative Documentation (ReDoc)
```
http://localhost:8000/redoc
```
- Clean, readable API documentation
- Better for reading and understanding

### OpenAPI JSON Schema
```
http://localhost:8000/openapi.json
```
- Raw OpenAPI specification
- For tools like Postman, Insomnia

### Health Check
```
http://localhost:8000/
```
Should return:
```json
{"message": "System is running with Modular Monolith Architecture"}
```

---

## 🧪 Test the API

### 1. Register a User

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "tier": "free"
  }'
```

**Using Swagger UI:**
1. Go to `http://localhost:8000/docs`
2. Find `POST /api/v1/register`
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"

### 2. Login to Get Token

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Test Market Data Endpoints

**Get Symbols (requires authentication):**
```bash
# Replace YOUR_TOKEN with the access_token from login
curl "http://localhost:8000/api/v1/market/symbols" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Price:**
```bash
curl "http://localhost:8000/api/v1/market/price/BTCUSDT" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Ticker:**
```bash
curl "http://localhost:8000/api/v1/market/ticker/BTCUSDT" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Klines:**
```bash
curl "http://localhost:8000/api/v1/market/klines/BTCUSDT?interval=1h&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Order Book:**
```bash
curl "http://localhost:8000/api/v1/market/depth/BTCUSDT?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Check WebSocket Status:**
```bash
curl "http://localhost:8000/api/v1/market/ws/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📝 Common Development Commands

### Start Server
```bash
# Standard development mode with auto-reload
uvicorn app.main:app --reload

# With custom port
uvicorn app.main:app --reload --port 3000

# With debug logging
uvicorn app.main:app --reload --log-level debug

# Accessible from other devices on network
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Stop Server
```
Press Ctrl+C in the terminal
```

### View Logs
Development server logs appear in the terminal where you started the server.

Application logs are also written to:
```
logs/app.log
```

To monitor logs in real-time:
```bash
# Windows PowerShell:
Get-Content logs\app.log -Wait

# Windows Command Prompt:
powershell Get-Content logs\app.log -Wait

# Linux/Mac:
tail -f logs/app.log
```

### Clear Database (Fresh Start)
```bash
# Delete database file
rm trading_controller.db  # Linux/Mac
del trading_controller.db  # Windows

# Recreate database
python -c "from app.shared.infrastructure.db import create_db_and_tables; create_db_and_tables()"
```

### Update Dependencies
```bash
# Using UV
uv sync

# Using pip
pip install -e .
```

---

## 🛠️ Development Tools

### Interactive API Testing (Swagger UI)

1. Start server: `uvicorn app.main:app --reload`
2. Open browser: `http://localhost:8000/docs`
3. Click on any endpoint
4. Click "Try it out"
5. Fill in parameters
6. Click "Execute"
7. See response

**To test authenticated endpoints:**
1. First, login using `/api/v1/login` endpoint
2. Copy the `access_token` from response
3. Click "Authorize" button (🔒 icon at top)
4. Enter: `Bearer YOUR_TOKEN`
5. Click "Authorize"
6. Now you can test protected endpoints

### Using Postman

1. Import OpenAPI spec from `http://localhost:8000/openapi.json`
2. Or manually create requests
3. For authentication:
   - Type: Bearer Token
   - Token: `YOUR_TOKEN`

### Using VS Code REST Client

Install "REST Client" extension, then create `test.http`:

```http
### Variables
@baseUrl = http://localhost:8000
@token = YOUR_TOKEN_HERE

### Register User
POST {{baseUrl}}/api/v1/register
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "testpass123",
  "tier": "free"
}

### Login
POST {{baseUrl}}/api/v1/login
Content-Type: application/x-www-form-urlencoded

username=test@example.com&password=testpass123

### Get Symbols
GET {{baseUrl}}/api/v1/market/symbols
Authorization: Bearer {{token}}

### Get Price
GET {{baseUrl}}/api/v1/market/price/BTCUSDT
Authorization: Bearer {{token}}
```

---

## 🔧 Configuration Options

### Environment Variables (.env)

```bash
# Security
SECRET_KEY=dev-secret-key            # Change in production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30       # Token validity duration

# Database
DATABASE_URL=sqlite:///./trading_controller.db

# Binance API
BINANCE_API_BASE_URL=https://api.binance.com
BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
BINANCE_API_KEY=                     # Optional for public endpoints
BINANCE_API_SECRET=                  # Optional for public endpoints

# Development
DEBUG=True                           # Enable debug mode
LOG_LEVEL=DEBUG                      # Logging level
```

### Server Options

```bash
# Basic
uvicorn app.main:app --reload

# Custom host and port
uvicorn app.main:app --reload --host 127.0.0.1 --port 3000

# Enable access from network
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With detailed logging
uvicorn app.main:app --reload --log-level debug

# Without access logs (cleaner output)
uvicorn app.main:app --reload --no-access-log

# With custom log config
uvicorn app.main:app --reload --log-config log_config.yaml
```

---

## 🐛 Troubleshooting

### Port Already in Use

**Error:** `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)`

**Solution:**

**Windows:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
uvicorn app.main:app --reload --port 3000
```

**Linux/Mac:**
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 3000
```

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Activate virtual environment
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# Install dependencies
uv sync
# or
pip install -e .
```

### Database Locked

**Error:** `database is locked`

**Solution:**
```bash
# Stop all running instances of the app
# Delete database and recreate
rm trading_controller.db
python -c "from app.shared.infrastructure.db import create_db_and_tables; create_db_and_tables()"
```

### WebSocket Connection Failed

**Error:** WebSocket connection errors in logs

**Solution:**
```bash
# Check internet connection
ping api.binance.com

# Verify Binance WebSocket endpoint
# Try: wss://stream.binance.com:9443/ws/btcusdt@ticker

# Check if firewall is blocking WebSocket connections
```

### Import Errors

**Error:** `ImportError: cannot import name 'app' from 'app.main'`

**Solution:**
```bash
# Make sure you're in the project root directory
cd /path/to/trading-controller

# Verify file structure
ls app/main.py

# Reinstall in development mode
pip install -e .
```

---

## 📚 Project Structure

```
trading-controller/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── modules/
│   │   ├── identity/                # Authentication & Authorization
│   │   │   ├── features/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   └── public_api.py
│   │   └── market/                  # Market Data module
│   │       ├── domain/              # Domain models
│   │       ├── infrastructure/      # External integrations
│   │       └── features/            # Feature slices
│   │           ├── get_symbols/
│   │           ├── get_price/
│   │           ├── get_ticker/
│   │           ├── get_klines/
│   │           ├── get_depth/
│   │           └── ws_status/
│   └── shared/
│       └── core/
│           ├── config.py            # Configuration
│           ├── logging_config.py    # Logging setup
│           └── db.py                # Database setup
├── logs/                            # Application logs
├── .env                             # Environment variables (local)
├── .env.production                  # Production environment
├── pyproject.toml                   # Dependencies
└── README_LOCAL.md                  # This file
```

---

## 🎓 Development Workflow

### Typical Development Session

```bash
# 1. Start your day
cd /path/to/trading-controller

# 2. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Pull latest changes (if working with team)
git pull origin main

# 4. Update dependencies (if needed)
uv sync

# 5. Start development server
uvicorn app.main:app --reload

# 6. Open browser to test
http://localhost:8000/docs

# 7. Make changes to code
# Files auto-reload when you save!

# 8. Test your changes
# Use Swagger UI or curl

# 9. When done, stop server
Ctrl+C
```

### Making Changes

The development server auto-reloads when you save files:

1. Edit any `.py` file
2. Save the file
3. Server automatically restarts
4. Refresh browser to see changes

**Example:**
```python
# Edit: app/main.py
@app.get("/hello")
def hello():
    return {"message": "Hello World!"}

# Save file -> Server reloads automatically
# Visit: http://localhost:8000/hello
```

### Adding New Endpoints

1. Create feature folder: `app/modules/market/features/new_feature/`
2. Add files:
   - `dtos.py` - Request/Response models
   - `handler.py` - Business logic
   - `router.py` - FastAPI routes
3. Register router in `app/main.py`:
```python
from app.modules.market.features.new_feature.router import router as new_router
app.include_router(new_router, prefix="/api/v1/market", tags=["market"])
```
4. Server auto-reloads
5. Check `http://localhost:8000/docs` for new endpoint

---

## ✅ Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Activate venv (Windows) | `.venv\Scripts\activate` |
| Activate venv (Linux/Mac) | `source .venv/bin/activate` |
| Start server | `uvicorn app.main:app --reload` |
| Stop server | `Ctrl+C` |
| View API docs | `http://localhost:8000/docs` |
| Initialize database | `python -c "from app.shared.infrastructure.db import create_db_and_tables; create_db_and_tables()"` |
| View logs | `tail -f logs/app.log` |

### Default URLs

| Resource | URL |
|----------|-----|
| Application | `http://localhost:8000/` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |

### Authentication Flow

1. Register: `POST /api/v1/register`
2. Login: `POST /api/v1/login` → Get `access_token`
3. Use token: Add header `Authorization: Bearer {access_token}`
4. Access protected endpoints

---

## 🔥 Pro Tips

### Hot Reload

Server automatically reloads when you edit `.py` files. No need to restart manually!

### Debug Mode

In `.env`, set:
```bash
DEBUG=True
```

This enables:
- Detailed error messages
- Stack traces in responses
- Debug logging

### Database Browser

View your SQLite database:
```bash
# Install sqlite3
# Then:
sqlite3 trading_controller.db

# In sqlite3 shell:
.tables          # List tables
.schema users    # Show table schema
SELECT * FROM users;  # Query data
.quit            # Exit
```

Or use GUI tools:
- [DB Browser for SQLite](https://sqlitebrowser.org/)
- [DBeaver](https://dbeaver.io/)

### Code Auto-formatting

Install development tools:
```bash
pip install black isort flake8

# Format code
black app/
isort app/

# Check style
flake8 app/
```

### Environment Switching

Quick switch between environments:
```bash
# Development
uvicorn app.main:app --reload

# Load production config locally
export $(cat .env.production | xargs)
uvicorn app.main:app
```

---

## 🎉 You're Ready!

Your local development environment is set up. Start coding!

```bash
# Quick start
uv sync
uvicorn app.main:app --reload
```

Then open `http://localhost:8000/docs` and start exploring! 🚀

---

**Need help?** Check the troubleshooting section above or review the main documentation files.
