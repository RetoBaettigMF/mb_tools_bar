# crm-ai — AI-Powered CRM CLI

Answer free-text questions about the CRM using an AI agent that queries the CRM on your behalf.

## Overview

`crm-ai` takes a natural-language task, runs an agentic loop using an OpenRouter LLM, and returns the answer in a machine-readable format. The agent can issue multiple CRM queries across several turns to resolve complex questions.

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

# Limit result size (default: 50,000 chars)
crm-ai "Find open potentials" --max-chars 10000

# Verbose (shows agent progress on stderr)
crm-ai "Find contacts named Müller" --verbose
```

## Output Format

The agent picks the most appropriate format for the data:

- **Markdown table** — for lists of records
- **JSON object** — for structured/nested data
- **Simple list** — for short enumerations
- **CSV table** — for tabular data meant for further processing

Custom field names (e.g. `cf_958`) and user IDs (e.g. `19x7`) are resolved to their real names using built-in lookup tables in the system prompt.

On error (exit code 1):
```json
{"error": "reason"}
```

A detailed run log is written to `crm_agent.log` on every run (overwritten each time).

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `task` | (required) | Free-text question or task |
| `--timeout SECONDS` | 120 | Max time before giving up |
| `--max-chars N` | 50000 | Max characters per CRM result; triggers AI re-query if exceeded |
| `--verbose` | off | Print agent progress to stderr |

## Configuration

All config is read from `.env` (in the same directory) or environment variables:

| Variable | Description |
|----------|-------------|
| `CRM_URL` | CRM base URL |
| `CRM_USER` | CRM username |
| `CRM_API_KEY` | CRM API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENROUTER_MODEL` | Model to use (e.g. `google/gemini-2.5-flash-lite`) |

## Dependencies

Python stdlib only: `argparse`, `json`, `urllib`, `hashlib`, `pathlib`
