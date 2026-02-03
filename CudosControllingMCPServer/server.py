#!/usr/bin/env python3
"""
MCP Server for Cudos Controlling API (RolX and Bexio queries).
Supports: controlling_query_rolx, controlling_query_bexio
"""

import json
import sys
import os
import urllib.request
import urllib.parse
from typing import Optional
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from repository root (parent of this script's directory)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Fallback: try loading from /home/reto/Development/mb_tools_bar/.env
        fallback_path = Path('/home/reto/Development/mb_tools_bar/.env')
        if fallback_path.exists():
            load_dotenv(fallback_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

API_BASE_URL = "https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io"

def log(msg: str):
    """Log to stderr for debugging."""
    print(msg, file=sys.stderr)
    # Also log to file for debugging mcporter issues
    try:
        with open('/tmp/cudos_controlling_mcp.log', 'a') as f:
            import datetime
            f.write(f"[{datetime.datetime.now()}] {msg}\n")
    except:
        pass

def send_response(response: dict):
    """Send JSON response to stdout."""
    response_json = json.dumps(response)
    log(f"Full response: {response_json[:200]}")
    print(response_json, flush=True)

def get_api_key() -> Optional[str]:
    """Get API key from environment or config file."""
    # Try environment variable first
    api_key = os.environ.get('MBTOOLS_API_KEY')
    if api_key:
        return api_key

    # Try config file
    config_path = os.path.expanduser('~/.mbtools/config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('api_key')

    return None

def query_api(endpoint: str, request_text: str) -> dict:
    """Make a query to the Controlling API."""
    api_key = get_api_key()
    if not api_key:
        return {
            "error": "No API key found. Set MBTOOLS_API_KEY environment variable or create ~/.mbtools/config.json"
        }

    url = f"{API_BASE_URL}/{endpoint}/query"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    payload = json.dumps({'request': request_text}).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No error details'
        return {
            "error": f"HTTP {e.code}: {e.reason}",
            "details": error_body
        }
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}

def query_rolx(query: str) -> dict:
    """Query RolX time tracking system."""
    log(f"Querying RolX: {query}")
    return query_api('rolx', query)

def query_bexio(query: str) -> dict:
    """Query Bexio invoicing system."""
    log(f"Querying Bexio: {query}")
    return query_api('bexio', query)

def handle_request(request: dict) -> dict:
    """Handle incoming MCP request."""
    method = request.get('method')
    params = request.get('params', {})

    if method == 'initialize':
        # Use the protocol version requested by the client
        requested_version = params.get('protocolVersion', '2024-11-05')
        return {
            "protocolVersion": requested_version,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "cudos-controlling-mcp",
                "version": "1.0.0"
            }
        }

    elif method == 'tools/list':
        return {
            "tools": [
                {
                    "name": "controlling_query_rolx",
                    "description": "Query RolX timesheet data using natural language. Ask about hours worked, tasks, projects, time periods, etc.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query for RolX timesheet data (e.g., 'How many hours did Reto Bättig work in 2025 per task')"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "controlling_query_bexio",
                    "description": "Query Bexio invoicing data using natural language. Ask about invoices, project numbers, amounts, dates, etc.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query for Bexio invoice data (e.g., 'Give me invoice #0290.001.01.01' or 'Show all invoices with Project Number 290')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }

    elif method == 'tools/call':
        tool_name = params.get('name')
        args = params.get('arguments', {})
        query = args.get('query', '')

        if tool_name == 'controlling_query_rolx':
            result = query_rolx(query)
        elif tool_name == 'controlling_query_bexio':
            result = query_bexio(query)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]
        }

    return {"error": f"Unknown method: {method}"}

def main():
    """Main loop for MCP server."""
    # Set stdin to unbuffered mode
    import io
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, line_buffering=True)

    log("Cudos Controlling MCP Server starting...")
    log("Waiting for input...")

    while True:
        try:
            log("Reading from stdin...")
            line = sys.stdin.readline()
            log(f"Received line ({len(line)} chars): {line[:100] if line else 'empty'}")

            if not line:
                log("Empty line, continuing...")
                continue

            line = line.strip()
            if not line:
                log("Line was only whitespace, continuing...")
                continue

            request = json.loads(line)
            log(f"Parsed request: method={request.get('method', 'unknown')}, id={request.get('id', 'none')}")
            response = handle_request(request)

            # Add request ID if present
            if 'id' in request:
                response['id'] = request['id']

            log(f"Sending response for {request.get('method')}...")
            send_response(response)
            log("Response sent, flushing...")
            sys.stdout.flush()
            log("Flush complete")

        except json.JSONDecodeError as e:
            log(f"JSON decode error: {e} - line was: {line}")
        except EOFError:
            log("EOF received, shutting down")
            break
        except Exception as e:
            log(f"Error: {e}")
            import traceback
            log(traceback.format_exc())
            send_response({"error": str(e)})

if __name__ == '__main__':
    main()
