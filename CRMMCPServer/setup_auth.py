#!/usr/bin/env python3
"""Setup script for CRM MCP Server authentication."""

import asyncio
import getpass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.auth_manager import AuthManager
from infrastructure.browser_client import BrowserClient


async def test_login(username: str, password: str) -> bool:
    """Test login credentials with Playwright.

    Args:
        username: CRM username
        password: CRM password

    Returns:
        True if login successful, False otherwise
    """
    print("Testing login credentials...")

    client = BrowserClient(username, password, headless=False)

    try:
        await client.initialize()
        print("✓ Login successful!")

        # Save session state
        print(f"✓ Session saved to {client.state_file}")

        return True

    except Exception as e:
        print(f"✗ Login failed: {e}")
        return False

    finally:
        await client.close()


def main():
    """Interactive credential setup."""
    print("=== CRM MCP Server Authentication Setup ===\n")

    # Check if credentials already exist
    auth = AuthManager()
    if auth.has_credentials():
        print("Existing credentials found.")
        response = input("Do you want to update them? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return

    # Prompt for credentials
    print("\nPlease enter your CRM credentials:")
    username = input("Username: ").strip()

    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    password = getpass.getpass("Password: ")

    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)

    # Test login
    print()
    success = asyncio.run(test_login(username, password))

    if not success:
        print("\nSetup failed. Please check your credentials and try again.")
        sys.exit(1)

    # Save credentials
    AuthManager.save_credentials(username, password)
    print(f"\n✓ Credentials saved to ~/.config/crm-mcp/credentials.json")

    print("\nSetup complete! You can now use the CRM MCP server.")
    print("\nTo register with mcporter:")
    print("  mcporter config add crm --command \"python3 $(pwd)/crm-mcp\"")


if __name__ == '__main__':
    main()
