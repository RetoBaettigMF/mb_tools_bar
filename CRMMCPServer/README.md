# CRM MCP Server

MCP (Model Context Protocol) server for automating interactions with the web-based CRM system at https://mf250.co.crm-now.de/. Provides tools for searching, creating, updating, and commenting on CRM records.

## Features

- **11 MCP Tools** for comprehensive CRM automation
- **Fuzzy Search** with 5 retry strategies (special chars, shortening, umlaut replacement)
- **Duplicate Checking** for accounts and contacts
- **Persistent Browser Session** to avoid repeated logins
- **Clean Architecture** with layered design (domain, infrastructure, application, MCP)
- **Page Object Model** for maintainable browser automation

## Architecture

```
CRMMCPServer/
├── server.py                      # Main MCP entry point
├── setup_auth.py                  # Credential setup script
├── infrastructure/                # External systems
│   ├── auth_manager.py           # Credential management
│   └── browser_client.py         # Playwright wrapper
├── domain/                        # Business logic
│   ├── models.py                 # Data classes
│   ├── page_objects.py           # Page Object Model
│   └── fuzzy_search.py           # Search retry logic
├── application/                   # Use cases
│   ├── search_service.py         # Search operations
│   ├── create_service.py         # Create with duplicate checking
│   ├── update_service.py         # Update operations
│   └── comment_service.py        # Comment operations
└── mcp/                           # MCP protocol
    ├── protocol.py               # Communication helpers
    └── tool_definitions.py       # Tool schemas
```

## Tools

### Search & Read (4 tools)

**search_account** - Search for companies
```bash
mcporter call crm.search_account name="Cudos" ort="Zürich"
```

**search_person** - Search for contacts
```bash
mcporter call crm.search_person nachname="Bättig" vorname="Reto"
```

**search_potential** - Search for sales potentials
```bash
mcporter call crm.search_potential status="gewonnen" firma="Cudos"
```

**get_comments** - Get comments from an account
```bash
mcporter call crm.get_comments account_id="12345" limit=5
```

### Create with Duplicate Checking (3 tools)

**create_account** - Create a company (checks for duplicates)
```bash
mcporter call crm.create_account data='{"accountname": "Test Company", "bill_city": "Zürich"}'
```

**create_person** - Create a contact (checks for duplicates)
```bash
mcporter call crm.create_person firma_id="12345" data='{"firstname": "Jane", "lastname": "Doe", "email": "jane@example.com"}'
```

**create_potential** - Create a sales potential
```bash
mcporter call crm.create_potential firma_id="12345" data='{"potentialname": "New Deal", "amount": "50000"}'
```

### Update (3 tools)

**update_account** - Update company fields
```bash
mcporter call crm.update_account account_id="12345" updates='{"bill_city": "Bern", "phone": "+41 44 123 45 67"}'
```

**update_person** - Update contact fields
```bash
mcporter call crm.update_person person_id="67890" updates='{"email": "new@example.com"}'
```

**update_potential** - Update potential fields
```bash
mcporter call crm.update_potential potential_id="11111" updates='{"sales_stage": "Negotiation"}'
```

### Interaction (1 tool)

**add_comment_to_account** - Add a comment to an account
```bash
mcporter call crm.add_comment_to_account account_id="12345" autor="Test User" text="Follow-up meeting scheduled"
```

## Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Credentials

Run the interactive setup script:

```bash
python3 CRMMCPServer/setup_auth.py
```

This will:
- Prompt for your CRM username and password
- Test login with Playwright
- Save credentials to `~/.config/crm-mcp/credentials.json`
- Save browser session to `./.auth/state.json`

**Alternative credential methods:**

**Option 1: Environment variables**
```bash
export CRM_USERNAME="your-username"
export CRM_PASSWORD="your-password"
```

**Option 2: .env file**
Create `.env` in repository root:
```
CRM_USERNAME=your-username
CRM_PASSWORD=your-password
```

### 3. Register with mcporter

```bash
mcporter config add crm --command "python3 $(pwd)/crm-mcp"
```

Or use the symlink:
```bash
mcporter config add crm --command "$(pwd)/crm-mcp"
```

## Usage Examples

### Search Examples

```bash
# Search for a company
mcporter call crm.search_account name="Cudos"

# Fuzzy search (finds "Müller" even with partial match)
mcporter call crm.search_account name="Mül"

# Search with city filter
mcporter call crm.search_account name="Cudos" ort="Zürich"

# Search for a person
mcporter call crm.search_person nachname="Bättig" vorname="Reto"

# Search by company affiliation
mcporter call crm.search_person firma="Cudos"

# Search potentials by status
mcporter call crm.search_potential status="gewonnen"
```

