# GoogleDocsMCPServer

MCP server for editing Google Docs via the Google Docs API.

**Version 2.0** - Refactored with clean architecture and enhanced Markdown support.

## Features

The server provides 7 tools organized into two categories:

### Unformatted Text Tools (3)

- **`text_read`** - Read plain text with pagination
- **`text_write`** - Write/insert plain text (unified append/insert)
- **`text_replace`** - Replace all occurrences of plain text

### Formatted Markdown Tools (4)

- **`markdown_read`** - Read document with formatting converted to Markdown (enables round-trip editing)
- **`markdown_write`** - Write/insert with Markdown formatting
- **`markdown_replace`** - Replace text and apply Markdown formatting
- **`markdown_format`** - Apply formatting to existing text

## Markdown Support

Supported Markdown syntax:

- **Headings:** `# H1`, `## H2`, `### H3`
- **Bold:** `**text**`
- **Italic:** `*text*`
- **Unordered lists:** `- item`
- **Ordered lists:** `1. item`
- **Code blocks:** ` ```code``` `

## Setup

### 1. OAuth Authentication

First-time setup requires OAuth authentication with the bar.ai.bot@cudos.ch service account:

```bash
python3 setup_auth.py
```

This will:
- Open a browser for OAuth consent
- Save credentials to `~/.config/gogcli/tokens/bar.ai.bot@cudos.ch.json`
- Grant access to Google Docs API (`https://www.googleapis.com/auth/documents`)

### 2. Register with mcporter

Add the server to mcporter configuration:

```bash
mcporter config add google-docs --command "python3 $(pwd)/google-docs-mcp"
```

Or use the full path:

```bash
mcporter config add google-docs --command "python3 /path/to/GoogleDocsMCPServer/server.py"
```

## Usage Examples

### Unformatted Text Operations

**Read plain text:**
```bash
mcporter call google-docs.text_read documentId=1ABC123XYZ maxLines=50 startLine=1
```

**Write text to end:**
```bash
mcporter call google-docs.text_write \
    documentId=1ABC123XYZ \
    text="New paragraph at the end" \
    position=end
```

**Write text to start:**
```bash
mcporter call google-docs.text_write \
    documentId=1ABC123XYZ \
    text="First paragraph" \
    position=start
```

**Replace text:**
```bash
mcporter call google-docs.text_replace \
    documentId=1ABC123XYZ \
    oldText="old value" \
    newText="new value"
```

### Markdown Operations

**Read as Markdown (enables round-trip editing):**
```bash
# Read document with formatting converted to Markdown
mcporter call google-docs.markdown_read documentId=1ABC123XYZ maxLines=100

# Output will show: # Heading 1, **bold**, *italic*, - lists, etc.
```

**Write Markdown:**
```bash
mcporter call google-docs.markdown_write \
    documentId=1ABC123XYZ \
    markdown="# Section Title\n\nThis is **bold** and *italic*.\n\nFeatures:\n- Item 1\n- Item 2" \
    position=end
```

**Write Markdown with code and lists:**
```bash
mcporter call google-docs.markdown_write \
    documentId=1ABC123XYZ \
    markdown="## Code Example\n\nRun this: ```npm install```\n\nSteps:\n1. First step\n2. Second step" \
    position=end
```

**Replace with Markdown:**
```bash
mcporter call google-docs.markdown_replace \
    documentId=1ABC123XYZ \
    oldText="Section Title" \
    newMarkdown="# Executive Summary"
```

**Format existing text:**
```bash
# Convert to heading
mcporter call google-docs.markdown_format \
    documentId=1ABC123XYZ \
    text="Executive Summary" \
    style=heading1

# Convert to normal text
mcporter call google-docs.markdown_format \
    documentId=1ABC123XYZ \
    text="Some Heading" \
    style=normal
```

### Round-Trip Editing Workflow

```bash
# 1. Read document as Markdown
content=$(mcporter call google-docs.markdown_read documentId=1ABC123XYZ)

# 2. Modify the Markdown locally (using sed, awk, or text editor)
modified_content=$(echo "$content" | sed 's/Old Title/New Title/')

# 3. Write it back with formatting preserved
mcporter call google-docs.markdown_write \
    documentId=1ABC123XYZ \
    markdown="$modified_content" \
    position=end
```

## Architecture

The server is organized into clean layers:

```
GoogleDocsMCPServer/
├── server.py                    # Entry point (routing)
├── domain/                      # Business logic
│   ├── models.py               # Data classes
│   ├── markdown_parser.py      # Markdown ↔ Google Docs conversion
│   └── text_operations.py      # Text manipulation
├── infrastructure/              # External systems
│   ├── auth_manager.py         # OAuth credentials
│   └── google_docs_client.py   # Google Docs API wrapper
├── application/                 # Use cases
│   ├── unformatted_service.py  # Plain text operations
│   └── formatted_service.py    # Markdown operations
└── mcp/                        # MCP protocol
    ├── protocol.py             # Communication helpers
    └── tool_definitions.py     # Tool schemas
```

## Migration from v1.0

**Breaking Changes:**

Old tool names have been replaced:

| Old Tool | New Tool | Notes |
|----------|----------|-------|
| `docs_read` | `text_read` | Same functionality |
| `docs_append` | `text_write` (position=end) | Unified operation |
| `docs_insert` | `text_write` (position=start or index=N) | Unified operation |
| `docs_replace` | `text_replace` | Same functionality |
| `docs_insert_formatted` | `markdown_write` | Enhanced with lists/code |
| `docs_format_as_heading` | `markdown_format` (style=heading1/2/3) | Generalized |
| `docs_format_as_normal` | `markdown_format` (style=normal) | Generalized |

**New feature:** `markdown_read` enables round-trip editing by reading documents with formatting converted to Markdown.

## Credentials

- Service account: `bar.ai.bot@cudos.ch`
- Token location: `~/.config/gogcli/tokens/bar.ai.bot@cudos.ch.json`
- OAuth scope: `https://www.googleapis.com/auth/documents`

## Dependencies

- `google-api-python-client>=2.0.0`
- `google-auth-httplib2>=0.1.0`
- `google-auth-oauthlib>=0.5.0`

Install via:

```bash
pip install -r ../requirements.txt
```
