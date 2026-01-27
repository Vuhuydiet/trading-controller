#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$DIR/.."

echo "========================================================"
echo "TRIGGERING MOCK NEWS TO KAFKA"
echo "========================================================"

cd "$PROJECT_ROOT"

# Kiểm tra uv
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    exit 1
fi

# Chạy lệnh
echo "Sending test message..."
uv run python scripts/test_kafka_msg.py

if [ $? -eq 0 ]; then
    echo "Message sent successfully! Check your AI Consumer terminal."
else
    echo "Failed to send message."
fi