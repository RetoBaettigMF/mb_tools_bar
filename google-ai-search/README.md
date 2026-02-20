# Google AI Search

Kommandozeilen-Tool für Google Search AI via Gemini API.

## Features

- 🔍 Natürlichsprachige Suche mit Google Search AI
- 📚 Quellen werden automatisch zitiert
- 🎯 Direkt in der Shell nutzbar
- 📦 JSON-Output für Weiterverarbeitung
- 💬 Interaktiver Modus verfügbar

## Voraussetzungen

1. **Gemini CLI** installiert:
   ```bash
   brew install gemini-cli
   ```

2. **Authentifizierung** (einmalig):
   ```bash
   gemini
   # Folge dem Login-Flow
   ```

## Installation

```bash
# Symlink erstellen (optional)
ln -s ~/Development/mb_tools_bar/google-ai-search/google-ai-search ~/.local/bin/
```

## Verwendung

### Einfache Suche
```bash
google-ai-search "Aktueller Stand von Fusion Energy"
```

### JSON-Output
```bash
google-ai-search --json "Wetter in Zürich morgen"
```

### Bestimmtes Modell verwenden
```bash
google-ai-search --model gemini-1.5-pro "Python 3.12 neue Features"
```

### Interaktiver Modus
```bash
google-ai-search -i
```

## Hilfe

```bash
google-ai-search --help
```

## Technische Details

Das Tool nutzt die offizielle Gemini CLI mit automatischer Google Search Extension. Die Extension wird bei Bedarf automatisch aktiviert.
