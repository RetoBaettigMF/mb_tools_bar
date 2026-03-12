"""
CRM Chat Backend — stateless FastAPI app.

Single endpoint: POST /chat
Request:  {"messages": [{"role": "user|assistant", "content": "..."}]}
Response: {"response": "...", "role": "assistant"}
"""

import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Load .env from crm-ai-service directory (where the keys live)
_env_path = Path(__file__).parent.parent.parent / "crm-ai-service" / ".env"
load_dotenv(_env_path)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "moonshotai/kimi-k2.5")
CRM_AGENT_PATH = Path(__file__).parent.parent.parent / "crm-ai-service" / "crm_agent"

SYSTEM_PROMPT = """You are a helpful assistant for a CRM system.
You help users query and understand their CRM data using natural language.
When users ask about contacts, companies, deals, or other CRM data, use the query_crm tool to get the information.
Present results clearly and helpfully. If the CRM returns data, summarize and explain it in a readable way.
"""

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="CRM Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_crm",
            "description": "Query the CRM with a natural language question to retrieve contacts, companies, deals, or other CRM data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural language query to send to the CRM",
                    }
                },
                "required": ["query"],
            },
        },
    }
]

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    messages: list[dict]


class ChatResponse(BaseModel):
    response: str
    role: str = "assistant"


# ---------------------------------------------------------------------------
# CRM tool execution
# ---------------------------------------------------------------------------


def run_crm_agent(query: str) -> str:
    """Run the crm_agent CLI and return its output."""
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
            return json.dumps({"error": error or "CRM agent returned no output"})
        return output or json.dumps({"error": "CRM agent returned empty output"})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "CRM agent timed out after 60 seconds"})
    except Exception as e:
        return json.dumps({"error": f"Failed to run CRM agent: {str(e)}"})


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + request.messages

    # Agentic loop: keep calling LLM until it stops asking for tools
    for _ in range(10):  # max 10 iterations to avoid infinite loops
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            # Execute all tool calls
            assistant_msg = {
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ],
            }
            messages.append(assistant_msg)

            for tool_call in choice.message.tool_calls:
                if tool_call.function.name == "query_crm":
                    args = json.loads(tool_call.function.arguments)
                    crm_result = run_crm_agent(args["query"])
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": crm_result,
                        }
                    )
        else:
            # LLM is done — return the final text response
            content = choice.message.content or ""
            return ChatResponse(response=content, role="assistant")

    return ChatResponse(
        response="I was unable to complete the request after multiple attempts.",
        role="assistant",
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok", "model": OPENROUTER_MODEL, "crm_agent": str(CRM_AGENT_PATH)}
