# OpenClaw.ai Toolbox

Collection of CLI Tools for Cudos internal systems, designed for use with OpenClaw.ai.

## Quick Start

### 1. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env and add your keys (MBTOOLS_API_KEY, CRM_URL, CRM_USER, CRM_API_KEY, OPENROUTER_API_KEY, etc.)
```

### 2. Setup Virtual Environment

```bash
bash setup_venv.sh
source venv/bin/activate
```

## Tools Overview

---

### [Cudos Controlling CLI](./CudosControllingTool/README.md)

Query RolX (timesheet) and Bexio (invoicing) via natural language.

**Usage:**
```bash
# Timesheet queries (RolX)
./cudos-controlling rolx "How many hours did Reto Bättig work in 2025 per task"
./cudos-controlling rolx "Gib mir alle Stunden für Projekt #0123.002 im Februar 2026"

# Invoice queries (Bexio)
./cudos-controlling bexio "Give me invoice #0290.001.01.01"
./cudos-controlling bexio "Show all invoices for project 290" --json
```

**Setup:** Set `MBTOOLS_API_KEY` in `.env` or as environment variable.

---

### [CRM REST CLI](./crm-rest/README.md)

Direct queries against berliCRM via REST API. All output is JSON.

**Usage:**
```bash
crm search-contacts "Max Muster"
crm search-accounts "Cudos"
crm search-potentials "Cloud Migration"
crm account-comments "Cudos AG"
crm details 3x12345
crm query "select * from Potentials where sales_stage != 'Closed Won' limit 0, 50;"
```

**Setup:** Set `CRM_URL`, `CRM_USER`, `CRM_API_KEY` in `crm-rest/.env`.

---

### [CRM AI Service](./crm-ai-service/README.md)

AI-powered CRM agent for complex, multi-step free-text queries. Slower and costlier than `crm` — use for complex questions.

**Usage:**
```bash
crm-ai "Show the last 3 comments for Cudos AG"
crm-ai "Find all contacts at cudos.ch"
crm-ai "List all open potentials" --timeout 60
crm-ai "Find contacts named Müller" --verbose
```

**Setup:** Set `CRM_URL`, `CRM_USER`, `CRM_API_KEY`, `OPENROUTER_API_KEY` (and optionally `OPENROUTER_MODEL`) in `crm-ai-service/.env`.

---

### [CRM Chat](./crm-chat/README.md)

Web chat UI on top of the CRM AI agent. Ask natural-language questions about the CRM in a browser.

**Setup & Start:**
```bash
# Backend
cd crm-chat/backend && pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (separate terminal)
cd crm-chat/frontend && npm install && npm run dev
```

Open http://localhost:5173. Reads CRM credentials from `crm-ai-service/.env`.

---

### [Sales Report](./sales_report/)

Creates a sales report from CRM open potentials and writes results to a Google Sheet (tabs «Summen» and «Anzahl»).

**Usage:**
```bash
./sales_report/sales_report.py
```

No arguments — reads CRM via `crm` CLI and writes to the configured Google Sheet.

---

### [Sales Reminder Tool](./SalesReminderTool/README.md)

Automated email reminder sent on the Wednesday before the 4th Monday of each month.

**Usage:**
```bash
# Manual run
python3 sales-reminder bu@cudos.ch

# Cron (every Wednesday at 09:00)
0 9 * * 3 cd /path/to/mb_tools_bar && python3 sales-reminder bu@cudos.ch
```

---

### [NZZ Reader](./nzz-reader/)

Read NZZ articles from the local scraping archive.

**Usage:**
```bash
# Latest 10 articles
./nzz-reader/nzz-reader.py

# All articles for a specific date
./nzz-reader/nzz-reader.py --date 2026-03-15

