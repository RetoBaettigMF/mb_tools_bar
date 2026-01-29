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

## Development

More tools coming soon...
