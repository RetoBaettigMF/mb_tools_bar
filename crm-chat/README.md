# CRM Chat

A simple chat UI on top of the `crm_agent` CLI tool. Ask natural-language questions about the CRM and get AI-generated answers.

## Architecture

```
crm-chat/
├── backend/
│   ├── main.py           # FastAPI app — single POST /chat endpoint
│   └── requirements.txt
└── frontend/             # React + Vite chat UI
    ├── src/
    │   ├── App.jsx
    │   └── App.css
    └── ...
```

**Backend** is stateless: the client sends the full chat history with every request. The backend prepends a system prompt, calls OpenRouter, and runs `crm_agent` when needed (agentic loop). It reads credentials from `../crm-ai-service/.env`.

**Frontend** manages chat history in React state, renders assistant messages with Markdown, and proxies `/chat` to `localhost:8000` via Vite.

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Usage

- Type a question and press **Enter** (or click **Send**)
- Press **Shift+Enter** for a newline
- **New Chat** clears the conversation
- **Copy** copies the full chat transcript to the clipboard

## Examples

- "How many contacts are in the CRM?"
- "Find all contacts at Acme AG"
- "Show me deals that closed last month"
