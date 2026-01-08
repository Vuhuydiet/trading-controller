@echo off
REM Local Development Start Script for Trading Controller API (Windows)

setlocal enabledelayedexpansion

echo =========================================
echo Trading Controller - Local Development
echo =========================================
echo.

set "APP_DIR=%~dp0"
set "VENV_DIR=%APP_DIR%.venv"
set "ENV_FILE=%APP_DIR%.env"

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo [ERROR] Virtual environment not found at %VENV_DIR%
    echo.
    echo Please install dependencies first:
    echo   uv sync
    echo   # or
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -e .
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Check if .env exists, create if not
if not exist "%ENV_FILE%" (
    echo [WARN] .env file not found. Creating template...
    (
        echo # Development Settings
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # Database
        echo DATABASE_URL=sqlite:///./trading_controller.db
        echo.
        echo # Binance API ^(optional for public endpoints^)
        echo BINANCE_API_BASE_URL=https://api.binance.com
        echo BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
        echo BINANCE_API_KEY=
        echo BINANCE_API_SECRET=
        echo.
        echo # Development
        echo DEBUG=True
    ) > "%ENV_FILE%"
    echo [INFO] Template .env created!
    echo.
)

REM Check if database exists
if not exist "trading_controller.db" (
    echo [INFO] Database not found. Initializing...
    python -c "from app.shared.infrastructure.db import create_db_and_tables; create_db_and_tables(); print('[OK] Database initialized!')" || (
        echo [ERROR] Failed to initialize database
        pause
        exit /b 1
    )
    echo.
)

REM Check if uvicorn is installed
where uvicorn >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Uvicorn not found!
    echo Installing uvicorn...
    pip install uvicorn[standard]
)

echo.
echo [INFO] Starting development server...
echo.
echo Configuration:
echo   - Environment: Development
echo   - Hot reload: Enabled
echo   - Host: localhost
echo   - Port: 8000
echo.
echo Access your application at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start development server with auto-reload
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to start server
    pause
    exit /b 1
)
