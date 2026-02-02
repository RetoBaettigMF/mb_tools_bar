# mb_tools_bar

Custom extensions and tools for moltbot.

## RolX/Bexio Query Tool

CLI tool for querying RolX (time tracking) and Bexio (invoicing) via natural language.

### Installation

```bash
cd mb_tools_bar
pip install -r requirements.txt
chmod +x mbtools.py
```

### Configuration

Set your API key via environment variable:

```bash
export MBTOOLS_API_KEY="your-api-key-here"
```

Or create a config file at `~/.mbtools/config.json`:

```json
{
  "api_key": "your-api-key-here"
}
```

### Usage

**Query RolX (time tracking):**
```bash
./mbtools.py rolx "How many hours did Reto Bättig work in 2025 per task"
./mbtools.py rolx "Show all hours for project 0123.110"
```

**Query Bexio (invoicing):**
```bash
./mbtools.py bexio "Give me invoice #0290.001.01.01"
./mbtools.py bexio "Show all invoices with Project Number 290"
./mbtools.py bexio "Give me all invoices for Subproject #0290.001"
```

### API Endpoints

The tool connects to:
- **RolX:** `POST /rolx/query` - Natural language queries for timesheet data
- **Bexio:** `POST /bexio/query` - Natural language queries for invoice data

Base URL: `https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io`

### OpenAPI Specification

See [RolXChatAPI-spec.json](./RolXChatAPI-spec.json) for the complete API definition.

## Sales Potential Reminder Tool

Automated reminder that sends an email on the **Wednesday before the 4th Monday** of each month (typically the 3rd Wednesday).

### Usage

```bash
python3 sales_reminder.py <recipient_email>
```

**Example:**
```bash
python3 sales_reminder.py bu@cudos.ch
```

### How it works

- Checks if today is the Wednesday before the 4th Monday of the month
- If yes: Sends reminder email via `gog` to update sales potentials
- If no: Exits silently (designed for weekly cron jobs)

### Cron Setup

To run automatically every Wednesday at 09:00:

```bash
# Add to crontab (crontab -e)
0 9 * * 3 cd /home/reto/Development/mb_tools_bar && python3 sales_reminder.py bu@cudos.ch
```

Or use OpenClaw's cron system for session-based execution.

### Email Content

The reminder email is sent from Reto's account and includes:
- Friendly reminder to update sales potentials
- Signature from "Retos Bot Morticia 💪"

## Google Docs MCP Server

MCP-Server für das Editieren von Google Docs direkt aus OpenClaw.

### Files

- `mcp_server_google_docs.py` - Der MCP-Server
- `setup_docs_auth.py` - Setup-Skript für OAuth

### Features

- `docs_read` - Dokument lesen mit Pagination (Standard: 100 Zeilen)
- `docs_append` - Text ans Ende anhängen
- `docs_insert` - Text an bestimmter Position einfügen
- `docs_replace` - Text ersetzen

### Setup

1. **Auth einrichten (einmalig):**
   ```bash
   python3 setup_docs_auth.py
   ```
   Dann im Browser mit `bar.ai.bot@cudos.ch` anmelden.

2. **Mit mcporter nutzen:**
   ```bash
   mcporter config add google-docs --command "python3 /home/reto/Development/mb_tools_bar/mcp_server_google_docs.py"
   
   # Dokument lesen
   mcporter call google-docs.docs_read documentId=XXX maxLines=50
   
   # Text ersetzen/einfügen
   mcporter call google-docs.docs_replace documentId=XXX oldText="..." newText="..."
   ```

### Account

Verwendetes Konto: `bar.ai.bot@cudos.ch` (eigener Google Account von Morticia)

---

## Development

More tools coming soon...
