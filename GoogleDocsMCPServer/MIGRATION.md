# Migration Guide: GoogleDocsMCPServer v1.0 → v2.0

## Overview

GoogleDocsMCPServer v2.0 is a complete refactoring with:
- **Clean architecture** (domain, infrastructure, application, MCP layers)
- **7 new tools** (was 7 old tools, but reorganized)
- **Enhanced Markdown support** (lists, code blocks)
- **Round-trip editing** via `markdown_read`
- **Breaking changes** (tool names changed)

## What Changed

### Tool Naming

All tool names have been changed for clarity:

| Old Tool (v1.0) | New Tool (v2.0) | Notes |
|-----------------|-----------------|-------|
| `docs_read` | `text_read` | Same functionality |
| `docs_append` | `text_write` (position=end) | Unified with insert |
| `docs_insert` | `text_write` (position=start/index=N) | Unified with append |
| `docs_replace` | `text_replace` | Same functionality |
| `docs_insert_formatted` | `markdown_write` | Enhanced: now supports lists, code |
| `docs_format_as_heading` | `markdown_format` (style=heading1/2/3) | Generalized |
| `docs_format_as_normal` | `markdown_format` (style=normal) | Generalized |

### New Features

1. **`markdown_read`** - NEW tool for reading documents with formatting as Markdown
   - Enables round-trip editing workflows
   - Example: read → modify → write back

2. **Enhanced Markdown** - Now supports:
   - Unordered lists: `- item`
   - Ordered lists: `1. item`
   - Code blocks: ` ```code``` `

3. **Unified write operation** - `text_write` replaces both `docs_append` and `docs_insert`
   - Use `position=end` for append
   - Use `position=start` for prepend
   - Use `index=N` for custom position

## Migration Examples

### Reading Documents

**Old (v1.0):**
```bash
mcporter call google-docs.docs_read documentId=XXX maxLines=50
```

**New (v2.0):**
```bash
# Plain text
mcporter call google-docs.text_read documentId=XXX maxLines=50

# With formatting as Markdown (NEW!)
mcporter call google-docs.markdown_read documentId=XXX maxLines=50
```

### Appending Text

**Old (v1.0):**
```bash
mcporter call google-docs.docs_append documentId=XXX text="New text"
```

**New (v2.0):**
```bash
mcporter call google-docs.text_write documentId=XXX text="New text" position=end
```

### Inserting Text

**Old (v1.0):**
```bash
mcporter call google-docs.docs_insert documentId=XXX text="Text" index=1
```

**New (v2.0):**
```bash
# At start
mcporter call google-docs.text_write documentId=XXX text="Text" position=start

# At custom index
mcporter call google-docs.text_write documentId=XXX text="Text" index=1
```

### Replacing Text

**Old (v1.0):**
```bash
mcporter call google-docs.docs_replace documentId=XXX oldText="old" newText="new"
```

**New (v2.0):**
```bash
mcporter call google-docs.text_replace documentId=XXX oldText="old" newText="new"
```

### Inserting Formatted Text

**Old (v1.0):**
```bash
mcporter call google-docs.docs_insert_formatted \
    documentId=XXX \
    text="# Heading\n**bold** and *italic*" \
    index=1
```

**New (v2.0):**
```bash
# With enhanced Markdown support (lists, code)
mcporter call google-docs.markdown_write \
    documentId=XXX \
    markdown="# Heading\n\n**bold** and *italic*\n\nFeatures:\n- Item 1\n- Item 2\n\nCode: ```npm install```" \
    position=end
```

### Formatting Existing Text

**Old (v1.0):**
```bash
# Convert to heading
mcporter call google-docs.docs_format_as_heading \
    documentId=XXX text="Title" level=1

# Convert to normal
mcporter call google-docs.docs_format_as_normal \
    documentId=XXX text="Title"
```

**New (v2.0):**
```bash
# Convert to heading (unified operation)
mcporter call google-docs.markdown_format \
    documentId=XXX text="Title" style=heading1

# Convert to normal
mcporter call google-docs.markdown_format \
    documentId=XXX text="Title" style=normal
```

## New Workflows

### Round-Trip Editing

This workflow is now possible with `markdown_read`:

```bash
# 1. Read document as Markdown
content=$(mcporter call google-docs.markdown_read documentId=XXX)

# 2. Modify the Markdown (use any text processing tool)
modified=$(echo "$content" | sed 's/Old Title/New Title/')

# 3. Write it back with formatting preserved
mcporter call google-docs.markdown_write \
    documentId=XXX \
    markdown="$modified" \
    position=end
```

### LLM-Powered Editing

```bash
# Read document with formatting
doc=$(mcporter call google-docs.markdown_read documentId=XXX)

# Process with LLM (example using Claude)
result=$(echo "$doc" | claude "Summarize this document in Markdown")

# Write summary back
mcporter call google-docs.markdown_write \
    documentId=XXX \
    markdown="# Summary\n\n$result" \
    position=end
```

## Architecture Changes

### v1.0 Structure
```
GoogleDocsMCPServer/
├── server.py (660 lines - monolithic)
└── setup_auth.py
```

### v2.0 Structure
```
GoogleDocsMCPServer/
├── server.py (150 lines - entry point)
├── setup_auth.py (no changes)
├── domain/                 # Business logic
├── infrastructure/         # External systems
├── application/           # Use cases
└── mcp/                   # Protocol
```

Benefits:
- **Separation of concerns** - Each layer has single responsibility
- **Testability** - Easier to unit test individual components
- **Maintainability** - Changes isolated to specific layers
- **Extensibility** - Easy to add new tools or features

## Compatibility

### No Backward Compatibility

v2.0 is **not backward compatible** with v1.0. All tool names have changed.

### Migration Required

If you have scripts or workflows using v1.0:
1. Update all tool names (see table above)
2. Update `docs_append`/`docs_insert` calls to use `text_write`
3. Update `docs_format_*` calls to use `markdown_format`
4. Test thoroughly

### Rollback

If you need to rollback to v1.0:

```bash
cd /home/reto/Development/mb_tools_bar/GoogleDocsMCPServer
mv server.py server_v2.py
mv server_old.py server.py
```

The old server is preserved as `server_old.py`.

## Testing

Basic smoke test:

```bash
# Test initialization
echo '{"method": "initialize", "params": {"protocolVersion": "2024-11-05"}, "id": 1}' | \
    python3 server.py 2>/dev/null

# Test tool listing
echo '{"method": "tools/list", "id": 2}' | \
    python3 server.py 2>/dev/null | \
    python3 -c "import json, sys; print('Tools:', len(json.load(sys.stdin)['tools']))"
```

Expected output:
- Initialize should return protocol version and server info
- Tool listing should show 7 tools

## Support

For issues or questions:
- Check `GoogleDocsMCPServer/README.md` for usage examples
- Check `CLAUDE.md` for architecture details
- Old server preserved as `server_old.py` for reference

## Timeline

- **v1.0**: Original implementation (660 lines, 7 tools)
- **v2.0**: Refactored implementation (1,200 lines across layers, 7 reorganized tools)
- **Breaking change**: Tool names changed, no backward compatibility
