# OpenClaw.ai Toolbox

Collection of CLI Tools for Cudos internal systems, designed for use with OpenClaw.ai.

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and add your secrets:

```bash
cp .env.example .env
# Edit .env and add your MBTOOLS_API_KEY
```

### 2. Setup Virtual Environment

```bash
bash setup_venv.sh
source venv/bin/activate
```

### 3. Configure Tools

Each tool has its own setup requirements. See individual tool READMEs for details.

## Tools Overview

### 🛠️ CLI Tools

#### [NZZ Reader](./nzz-reader/README.md)

Liest NZZ-Artikel aus dem lokalen Scraping-Archiv.

**Features:**
- Liste der neuesten Artikel anzeigen
- Vollständige Artikel-Texte lesen
- Direkt aus der Kommandozeile nutzbar

**Usage:**
```bash
# Zeige die neuesten 10 Artikel
./nzz-reader

# Zeige den vollständigen Text eines Artikels (z.B. Artikel #3)
./nzz-reader 3
```

#### [Google AI Search](./google-ai-search/README.md)

Kommandozeilen-Tool für Google Search AI via Gemini API.

**Features:**
- 🔍 Natürlichsprachige Suche mit Google Search AI
- 📚 Quellen werden automatisch zitiert
- 🎯 Direkt in der Shell nutzbar
- 📦 JSON-Output für Weiterverarbeitung
- 💬 Interaktiver Modus verfügbar

**Setup:**
```bash
# API Key in config.json hinterlegen
# ODER: GEMINI_API_KEY als Umgebungsvariable setzen
```

**Usage:**
```bash
# Einfache Suche
./google-ai-search "Aktueller Stand von Fusion Energy"

# JSON-Output
./google-ai-search --json "Wetter in Zürich morgen"

# Bestimmtes Modell verwenden
./google-ai-search --model gemini-1.5-pro "Python 3.12 neue Features"

# Interaktiver Modus
./google-ai-search -i
```

#### [Cudos Controlling CLI](./CudosControllingTool/README.md)

Query RolX (timesheet) and Bexio (invoicing) via natural language from the command line.

**Features:**
- `rolx` subcommand - Query timesheet data
- `bexio` subcommand - Query invoice data
- Natural language queries in English or German
- JSON mode for scripting

**Setup:**
```bash
# Set API key (either in .env file or export)
echo 'MBTOOLS_API_KEY=your-key' >> .env
# Or: export MBTOOLS_API_KEY="your-key"
```

**Usage:**
```bash
# RolX timesheet queries
./cudos-controlling rolx "How many hours did Reto Bättig work in 2025 per task"
./cudos-controlling rolx "Wie viele Stunden hat Reto gearbeitet?" --json

# Bexio invoicing queries
./cudos-controlling bexio "Give me invoice #0290.001.01.01"
./cudos-controlling bexio "Show all invoices for project 290" --json
```

#### [SalesReminderTool](./SalesReminderTool/README.md)

Automated email reminder sent on the Wednesday before the 4th Monday of each month.

**Setup:**
```bash
# Add to crontab
crontab -e
# Add: 0 9 * * 3 python3 /path/to/sales-reminder bu@cudos.ch
```

**Manual usage:**
```bash
python3 sales-reminder recipient@example.com
```

## Architecture

```
mb_tools_bar/
├── venv/                           # Shared virtual environment
├── CudosControllingTool/
│   ├── cudos_controlling.py        # CLI tool
│   └── README.md
├── SalesReminderTool/
│   ├── sales_reminder.py           # CLI tool
│   └── README.md
├── nzz-reader/                     # NZZ Reader CLI
│   ├── nzz-reader                  # Main script
│   └── README.md
├── google-ai-search/               # Google AI Search CLI
│   ├── google-ai-search            # Main script
│   ├── config.json                 # API key config (git-ignored)
│   └── README.md
├── cudos-controlling               # Symlink → CudosControllingTool/cudos_controlling.py
├── sales-reminder                  # Symlink → SalesReminderTool/sales_reminder.py
├── requirements.txt                # All dependencies
├── setup_venv.sh                   # Virtual environment setup
├── README.md                       # This file
└── CLAUDE.md                       # Development guidelines
```

## CLI Tool Pattern

All CLI tools follow a consistent architecture:

1. **Command-line arguments** - Using `argparse` for subcommands and flags
2. **Formatted output** - Pretty-printed by default, JSON mode with `--json` flag
3. **UTF-8 support** - Proper handling of German umlauts and special characters
4. **Exit codes** - 0 for success, 1 for errors
5. **Consistent error handling** - Clear error messages to stderr

## Dependencies

### Core (shared)
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`

### Cudos Controlling CLI
- Python stdlib only (argparse, json, urllib)
- Optional: python-dotenv (for .env file support)

### Sales Reminder Tool
- Python stdlib only (calendar, datetime)

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Development

### Adding a New Tool

1. Create directory: `NewToolCLI/`
2. Add main script with `argparse` CLI interface
3. Create tool-specific `README.md`
4. Add dependencies to `requirements.txt`
5. Create symlink in root: `ln -s NewToolCLI/tool_name.py new-tool`
6. Update this README

### Testing CLI Tools

Test directly from the command line:

```bash
# Basic test
./tool-name --help

# Test functionality
./tool-name subcommand "query or args"

# Test JSON output
./tool-name subcommand "query" --json | jq '.'
```

## License

[MIT Open Source License](https://opensource.org/license/mit)
