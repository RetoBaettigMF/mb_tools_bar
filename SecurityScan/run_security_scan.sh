#!/bin/bash

# Security Scan Script für OpenClaw Workspace
# Führt security_scan.py aus und sendet Resultat per Email

set -e

SCRIPT_DIR="$HOME/Development/mb_tools_bar/SecurityScan/"
WORKSPACE_DIR="$HOME/.openclaw/workspace/"
OUTPUT_FILE="security_scan.txt"
RECIPIENT="reto.baettig@cudos.ch"

# In das Script-Verzeichnis wechseln
cd "$SCRIPT_DIR"
cd ..
source venv/bin/activate
cd "$SCRIPT_DIR"


echo "Starte Security Scan für $WORKSPACE_DIR..."

# Security Scan ausführen (Exit-Code abfangen, nicht abbrechen)
set +e
./security_scan.py "$WORKSPACE_DIR" 1 > "$OUTPUT_FILE"
SCAN_EXIT_CODE=$?
set -e

echo "Scan abgeschlossen. Ergebnis in $OUTPUT_FILE"

# Betreff je nach Scan-Ergebnis
if [ $SCAN_EXIT_CODE -eq 0 ]; then
  SUBJECT="✅ OK - Security Scan $(date '+%Y-%m-%d %H:%M')"
else
  SUBJECT="🚨 GEFAHR - Security Scan $(date '+%Y-%m-%d %H:%M')"
fi

# Email senden via gog gmail
echo "Sende Ergebnis an $RECIPIENT..."
FILE_CONTENT=$(cat "$OUTPUT_FILE")

/home/linuxbrew/.linuxbrew/bin/gog gmail send \
  --to "$RECIPIENT" \
  --subject "$SUBJECT" \
  --body "Das automatische Security Scan Ergebnis für den Workspace ist angehängt.

$FILE_CONTENT"

echo "Email erfolgreich gesendet an $RECIPIENT"
