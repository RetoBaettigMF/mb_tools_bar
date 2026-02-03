# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**openclaw_toolbox** (formerly mb_tools_bar) is a collection of MCP servers and CLI tools for Cudos/moltbot internal systems:
- **GoogleDocsMCPServer**: MCP server for editing Google Docs
- **CudosControllingMCPServer**: MCP server for querying RolX (timesheet) and Bexio (invoicing) via natural language
- **SalesReminderTool**: Automated email reminder for sales potential updates

## Repository Structure

```
openclaw_toolbox/
├── venv/                           # Shared virtual environment
├── GoogleDocsMCPServer/
│   ├── server.py                   # Main MCP server
│   ├── setup_auth.py              # OAuth setup script
│   └── README.md                   # Tool-specific docs
├── CudosControllingMCPServer/
│   ├── server.py                   # Main MCP server (converted from mbtools.py)
│   └── README.md                   # Tool-specific docs
├── SalesReminderTool/
│   ├── sales_reminder.py          # CLI tool
│   └── README.md                   # Tool-specific docs
├── google-docs-mcp                 # Symlink → GoogleDocsMCPServer/server.py
├── cudos-controlling-mcp           # Symlink → CudosControllingMCPServer/server.py
├── sales-reminder                  # Symlink → SalesReminderTool/sales_reminder.py
├── requirements.txt               # All dependencies
├── setup_venv.sh                  # Virtual environment setup
├── README.md                      # Main documentation
├── CLAUDE.md                      # This file
└── RolXChatAPI-spec.json         # API specification
```

## Architecture

