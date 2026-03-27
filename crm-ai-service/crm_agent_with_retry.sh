#!/bin/bash
# crm_agent_with_retry.sh - CRM Agent mit automatischem Retry bei Timeout

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_RETRIES=2
RETRY_COUNT=0
EXIT_CODE=1

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # CRM Agent ausführen
    timeout 90 "$SCRIPT_DIR/crm_agent.py" "$@"
    EXIT_CODE=$?
    
    # Bei Erfolg (Exit Code 0) → fertig
    if [ $EXIT_CODE -eq 0 ]; then
        exit 0
    fi
    
    # Bei Timeout (Exit Code 124) oder LLM-Error → Retry
    if [ $EXIT_CODE -eq 124 ] || [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo ""
        echo "⚠️  Versuch $RETRY_COUNT fehlgeschlagen (Exit Code: $EXIT_CODE). Warte 3 Sekunden und versuche erneut..."
        sleep 3
    fi
done

echo ""
echo "❌ Alle $MAX_RETRIES Versuche fehlgeschlagen."
exit $EXIT_CODE
