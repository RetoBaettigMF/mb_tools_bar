# OpenClaw.ai Toolbox

Collection of MCP servers and CLI tools for Cudos internal systems, designed for use with OpenClaw.ai.

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

### 🔧 MCP Servers

#### [GoogleDocsMCPServer](./GoogleDocsMCPServer/README.md)

Edit Google Docs via MCP protocol.

**Tools:**
- `docs_read` - Read with pagination
- `docs_append` - Append text
- `docs_insert` - Insert at position
- `docs_replace` - Replace text
- `docs_insert_formatted` - Insert with Markdown-like formatting
- `docs_format_as_heading` - Convert text to heading
- `docs_format_as_normal` - Convert text to normal style

**Setup:**
```bash
# One-time OAuth
python3 GoogleDocsMCPServer/setup_auth.py

# Register with mcporter
mcporter config add google-docs --command "python3 $(pwd)/google-docs-mcp"
```

**Usage:**
```bash
mcporter call google-docs.docs_read documentId=<doc-id> maxLines=50
```

---

#### [CudosControllingMCPServer](./CudosControllingMCPServer/README.md)

Query RolX (timesheet) and Bexio (invoicing) via natural language.

**Tools:**
- `controlling_query_rolx` - Query timesheet data
- `controlling_query_bexio` - Query invoice data

**Setup:**
```bash
# Set API key (either in .env file or export)
echo 'MBTOOLS_API_KEY=your-key' >> .env
# Or: export MBTOOLS_API_KEY="your-key"

# Register with mcporter
mcporter config add cudos-controlling --command "python3 $(pwd)/cudos-controlling-mcp"
```

**Usage:**
```bash
mcporter call cudos-controlling.controlling_query_rolx \
    query="How many hours did Reto Bättig work in 2025 per task"

mcporter call cudos-controlling.controlling_query_bexio \
    query="Give me invoice #0290.001.01.01"
```

---

#### [CRMMCPServer](./CRMMCPServer/README.md)

Automate interactions with the web-based CRM system.

**Tools (11 total):**
- Search: `search_account`, `search_person`, `search_potential`, `get_comments`
- Create: `create_account`, `create_person`, `create_potential` (with duplicate checking)
- Update: `update_account`, `update_person`, `update_potential`
- Interact: `add_comment_to_account`

**Features:**
- Fuzzy search with 5 retry strategies
- Persistent browser session
- Duplicate checking for accounts and contacts

**Setup:**
```bash
# Install Playwright
pip install -r requirements.txt
playwright install chromium

# Configure credentials
python3 CRMMCPServer/setup_auth.py

# Register with mcporter
mcporter config add crm --command "python3 $(pwd)/crm-mcp"
```

**Usage:**
```bash
# Search for company
mcporter call crm.search_account name="Cudos" ort="Zürich"

# Create company
mcporter call crm.create_account data='{"accountname": "New Company", "bill_city": "Zürich"}'

# Update company
mcporter call crm.update_account account_id="12345" updates='{"phone": "+41 44 123 45 67"}'
```

---

### 🛠️ CLI Tools

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
├── GoogleDocsMCPServer/
│   ├── server.py                   # MCP server
│   ├── setup_auth.py               # OAuth setup
│   └── README.md
├── CudosControllingMCPServer/
│   ├── server.py                   # MCP server
│   └── README.md
├── CRMMCPServer/
│   ├── server.py                   # MCP server
│   ├── setup_auth.py               # Credential setup
│   └── README.md
├── SalesReminderTool/
│   ├── sales_reminder.py           # CLI tool
│   └── README.md
├── google-docs-mcp                 # Symlink → GoogleDocsMCPServer/server.py
├── cudos-controlling-mcp           # Symlink → CudosControllingMCPServer/server.py
├── crm-mcp                         # Symlink → CRMMCPServer/server.py
├── sales-reminder                  # Symlink → SalesReminderTool/sales_reminder.py
├── requirements.txt                # All dependencies
├── setup_venv.sh                   # Virtual environment setup
├── README.md                       # This file
└── CLAUDE.md                       # Development guidelines
```

## MCP Server Pattern

All MCP servers follow the same architecture:

1. **stdin/stdout communication** - JSON-RPC style protocol
2. **Standard handlers**:
   - `initialize` - Return protocol version and capabilities
   - `tools/list` - Return available tools
   - `tools/call` - Execute tool calls
3. **stderr logging** - Use `log()` function for debugging
4. **Consistent error handling** - Return structured error messages

## Dependencies

### Core (shared)
- `requests>=2.31.0`

### Google Docs MCP Server
- `google-api-python-client>=2.0.0`
- `google-auth-httplib2>=0.1.0`
- `google-auth-oauthlib>=0.5.0`

### Cudos Controlling MCP Server
- Python stdlib only (urllib, json)

### Sales Reminder Tool
- Python stdlib only (calendar, datetime)

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Development

### Adding a New Tool

1. Create directory: `NewToolMCPServer/` or `NewToolCLI/`
2. Add `server.py` (MCP) or main script (CLI)
3. Create tool-specific `README.md`
4. Add dependencies to `requirements.txt`
5. Create symlink in root: `ln -s NewToolMCPServer/server.py new-tool-mcp`
6. Update this README

### Testing MCP Servers

Use `mcporter` for testing:

```bash
# List tools
mcporter call <server-name>.tools/list

# Call a tool
mcporter call <server-name>.<tool-name> param1=value1 param2=value2
```

## API Specifications

- [RolX Chat API Spec](./RolXChatAPI-spec.json) - OpenAPI spec for Controlling API

## License

[MIT Open Source License](https://opensource.org/license/mit)
