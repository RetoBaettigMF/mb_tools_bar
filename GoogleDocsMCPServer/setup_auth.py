#!/usr/bin/env python3
"""Setup OAuth for Google Docs MCP Server."""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/documents']

def main():
    creds_path = os.path.expanduser('~/.config/gogcli/credentials.json')
    token_path = os.path.expanduser('~/.config/gogcli/tokens/bar.ai.bot@cudos.ch.json')
    
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found. Run 'gog auth credentials' first.")
        return
    
    print("Starting OAuth flow for Google Docs access...")
    print("Please login with bar.ai.bot@cudos.ch")
    
    # Load credentials and wrap in proper format
    with open(creds_path) as f:
        client_config = json.load(f)
    
    # Wrap in installed app format expected by Google Auth
    client_secrets = {
        "installed": {
            "client_id": client_config["client_id"],
            "client_secret": client_config["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save token
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, 'w') as f:
        f.write(creds.to_json())
    
    print(f"\nToken saved to: {token_path}")
    print("You can now use the Google Docs MCP Server!")

if __name__ == '__main__':
    main()
