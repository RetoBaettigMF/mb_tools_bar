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
from datetime import datetime
from pathlib import Path

from crm_api import crm_login, crm_query, crm_retrieve

MAX_RESULT_CHARS_DEFAULT = 50_000


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
# Logging
# ---------------------------------------------------------------------------

_log_file = None

def init_log():
    """Open (overwrite) the log file for this run."""
    global _log_file
    log_path = Path(__file__).parent / "crm_agent.log"
    _log_file = open(log_path, "w", encoding="utf-8")
    _log(f"=== crm-ai session started at {datetime.now().isoformat()} ===")

def _log(msg):
    if _log_file:
        _log_file.write(msg + "\n")
        _log_file.flush()

def _log_section(title):
    _log(f"\n{'─' * 60}")
    _log(f"  {title}")
    _log('─' * 60)

def _strip_markdown_json(text):
    """Strip ```json ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first line (```json or ```) and last ``` line
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return text

def _log_result_preview(label, result_json_str):
    """Log the first 5 lines of a JSON result."""
    lines = result_json_str.splitlines()
    preview = "\n".join(lines[:5])
    if len(lines) > 5:
        preview += f"\n  ... ({len(lines) - 5} more lines)"
    _log(f"{label}:\n{preview}")


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

def call_openrouter(messages, config, timeout, iteration):
    """Call OpenRouter chat completions API. Returns the parsed response dict."""
    payload = json.dumps({
        "model": config["OPENROUTER_MODEL"],
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
    }).encode()

    _log_section(f"OpenRouter API call — iteration {iteration}")
    _log(f"Model: {config['OPENROUTER_MODEL']}")
    _log(f"Messages in context: {len(messages)}")
    _log(f"Timeout: {timeout}s")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {config['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        }
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
    elapsed = time.time() - t0

    response = json.loads(raw)
    _log(f"Response received in {elapsed:.2f}s")
    finish_reason = response.get("choices", [{}])[0].get("finish_reason", "?")
    _log(f"finish_reason: {finish_reason}")
    usage = response.get("usage", {})
    if usage:
        _log(f"Tokens: prompt={usage.get('prompt_tokens','?')} completion={usage.get('completion_tokens','?')}")
    return response


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

def dispatch_tool(tool_call, base_url, session, verbose, max_result_chars):
    """Execute a tool call and return the result as a JSON string."""
    name = tool_call["function"]["name"]
    try:
        args = json.loads(tool_call["function"]["arguments"])
    except (json.JSONDecodeError, KeyError) as e:
        err = json.dumps({"error": f"Invalid tool arguments: {e}"})
        _log(f"Tool call ERROR (bad args): {e}")
        return err

    _log_section(f"AI tool call: {name}")
    _log(f"Arguments: {json.dumps(args, ensure_ascii=False)}")

    if verbose:
        print(f"  [tool] {name}({json.dumps(args)})", file=sys.stderr)

    t0 = time.time()
    try:
        if name == "crm_query":
            result = crm_query(base_url, session, args["sql"])
        elif name == "crm_retrieve":
            result = crm_retrieve(base_url, session, args["object_id"])
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e)}
    elapsed = time.time() - t0

    result_str = json.dumps(result, indent=2, ensure_ascii=False)
    record_count = len(result) if isinstance(result, list) else 1
    _log(f"CRM response in {elapsed:.2f}s — {record_count} record(s)")
    _log_result_preview("Result preview (first 5 lines)", result_str)

    # Check character limit
    full_str = json.dumps(result, ensure_ascii=False)
    if len(full_str) > max_result_chars:
        sample = result[:5] if isinstance(result, list) else result
        sample_str = json.dumps(sample, ensure_ascii=False)
        warning = (
            f"RESULT_TOO_LARGE: The API returned {len(full_str):,} characters "
            f"(limit is {max_result_chars:,}). "
            f"You MUST call crm_query again with a more specific query — "
            f"use stricter WHERE conditions, select only needed fields (not *), "
            f"or reduce the LIMIT. Do NOT give up or ask the user to refine — retry yourself. "
            f"Here are the first 5 records to show the data structure: {sample_str}"
        )
        _log(f"[LIMIT] Result truncated: {len(full_str):,} chars > {max_result_chars:,} limit — returned sample of {len(sample) if isinstance(sample, list) else 1} record(s)")
        if verbose:
            print(f"  [limit] Result too large ({len(full_str):,} chars), sending sample to AI", file=sys.stderr)
        return warning

    return full_str


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_agent(task, config, timeout_seconds, verbose, max_result_chars=MAX_RESULT_CHARS_DEFAULT):
    """Run the agentic loop. Returns a dict (the final answer or an error)."""
    deadline = time.time() + timeout_seconds

    _log_section("Task")
    _log(f"Task: {task}")
    _log(f"Timeout: {timeout_seconds}s")
    _log(f"Model: {config['OPENROUTER_MODEL']}")
    _log(f"Max result chars: {max_result_chars:,}")

    # Load system prompt
    prompt_file = Path(__file__).parent / "system_prompt.txt"
    system_prompt = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""

    # Login
    if verbose:
        print("[agent] Logging in to CRM...", file=sys.stderr)
    _log_section("CRM Login")
    t0 = time.time()
    session = crm_login(config["CRM_URL"], config["CRM_USER"], config["CRM_API_KEY"])
    _log(f"Login successful in {time.time()-t0:.2f}s — session: {session[:12]}...")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    iteration = 0
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            _log("\n[TIMEOUT] Deadline exceeded")
            return {"error": "Timeout"}

        call_timeout = min(remaining, 60)
        if verbose:
            print(f"[agent] Calling LLM (iteration {iteration}, timeout={call_timeout:.0f}s)...", file=sys.stderr)

        try:
            response = call_openrouter(messages, config, timeout=int(call_timeout), iteration=iteration)
        except urllib.error.URLError as e:
            _log(f"[ERROR] OpenRouter request failed: {e}")
            return {"error": f"OpenRouter request failed: {e}"}
        except Exception as e:
            _log(f"[ERROR] Unexpected: {e}")
            return {"error": f"Unexpected error calling LLM: {e}"}

        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        messages.append(message)

        finish_reason = choice.get("finish_reason")
        if finish_reason == "error":
            error_detail = message.get("content") or str(response.get("error", "unknown error"))
            raw_error = json.dumps(response, ensure_ascii=False)[:400]
            native_reason = choice.get("native_finish_reason", "")
            _log(f"[WARN] LLM finish_reason=error (native: {native_reason}): {repr(error_detail[:80])}")
            _log(f"[WARN] Raw response: {raw_error}")
            # Pop the failed message
            messages.pop()

            if "MALFORMED_FUNCTION" in native_reason:
                # Model generated an invalid tool call — tell it what went wrong and let it retry
                _log("[WARN] Malformed function call — injecting error feedback and continuing")
                messages.append({
                    "role": "user",
                    "content": (
                        "Your last function call was malformed and could not be executed. "
                        "Please try again with a valid crm_query or crm_retrieve call. "
                        "Remember: COUNT(DISTINCT ...), GROUP BY, JOIN, and subqueries are NOT supported. "
                        "For distinct counts, fetch the field values with pagination and count unique values yourself."
                    )
                })
                # Continue the loop — model will retry
            else:
                # Transient API error — wait and retry the same messages
                _log(f"[WARN] Transient API error — waiting 3s then retrying...")
                time.sleep(3)
                remaining = deadline - time.time()
                if remaining > 5:
                    try:
                        response = call_openrouter(messages, config, timeout=int(min(remaining, 60)), iteration=f"{iteration}e")
                        choice = response.get("choices", [{}])[0]
                        message = choice.get("message", {})
                        messages.append(message)
                        finish_reason = choice.get("finish_reason")
                        if finish_reason == "error":
                            error_detail = message.get("content") or str(response.get("error", "unknown error"))
                            _log(f"[ERROR] Retry also failed: {repr(error_detail[:80])}")
                            return {"error": f"LLM error: {error_detail}"}
                    except Exception as e:
                        _log(f"[ERROR] Retry failed: {e}")
                        return {"error": f"LLM error after retry: {e}"}
                else:
                    return {"error": f"LLM error: {error_detail}"}

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            # Final answer — prefer content, fall back to reasoning
            content = message.get("content") or message.get("reasoning") or ""
            if verbose:
                print(f"[agent] Final answer received. content={repr(content[:200])}", file=sys.stderr)
            _log_section("Final answer from LLM")
            _log_result_preview("Content (first 5 lines)", content)

            # Try to parse content as JSON (strip markdown code fences if present)
            try:
                result = json.loads(_strip_markdown_json(content))
                _log("Parsed as valid JSON.")
                return result
            except json.JSONDecodeError:
                pass

            # Content is prose — ask the model to reformat as JSON (one retry)
            remaining = deadline - time.time()
            if remaining > 5:
                if verbose:
                    print("[agent] Asking model to reformat answer as JSON...", file=sys.stderr)
                _log("Content is not JSON — requesting reformat...")
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
                    response2 = call_openrouter(messages, config, timeout=int(min(remaining, 30)), iteration=f"{iteration}r")
                    choice2 = response2.get("choices", [{}])[0]
                    content2 = choice2.get("message", {}).get("content") or ""
                    _log_section("JSON reformat response")
                    _log_result_preview("Content (first 5 lines)", content2)
                    result = json.loads(_strip_markdown_json(content2))
                    _log("Parsed as valid JSON.")
                    return result
                except json.JSONDecodeError as e:
                    _log(f"Reformat failed (JSON parse): {e} — falling back to wrapped answer")
                except Exception as e:
                    _log(f"Reformat failed: {e} — falling back to wrapped answer")
            return {"answer": content}

        # Execute tool calls
        for tc in tool_calls:
            tool_result = dispatch_tool(tc, config["CRM_URL"], session, verbose, max_result_chars)
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
    parser.add_argument("--max-chars", type=int, default=MAX_RESULT_CHARS_DEFAULT,
                        metavar="N",
                        help=f"Max characters per CRM result before asking AI to filter (default: {MAX_RESULT_CHARS_DEFAULT:,})")

    args = parser.parse_args()

    config = load_config()
    required = ("CRM_URL", "CRM_USER", "CRM_API_KEY", "OPENROUTER_API_KEY", "OPENROUTER_MODEL")
    missing = [k for k in required if not config.get(k)]
    if missing:
        result = {"error": f"Missing config keys: {', '.join(missing)}"}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    init_log()
    _log(f"Task: {args.task}")

    try:
        result = run_agent(args.task, config, args.timeout, args.verbose, args.max_chars)
    except Exception as e:
        result = {"error": str(e)}

    _log_section("Final result")
    _log(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    _log(f"\n=== Session ended at {datetime.now().isoformat()} ===")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if "error" in result else 0)


if __name__ == "__main__":
    main()
