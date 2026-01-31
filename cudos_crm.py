#!/usr/bin/env python3
"""
Cudos CRM Tool - vTiger CRM Integration
Search for persons and companies in the Cudos CRM system.
"""

import sys
import json
import os
import argparse
from typing import Optional, Dict, List

def load_crm_config() -> Dict:
    """Load CRM configuration from config file or environment variables"""
    config = {
        "crm_base_url": os.environ.get("CUDOS_CRM_URL", ""),
        "crm_username": os.environ.get("CUDOS_CRM_USER", ""),
        "crm_password": os.environ.get("CUDOS_CRM_PASSWORD", "")
    }
    
    # If environment variables not set, try config file
    if not all(config.values()):
        config_path = os.path.expanduser("~/.mbtools/crm_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge file config with env vars (env vars take precedence)
                    config["crm_base_url"] = config["crm_base_url"] or file_config.get("crm_base_url", "")
                    config["crm_username"] = config["crm_username"] or file_config.get("crm_username", "")
                    config["crm_password"] = config["crm_password"] or file_config.get("crm_password", "")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}", file=sys.stderr)
    
    return config

def get_crm_urls(config: Dict) -> tuple:
    """Generate CRM URLs from config"""
    base_url = config.get("crm_base_url", "")
    login_url = f"{base_url}/index.php" if base_url else ""
    contacts_url = f"{base_url}/index.php?module=Contacts&view=List" if base_url else ""
    account_url = f"{base_url}/index.php?module=Accounts&view=List" if base_url else ""
    return login_url, contacts_url, account_url

def get_browser_instructions(config: Dict, action: str, query: str = "") -> str:
    """Generate instructions for browser automation"""
    login_url, contacts_url, account_url = get_crm_urls(config)
    username = config.get("crm_username", "")
    password = config.get("crm_password", "")
    
    if action == "search_person":
        return f"""OpenClaw Browser Instructions for Cudos CRM Person Search:

1. Navigate to: {login_url}
2. Login with:
   - Username: {username}
   - Password: {'*' * len(password)}
3. After login, navigate to: {contacts_url}
4. Use the search box to search for: "{query}"
5. Wait for results to load
6. Extract the contact information from the results table
7. Return results as JSON with fields: name, email, phone, company, title
"""
    elif action == "search_company":
        return f"""OpenClaw Browser Instructions for Cudos CRM Company Search:

1. Navigate to: {login_url}
2. Login with:
   - Username: {username}
   - Password: {'*' * len(password)}
3. After login, navigate to: {account_url}
4. Use the search box to search for: "{query}"
5. Wait for results to load
6. Extract the company information from the results table
7. Return results as JSON with fields: company_name, phone, email, website, industry
"""
    else:
        return "Unknown action"

def search_person(config: Dict, query: str) -> None:
    """Search for a person in the CRM"""
    _, contacts_url, _ = get_crm_urls(config)
    username = config.get("crm_username", "")
    password = config.get("crm_password", "")
    
    if not all([contacts_url, username, password]):
        print("Error: CRM configuration missing. Please set up ~/.mbtools/crm_config.json", file=sys.stderr)
        sys.exit(1)
    
    print(f"Searching for person: '{query}'")
    print(f"\nCRM URL: {contacts_url}")
    print(f"Login: {username} / {'*' * len(password)}")
    print("\nNote: This tool provides browser instructions for manual search.")
    print("For automation, use the browser tool with these parameters:\n")
    print(get_browser_instructions(config, "search_person", query))

def search_company(config: Dict, query: str) -> None:
    """Search for a company in the CRM"""
    _, _, account_url = get_crm_urls(config)
    username = config.get("crm_username", "")
    password = config.get("crm_password", "")
    
    if not all([account_url, username, password]):
        print("Error: CRM configuration missing. Please set up ~/.mbtools/crm_config.json", file=sys.stderr)
        sys.exit(1)
    
    print(f"Searching for company: '{query}'")
    print(f"\nCRM URL: {account_url}")
    print(f"Login: {username} / {'*' * len(password)}")
    print("\nNote: This tool provides browser instructions for manual search.")
    print("For automation, use the browser tool with these parameters:\n")
    print(get_browser_instructions(config, "search_company", query))

def show_crm_info(config: Dict) -> None:
    """Display CRM connection information"""
    base_url = config.get("crm_base_url", "")
    login_url, contacts_url, account_url = get_crm_urls(config)
    username = config.get("crm_username", "")
    password = config.get("crm_password", "")
    
    info = {
        "crm_system": "vTiger CRM",
        "base_url": base_url,
        "login_url": login_url,
        "contacts_url": contacts_url,
        "accounts_url": account_url,
        "username": username,
        "password": "***" + password[-4:] if password else "not set",
        "config_source": "environment" if os.environ.get("CUDOS_CRM_URL") else "~/.mbtools/crm_config.json"
    }
    print(json.dumps(info, indent=2))

def main():
    parser = argparse.ArgumentParser(
        description="Cudos CRM Tool - Search persons and companies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s person "Max Mustermann"
  %(prog)s company "Cudos AG"
  %(prog)s info

Configuration:
  Set credentials in ~/.mbtools/crm_config.json or via environment variables:
  - CUDOS_CRM_URL
  - CUDOS_CRM_USER
  - CUDOS_CRM_PASSWORD
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Person search command
    person_parser = subparsers.add_parser("person", help="Search for a person/contact")
    person_parser.add_argument("query", help="Name or keyword to search for")
    
    # Company search command
    company_parser = subparsers.add_parser("company", help="Search for a company/account")
    company_parser.add_argument("query", help="Company name or keyword to search for")
    
    # Info command
    subparsers.add_parser("info", help="Show CRM connection information")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_crm_config()
    
    if args.command == "person":
        search_person(config, args.query)
    elif args.command == "company":
        search_company(config, args.query)
    elif args.command == "info":
        show_crm_info(config)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
