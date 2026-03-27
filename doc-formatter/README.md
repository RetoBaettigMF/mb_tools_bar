# doc-formatter

A CLI tool that fills Microsoft Word templates (`.dotx`) with text input using AI (OpenRouter).

## Overview

Give it a Word template and some text, and it uses a two-step AI process to intelligently fill in the template:

1. **Schema generation** — AI analyzes the template structure and identifies all fillable fields and sections
2. **Content filling** — AI maps your input text to the template's fields and sections

The template's branding (headers, footers, logos, styles) is preserved in the output.

## Usage

```bash
# Using the symlink from the parent directory
./doc-format <template> <input> [--output <output_file>] [--model <model_id>]

# Or directly
python3 doc-formatter/doc_formatter.py <template> <input>
```

### Arguments

| Argument | Description |
|---|---|
| `template` | Path to a `.dotx` Word template file |
| `input` | Path to an input text file, or a literal text string |
| `--output`, `-o` | Output `.docx` path (default: auto-generated with timestamp) |
| `--model` | OpenRouter model ID (default: `moonshotai/kimi-k2.5`) |

### Examples

```bash
# Fill a meeting protocol from a text file
./doc-format doc-formatter/Protokoll.dotx meeting_notes.txt

# Specify output path
./doc-format doc-formatter/Protokoll.dotx meeting_notes.txt --output output/protokoll_2026.docx

# Use a different AI model
./doc-format doc-formatter/Bericht.dotx bericht_input.md --model anthropic/claude-3-5-haiku

# Pass text directly on the command line
./doc-format doc-formatter/Protokoll.dotx "Meeting on 19.3.2026, Participants: ..."
```

## Setup

1. Add your OpenRouter API key to the `.env` file in the repository root:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

2. Install dependencies:
   ```bash
   pip install python-docx
   # or use the shared venv:
   source venv/bin/activate
   ```

## Templates

Two templates are included:

| Template | Purpose |
|---|---|
| `Protokoll.dotx` | Meeting minutes (Sitzungsprotokoll) |
| `Bericht.dotx` | Report (Bericht) |

## How it works

1. The template is opened using `python-docx` (the `.dotx` format is handled transparently)
2. The template structure is extracted as a text outline (paragraphs, tables, styles)
3. **AI Step 1**: The outline is sent to the AI, which returns a fill schema describing each field's location and type
4. **AI Step 2**: The schema and input text are sent to the AI, which returns filled content for each field and section
5. The template is filled: title, table fields, and content sections are populated with the AI's output
6. The result is saved as a `.docx` file

## Output

Console output (stderr) shows progress:
```
Template:  /path/to/Protokoll.dotx
Input:     1866 characters
Output:    /path/to/Protokoll_20260319_143022.docx
Model:     moonshotai/kimi-k2.5

Extracting template structure...
Step 1/2: Generating fill schema from template...
  Schema: 19 fields, 3 sections
Step 2/2: Filling template with input content...
  Content: title='ERFA CRA 19.3.26 - Protokoll', 3 sections

Writing output document...

Done. Output saved to: /path/to/Protokoll_20260319_143022.docx
```
