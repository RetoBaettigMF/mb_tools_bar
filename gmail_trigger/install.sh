#!/bin/bash
#
# install.sh - Installiert gmail_trigger als systemd Service
#
# Verwendung:
#   sudo ./install.sh              # Installiert und startet Service
#   sudo ./install.sh --remove     # Entfernt Service
#   sudo ./install.sh --status     # Zeigt Service-Status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="gmail-trigger"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
USER="${SUDO_USER:-$USER}"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Dieses Script muss als root laufen. Bitte mit sudo ausführen."
        exit 1
    fi
}

check_env() {
    ENV_FILE="${SCRIPT_DIR}/../.env"
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env Datei nicht gefunden: $ENV_FILE"
        echo "Bitte zuerst .env aus .env.example erstellen:"
        echo "  cp ${SCRIPT_DIR}/../.env.example ${SCRIPT_DIR}/../.env"
        echo "  nano ${SCRIPT_DIR}/../.env"
        exit 1
    fi
    
    # Prüfe ob required vars gesetzt
    if ! grep -q "GMAIL_EMAIL=" "$ENV_FILE" || ! grep -q "GMAIL_APP_PASSWORD=" "$ENV_FILE"; then
        log_error "GMAIL_EMAIL oder GMAIL_APP_PASSWORD nicht in .env gesetzt!"
        exit 1
    fi
    
    log_info ".env gefunden und konfiguriert"
}

install_service() {
    log_info "Installiere gmail-trigger Service..."
    
    # Virtual Environment im Parent-Verzeichnis verwenden
    VENV_PATH="${SCRIPT_DIR}/../venv"
    if [[ ! -d "$VENV_PATH" ]]; then
        log_error "Virtual Environment nicht gefunden: $VENV_PATH"
        echo "Bitte zuerst das venv im Parent-Verzeichnis erstellen:"
        echo "  cd ${SCRIPT_DIR}/.. && bash setup_venv.sh"
        exit 1
    fi

    # Requirements installieren
    log_info "Installiere Python Dependencies..."
    "$VENV_PATH/bin/pip" install -q -r "${SCRIPT_DIR}/../requirements.txt"
    
    # Service Datei erstellen
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Gmail Trigger for OpenClaw
After=network.target
Wants=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${SCRIPT_DIR}
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=${SCRIPT_DIR}/../.env
ExecStart=${VENV_PATH}/bin/python ${SCRIPT_DIR}/gmail_trigger.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=gmail-trigger

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/tmp

[Install]
WantedBy=multi-user.target
EOF
    
    log_info "Service-Datei erstellt: $SERVICE_FILE"
    
    # Systemd neu laden
    systemctl daemon-reload
    
    # Service aktivieren
    systemctl enable "$SERVICE_NAME"
    log_info "Service aktiviert (startet automatisch beim Boot)"
    
    # Service starten
    systemctl start "$SERVICE_NAME"
    log_info "Service gestartet"
    
    # Status anzeigen
    sleep 1
    show_status
}

remove_service() {
    log_info "Entferne gmail-trigger Service..."
    
    # Service stoppen
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    
    # Service deaktivieren
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    
    # Service-Datei löschen
    if [[ -f "$SERVICE_FILE" ]]; then
        rm "$SERVICE_FILE"
        log_info "Service-Datei entfernt"
    fi
    
    # Systemd neu laden
    systemctl daemon-reload
    
    log_info "Service entfernt"
}

show_status() {
    echo ""
    echo "=== Service Status ==="
    systemctl status "$SERVICE_NAME" --no-pager || true
    echo ""
    echo "=== Letzte Logs ==="
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager || true
    echo ""
    echo "=== Nützliche Befehle ==="
    echo "Status prüfen:  sudo systemctl status $SERVICE_NAME"
    echo "Logs anzeigen:  sudo journalctl -u $SERVICE_NAME -f"
    echo "Neu starten:    sudo systemctl restart $SERVICE_NAME"
    echo "Stoppen:        sudo systemctl stop $SERVICE_NAME"
}

show_help() {
    echo "Gmail Trigger - Installation Script"
    echo ""
    echo "Verwendung:"
    echo "  sudo ./install.sh         Installiert und startet den Service"
    echo "  sudo ./install.sh --remove   Entfernt den Service"
    echo "  sudo ./install.sh --status   Zeigt Service-Status und Logs"
    echo "  ./install.sh --help          Zeigt diese Hilfe"
    echo ""
    echo "Voraussetzungen:"
    echo "  1. .env Datei im Parent-Verzeichnis (~/Development/mb_tools_bar/.env)"
    echo "  2. GMAIL_EMAIL und GMAIL_APP_PASSWORD in .env gesetzt"
    echo "  3. openclaw CLI muss verfügbar sein"
}

# Main
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

if [[ "$1" == "--remove" ]]; then
    check_root
    remove_service
    exit 0
fi

if [[ "$1" == "--status" ]]; then
    show_status
    exit 0
fi

# Default: Installieren
check_root
check_env
install_service

log_info "Installation abgeschlossen!"
log_info "Emails werden jetzt überwacht und an OpenClaw gesendet."
