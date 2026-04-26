#!/bin/bash

# Gmail trigger loop: checks for unread mail, triggers openclaw, then waits 1 minute.
# Processing completes before the timer starts.

LOG_TAG="gmail-trigger"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
    logger -t "$LOG_TAG" "$*"
}

log "Service started"

while true; do
    RESULT=$(gog gmail search "is:unread" 2>/dev/null)

    if echo "$RESULT" | grep -q "THREAD"; then
        log "New mail detected – triggering openclaw"
        openclaw agent --agent main -m "You've got mail. Please handle them."
        log "openclaw finished"
    fi

    sleep 60
done
