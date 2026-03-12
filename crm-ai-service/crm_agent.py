#!/usr/bin/env python3
"""
crm_agent — AI-powered CRM CLI tool.

Uses an OpenRouter LLM agent with CRM tools to answer free-text questions
about the CRM, returning results as JSON.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

from crm_api import crm_login, crm_query, crm_retrieve


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config():
    """Load config from .env file, with environment variables taking precedence."""
    env_file = Path(__file__).parent / ".env"
    config = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    config[key.strip()] = value.strip()
    for key in ("CRM_URL", "CRM_USER", "CRM_API_KEY", "OPENROUTER_API_KEY", "OPENROUTER_MODEL"):
        if key in os.environ:
            config[key] = os.environ[key]
    return config


# ---------------------------------------------------------------------------
# Tool definitions (OpenAI-compatible)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "crm_query",
            "description": "Run a SQL-like query against the CRM. Returns a list of records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL-like query string, e.g. \"select * from Contacts where email like '%cudos.ch%' limit 0, 50;\""
                    }
                },
                "required": ["sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crm_retrieve",
            "description": "Fetch a single CRM record by its ID (e.g. '4x2712'). Returns all fields of the record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_id": {
                        "type": "string",
                        "description": "CRM object ID in the form '<module_id>x<record_id>', e.g. '4x2712'"
                    }
                },
                "required": ["object_id"]
            }
        }
    }
]


# ---------------------------------------------------------------------------
# OpenRouter API
# ---------------------------------------------------------------------------

def call_openrouter(messages, config, timeout):
    """Call OpenRouter chat completions API. Returns the parsed response dict."""
    payload = json.dumps({
        "model": config["OPENROUTER_MODEL"],
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {config['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

def dispatch_tool(tool_call, base_url, session, verbose):
    """Execute a tool call and return the result as a JSON string."""
    name = tool_call["function"]["name"]
    try:
        args = json.loads(tool_call["function"]["arguments"])
    except (json.JSONDecodeError, KeyError) as e:
        return json.dumps({"error": f"Invalid tool arguments: {e}"})

    if verbose:
        print(f"  [tool] {name}({json.dumps(args)})", file=sys.stderr)

    try:
        if name == "crm_query":
            result = crm_query(base_url, session, args["sql"])
        elif name == "crm_retrieve":
            result = crm_retrieve(base_url, session, args["object_id"])
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_agent(task, config, timeout_seconds, verbose):
    """Run the agentic loop. Returns a dict (the final answer or an error)."""
    deadline = time.time() + timeout_seconds

    # Load system prompt
    prompt_file = Path(__file__).parent / "system_prompt.txt"
    system_prompt = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""

    # Login
    if verbose:
        print("[agent] Logging in to CRM...", file=sys.stderr)
    session = crm_login(config["CRM_URL"], config["CRM_USER"], config["CRM_API_KEY"])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    iteration = 0
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            return {"error": "Timeout"}

        call_timeout = min(remaining, 60)
        if verbose:
            print(f"[agent] Calling LLM (iteration {iteration}, timeout={call_timeout:.0f}s)...", file=sys.stderr)

        try:
            response = call_openrouter(messages, config, timeout=int(call_timeout))
        except urllib.error.URLError as e:
            return {"error": f"OpenRouter request failed: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error calling LLM: {e}"}

        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        messages.append(message)

        finish_reason = choice.get("finish_reason")
        if finish_reason == "error":
            error_detail = message.get("content") or str(response.get("error", "unknown error"))
            return {"error": f"LLM error: {error_detail}"}

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            # Final answer — prefer content, fall back to reasoning
            content = message.get("content") or message.get("reasoning") or ""
            if verbose:
                print(f"[agent] Final answer received. content={repr(content[:200])}", file=sys.stderr)
            # Try to parse content as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
            # Content is prose — ask the model to reformat as JSON (one retry)
            remaining = deadline - time.time()
            if remaining > 5:
                if verbose:
                    print("[agent] Asking model to reformat answer as JSON...", file=sys.stderr)
                messages.append({
                    "role": "user",
                    "content": (
                        "Now output your answer as a single valid JSON object ONLY. "
                        "No prose, no markdown, no explanation — just the JSON. "
                        "Use {\"records\":[...]} for lists, {\"count\":N} for numbers, "
                        "{\"answer\":\"...\"} for text answers."
                    )
                })
                try:
                    response2 = call_openrouter(messages, config, timeout=int(min(remaining, 30)))
                    choice2 = response2.get("choices", [{}])[0]
                    content2 = choice2.get("message", {}).get("content") or ""
                    return json.loads(content2)
                except (json.JSONDecodeError, Exception):
                    pass
            return {"answer": content}

        # Execute tool calls
        for tc in tool_calls:
            tool_result = dispatch_tool(tc, config["CRM_URL"], session, verbose)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_result,
            })

        iteration += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="crm-ai",
        description="AI-powered CRM CLI — answer free-text questions about the CRM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  crm-ai "How many contacts are in the CRM?"
  crm-ai "Show the last 3 comments for Cudos AG"
  crm-ai "Find contacts at cudos.ch" --json
  crm-ai "List open potentials" --timeout 60
        """
    )
    parser.add_argument("task", help="Free-text task or question")
    parser.add_argument("--timeout", type=int, default=120, metavar="SECONDS",
                        help="Maximum time to spend (default: 120)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Output raw JSON (always true; flag kept for compatibility)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print agent progress to stderr")

    args = parser.parse_args()

    config = load_config()
    required = ("CRM_URL", "CRM_USER", "CRM_API_KEY", "OPENROUTER_API_KEY", "OPENROUTER_MODEL")
    missing = [k for k in required if not config.get(k)]
    if missing:
        result = {"error": f"Missing config keys: {', '.join(missing)}"}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    try:
        result = run_agent(args.task, config, args.timeout, args.verbose)
    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if "error" in result else 0)


if __name__ == "__main__":
    main()
