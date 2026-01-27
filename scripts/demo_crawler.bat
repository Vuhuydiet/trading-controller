@echo off
REM Demo Crawler Script - For presentations
REM No Kafka required!

cd /d "%~dp0.."

echo.
echo ========================================================
echo    ADAPTIVE CRAWLER DEMO
echo    (No Kafka Required)
echo ========================================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Run the demo
python scripts\demo_crawler.py

echo.
pause
