@echo off
cd /d %~dp0..

echo ========================================================
echo TRIGGERING MOCK NEWS TO KAFKA
echo ========================================================

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: 'uv' is not installed or not in PATH.
    pause
    exit /b 1
)

:: Chạy lệnh test
echo Sending test message...
uv run python scripts/test_kafka_msg.py

if %errorlevel% neq 0 (
    echo Failed to send message. Check Kafka connection!
) else (
    echo Message sent successfully! Check your AI Consumer terminal.
)

echo.
pause