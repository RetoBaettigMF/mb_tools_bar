# Google AI Search

Kommandozeilen-Tool für Google-Suche mit echten Quellen-URLs.

## Funktionsweise

Das Tool kombiniert:
1. **Google Custom Search API** - Für echte Suchergebnisse mit funktionierenden URLs
2. **Gemini API** - Für intelligente Zusammenfassung der Suchergebnisse

## Installation

```bash
git clone <repo-url>
cd google-ai-search
chmod +x google-ai-search
```

## Einrichtung

### 1. Google API Key erstellen

1. Gehe zu [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Erstelle ein neues Projekt (oder verwende ein bestehendes)
3. Klicke auf "Create Credentials" → "API Key"
4. Speichere den API Key

### 2. Custom Search API aktivieren

1. Gehe zu [API Library](https://console.cloud.google.com/apis/library)
2. Suche nach "Custom Search API"
3. Klicke auf "Enable"

### 3. Custom Search Engine (CSE) erstellen

1. Gehe zu [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Klicke auf "Create a search engine"
3. Gib einen Namen ein (z.B. "AI Search")
4. Wähle "Search the entire web" unter "What to search?"
5. Klicke auf "Create"
6. Kopiere die "Search engine ID" (z.B. `0123456789abcdef0:abc123def456`)

### 4. Konfiguration

Erstelle eine `config.json` im Tool-Verzeichnis:

```json
{
  "google_api_key": "AIza...",
  "google_cse_id": "0123456789abcdef0:abc123def456"
}
```

Oder nutze Umgebungsvariablen:

```bash
export GOOGLE_API_KEY="AIza..."
export GOOGLE_CSE_ID="0123456789abcdef0:abc123def456"
```

## Nutzung

```bash
# Einfache Suche
./google-ai-search "Aktuelle Temperatur Zürich"

# Mit mehr Ergebnissen
./google-ai-search -n 10 "Python 3.12 Features"

# JSON-Ausgabe
./google-ai-search --json "Wetter in Zürich morgen"

# Interaktiver Modus
./google-ai-search -i

# Rohe Ausgabe ohne Formatierung
./google-ai-search --raw "Aktuelle Nachrichten Schweiz"
```

## Optionen

```
-i, --interactive      Interaktiver Modus
-m, --model           Gemini-Modell (default: gemini-2.5-flash)
-j, --json            Ausgabe als JSON
-r, --raw             Rohe Ausgabe
-t, --timeout         Timeout in Sekunden (default: 30)
-n, --num-results     Anzahl Ergebnisse (default: 5, max: 10)
--show-tools          Zeige verwendete Tools
```

## Kosten

- **Google Custom Search API**: 100 queries/Tag kostenlos, danach $5 pro 1000 queries
- **Gemini API**: Generous free tier, für Details siehe [Gemini Pricing](https://ai.google.dev/pricing)

## Fehlerbehebung

### "Kein API Key gefunden"
- Prüfe ob `GOOGLE_API_KEY` oder `GEMINI_API_KEY` gesetzt ist
- Oder ob `config.json` existiert mit korrektem Key

### "Keine CSE ID gefunden"
- CSE ID muss in `GOOGLE_CSE_ID` Umgebungsvariable oder `config.json` sein

### "Permission denied"
- Custom Search API ist nicht aktiviert
- API Key ist ungültig

### "Rate limit überschritten"
- 100 queries/Tag Limit erreicht
- Warte bis morgen oder upgrade deinen Plan

## Lizenz

MIT
