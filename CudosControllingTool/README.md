# Cudos Controlling CLI Tool

Command-line tool for querying Cudos internal controlling systems (RolX timesheet and Bexio invoicing) via natural language.

## Features

- **RolX queries** - Query timesheet data, hours worked, tasks, projects, and time periods
- **Bexio queries** - Query invoicing data, invoices, project numbers, amounts, and dates
- **Natural language interface** - Ask questions in plain English or German
- **JSON mode** - Machine-readable output for scripting and piping
- **UTF-8 support** - Handles German umlauts and special characters correctly

## Setup

### 1. Configure API Key

**Option 1: Use .env file (recommended)**

```bash
# In repository root
cp .env.example .env
# Edit .env and set: MBTOOLS_API_KEY=your-actual-key
```

**Option 2: Environment variable**

```bash
export MBTOOLS_API_KEY="your-api-key-here"
```

**Option 3: Config file**

Create `~/.mbtools/config.json`:

```json
{
  "api_key": "your-api-key-here"
}
```

## Usage

### Basic Command Structure

```bash
cudos-controlling <subcommand> <query> [--json]
```

**Subcommands:**
- `rolx` - Query RolX timesheet data
- `bexio` - Query Bexio invoicing data

**Flags:**
- `--json` - Output raw JSON (for scripting/piping)
- `--help` - Show help message

### RolX Timesheet Queries

```bash
# Hours worked by person
./cudos-controlling rolx "How many hours did Reto Bättig work in 2025 per task"

# Hours for specific project
./cudos-controlling rolx "Show all hours for project 0123.110"

# Time period analysis
./cudos-controlling rolx "What are the total hours logged in Q1 2025"

# German queries work too
./cudos-controlling rolx "Wie viele Stunden hat Reto gearbeitet in Januar 2025?"
```

### Bexio Invoicing Queries

```bash
# Get specific invoice
./cudos-controlling bexio "Give me invoice #0290.001.01.01"

# Find invoices by project
./cudos-controlling bexio "Show all invoices with Project Number 290"

# Invoice statistics
./cudos-controlling bexio "What is the total invoiced amount for 2025"

# German queries
./cudos-controlling bexio "Zeige Rechnung #0290.001.01.01"
```

### JSON Output for Scripting

Use the `--json` flag to get machine-readable output:

```bash
# Get JSON output
./cudos-controlling rolx "Show hours for project 0123.110" --json

# Pipe to jq for processing
./cudos-controlling bexio "Show all invoices for 2025" --json | jq '.response'

# Save to file
./cudos-controlling rolx "Hours by person in 2025" --json > report.json
```

### Help

```bash
# General help
./cudos-controlling --help

# Subcommand-specific help
./cudos-controlling rolx --help
./cudos-controlling bexio --help
```

## Output Format

### Default Mode (Formatted Text)

Pretty-printed JSON with indentation and UTF-8 support:

```json
{
  "response": "Data here...",
  "metadata": {
    "query": "original query"
  }
}
```

### Error Messages

Errors are formatted clearly:

```
Error: No API key found. Set MBTOOLS_API_KEY environment variable or create ~/.mbtools/config.json
```

### Exit Codes

- `0` - Success
- `1` - Error (missing API key, API error, invalid arguments)

## API Details

- **Base URL**: `https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io`
- **Endpoints**:
  - `/rolx/query` - RolX timesheet queries
  - `/bexio/query` - Bexio invoice queries
- **Authentication**: Bearer token via `Authorization` header
- **Timeout**: 30 seconds per request

## Dependencies

- Python 3 standard library only (`argparse`, `json`, `urllib`)
- Optional: `python-dotenv` (for .env file support)
- No external dependencies required for core functionality

## Error Handling

Common errors and solutions:

| Error | Solution |
|-------|----------|
| Missing API key | Set `MBTOOLS_API_KEY` environment variable or create config file |
| HTTP 401 | Invalid API key - check your credentials |
| HTTP 500 | Backend API error - contact system administrator |
| Timeout | Request took longer than 30 seconds - try a simpler query |

## Troubleshooting

### Tool not found

Make sure you're in the repository root or use the full path:

```bash
# From repository root
./cudos-controlling rolx "query"

# Or use full path
/path/to/openclaw_toolbox/cudos-controlling rolx "query"
```

### API key not recognized

Check that your API key is set correctly:

```bash
# Check environment variable
echo $MBTOOLS_API_KEY

# Or check config file
cat ~/.mbtools/config.json
```

### UTF-8 encoding issues

The tool uses `ensure_ascii=False` for proper UTF-8 handling. If you see encoding issues, make sure your terminal supports UTF-8:

```bash
# Check locale
locale

# Set UTF-8 if needed
export LANG=en_US.UTF-8
```
