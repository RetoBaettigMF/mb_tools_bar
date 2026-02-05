"""Authentication and credential management for CRM MCP Server."""

import json
import os
from pathlib import Path
from typing import Optional, Dict

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class AuthManager:
    """Manages CRM credentials from multiple sources."""

    def __init__(self):
        """Initialize the authentication manager."""
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self._load_credentials()

    def _load_credentials(self):
        """Load credentials from multiple sources in priority order:
        1. Environment variables (CRM_USERNAME, CRM_PASSWORD)
        2. .env file in repository root
        3. Config file: ~/.config/crm-mcp/credentials.json
        """
        # Priority 1: Environment variables
        self.username = os.environ.get('CRM_USERNAME')
        self.password = os.environ.get('CRM_PASSWORD')

        if self.username and self.password:
            return

        # Priority 2: .env file in repository root
        if DOTENV_AVAILABLE:
            repo_root = Path(__file__).parent.parent.parent
            env_file = repo_root / '.env'
            if env_file.exists():
                load_dotenv(env_file)
                self.username = os.environ.get('CRM_USERNAME')
                self.password = os.environ.get('CRM_PASSWORD')
                if self.username and self.password:
                    return

        # Priority 3: Config file
        config_path = Path.home() / '.config' / 'crm-mcp' / 'credentials.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.username = config.get('username')
                    self.password = config.get('password')
            except (json.JSONDecodeError, IOError):
                pass

    def get_credentials(self) -> Dict[str, str]:
        """Get credentials as a dictionary.

        Returns:
            Dictionary with 'username' and 'password' keys

        Raises:
            ValueError: If credentials are not configured
        """
        if not self.username or not self.password:
            raise ValueError(
                "CRM credentials not configured. Please set CRM_USERNAME and CRM_PASSWORD "
                "environment variables, create a .env file, or run setup_auth.py"
            )

        return {
            'username': self.username,
            'password': self.password
        }

    def has_credentials(self) -> bool:
        """Check if credentials are available.

        Returns:
            True if both username and password are configured
        """
        return bool(self.username and self.password)

    @staticmethod
    def save_credentials(username: str, password: str):
        """Save credentials to config file.

        Args:
            username: CRM username
            password: CRM password
        """
        config_dir = Path.home() / '.config' / 'crm-mcp'
        config_dir.mkdir(parents=True, exist_ok=True)

        config_path = config_dir / 'credentials.json'
        config = {
            'username': username,
            'password': password
        }

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        # Set restrictive permissions (owner read/write only)
        config_path.chmod(0o600)
