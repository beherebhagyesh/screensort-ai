#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$PROJECT_DIR/sort_log.txt"
SCRIPT="sort_screenshots.py"

# Check if running
if pgrep -f "python3 .*$SCRIPT" > /dev/null; then
    echo "Sorting service is already running."
else
    echo "Starting sorting service..."
    cd "$PROJECT_DIR"
    nohup python3 "$SCRIPT" > "$LOG_FILE" 2>&1 &
    echo "Service started. Logs at $LOG_FILE"
fi
