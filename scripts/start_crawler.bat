@echo off
REM Start the news crawler in periodic mode

cd /d "%~dp0.."

REM Load environment variables from .env if it exists
if exist .env (
    for /f "tokens=*" %%a in (.env) do (
        set "%%a"
    )
)

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo =========================================
echo Starting News Crawler (Periodic Mode)
echo =========================================
echo Kafka Servers: %KAFKA_BOOTSTRAP_SERVERS%
echo LLM Provider: %LLM_PROVIDER%
echo Crawl Interval: %NEWS_CRAWL_INTERVAL_MINUTES% minutes
echo =========================================
echo.

REM Run the crawler
python scripts\crawl_news.py

pause
