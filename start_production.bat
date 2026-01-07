@echo off
REM Production Start Script for Trading Controller API (Windows)
REM This script helps you start the application in production mode

setlocal enabledelayedexpansion

echo =========================================
echo Trading Controller - Production Startup
echo =========================================
echo.

set "APP_DIR=%~dp0"
set "ENV_FILE=%APP_DIR%.env.production"
set "LOG_DIR=%APP_DIR%logs"
set "VENV_DIR=%APP_DIR%.venv"

REM Check if .env.production exists
if not exist "%ENV_FILE%" (
    echo [ERROR] .env.production not found!
    echo.
    echo Creating template .env.production file...
    (
        echo # Application Settings
        echo APP_ENV=production
        echo DEBUG=False
        echo LOG_LEVEL=INFO
        echo.
        echo # Security - CHANGE THESE!
        echo SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_STRING
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # Database
        echo DATABASE_URL=sqlite:///./trading_controller_prod.db
        echo.
        echo # Binance API Configuration
        echo BINANCE_API_BASE_URL=https://api.binance.com
        echo BINANCE_WS_BASE_URL=wss://stream.binance.com:9443
        echo BINANCE_API_KEY=your_binance_api_key_here
        echo BINANCE_API_SECRET=your_binance_api_secret_here
        echo.
        echo # Server Settings
        echo HOST=0.0.0.0
        echo PORT=8000
        echo WORKERS=4
    ) > "%ENV_FILE%"

    echo [WARN] Template .env.production created. Please edit it with your configuration!
    echo.
    echo To generate a secure SECRET_KEY, run:
    echo   python -c "import secrets; print(secrets.token_urlsafe(32))"
    echo.
    pause
    exit /b 1
)

REM Check if SECRET_KEY is still default
findstr /C:"CHANGE_THIS_TO_A_SECURE_RANDOM_STRING" "%ENV_FILE%" >nul
if !errorlevel! equ 0 (
    echo [ERROR] SECRET_KEY is still set to default value!
    echo.
    echo Generate a secure key with:
    echo   python -c "import secrets; print(secrets.token_urlsafe(32))"
    echo.
    echo Then update SECRET_KEY in .env.production
    pause
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" (
    echo [INFO] Creating logs directory...
    mkdir "%LOG_DIR%"
)

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
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Load environment variables from .env.production
echo [INFO] Loading environment variables from .env.production...
for /f "usebackq tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
    set "line=%%a"
    if not "!line:~0,1!"=="#" (
        set "%%a=%%b"
    )
)

REM Check if gunicorn is installed
where gunicorn >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARN] Gunicorn not found. On Windows, using uvicorn instead...
    where uvicorn >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Neither gunicorn nor uvicorn found!
        echo Installing uvicorn...
        pip install uvicorn[standard]
    )
)

REM Initialize database if it doesn't exist
if not exist "trading_controller_prod.db" (
    echo [INFO] Initializing database...
    python -c "from app.shared.infrastructure.db import create_db_and_tables; create_db_and_tables(); print('Database initialized successfully!')"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to initialize database
        pause
        exit /b 1
    )
)

REM Set default values if not set
if not defined PORT set PORT=8000
if not defined HOST set HOST=0.0.0.0
if not defined WORKERS set WORKERS=4

REM Check if port is available
netstat -ano | findstr ":%PORT%" >nul
if !errorlevel! equ 0 (
    echo [ERROR] Port %PORT% is already in use!
    echo.
    echo To find the process using the port:
    echo   netstat -ano ^| findstr ":%PORT%"
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting Trading Controller API in production mode...
echo.
echo Configuration:
echo   - Host: %HOST%
echo   - Port: %PORT%
echo   - Workers: %WORKERS%
echo   - Log Directory: %LOG_DIR%
echo   - Environment: production
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start with uvicorn (Windows-friendly)
uvicorn app.main:app ^
    --host %HOST% ^
    --port %PORT% ^
    --workers %WORKERS% ^
    --log-level info ^
    --no-access-log ^
    --proxy-headers

if !errorlevel! neq 0 (
    echo [ERROR] Failed to start application
    pause
    exit /b 1
)
