"""
CRM Chat Backend — stateless FastAPI app.

Single endpoint: POST /chat
Request:  {"query": "..."}
Response: {"response": "..."}
"""

import json
import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

CRM_AGENT_PATH = Path(__file__).parent.parent.parent / "crm-ai-service" / "crm_agent"

app = FastAPI(title="CRM Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    response: str


def run_crm_agent(query: str) -> str:
    try:
        result = subprocess.run(
            [str(CRM_AGENT_PATH), query],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and not output:
            error = result.stderr.strip()
            return error or "CRM agent returned no output"
        return output or "CRM agent returned empty output"
    except subprocess.TimeoutExpired:
        return "CRM agent timed out after 60 seconds"
    except Exception as e:
        return f"Failed to run CRM agent: {str(e)}"


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    response = run_crm_agent(request.query)
    return ChatResponse(response=response)


@app.get("/health")
async def health():
    return {"status": "ok", "crm_agent": str(CRM_AGENT_PATH)}


# Serve static frontend files
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"error": "Frontend not built. Run 'npm run build' in frontend/"}
