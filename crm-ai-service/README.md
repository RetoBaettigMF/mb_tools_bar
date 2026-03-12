# crm-ai — AI-Powered CRM CLI

Answer free-text questions about the CRM using an AI agent that queries the CRM on your behalf.

## Overview

`crm-ai` takes a natural-language task, runs an agentic loop using an OpenRouter LLM, and returns the answer as JSON. The agent can issue multiple CRM queries across several turns to resolve complex questions.

## Setup

1. Copy and fill in the config:
   ```bash
   cp .env.example .env
   # Edit .env with your CRM and OpenRouter credentials
   ```

2. No additional dependencies — uses Python stdlib only.

## Usage

```bash
# Count records
crm-ai "How many contacts are in the CRM?"

# Multi-step query
crm-ai "Show the last 3 comments for Cudos AG"

# Find by email domain
crm-ai "Find all contacts at cudos.ch"

# With timeout
crm-ai "List all open potentials" --timeout 60

# Verbose (shows agent progress on stderr)
crm-ai "Find contacts named Müller" --verbose

# Pipe to json.tool for formatting
crm-ai "Find contacts at cudos.ch" | python3 -m json.tool
```

## Output Format

Always outputs a single JSON object to stdout:

```json
{"records": [...]}       // list of records
{"record": {...}}        // single record
{"count": 42}            // numeric result
{"error": "reason"}      // on failure (exit code 1)
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `task` | (required) | Free-text question or task |
| `--timeout SECONDS` | 120 | Max time before giving up |
| `--verbose` | off | Print agent progress to stderr |

## Configuration

All config is read from `.env` (in the same directory) or environment variables:

| Variable | Description |
|----------|-------------|
| `CRM_URL` | CRM base URL |
| `CRM_USER` | CRM username |
| `CRM_API_KEY` | CRM API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENROUTER_MODEL` | Model to use (e.g. `anthropic/claude-sonnet-4-6`) |

## Dependencies

Python stdlib only: `argparse`, `json`, `urllib`, `hashlib`, `pathlib`
