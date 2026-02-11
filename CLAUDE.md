# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**openclaw_toolbox** (formerly mb_tools_bar) is a collection of CLI tools for Cudos/moltbot internal systems:
- **Cudos Controlling CLI**: Command-line tool for querying RolX (timesheet) and Bexio (invoicing) via natural language
- **SalesReminderTool**: Automated email reminder for sales potential updates

## Repository Structure

```
openclaw_toolbox/
├── venv/                           # Shared virtual environment
├── CudosControllingTool/
│   ├── cudos_controlling.py        # CLI tool
│   └── README.md                   # Tool-specific docs
├── SalesReminderTool/
│   ├── sales_reminder.py          # CLI tool
│   └── README.md                   # Tool-specific docs
├── cudos-controlling               # Symlink → CudosControllingTool/cudos_controlling.py
├── sales-reminder                  # Symlink → SalesReminderTool/sales_reminder.py
├── requirements.txt               # All dependencies
├── setup_venv.sh                  # Virtual environment setup
├── README.md                      # Main documentation
├── CLAUDE.md                      # This file
└── RolXChatAPI-spec.json         # API specification
```

## Architecture

### Cudos Controlling CLI (CudosControllingTool/cudos_controlling.py)
- Command-line tool for RolX and Bexio queries via natural language
- Uses argparse for CLI interface with subcommands
- Authentication via:
  - `.env` file in repository root (loaded via python-dotenv if available)
  - Environment variable `MBTOOLS_API_KEY`
  - Config file `~/.mbtools/config.json`
- API base URL: `https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io`
- Subcommands:
  - `rolx` - Natural language timesheet queries
  - `bexio` - Natural language invoice queries
- API endpoints:
  - `/rolx/query` - RolX timesheet data
  - `/bexio/query` - Bexio invoice data
- Output modes:
  - Default: Pretty-printed JSON with UTF-8 support (German umlauts)
  - `--json` flag: Raw JSON for scripting
- Exit codes: 0 for success, 1 for errors
- Dependencies: Python stdlib only (argparse, urllib, json)

### SalesReminderTool (SalesReminderTool/sales_reminder.py)
- CLI tool for automated sales potential reminders
- Calculates "Wednesday before 4th Monday" using Python's calendar module
- Algorithm: Find 4th Monday, subtract 5 days to get prior Wednesday
- Uses `gog gmail send` CLI command to send email via bar account
- Designed for cron scheduling (exits silently when not the target date)
- Email signature: "Retos Bot Morticia 💪"
- Dependencies: Python stdlib only (calendar, datetime)

## CLI Tool Pattern

All CLI tools follow a consistent architecture:

### Command Structure
- **Subcommands**: Use argparse with subparsers for different operations
- **Flags**: Common flags like `--json` for machine-readable output
- **Exit codes**: 0 for success, 1 for errors

### Standard Implementation
```python
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(
        prog='tool-name',
        description='Tool description',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Usage examples here'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Add subcommands
    parser_cmd1 = subparsers.add_parser('cmd1', help='Command 1 help')
    parser_cmd1.add_argument('query', help='Query argument')
    parser_cmd1.add_argument('--json', action='store_true', help='Output JSON')

    args = parser.parse_args()

    # Execute command
    result = execute_command(args.command, args.query)

    # Format and output
    output = format_output(result, as_json=args.json)
    print(output)

    # Exit with appropriate code
    sys.exit(1 if "error" in result else 0)

if __name__ == '__main__':
    main()
```

### Output Formatting
```python
def format_output(result: dict, as_json: bool = False) -> str:
    """Format API result for display."""
    if as_json:
        return json.dumps(result, indent=2, ensure_ascii=False)

    # Pretty-print by default
    if "error" in result:
        return f"Error: {result['error']}"

    return json.dumps(result, indent=2, ensure_ascii=False)
```

## Common Commands

### Setup Virtual Environment
```bash
bash setup_venv.sh
source venv/bin/activate
```

