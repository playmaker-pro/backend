#!/bin/bash
# Watchdog script for Celery Beat - auto-restarts on failure

LOG_FILE="$1"
PID_FILE="$2"

if [ -z "$LOG_FILE" ] || [ -z "$PID_FILE" ]; then
    echo "Usage: $0 <log_file> <pid_file>"
    exit 1
fi

echo "Starting Celery Beat Watchdog" | tee -a "$LOG_FILE"

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
