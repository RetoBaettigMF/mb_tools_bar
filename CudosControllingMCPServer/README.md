# CudosControllingMCPServer

MCP server for querying Cudos internal controlling systems (RolX timesheet and Bexio invoicing) via natural language.

## Features

- `controlling_query_rolx` - Query RolX timesheet data
- `controlling_query_bexio` - Query Bexio invoicing data

Both tools accept natural language queries and return structured JSON responses from the Cudos Controlling API.

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

### 2. Register with mcporter

Add the server to mcporter configuration:

```bash
mcporter config add cudos-controlling --command "python3 /path/to/openclaw_toolbox/cudos-controlling-mcp"
```

Or use the full path to the server:

```bash
mcporter config add cudos-controlling --command "python3 /path/to/CudosControllingMCPServer/server.py"
```

## Usage Examples

### Query RolX Timesheet

```bash
# Hours worked by person
mcporter call cudos-controlling.controlling_query_rolx \
    query="How many hours did Reto Bättig work in 2025 per task"

# Hours for specific project
mcporter call cudos-controlling.controlling_query_rolx \
    query="Show all hours for project 0123.110"

# Time period analysis
mcporter call cudos-controlling.controlling_query_rolx \
    query="What are the total hours logged in Q1 2025"
```

### Query Bexio Invoicing

```bash
# Get specific invoice
mcporter call cudos-controlling.controlling_query_bexio \
    query="Give me invoice #0290.001.01.01"

# Find invoices by project
mcporter call cudos-controlling.controlling_query_bexio \
    query="Show all invoices with Project Number 290"

# Invoice statistics
mcporter call cudos-controlling.controlling_query_bexio \
    query="What is the total invoiced amount for 2025"
```

## API Details

- **Base URL**: `https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io`
- **Endpoints**:
  - `/rolx/query` - RolX timesheet queries
  - `/bexio/query` - Bexio invoice queries
- **Authentication**: Bearer token via `Authorization` header

## Dependencies

- Python 3 standard library only (urllib, json)
- No external dependencies required

## Error Handling

The server returns structured error messages in JSON format:

```json
{
  "error": "Description of error",
  "details": "Additional error information"
}
```

Common errors:
- Missing API key: Set `MBTOOLS_API_KEY` or create config file
- HTTP 401: Invalid API key
- HTTP 500: Backend API error
- Timeout: Request took longer than 30 seconds
