"""Playwright browser automation wrapper for CRM."""

import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

# Timeouts in milliseconds
DEFAULT_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 60000  # 60 seconds


class BrowserClient:
    """Manages Playwright browser instance with persistent session."""

    def __init__(self, username: str, password: str, headless: bool = True):
        """Initialize browser client.

        Args:
            username: CRM username for login
            password: CRM password for login
            headless: Whether to run browser in headless mode
        """
        self.username = username
        self.password = password
        self.headless = headless

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # State file for persistent session
        self.state_file = Path('.auth') / 'state.json'

    async def initialize(self):
        """Initialize Playwright and browser with persistent context."""
        self.playwright = await async_playwright().start()

        # Launch Chromium
        self.browser = await self.playwright.chromium.launch(headless=self.headless)

        # Try to load persistent context from saved state
        state_exists = self.state_file.exists()

        if state_exists:
            # Load existing session
            try:
                self.context = await self.browser.new_context(
                    storage_state=str(self.state_file)
                )
            except Exception:
                # If loading fails, create new context
                state_exists = False

        if not state_exists:
            # Create new context
            self.context = await self.browser.new_context()

        # Set default timeouts
        self.context.set_default_timeout(DEFAULT_TIMEOUT)
        self.context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)

        # Create initial page
        self._page = await self.context.new_page()

        # Perform login if no saved state or if state was invalid
        if not state_exists:
            await self._login()

    async def _login(self):
        """Perform initial login to CRM."""
        if not self._page:
            raise RuntimeError("Browser not initialized")

        # Navigate to login page
        await self._page.goto('https://mf250.co.crm-now.de/')

        # Fill login form
        await self._page.fill('input[name="username"]', self.username)
        await self._page.fill('input[name="password"]', self.password)

        # Submit form
        await self._page.click('button[type="submit"]')

        # Wait for navigation to complete
        await self._page.wait_for_load_state('networkidle')

        # Save session state
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        await self.context.storage_state(path=str(self.state_file))

    async def get_page(self) -> Page:
        """Get the current page instance.

        Returns:
            The current Playwright page

        Raises:
            RuntimeError: If browser is not initialized
        """
        if not self._page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        return self._page

    async def navigate(self, url: str):
        """Navigate to a URL.

        Args:
            url: URL to navigate to
        """
        page = await self.get_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

    async def check_session(self) -> bool:
        """Check if session is still valid.

        Returns:
            True if session is valid, False if re-login is needed
        """
        page = await self.get_page()

        # Navigate to a known authenticated page
        await page.goto('https://mf250.co.crm-now.de/index.php?module=Accounts&view=List')

        # Check if redirected to login page
        current_url = page.url
        if 'login' in current_url.lower() or 'index.php?module=Users' in current_url:
            return False

        return True

    async def ensure_logged_in(self):
        """Ensure user is logged in, re-login if session expired."""
        if not await self.check_session():
            # Delete invalid state file
            if self.state_file.exists():
                self.state_file.unlink()

            # Perform login
            await self._login()

    async def close(self):
        """Close browser and cleanup resources."""
        if self._page:
            await self._page.close()
            self._page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