### Create Examples

```bash
# Create a new company
mcporter call crm.create_account data='{
  "accountname": "New Company AG",
  "bill_city": "Zürich",
  "bill_street": "Bahnhofstrasse 1",
  "bill_code": "8001",
  "phone": "+41 44 123 45 67",
  "website": "https://example.com"
}'

# Create a contact linked to company
mcporter call crm.create_person firma_id="12345" data='{
  "firstname": "Jane",
  "lastname": "Doe",
  "email": "jane.doe@example.com",
  "phone": "+41 44 123 45 68",
  "title": "CEO"
}'

# Attempt duplicate (will fail with error)
mcporter call crm.create_account data='{"accountname": "New Company AG"}'
```

### Update Examples

```bash
# Update company information
mcporter call crm.update_account account_id="12345" updates='{
  "bill_city": "Bern",
  "phone": "+41 31 123 45 67"
}'

# Update contact email
mcporter call crm.update_person person_id="67890" updates='{
  "email": "jane.new@example.com",
  "mobile": "+41 79 123 45 67"
}'
```

### Comment Examples

```bash
# Get latest comments
mcporter call crm.get_comments account_id="12345" limit=10

# Add a comment
mcporter call crm.add_comment_to_account \
  account_id="12345" \
  autor="Reto Bättig" \
  text="Follow-up meeting scheduled for next week"
```

## Fuzzy Search

The server implements intelligent fuzzy search with 5 retry strategies:

1. **Original term** - Search as-is
2. **Remove special chars** - Strip *, ?, etc.
3. **Shorten incrementally** - "Müller" → "Mülle" → "Müll"
4. **Replace umlauts** - ä→ae, ö→oe, ü→ue, ß→ss
5. **Shorten umlaut-replaced** - Combine strategies 3 & 4

Maximum 5 attempts per search. First successful match is returned.

## Response Format

All tools return consistent JSON:

**Success:**
```json
{
  "success": true,
  "data": {
    "results": [...],
    "count": 5
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message",
  "error_type": "duplicate|timeout|not_found|validation",
  "details": {}
}
```

## Troubleshooting

### Session Expired

If you see authentication errors:
```bash
# Delete saved session
rm .auth/state.json

# Re-run setup
python3 CRMMCPServer/setup_auth.py
```

### Selector Not Found

The CRM HTML structure may change. Update selectors in:
```
CRMMCPServer/domain/page_objects.py
```

Look for the `SELECTORS` dictionaries in each page class.

### Timeout Errors

Increase timeouts in `browser_client.py`:
```python
DEFAULT_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 60000  # 60 seconds
```

### Duplicate Check False Positive

Fuzzy search may be too aggressive. Adjust retry strategies in:
```
CRMMCPServer/domain/fuzzy_search.py
```

## Technical Details

### Persistent Browser Context

- Session saved to `./.auth/state.json`
- Chromium browser in headless mode
- Automatic session refresh on expiry
- Network idle detection for page loads

### Page Object Model

Three main page objects:
- **AccountPage** - Companies module
- **ContactPage** - Contacts module
- **PotentialPage** - Potentials module
- **CommentManager** - Comments (shared across modules)

Each page object handles:
- Module-specific selectors
- Search, create, update methods
- Record ID extraction from URLs

### Clean Architecture

- **Infrastructure Layer** - Browser automation, authentication
- **Domain Layer** - Business logic, page objects, fuzzy search
- **Application Layer** - Service orchestration
- **MCP Layer** - Protocol communication

## Dependencies

- **playwright>=1.41.0** - Browser automation
- **python-dotenv>=1.0.0** - Environment configuration

## Development

### Running in Non-Headless Mode

For debugging, edit `server.py`:
```python
self.browser_client = BrowserClient(
    username=credentials['username'],
    password=credentials['password'],
    headless=False  # Change to False
)
```

### Logging

All logs go to stderr via `log()` function. View with:
```bash
mcporter call crm.search_account name="Test" 2>&1 | grep "Search"
```

### Testing Selectors

Use browser dev tools to inspect CRM HTML:
1. Open https://mf250.co.crm-now.de/ in browser
2. Navigate to list/edit views
3. Inspect elements with dev tools (F12)
4. Update selectors in `page_objects.py`

## License

Part of openclaw_toolbox (formerly mb_tools_bar).
