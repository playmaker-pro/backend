#!/bin/bash
# Watchdog script for Celery Worker - auto-restarts on failure

PROJECT_NAME="$1"
LOG_FILE="$2"

if [ -z "$PROJECT_NAME" ] || [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 <project_name> <log_file>"
    exit 1
fi

echo "Starting Celery Worker Watchdog for $PROJECT_NAME" | tee -a "$LOG_FILE"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Celery worker..." | tee -a "$LOG_FILE"
    
    poetry run celery -A backend worker \
        --autoscale=0,6 \
        --without-mingle \
        --without-gossip \
        --loglevel=DEBUG \
        -n "worker_${PROJECT_NAME}@%h" \
        --max-tasks-per-child=1000 \
        --task-events \
        --pool=prefork 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Celery worker exited with code $EXIT_CODE" | tee -a "$LOG_FILE"
    
    # If explicitly stopped (SIGTERM), don't restart
    if [ $EXIT_CODE -eq 143 ] || [ $EXIT_CODE -eq 130 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Celery worker stopped gracefully. Exiting watchdog." | tee -a "$LOG_FILE"
        exit 0
    fi
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restarting in 5 seconds..." | tee -a "$LOG_FILE"
    sleep 5
done