### Cudos Controlling CLI
```bash
# Setup API key (option 1: .env file - recommended)
cp .env.example .env
# Edit .env and set MBTOOLS_API_KEY=your-key

# Or option 2: export environment variable
export MBTOOLS_API_KEY="your-key"

# Or option 3: create ~/.mbtools/config.json with {"api_key": "..."}

# Query RolX timesheet
./cudos-controlling rolx "How many hours did Reto Bättig work in 2025 per task"
./cudos-controlling rolx "Wie viele Stunden hat Reto gearbeitet?" --json

# Query Bexio invoicing
./cudos-controlling bexio "Give me invoice #0290.001.01.01"
./cudos-controlling bexio "Show all invoices with Project Number 290" --json

# Help
./cudos-controlling --help
./cudos-controlling rolx --help
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

**Cudos Controlling CLI:**
- Python stdlib only (argparse, urllib, json)
- Optional: python-dotenv (for .env file support)

**SalesReminderTool:**
- Python stdlib only (calendar, datetime)

Install all:
```bash
pip install -r requirements.txt
```

## File Paths (Important for Tools)

All tools are in subdirectories:
- `CudosControllingTool/cudos_controlling.py` - Controlling CLI tool
- `SalesReminderTool/sales_reminder.py` - Sales reminder CLI

Symlinks in root for convenience:
- `cudos-controlling` → `CudosControllingTool/cudos_controlling.py`
- `sales-reminder` → `SalesReminderTool/sales_reminder.py`

## Testing

No formal test suite exists. Manual testing approach:

**Cudos Controlling CLI:**
- Test against live API with known queries
- Verify error handling (missing API key, invalid query, etc.)
- Check UTF-8 handling with German umlauts
- Test subcommands and flags (--json, --help)
- Verify exit codes (0 for success, 1 for errors)

**SalesReminderTool:**
- Test with specific dates by temporarily modifying the date check
- Verify email sending via gog CLI
- Test cron integration

## Code Patterns

**Error handling**:
- CLI tools: Return error dict with `{"error": "..."}` key
- Print error messages to stderr when appropriate
- Exit with code 1 on errors, 0 on success

**Output**:
- CLI tools: Print to stdout (data) and stderr (errors/logging)
- Support both formatted (default) and JSON (--json flag) output
- Use `ensure_ascii=False` for UTF-8 support

**Configuration**:
- Prefer environment variables over config files where possible
- Fallback to config files in `~/.config/` or `~/.<tool>/`

**JSON output**:
- Always use `ensure_ascii=False` for proper UTF-8 handling (German umlauts, special characters)
- Use `indent=2` for readable output

## Adding New Tools

1. Create directory: `NewToolCLI/`
2. Add main script with CLI implementation using argparse
3. Create tool-specific `README.md`
4. Add dependencies to `requirements.txt` if needed
5. Create symlink in root: `ln -s NewToolCLI/tool_name.py new-tool`
6. Update main `README.md`
7. Update this `CLAUDE.md`

For CLI tools, follow the established pattern:
- Use `argparse` with subparsers for subcommands
- Implement `--json` flag for machine-readable output
- Use `ensure_ascii=False` for UTF-8 support
- Exit with code 0 for success, 1 for errors
- Print data to stdout, errors to stderr

## Legacy Files (Removed)

The following files were removed during restructuring:
- `mbtools.py` - Original CLI tool, converted to MCP server, then to CLI again
- `CudosControllingTool/server.py` - MCP server version (removed, replaced by cudos_controlling.py CLI)
- `mcp_server_google_docs.py` - Removed (Google Docs MCP Server)
- `setup_docs_auth.py` - Removed (Google Docs MCP Server)
- `GoogleDocsMCPServer/` - Removed completely
- `CRMMCPServer/` - Removed completely
- `crm_browser.py` - Deprecated Selenium-based CRM tool
- `simple_crm_search.py` - Deprecated Selenium-based CRM tool
