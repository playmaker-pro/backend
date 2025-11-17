#!/bin/bash
# Watchdog script for Celery Beat - auto-restarts on failure

PROJECT_NAME="$1"
LOG_FILE="$2"
PID_FILE="$3"

if [ -z "$PROJECT_NAME" ] || [ -z "$LOG_FILE" ] || [ -z "$PID_FILE" ]; then
    echo "Usage: $0 <project_name> <log_file> <pid_file>"
    exit 1
fi

echo "Starting Celery Beat Watchdog for $PROJECT_NAME" | tee -a "$LOG_FILE"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Celery beat..." | tee -a "$LOG_FILE"
    
    poetry run celery -A backend beat \
        -l info \
        --scheduler django \
        --pidfile "$PID_FILE" 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Celery beat exited with code $EXIT_CODE" | tee -a "$LOG_FILE"
    
    # If explicitly stopped (SIGTERM), don't restart
    if [ $EXIT_CODE -eq 143 ] || [ $EXIT_CODE -eq 130 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Celery beat stopped gracefully. Exiting watchdog." | tee -a "$LOG_FILE"
        exit 0
    fi
    
    # Clean up stale pid file
    rm -f "$PID_FILE"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restarting in 5 seconds..." | tee -a "$LOG_FILE"
    sleep 5
done
