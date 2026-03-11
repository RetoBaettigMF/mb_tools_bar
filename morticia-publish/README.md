# morticia-publish

Tool zum Publizieren von Webseiten und Dateien auf https://baettig.org/morticia

## Installation

Bereits vorhanden in `~/Development/mb_tools_bar/morticia-publish/`

## Verwendung

```bash
# Einzelne Dateien publizieren
morticia-publish index.html style.css bild.png

# Alle Dateien im Verzeichnis auflisten
morticia-publish --list

# Ein ganzes Verzeichnis synchronisieren
morticia-publish --sync-dir ./meine-webseite/

# Datei löschen
morticia-publish --delete alte-datei.html

# Index-Seite erstellen (zeigt alle Dateien an)
morticia-publish --index "Meine Sammlung"
```

## Basis-URL

Nach dem Publizieren sind Dateien verfügbar unter:
```
https://baettig.org/morticia/<dateiname>
```

## Beispiele

```bash
# HTML-Datei publizieren
morticia-publish bericht.html
# → https://baettig.org/morticia/bericht.html

# Mehrere CSS/JS-Dateien
morticia-publish app.js styles.css

# Komplette Webseite hochladen
morticia-publish --sync-dir ~/Documents/meine-webseite/
```