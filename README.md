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
openclaw_toolbox/
├── venv/                           # Shared virtual environment
├── CudosControllingTool/
│   ├── cudos_controlling.py        # CLI tool
│   └── README.md
├── SalesReminderTool/
│   ├── sales_reminder.py           # CLI tool
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