# Full text of article #12 on that date
./nzz-reader/nzz-reader.py --date 2026-03-15 12
```

---

### [Google AI Search](./google-ai-search/README.md)

Web search powered by Google Custom Search API + Gemini for AI-summarized results with source URLs.

**Usage:**
```bash
./google-ai-search/google-ai-search "Aktueller Stand von Fusion Energy"
./google-ai-search/google-ai-search --json "Wetter Zürich morgen"
./google-ai-search/google-ai-search -n 10 "Python 3.12 Features"
./google-ai-search/google-ai-search -i    # Interactive mode
```

**Setup:** Set `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` in environment or `google-ai-search/config.json`.

---

### [Moneyhouse Scraper](./moneyhouse-scraper/README.md)

Scrapes company information from moneyhouse.ch (Handelsregister, employee count, authorized signatories, etc.).

**Usage:**
```bash
./moneyhouse-scraper/moneyhouse_scraper.py "Cudos AG" --email user@example.com --password geheim --headless
```

Output: JSON with company details (name, address, employee count, authorized signatories, MwSt-Nr, purpose, etc.).

**Setup:** Requires Playwright: `pip install playwright && playwright install chromium`

---

### [Morticia Publish](./morticia-publish/README.md)

Publish files and websites to `https://baettig.org/morticia/`.

**Usage:**
```bash
./morticia-publish/morticia-publish index.html style.css   # Upload files
./morticia-publish/morticia-publish --list                  # List published files
./morticia-publish/morticia-publish --sync-dir ./mysite/    # Sync whole directory
./morticia-publish/morticia-publish --delete old-file.html  # Delete a file
./morticia-publish/morticia-publish --index "My Collection" # Create index page
```

---

### [BPM Sensor](./bpm-sensor/)

Detects the BPM (Beats Per Minute) of an MP3 file by sampling 3 evenly-distributed sections and returning the median.

**Usage:**
```bash
./bpm track.mp3
./bpm track.mp3 --verbose     # Show per-section breakdown
./bpm track.mp3 --json        # Full JSON output
./bpm track.mp3 --sections 5 --window 20
```

**Setup:** Requires `librosa` and `numpy` (included in `requirements.txt`).

---

### [YouTube MP3 Downloader](./YouTubeDownload/)

Downloads a YouTube video as an MP3 file.

**Usage:**
```bash
cd YouTubeDownload
./yt2mp3.py https://www.youtube.com/watch?v=VIDEO_ID [output-dir]
./upload.sh   # Upload to Google Drive
```

**Setup:** Requires `yt-dlp` and `ffmpeg`.

---

### [Security Scan](./SecurityScan/Requirements.md)

Recursively scans Markdown files in a directory for potentially unsafe content using AI.

**Usage:**
```bash
./SecurityScan/security_scan.py <start-directory> --days-back 7
```

Checks all `.md` files modified within the last N days. Uses `moonshotai/kimi-k2.5` via OpenRouter. Outputs JSON with `OK` or `DANGER` per file.

---

## Architecture

```
mb_tools_bar/
├── venv/                      # Shared virtual environment
├── CudosControllingTool/      # RolX + Bexio CLI
├── SalesReminderTool/         # Monthly email reminder
├── SecurityScan/              # Markdown security scanner
├── crm-ai-service/            # AI-powered CRM agent CLI
├── crm-chat/                  # Web chat UI for CRM
├── crm-rest/                  # CRM REST CLI
├── google-ai-search/          # Google search + AI summaries
├── moneyhouse-scraper/        # moneyhouse.ch scraper
├── morticia-publish/          # File publisher to baettig.org
├── nzz-reader/                # NZZ article reader
├── sales_report/              # CRM → Google Sheets sales report
├── bpm-sensor/                # MP3 BPM detector
├── YouTubeDownload/           # YouTube → MP3 downloader
├── requirements.txt           # All dependencies
├── setup_venv.sh              # Virtual environment setup
├── .env.example               # Environment variable template
└── CLAUDE.md                  # Development guidelines
```

## Dependencies

Install all:
```bash
pip install -r requirements.txt
```

Key dependencies:
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`
- `playwright` (moneyhouse-scraper only)
- `yt-dlp` (YouTubeDownload only)

## License

[MIT Open Source License](https://opensource.org/license/mit)
