# GoogleDocsMCPServer

MCP server for editing Google Docs via the Google Docs API.

## Features

- `docs_read` - Read document content with pagination
- `docs_append` - Append text to end of document
- `docs_insert` - Insert text at specific index
- `docs_replace` - Replace all occurrences of text
- `docs_insert_formatted` - Insert Markdown-like formatted text (# heading, **bold**, *italic*)
- `docs_format_as_heading` - Convert existing text to heading (level 1-3)
- `docs_format_as_normal` - Convert existing text to normal style

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
mcporter config add google-docs --command "python3 /path/to/openclaw_toolbox/google-docs-mcp"
```

Or use the full path to the server:

```bash
mcporter config add google-docs --command "python3 /path/to/GoogleDocsMCPServer/server.py"
```

## Usage Examples

### Read a document

```bash
mcporter call google-docs.docs_read documentId=1ABC123XYZ maxLines=50
```

### Append text

```bash
mcporter call google-docs.docs_append documentId=1ABC123XYZ text="New paragraph at the end"
```

### Replace text

```bash
mcporter call google-docs.docs_replace \
    documentId=1ABC123XYZ \
    oldText="old value" \
    newText="new value"
```

### Insert formatted text

```bash
mcporter call google-docs.docs_insert_formatted \
    documentId=1ABC123XYZ \
    text="# Section Title\n\nThis is **bold** and this is *italic*." \
    index=1
```

### Format existing text as heading

```bash
mcporter call google-docs.docs_format_as_heading \
    documentId=1ABC123XYZ \
    text="Executive Summary" \
    level=1
```

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