### GoogleDocsMCPServer (GoogleDocsMCPServer/server.py)
- Implements MCP (Model Context Protocol) for Google Docs API integration
- Uses stdin/stdout for MCP communication (JSON-RPC style)
- Credentials stored at `~/.config/gogcli/tokens/bar.ai.bot@cudos.ch.json`
- Service account: `bar.ai.bot@cudos.ch`
- OAuth scope: `https://www.googleapis.com/auth/documents`
- Tools exposed:
  - `docs_read` - Read with pagination (default 100 lines)
  - `docs_append` - Append text to end
  - `docs_insert` - Insert at specific index
  - `docs_replace` - Replace all occurrences
  - `docs_insert_formatted` - Insert with Markdown-like formatting (# heading, **bold**, *italic*)
  - `docs_format_as_heading` - Convert existing text to heading (level 1-3)
  - `docs_format_as_normal` - Convert existing text to normal style
- Formatting system uses Google Docs API batch updates with paragraph and text style requests
- Dependencies: `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`

### CudosControllingMCPServer (CudosControllingMCPServer/server.py)
- MCP server for RolX and Bexio queries (converted from CLI to MCP protocol)
- Uses stdin/stdout for MCP communication (JSON-RPC style)
- Authentication via:
  - `.env` file in repository root (loaded via python-dotenv if available)
  - Environment variable `MBTOOLS_API_KEY`
  - Config file `~/.mbtools/config.json`
- API base URL: `https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io`
- Tools exposed:
  - `controlling_query_rolx` - Natural language timesheet queries
  - `controlling_query_bexio` - Natural language invoice queries
- API endpoints:
  - `/rolx/query` - RolX timesheet data
  - `/bexio/query` - Bexio invoice data
- Returns JSON responses with `ensure_ascii=False` for proper UTF-8 handling (German umlauts)
- Dependencies: Python stdlib only (urllib, json)

### SalesReminderTool (SalesReminderTool/sales_reminder.py)
- CLI tool for automated sales potential reminders
- Calculates "Wednesday before 4th Monday" using Python's calendar module
- Algorithm: Find 4th Monday, subtract 5 days to get prior Wednesday
- Uses `gog gmail send` CLI command to send email via bar account
- Designed for cron scheduling (exits silently when not the target date)
- Email signature: "Retos Bot Morticia 💪"
- Dependencies: Python stdlib only (calendar, datetime)

## MCP Server Pattern

All MCP servers follow the same architecture:

### Communication
- **stdin/stdout**: JSON-RPC style protocol
- **stderr**: Logging via `log()` function

### Standard Handlers
```python
def handle_request(request: dict) -> dict:
    method = request.get('method')
    params = request.get('params', {})

    if method == 'initialize':
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "...", "version": "1.0.0"}
        }

    elif method == 'tools/list':
        return {"tools": [...]}  # List of tool definitions

    elif method == 'tools/call':
        tool_name = params.get('name')
        args = params.get('arguments', {})
        result = execute_tool(tool_name, args)
        return {
            "content": [{"type": "text", "text": json.dumps(result, ...)}]
        }
```

### Main Loop
```python
def main():
    log("Server starting...")
    while True:
        try:
            line = input()
            request = json.loads(line)
            response = handle_request(request)
            if 'id' in request:
                response['id'] = request['id']
            send_response(response)
        except EOFError:
            break
```

## Common Commands

### Setup Virtual Environment
```bash
bash setup_venv.sh
source venv/bin/activate
```

### GoogleDocsMCPServer
```bash
# One-time OAuth setup
python3 GoogleDocsMCPServer/setup_auth.py
# Login with bar.ai.bot@cudos.ch when browser opens

# Register with mcporter (use symlink or full path)
mcporter config add google-docs --command "python3 $(pwd)/google-docs-mcp"

# Read document
mcporter call google-docs.docs_read documentId=XXX maxLines=50

# Replace text
mcporter call google-docs.docs_replace documentId=XXX oldText="..." newText="..."

# Insert formatted text
mcporter call google-docs.docs_insert_formatted documentId=XXX text="# Heading\n**bold** and *italic*" index=1
```

### CudosControllingMCPServer
```bash
# Setup API key (option 1: .env file - recommended)
cp .env.example .env
# Edit .env and set MBTOOLS_API_KEY=your-key

# Or option 2: export environment variable
export MBTOOLS_API_KEY="your-key"

# Or option 3: create ~/.mbtools/config.json with {"api_key": "..."}

# Register with mcporter
mcporter config add cudos-controlling --command "python3 $(pwd)/cudos-controlling-mcp"

# Query RolX timesheet
mcporter call cudos-controlling.controlling_query_rolx query="How many hours did Reto Bättig work in 2025 per task"

# Query Bexio invoicing
mcporter call cudos-controlling.controlling_query_bexio query="Give me invoice #0290.001.01.01"
```

### SalesReminderTool
```bash
# Manual test
python3 sales-reminder bu@cudos.ch

# Cron setup (runs every Wednesday at 09:00)
0 9 * * 3 cd /path/to/openclaw_toolbox && python3 sales-reminder bu@cudos.ch
```

## Dependencies

Consolidated in `requirements.txt`:

**Core (shared):**
- `requests>=2.31.0`
- `python-dotenv>=1.0.0` (for .env file support)

**GoogleDocsMCPServer:**
- `google-api-python-client>=2.0.0`
- `google-auth-httplib2>=0.1.0`
- `google-auth-oauthlib>=0.5.0`

**CudosControllingMCPServer:**
- Python stdlib only (urllib, json)

**SalesReminderTool:**
- Python stdlib only (calendar, datetime)

Install all:
```bash
pip install -r requirements.txt
```

## File Paths (Important for Tools)

All tools are in subdirectories:
- `GoogleDocsMCPServer/server.py` - Google Docs MCP server
- `GoogleDocsMCPServer/setup_auth.py` - OAuth setup
- `CudosControllingMCPServer/server.py` - Controlling MCP server
- `SalesReminderTool/sales_reminder.py` - Sales reminder CLI

Symlinks in root for convenience:
- `google-docs-mcp` → `GoogleDocsMCPServer/server.py`
- `cudos-controlling-mcp` → `CudosControllingMCPServer/server.py`
- `sales-reminder` → `SalesReminderTool/sales_reminder.py`

## Testing

No formal test suite exists. Manual testing approach:

**GoogleDocsMCPServer:**
- Use `mcporter call` to verify operations on test documents
- Test formatting with sample Markdown text
- Verify OAuth token refresh

**CudosControllingMCPServer:**
- Test against live API with known queries
- Verify error handling (missing API key, invalid query, etc.)
- Check UTF-8 handling with German umlauts

**SalesReminderTool:**
- Test with specific dates by temporarily modifying the date check
- Verify email sending via gog CLI
- Test cron integration

## Code Patterns

**Error handling**:
- MCP servers: Return `{"error": "..."}` in response
- CLI tools: Print to stderr and sys.exit(1)

**Logging**:
- MCP servers: Use stderr via `log()` function
- CLI tools: Use stdout/stderr directly

**Configuration**:
- Prefer environment variables over config files where possible
- Fallback to config files in `~/.config/` or `~/.<tool>/`

**JSON output**:
- Always use `ensure_ascii=False` for proper UTF-8 handling (German umlauts, special characters)
- Use `indent=2` for readable output

**OAuth tokens**:
- Shared with `gog` CLI tool via `~/.config/gogcli/tokens/`
- Service account: `bar.ai.bot@cudos.ch`

## Adding New Tools

1. Create directory: `NewToolMCPServer/` or `NewToolCLI/`
2. Add main script: `server.py` (MCP) or tool-specific name (CLI)
3. Create tool-specific `README.md`
4. Add dependencies to `requirements.txt` if needed
5. Create symlink in root: `ln -s NewToolMCPServer/server.py new-tool-mcp`
6. Update main `README.md`
7. Update this `CLAUDE.md`

For MCP servers, follow the established pattern:
- Use `handle_request()` with initialize/tools/list/tools/call
- Use `log()` for stderr logging
- Use `send_response()` for JSON output
- Include request ID in response if present

## Legacy Files (Removed)

The following files were removed during restructuring:
- `mbtools.py` - Converted to `CudosControllingMCPServer/server.py`
- `mcp_server_google_docs.py` - Moved to `GoogleDocsMCPServer/server.py`
- `setup_docs_auth.py` - Moved to `GoogleDocsMCPServer/setup_auth.py`
- `crm_browser.py` - Deprecated Selenium-based CRM tool
- `simple_crm_search.py` - Deprecated Selenium-based CRM tool
