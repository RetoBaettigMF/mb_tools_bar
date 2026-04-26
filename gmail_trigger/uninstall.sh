#!/bin/bash
# uninstall.sh - Entfernt den gmail-trigger systemd User-Service

set -e

SERVICE_NAME="gmail-trigger"
SERVICE_FILE="${HOME}/.config/systemd/user/${SERVICE_NAME}.service"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }

systemctl --user stop    "$SERVICE_NAME" 2>/dev/null && info "Service gestoppt."    || warn "Service war nicht aktiv."
systemctl --user disable "$SERVICE_NAME" 2>/dev/null && info "Service deaktiviert." || true

if [[ -f "$SERVICE_FILE" ]]; then
    rm "$SERVICE_FILE"
    info "Service-Datei entfernt: $SERVICE_FILE"
else
    warn "Service-Datei nicht gefunden (bereits entfernt?)."
fi

systemctl --user daemon-reload
info "Deinstallation abgeschlossen."
