"""Page Object Model for CRM web interface."""

import re
from typing import List, Optional, Dict, Any
from playwright.async_api import Page

from domain.models import (
    AccountSearchResult, ContactSearchResult, PotentialSearchResult,
    Comment, CreateResult, UpdateResult
)


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page):
        """Initialize base page.

        Args:
            page: Playwright page instance
        """
        self.page = page

    @staticmethod
    def extract_record_id(url: str) -> Optional[str]:
        """Extract record ID from URL.

        Args:
            url: URL containing record parameter

        Returns:
            Record ID or None if not found
        """
        match = re.search(r'record=(\d+)', url)
        return match.group(1) if match else None

    async def wait_for_load(self):
        """Wait for page to fully load."""
        await self.page.wait_for_load_state('networkidle')

    async def fill_field(self, selector: str, value: str):
        """Fill a form field with value.

        Args:
            selector: CSS selector for the field
            value: Value to fill
        """
        await self.page.fill(selector, value)

    async def click_button(self, selector: str):
        """Click a button.

        Args:
            selector: CSS selector for the button
        """
        await self.page.click(selector)


class AccountPage(BasePage):
    """Page object for Accounts (Companies) module."""

    LIST_URL = 'https://mf250.co.crm-now.de/index.php?module=Accounts&view=List'

    # Selectors based on actual CRM HTML
    SELECTORS = {
        'search_name': 'input[name="accountname"]',
        'search_city': 'input[name="bill_city"]',
        'search_button': 'button[data-trigger="listSearch"]',  # Confirmed working
        'result_table': 'table.listViewEntries',
        'result_row': 'tr.listViewEntries',  # Class is on TR element itself
        'create_button': 'button#Accounts_listView_basicAction_LBL_ADD_RECORD',  # Confirmed correct
        'save_button': 'button[name="saveButton"]',
    }

    async def search(self, name: Optional[str] = None, city: Optional[str] = None) -> List[AccountSearchResult]:
        """Search for accounts.

        Args:
            name: Account/organization name
            city: City (Ort) filter

        Returns:
            List of search results
        """
        # Navigate to list view
        await self.page.goto(self.LIST_URL)
        await self.wait_for_load()

        # Fill search fields
        if name:
            try:
                await self.fill_field(self.SELECTORS['search_name'], name)
            except Exception:
                # Try alternative selector
                await self.fill_field('input[name="search_field_accountname"]', name)

        if city:
            try:
                await self.fill_field(self.SELECTORS['search_city'], city)
            except Exception:
                # Try alternative selector
                await self.fill_field('input[name="search_field_bill_city"]', city)

        # Click search button
        try:
            await self.click_button(self.SELECTORS['search_button'])
        except Exception:
            # Try alternative selector
            await self.click_button('button.btn.searchButton')

        await self.wait_for_load()

        # Parse results
        return await self._parse_search_results()

    async def _parse_search_results(self) -> List[AccountSearchResult]:
        """Parse search results from the table.

        Returns:
            List of account search results
        """
        results = []

        try:
            # Get all result rows (don't wait for table as results are immediate)
            rows = await self.page.query_selector_all(self.SELECTORS['result_row'])

            for row in rows:
                try:
                    # Extract link to detail page
                    link_element = await row.query_selector('a[href*="record="]')
                    if not link_element:
                        continue

                    href = await link_element.get_attribute('href')
                    if not href:
                        continue

                    record_id = self.extract_record_id(href)
                    if not record_id:
                        continue

                    # Extract account name
                    name_text = await link_element.inner_text()
                    name = name_text.strip() if name_text else ''

                    # Extract city (from specific column)
                    city_element = await row.query_selector('td[data-field="bill_city"]')
                    city = None
                    if city_element:
                        city_text = await city_element.inner_text()
                        city = city_text.strip() if city_text else None

                    # Build full URL (handle relative paths)
                    if href.startswith('http'):
                        url = href
                    elif href.startswith('/'):
                        url = f"https://mf250.co.crm-now.de{href}"
                    else:
                        url = f"https://mf250.co.crm-now.de/{href}"

                    results.append(AccountSearchResult(
                        record_id=record_id,
                        name=name,
                        url=url,
                        city=city
                    ))

                except Exception:
                    # Skip rows that can't be parsed
                    continue

        except Exception:
            # No results or table not found
            pass

        return results

    async def create(self, data: Dict[str, Any]) -> CreateResult:
        """Create a new account.

        Args:
            data: Account data (accountname, bill_city, etc.)

        Returns:
            CreateResult with record ID and URL
        """
        # Navigate to list view
        await self.page.goto(self.LIST_URL)
        await self.wait_for_load()

        # Click create button
        try:
            await self.click_button(self.SELECTORS['create_button'])
        except Exception:
            # Try alternative selector
            await self.click_button('button[data-url*="EditView"]')

        await self.wait_for_load()

        # Fill form fields
        for field_name, value in data.items():
            if value:
                try:
                    selector = f'input[name="{field_name}"]'
                    await self.fill_field(selector, str(value))
                except Exception:
                    # Try textarea
                    try:
                        selector = f'textarea[name="{field_name}"]'
                        await self.fill_field(selector, str(value))
                    except Exception:
                        # Field not found, skip
                        continue

        # Save - use form.submit() as button click doesn't work in this CRM
        await self.page.evaluate('document.querySelector("form#EditView").submit()')

        # Wait for navigation to detail view with record ID
        try:
            await self.page.wait_for_url('**/view=Detail**record=**', timeout=10000)
        except Exception:
            pass  # Continue anyway

        await self.wait_for_load()

        # Extract record ID from URL
        current_url = self.page.url
        record_id = self.extract_record_id(current_url)

        if record_id:
            return CreateResult(
                success=True,
                record_id=record_id,
                url=current_url,
                message="Account created successfully"
            )
        else:
            return CreateResult(
                success=False,
                message="Failed to extract record ID after creation"
            )

    async def update_fields(self, record_id: str, updates: Dict[str, Any]) -> UpdateResult:
        """Update account fields.

        Args:
            record_id: Account record ID
            updates: Dictionary of field names and values to update

        Returns:
            UpdateResult with success status
        """
        # Navigate to edit view
        edit_url = f'https://mf250.co.crm-now.de/index.php?module=Accounts&view=Edit&record={record_id}'
        await self.page.goto(edit_url)
        await self.wait_for_load()

        updated_fields = []

        # Update each field
        for field_name, value in updates.items():
            try:
                selector = f'input[name="{field_name}"]'
                await self.fill_field(selector, str(value))
                updated_fields.append(field_name)
            except Exception:
                # Try textarea
                try:
                    selector = f'textarea[name="{field_name}"]'
                    await self.fill_field(selector, str(value))
                    updated_fields.append(field_name)
                except Exception:
                    # Field not found, skip
                    continue

        # Save - use form.submit() as button click doesn't work in this CRM
        await self.page.evaluate('document.querySelector("form#EditView").submit()')
        await self.wait_for_load()

        return UpdateResult(
            success=True,
            record_id=record_id,
            updated_fields=updated_fields,
            message=f"Updated {len(updated_fields)} fields"
        )

    async def get_detail(self, record_id: str) -> Dict[str, Any]:
        """Get account details.

        Args:
            record_id: Account record ID

        Returns:
            Dictionary of account data
        """
        detail_url = f'https://mf250.co.crm-now.de/index.php?module=Accounts&view=Detail&record={record_id}'
        await self.page.goto(detail_url)
        await self.wait_for_load()

        # Extract data from detail view
        # This is a simplified implementation
        data = {'record_id': record_id, 'url': detail_url}

        return data


