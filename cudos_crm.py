#!/usr/bin/env python3
"""
Cudos CRM Tool - vTiger CRM Integration
Search for persons and companies in the Cudos CRM system.
"""

import sys
import json
import argparse
from typing import Optional, Dict, List

# CRM Configuration
CRM_BASE_URL = "https://mf250.co.crm-now.de"
CRM_LOGIN_URL = f"{CRM_BASE_URL}/index.php"
CRM_CONTACTS_URL = f"{CRM_BASE_URL}/index.php?module=Contacts&view=List"
CRM_ACCOUNT_URL = f"{CRM_BASE_URL}/index.php?module=Accounts&view=List"

# Credentials
CRM_USER = "bar"
CRM_PASSWORD = "Reb@g96vtig"

def get_browser_instructions(action: str, query: str = "") -> str:
    """Generate instructions for browser automation"""
    if action == "search_person":
        return f"""OpenClaw Browser Instructions for Cudos CRM Person Search:

1. Navigate to: {CRM_LOGIN_URL}
2. Login with:
   - Username: {CRM_USER}
   - Password: {CRM_PASSWORD}
3. After login, navigate to: {CRM_CONTACTS_URL}
4. Use the search box to search for: "{query}"
5. Wait for results to load
6. Extract the contact information from the results table
7. Return results as JSON with fields: name, email, phone, company, title
"""
    elif action == "search_company":
        return f"""OpenClaw Browser Instructions for Cudos CRM Company Search:

1. Navigate to: {CRM_LOGIN_URL}
2. Login with:
   - Username: {CRM_USER}
   - Password: {CRM_PASSWORD}
3. After login, navigate to: {CRM_ACCOUNT_URL}
4. Use the search box to search for: "{query}"
5. Wait for results to load
6. Extract the company information from the results table
7. Return results as JSON with fields: company_name, phone, email, website, industry
"""
    else:
        return "Unknown action"

def search_person(query: str) -> None:
    """Search for a person in the CRM"""
    print(f"Searching for person: '{query}'")
    print(f"\nCRM URL: {CRM_CONTACTS_URL}")
    print(f"Login: {CRM_USER} / {'*' * len(CRM_PASSWORD)}")
    print("\nNote: This tool provides browser instructions for manual search.")
    print("For automation, use the browser tool with these parameters:\n")
    print(get_browser_instructions("search_person", query))

def search_company(query: str) -> None:
    """Search for a company in the CRM"""
    print(f"Searching for company: '{query}'")
    print(f"\nCRM URL: {CRM_ACCOUNT_URL}")
    print(f"Login: {CRM_USER} / {'*' * len(CRM_PASSWORD)}")
    print("\nNote: This tool provides browser instructions for manual search.")
    print("For automation, use the browser tool with these parameters:\n")
    print(get_browser_instructions("search_company", query))

def show_crm_info() -> None:
    """Display CRM connection information"""
    info = {
        "crm_system": "vTiger CRM",
        "base_url": CRM_BASE_URL,
        "login_url": CRM_LOGIN_URL,
        "contacts_url": CRM_CONTACTS_URL,
        "accounts_url": CRM_ACCOUNT_URL,
        "username": CRM_USER,
        "password": "***" + CRM_PASSWORD[-4:]  # Show last 4 chars only
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

Note: This tool provides quick access to CRM URLs and credentials.
For automated searches, use OpenClaw's browser tool.
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
    
    if args.command == "person":
        search_person(args.query)
    elif args.command == "company":
        search_company(args.query)
    elif args.command == "info":
        show_crm_info()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
