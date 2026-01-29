#!/usr/bin/env python3
"""
MB Tools - CLI for RolX and Bexio queries
"""
import os
import sys
import json
import requests
from typing import Optional

API_BASE_URL = "https://controlling-assistant-prod.nicedune-9fff3676.switzerlandnorth.azurecontainerapps.io"

def get_api_key() -> Optional[str]:
    """Get API key from environment or config file"""
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
    """Make a query to the API"""
    api_key = get_api_key()
    if not api_key:
        print("Error: No API key found. Set MBTOOLS_API_KEY environment variable or create ~/.mbtools/config.json", file=sys.stderr)
        sys.exit(1)
    
    url = f"{API_BASE_URL}/{endpoint}/query"
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key
    }
    payload = {'request': request_text}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed: {e}", file=sys.stderr)
        sys.exit(1)

def rolx(query: str):
    """Query RolX time tracking system"""
    result = query_api('rolx', query)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def bexio(query: str):
    """Query Bexio invoicing system"""
    result = query_api('bexio', query)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  mbtools.py rolx <query>   - Query RolX time tracking")
        print("  mbtools.py bexio <query>  - Query Bexio invoicing")
        print("\nExamples:")
        print('  mbtools.py rolx "How many hours did Reto Bättig work in 2025 per task"')
        print('  mbtools.py bexio "Give me invoice #0290.001.01.01"')
        sys.exit(1)
    
    command = sys.argv[1].lower()
    query = ' '.join(sys.argv[2:])
    
    if command == 'rolx':
        rolx(query)
    elif command == 'bexio':
        bexio(query)
    else:
        print(f"Error: Unknown command '{command}'. Use 'rolx' or 'bexio'.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
