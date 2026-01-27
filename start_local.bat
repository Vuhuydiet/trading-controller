@echo off
REM Local Development Start Script for Trading Controller API (Windows)

echo =========================================
echo Trading Controller - Local Development
echo =========================================
echo.

set "APP_DIR=%~dp0"
set "VENV_DIR=%APP_DIR%.venv"

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo [ERROR] Virtual environment not found at %VENV_DIR%
    echo Please run: uv sync
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Start Docker services
echo [INFO] Starting infrastructure services (Kafka + Ollama)...
docker compose -f docker-compose.local.yml up -d

echo [INFO] Waiting for services to be ready (15 seconds)...
timeout /t 15 /nobreak > nul

echo.
echo [INFO] Starting development server...
echo.
echo Access your application at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
