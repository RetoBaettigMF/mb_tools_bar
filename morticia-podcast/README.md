# morticia-podcast

Generiert einen täglichen News-Podcast (ca. 15 Minuten) aus NZZ-Artikeln und aktuellen Web-Suchen.

## Features

- **4 Kategorien:** International, Schweiz, Wissenschaft, Wirtschaft
- **Kein Sport/Promis:** Explizit ausgeschlossen
- **Automatische Quellen:** NZZ + Google AI Search
- **Output:** MP3 + Markdown mit Quellenangaben
- **Publikation:** Direkt auf baettig.org/morticia

## Verwendung

```bash
# Heutigen Podcast generieren
morticia-podcast

# Für spezifisches Datum
morticia-podcast --date 2024-01-15

# Generieren und publizieren
morticia-podcast --publish

# Kombiniert
morticia-podcast --date 2024-01-15 --publish
```

## Abhängigkeiten

- `nzz-reader` (lokal installiert)
- `google-ai-search` (lokal installiert)
- `morticia-publish` (lokal installiert)
- Optional: `gTTS` oder `espeak` für TTS

## Output

Nach Publikation verfügbar unter:
- `https://baettig.org/morticia/morticia-podcast-YYYY-MM-DD.mp3`
- `https://baettig.org/morticia/morticia-podcast-YYYY-MM-DD.md`

## Automatisierung

Für tägliche Generierung kann ein Cron-Job eingerichtet werden:

```bash
# Jeden Morgen um 7:00 Uhr
0 7 * * * /home/reto/Development/mb_tools_bar/morticia-podcast/morticia-podcast --publish
```