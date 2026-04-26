#!/bin/bash
# install.sh - Richtet gmail-trigger als systemd User-Service ein

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="gmail-trigger"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/${SERVICE_NAME}.service"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_deps() {
    local missing=()
    command -v gog      &>/dev/null || missing+=("gog")
    command -v openclaw &>/dev/null || missing+=("openclaw")

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Fehlende Programme: ${missing[*]}"
        echo "Bitte erst installieren, dann erneut ausführen."
        exit 1
    fi

    info "Abhängigkeiten OK (gog, openclaw)"
}

install_service() {
    mkdir -p "$SERVICE_DIR"

    # PATH aus der aktuellen Shell-Session übernehmen
    local service_path="$PATH"

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Gmail Trigger for OpenClaw
After=network.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${SCRIPT_DIR}
Environment=PATH=${service_path}
ExecStart=${SCRIPT_DIR}/gmail_trigger.sh
Restart=always
RestartSec=30

StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=default.target
EOF

    info "Service-Datei erstellt: $SERVICE_FILE"

    systemctl --user daemon-reload
    systemctl --user enable "$SERVICE_NAME"
    systemctl --user start  "$SERVICE_NAME"

    # Lingering aktivieren: Service läuft auch ohne aktive Login-Session
    if loginctl enable-linger "$USER" 2>/dev/null; then
        info "Lingering aktiviert – Service startet auch ohne Login"
    else
        warn "Lingering konnte nicht aktiviert werden (kein sudo?). Service läuft nur bei aktiver Session."
    fi

    sleep 1
    show_status
    info "Installation abgeschlossen."
}

show_status() {
    echo ""
    echo "=== Service Status ==="
    systemctl --user status "$SERVICE_NAME" --no-pager || true
    echo ""
    echo "=== Letzte Logs ==="
    journalctl --user -u "$SERVICE_NAME" -n 15 --no-pager || true
    echo ""
    echo "=== Nützliche Befehle ==="
    echo "  Logs live:    journalctl --user -u $SERVICE_NAME -f"
    echo "  Neu starten:  systemctl --user restart $SERVICE_NAME"
    echo "  Stoppen:      systemctl --user stop $SERVICE_NAME"
    echo "  Deinstall:    ./uninstall.sh"
}

show_help() {
    echo "Gmail Trigger – Install Script"
    echo ""
    echo "Verwendung:"
    echo "  ./install.sh           Installiert und startet den Service"
    echo "  ./install.sh --status  Zeigt Status und Logs"
    echo "  ./install.sh --help    Diese Hilfe"
    echo ""
    echo "Für Deinstallation: ./uninstall.sh"
}

case "${1:-}" in
    --help|-h) show_help; exit 0 ;;
    --status)  show_status; exit 0 ;;
    "")
        check_deps
        install_service
        ;;
    *)
        error "Unbekannte Option: $1"
        show_help
        exit 1
        ;;
esac
