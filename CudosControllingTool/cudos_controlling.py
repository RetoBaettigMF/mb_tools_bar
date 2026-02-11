#!/usr/bin/env python3
"""
CLI tool for Cudos Controlling API (RolX and Bexio queries).
Query Cudos internal systems using natural language from the command line.
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import argparse
from typing import Optional
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from repository root (parent of this script's directory)
    # Use resolve() to follow symlinks to the actual file location
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

API_BASE_URL = "https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io"

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
    return query_api('rolx', query)

def query_bexio(query: str) -> dict:
    """Query Bexio invoicing system."""
    return query_api('bexio', query)

def format_output(result: dict, as_json: bool = False) -> str:
    """Format API result for display (formatted text or raw JSON)."""
    if as_json:
        return json.dumps(result, indent=2, ensure_ascii=False)

    # Check for errors
    if "error" in result:
        error_msg = f"Error: {result['error']}"
        if 'details' in result:
            error_msg += f"\nDetails: {result['details']}"
        return error_msg

    # Pretty-print the result
    return json.dumps(result, indent=2, ensure_ascii=False)

def main():
    """Main CLI entry point using argparse."""
    parser = argparse.ArgumentParser(
        prog='cudos-controlling',
        description='Query Cudos Controlling systems (RolX timesheet and Bexio invoicing) via natural language',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s rolx "Wie viele Stunden hat Reto gearbeitet in Januar 2025?"
  %(prog)s bexio "Zeige Rechnung #0290.001.01.01"
  %(prog)s rolx "Show all hours for project 0123.110" --json
  %(prog)s bexio "Total invoiced amount for 2025" --json
        """
    )

    subparsers = parser.add_subparsers(dest='command', required=True, help='Subcommands')

    # RolX subcommand
    parser_rolx = subparsers.add_parser(
        'rolx',
        help='Query RolX timesheet data',
        description='Query RolX time tracking system using natural language'
    )
    parser_rolx.add_argument('query', help='Natural language query for RolX data')
    parser_rolx.add_argument('--json', action='store_true', help='Output raw JSON')

    # Bexio subcommand
    parser_bexio = subparsers.add_parser(
        'bexio',
        help='Query Bexio invoicing data',
        description='Query Bexio invoicing system using natural language'
    )
    parser_bexio.add_argument('query', help='Natural language query for Bexio data')
    parser_bexio.add_argument('--json', action='store_true', help='Output raw JSON')

    args = parser.parse_args()

    # Execute the appropriate query
    if args.command == 'rolx':
        result = query_rolx(args.query)
    elif args.command == 'bexio':
        result = query_bexio(args.query)
    else:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        sys.exit(1)

    # Format and output result
    output = format_output(result, as_json=args.json)
    print(output)

    # Exit with error code if API returned an error
    sys.exit(1 if "error" in result else 0)

if __name__ == '__main__':
    main()
