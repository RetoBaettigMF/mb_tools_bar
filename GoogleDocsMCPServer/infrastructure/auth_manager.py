"""Authentication manager for Google Docs API."""

import json
import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class AuthManager:
    """Manages OAuth credentials for Google Docs API."""

    SCOPES = ['https://www.googleapis.com/auth/documents']
    TOKEN_PATH = os.path.expanduser('~/.config/gogcli/tokens/bar.ai.bot@cudos.ch.json')
    CREDENTIALS_PATH = os.path.expanduser('~/.config/gogcli/credentials.json')

    def __init__(self, log_func=None):
        """Initialize auth manager.

        Args:
            log_func: Optional logging function (defaults to no-op)
        """
        self.log = log_func if log_func else lambda msg: None

    def get_credentials(self) -> Credentials:
        """Get valid credentials, refreshing if necessary.

        Returns:
            Valid Google OAuth credentials

        Raises:
            Exception: If credentials cannot be obtained
        """
        creds = self._load_existing_credentials()

        if creds and not creds.valid:
            creds = self._refresh_credentials(creds)

        if not creds:
            creds = self._perform_oauth_flow()

        if not creds or not creds.valid:
            raise Exception("Could not obtain valid credentials.")

        return creds

    def _load_existing_credentials(self) -> Optional[Credentials]:
        """Load credentials from token file."""
        if not os.path.exists(self.TOKEN_PATH):
            return None

        try:
            with open(self.TOKEN_PATH, 'r') as f:
                token_data = json.load(f)
            return Credentials.from_authorized_user_info(token_data, self.SCOPES)
        except Exception as e:
            self.log(f"Warning: Could not load gog token: {e}")
            return None

    def _refresh_credentials(self, creds: Credentials) -> Optional[Credentials]:
        """Refresh expired credentials."""
        if not (creds.expired and creds.refresh_token):
            return None

        try:
            self.log("Refreshing expired token...")
            creds.refresh(Request())

            # Save refreshed token
            with open(self.TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())

            self.log("Token refreshed successfully")
            return creds
        except Exception as e:
            self.log(f"Warning: Could not refresh token: {e}")
            return None

    def _perform_oauth_flow(self) -> Optional[Credentials]:
        """Perform OAuth flow to get new credentials."""
        if not os.path.exists(self.CREDENTIALS_PATH):
            raise Exception("No credentials found. Please run setup_auth.py first.")

        self.log("Starting OAuth flow (this will open a browser)...")
        flow = InstalledAppFlow.from_client_secrets_file(
            self.CREDENTIALS_PATH,
            self.SCOPES
        )
        creds = flow.run_local_server(port=0)

        # Save for future use
        os.makedirs(os.path.dirname(self.TOKEN_PATH), exist_ok=True)
        with open(self.TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

        return creds