class ContactPage(BasePage):
    """Page object for Contacts (People) module."""

    LIST_URL = 'https://mf250.co.crm-now.de/index.php?module=Contacts&view=List'

    SELECTORS = {
        'search_firstname': 'input[name="firstname"]',
        'search_lastname': 'input[name="lastname"]',
        'search_company': 'input[name="account_id"]',
        'search_button': 'button[data-trigger="listSearch"]',  # Updated
        'result_table': 'table.listViewEntries',
        'result_row': 'tr.listViewEntries',  # Class on TR element
        'create_button': 'button#Contacts_listView_basicAction_LBL_ADD_RECORD',
        'save_button': 'button[name="saveButton"]',
    }

    async def search(
        self,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        company: Optional[str] = None
    ) -> List[ContactSearchResult]:
        """Search for contacts.

        Args:
            firstname: First name
            lastname: Last name
            company: Company/organization name

        Returns:
            List of search results
        """
        await self.page.goto(self.LIST_URL)
        await self.wait_for_load()

        # Fill search fields
        if firstname:
            try:
                await self.fill_field(self.SELECTORS['search_firstname'], firstname)
            except Exception:
                await self.fill_field('input[name="search_field_firstname"]', firstname)

        if lastname:
            try:
                await self.fill_field(self.SELECTORS['search_lastname'], lastname)
            except Exception:
                await self.fill_field('input[name="search_field_lastname"]', lastname)

        if company:
            try:
                await self.fill_field(self.SELECTORS['search_company'], company)
            except Exception:
                await self.fill_field('input[name="search_field_account_id"]', company)

        # Click search
        try:
            await self.click_button(self.SELECTORS['search_button'])
        except Exception:
            await self.click_button('button.btn.searchButton')

        await self.wait_for_load()

        return await self._parse_search_results()

    async def _parse_search_results(self) -> List[ContactSearchResult]:
        """Parse contact search results."""
        results = []

        try:
            # Get all result rows
            rows = await self.page.query_selector_all(self.SELECTORS['result_row'])

            for row in rows:
                try:
                    link_element = await row.query_selector('a[href*="record="]')
                    if not link_element:
                        continue

                    href = await link_element.get_attribute('href')
                    if not href:
                        continue

                    record_id = self.extract_record_id(href)
                    if not record_id:
                        continue

                    name_text = await link_element.inner_text()
                    name = name_text.strip() if name_text else ''

                    # Try to extract first/last name from full name
                    firstname = None
                    lastname = None
                    if ' ' in name:
                        parts = name.split(' ', 1)
                        firstname = parts[0]
                        lastname = parts[1]

                    # Build full URL (handle relative paths)
                    if href.startswith('http'):
                        url = href
                    elif href.startswith('/'):
                        url = f"https://mf250.co.crm-now.de{href}"
                    else:
                        url = f"https://mf250.co.crm-now.de/{href}"

                    results.append(ContactSearchResult(
                        record_id=record_id,
                        name=name,
                        url=url,
                        firstname=firstname,
                        lastname=lastname
                    ))

                except Exception:
                    continue

        except Exception:
            pass

        return results

    async def create(self, company_id: str, data: Dict[str, Any]) -> CreateResult:
        """Create a new contact linked to a company.

        Args:
            company_id: Account (company) record ID to link to
            data: Contact data (firstname, lastname, email, etc.)

        Returns:
            CreateResult with record ID and URL
        """
        await self.page.goto(self.LIST_URL)
        await self.wait_for_load()

        try:
            await self.click_button(self.SELECTORS['create_button'])
        except Exception:
            await self.click_button('button[data-url*="EditView"]')

        await self.wait_for_load()

        # Link to company
        try:
            await self.fill_field('input[name="account_id"]', company_id)
        except Exception:
            pass

        # Fill contact data
        for field_name, value in data.items():
            if value:
                try:
                    selector = f'input[name="{field_name}"]'
                    await self.fill_field(selector, str(value))
                except Exception:
                    try:
                        selector = f'textarea[name="{field_name}"]'
                        await self.fill_field(selector, str(value))
                    except Exception:
                        continue

        await self.page.evaluate('document.querySelector("form#EditView").submit()')
        await self.wait_for_load()

        current_url = self.page.url
        record_id = self.extract_record_id(current_url)

        if record_id:
            return CreateResult(
                success=True,
                record_id=record_id,
                url=current_url,
                message="Contact created successfully"
            )
        else:
            return CreateResult(
                success=False,
                message="Failed to extract record ID after creation"
            )

    async def update_fields(self, record_id: str, updates: Dict[str, Any]) -> UpdateResult:
        """Update contact fields."""
        edit_url = f'https://mf250.co.crm-now.de/index.php?module=Contacts&view=Edit&record={record_id}'
        await self.page.goto(edit_url)
        await self.wait_for_load()

        updated_fields = []

        for field_name, value in updates.items():
            try:
                selector = f'input[name="{field_name}"]'
                await self.fill_field(selector, str(value))
                updated_fields.append(field_name)
            except Exception:
                try:
                    selector = f'textarea[name="{field_name}"]'
                    await self.fill_field(selector, str(value))
                    updated_fields.append(field_name)
                except Exception:
                    continue

        await self.page.evaluate('document.querySelector("form#EditView").submit()')
        await self.wait_for_load()

        return UpdateResult(
            success=True,
            record_id=record_id,
            updated_fields=updated_fields,
            message=f"Updated {len(updated_fields)} fields"
        )


