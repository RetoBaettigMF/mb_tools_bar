# gmail-trigger

Pollt alle 60 Sekunden auf ungelesene Gmail-Nachrichten und übergibt sie an den OpenClaw-Agent.

## Funktionsweise

```
gog gmail search "is:unread"
        ↓ (neue Mail gefunden)
openclaw agent --agent main -m "You've got mail. Please handle them."
        ↓
OpenClaw Main Session
```

Der Service läuft als systemd User-Service, startet automatisch beim Boot und schreibt Logs ins systemd Journal.

## Voraussetzungen

- [`gog`](https://github.com/...) CLI – muss im PATH sein und Gmail-Zugriff haben
- [`openclaw`](https://github.com/...) CLI – muss im PATH sein

## Installation

```bash
cd gmail_trigger
chmod +x install.sh uninstall.sh gmail_trigger.sh
./install.sh
```

Das Script prüft die Abhängigkeiten, erstellt den systemd User-Service und startet ihn.

## Deinstallation

```bash
./uninstall.sh
```

## Service verwalten

```bash
# Status und letzte Logs
./install.sh --status

# Logs live verfolgen
journalctl --user -u gmail-trigger -f

# Neu starten / stoppen / starten
systemctl --user restart gmail-trigger
systemctl --user stop    gmail-trigger
systemctl --user start   gmail-trigger
```

## Dateien

| Datei               | Beschreibung                        |
|---------------------|-------------------------------------|
| `gmail_trigger.sh`  | Haupt-Script (Polling-Loop)         |
| `install.sh`        | Richtet den systemd Service ein     |
| `uninstall.sh`      | Entfernt den systemd Service        |
