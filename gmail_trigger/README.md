# Gmail Trigger für OpenClaw

Lauscht auf neue Gmail-Mails via IMAP IDLE und benachrichtigt OpenClaw in Echtzeit.

## Features

- **Echtzeit-Push** via IMAP IDLE (kein Polling)
- **Duplikat-Filterung** - gleiche Mails werden nicht mehrfach gemeldet
- **Multi-Label** - kann mehrere Labels überwachen (INBOX, Sent, etc.)
- **Systemd-Service** - läuft als Hintergrund-Service
- **Auto-Reconnect** - verbindet sich automatisch neu bei Verbindungsabbruch

## Schnellstart

### 1. Gmail App-Passwort erstellen

1. Google Account (bar.ai.bot@cudos.ch) → Sicherheit
2. **2-Schritt-Verifizierung** aktivieren (falls noch nicht)
3. App-Passwörter → Andere (benutzerdefinierter Name)
4. Name: "OpenClaw Gmail Trigger"
5. Passwort kopieren (z.B. `abcd efgh ijkl mnop`)

### 2. Konfiguration

```bash
cd ~/Development/mb_tools_bar

# .env aus Template erstellen
cp .env.example .env

# Bearbeiten
nano .env
```

```env
GMAIL_EMAIL=bar.ai.bot@cudos.ch
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
OPENCLAW_SESSION=main
GMAIL_LABELS=INBOX
```

### 3. Installation

```bash
cd gmail_trigger
sudo ./install.sh
```

Das Script:
- Erstellt ein Python Virtual Environment
- Installiert Dependencies
- Richtet einen systemd Service ein
- Startet den Service

### 4. Status prüfen

```bash
# Service-Status
sudo ./install.sh --status

# Oder direkt
sudo systemctl status gmail-trigger
sudo journalctl -u gmail-trigger -f
```

## Verwendung

### Einmalige Prüfung (manuell)

```bash
cd ~/Development/mb_tools_bar
source venv/bin/activate
cd gmail_trigger
./gmail_trigger.py --once
```

### Bestimmtes Label prüfen

```bash
./gmail_trigger.py --label INBOX --label Sent --once
```

### Service verwalten

```bash
# Stoppen
sudo systemctl stop gmail-trigger

# Starten
sudo systemctl start gmail-trigger

# Neustarten
sudo systemctl restart gmail-trigger

# Deaktivieren (nicht mehr automatisch starten)
sudo systemctl disable gmail-trigger

# Entfernen
sudo ./install.sh --remove
```

## Troubleshooting

### "Authentication failed"
- Prüfe ob 2FA aktiviert ist
- App-Passwort korrekt kopiert? (mit Leerzeichen)
- Normales Passwort funktioniert nicht - muss App-Passwort sein!

### "openclaw: command not found"
- openclaw CLI muss im PATH sein
- oder: `~/.local/bin/openclaw` stattdessen verwenden

### Service startet nicht
```bash
# Logs prüfen
sudo journalctl -u gmail-trigger -n 50 --no-pager

# Manuell testen
sudo systemctl stop gmail-trigger
cd ~/Development/mb_tools_bar
cd gmail_trigger
../venv/bin/python gmail_trigger.py --once
```

### Verbindung bricht ständig ab
- Gmail killt IDLE nach ~29 Minuten - das ist normal
- Script macht automatisch Reconnect
- Bei häufigen Abbrüchen: Netzwerk prüfen

## Architektur

```
Gmail IMAP Server
       ↓ (IDLE - push on new mail)
gmail_trigger.py
       ↓ (subprocess)
openclaw sessions_send
       ↓
OpenClaw Main Session
```

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `gmail_trigger.py` | Haupt-Script |
| `requirements.txt` | Python Dependencies |
| `install.sh` | Installation Script |
| `../.env` | Konfiguration (nicht im Git!) |

## Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `GMAIL_EMAIL` | - | Gmail Adresse |
| `GMAIL_APP_PASSWORD` | - | 16-stelliges App-Passwort |
| `GMAIL_IMAP_SERVER` | imap.gmail.com | IMAP Server |
| `OPENCLAW_SESSION` | main | OpenClaw Session-Key |
| `GMAIL_LABELS` | INBOX | Komma-getrennte Labels |
| `IDLE_TIMEOUT` | 600 | IDLE Timeout (Sekunden) |
| `PROCESSED_IDS_FILE` | /tmp/... | Cache für verarbeitete IDs |

## Lizenz

Internes Tool für Cudos AG / Reto Bättig