class PotentialPage(BasePage):
    """Page object for Potentials (Sales) module."""

    LIST_URL = 'https://mf250.co.crm-now.de/index.php?module=Potentials&view=List'

    SELECTORS = {
        'search_name': 'input[name="potentialname"]',
        'search_company': 'input[name="related_to"]',
        'search_owner': 'input[name="assigned_user_id"]',
        'search_status': 'select[name="sales_stage"]',
        'search_button': 'button[data-trigger="listSearch"]',  # Updated
        'result_table': 'table.listViewEntries',
        'result_row': 'tr.listViewEntries',  # Class on TR element
        'create_button': 'button#Potentials_listView_basicAction_LBL_ADD_RECORD',
        'save_button': 'button[name="saveButton"]',
    }

    VALID_STATUS = ["inaktiv", "gewonnen", "verloren", "gestorben", ""]

    async def search(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[PotentialSearchResult]:
        """Search for potentials.

        Args:
            name: Potential name
            company: Company/organization name
            owner: Owner (zuständig)
            status: Status filter (inaktiv, gewonnen, verloren, gestorben)

        Returns:
            List of search results
        """
        await self.page.goto(self.LIST_URL)
        await self.wait_for_load()

        # Fill search fields
        if name:
            try:
                await self.fill_field(self.SELECTORS['search_name'], name)
            except Exception:
                await self.fill_field('input[name="search_field_potentialname"]', name)

        if company:
            try:
                await self.fill_field(self.SELECTORS['search_company'], company)
            except Exception:
                await self.fill_field('input[name="search_field_related_to"]', company)

        if owner:
            try:
                await self.fill_field(self.SELECTORS['search_owner'], owner)
            except Exception:
                await self.fill_field('input[name="search_field_assigned_user_id"]', owner)

        if status and status in self.VALID_STATUS:
            try:
                await self.page.select_option(self.SELECTORS['search_status'], status)
            except Exception:
                pass

        # Click search
        try:
            await self.click_button(self.SELECTORS['search_button'])
        except Exception:
            await self.click_button('button.btn.searchButton')

        await self.wait_for_load()

        return await self._parse_search_results()

    async def _parse_search_results(self) -> List[PotentialSearchResult]:
        """Parse potential search results."""
        results = []

        try:
            await self.page.wait_for_selector(self.SELECTORS['result_table'], timeout=5000)
            rows = await self.page.query_selector_all(self.SELECTORS['result_row'])

            for row in rows:
                try:
                    link_element = await row.query_selector('a[href*="record="]')
                    if not link_element:
                        continue

                    href = await link_element.get_attribute('href')
                    if not href:
                        continue

                    record_id = self.extract_record_id(href)
                    if not record_id:
                        continue

                    name_text = await link_element.text_content()
                    name = name_text.strip() if name_text else ''

                    url = f"https://mf250.co.crm-now.de/{href}" if not href.startswith('http') else href

                    results.append(PotentialSearchResult(
                        record_id=record_id,
                        name=name,
                        url=url
                    ))

                except Exception:
                    continue

        except Exception:
            pass

        return results

    async def create(self, company_id: str, data: Dict[str, Any]) -> CreateResult:
        """Create a new potential linked to a company."""
        await self.page.goto(self.LIST_URL)
        await self.wait_for_load()

        try:
            await self.click_button(self.SELECTORS['create_button'])
        except Exception:
            await self.click_button('button[data-url*="EditView"]')

        await self.wait_for_load()

        # Link to company
        try:
            await self.fill_field('input[name="related_to"]', company_id)
        except Exception:
            pass

        # Fill potential data
        for field_name, value in data.items():
            if value:
                try:
                    selector = f'input[name="{field_name}"]'
                    await self.fill_field(selector, str(value))
                except Exception:
                    try:
                        selector = f'textarea[name="{field_name}"]'
                        await self.fill_field(selector, str(value))
                    except Exception:
                        continue

        await self.page.evaluate('document.querySelector("form#EditView").submit()')
        await self.wait_for_load()

        current_url = self.page.url
        record_id = self.extract_record_id(current_url)

        if record_id:
            return CreateResult(
                success=True,
                record_id=record_id,
                url=current_url,
                message="Potential created successfully"
            )
        else:
            return CreateResult(
                success=False,
                message="Failed to extract record ID after creation"
            )

    async def update_fields(self, record_id: str, updates: Dict[str, Any]) -> UpdateResult:
        """Update potential fields."""
        edit_url = f'https://mf250.co.crm-now.de/index.php?module=Potentials&view=Edit&record={record_id}'
        await self.page.goto(edit_url)
        await self.wait_for_load()

        updated_fields = []

        for field_name, value in updates.items():
            try:
                selector = f'input[name="{field_name}"]'
                await self.fill_field(selector, str(value))
                updated_fields.append(field_name)
            except Exception:
                try:
                    selector = f'textarea[name="{field_name}"]'
                    await self.fill_field(selector, str(value))
                    updated_fields.append(field_name)
                except Exception:
                    continue

        await self.page.evaluate('document.querySelector("form#EditView").submit()')
        await self.wait_for_load()

        return UpdateResult(
            success=True,
            record_id=record_id,
            updated_fields=updated_fields,
            message=f"Updated {len(updated_fields)} fields"
        )


class CommentManager:
    """Manages comments across all modules."""

    def __init__(self, page: Page):
        """Initialize comment manager.

        Args:
            page: Playwright page instance
        """
        self.page = page

    async def get_comments(self, module: str, record_id: str, limit: int = 5) -> List[Comment]:
        """Get comments from a record.

        Args:
            module: Module name (Accounts, Contacts, Potentials)
            record_id: Record ID
            limit: Maximum number of comments to retrieve

        Returns:
            List of comments
        """
        # Navigate to detail view
        detail_url = f'https://mf250.co.crm-now.de/index.php?module={module}&view=Detail&record={record_id}'
        await self.page.goto(detail_url)
        await self.page.wait_for_load_state('networkidle')

        comments = []

        # Placeholder selectors - will need refinement
        try:
            # Try to find comment section
            comment_elements = await self.page.query_selector_all('.commentDiv, .comment, [data-type="comment"]')

            for element in comment_elements[:limit]:
                try:
                    # Extract author
                    author_element = await element.query_selector('.author, .commentAuthor, .user')
                    author = 'Unknown'
                    if author_element:
                        author_text = await author_element.text_content()
                        author = author_text.strip() if author_text else 'Unknown'

                    # Extract date
                    date_element = await element.query_selector('.date, .commentDate, .time')
                    date = ''
                    if date_element:
                        date_text = await date_element.text_content()
                        date = date_text.strip() if date_text else ''

                    # Extract text
                    text_element = await element.query_selector('.commentText, .text, .content')
                    text = ''
                    if text_element:
                        text_content = await text_element.text_content()
                        text = text_content.strip() if text_content else ''

                    comments.append(Comment(
                        author=author,
                        date=date,
                        text=text
                    ))

                except Exception:
                    continue

        except Exception:
            pass

        return comments

    async def add_comment(self, module: str, record_id: str, author: str, text: str) -> bool:
        """Add a comment to a record.

        Args:
            module: Module name (Accounts, Contacts, Potentials)
            record_id: Record ID
            author: Comment author
            text: Comment text

        Returns:
            True if successful
        """
        # Navigate to detail view
        detail_url = f'https://mf250.co.crm-now.de/index.php?module={module}&view=Detail&record={record_id}'
        await self.page.goto(detail_url)
        await self.page.wait_for_load_state('networkidle')

        try:
            # Find comment input field (placeholder selector)
            comment_input = 'textarea[name="commentcontent"], textarea.commentInput, #commentText'
            await self.page.fill(comment_input, text)

            # Click submit button
            submit_button = 'button[name="saveButton"], button.btn.addCommentButton, button[type="submit"]'
            await self.page.click(submit_button)

            await self.page.wait_for_load_state('networkidle')

            return True

        except Exception:
            return False
