"""Create operations service with duplicate checking."""

from typing import Dict, Any
from playwright.async_api import Page

from domain.page_objects import AccountPage, ContactPage, PotentialPage
from application.search_service import SearchService


class CreateService:
    """Service for create operations with duplicate checking."""

    def __init__(self, page: Page, log_func=None):
        """Initialize create service.

        Args:
            page: Playwright page instance
            log_func: Optional logging function
        """
        self.page = page
        self.log_func = log_func
        self.account_page = AccountPage(page)
        self.contact_page = ContactPage(page)
        self.potential_page = PotentialPage(page)
        self.search_service = SearchService(page, log_func)

    def _log(self, message: str):
        """Log a message if log function is available."""
        if self.log_func:
            self.log_func(message)

    async def create_account(self, data: Dict[str, Any]) -> dict:
        """Create a new account after checking for duplicates.

        Args:
            data: Account data (must include 'accountname')

        Returns:
            Dictionary with creation result or duplicate error
        """
        account_name = data.get('accountname')
        if not account_name:
            return {
                'success': False,
                'error': 'accountname is required',
                'error_type': 'validation'
            }

        self._log(f"Creating account: {account_name}")

        # Check for duplicates
        search_results = await self.search_service.search_account(name=account_name)

        if search_results['count'] > 0:
            self._log(f"Found {search_results['count']} duplicate(s)")
            return {
                'success': False,
                'error': f"Found {search_results['count']} existing account(s) with similar name",
                'error_type': 'duplicate',
                'details': {
                    'duplicates': search_results['results']
                }
            }

        # No duplicates, create account
        self._log("No duplicates found, creating account")
        result = await self.account_page.create(data)

        if result.success:
            return {
                'success': True,
                'data': {
                    'record_id': result.record_id,
                    'url': result.url,
                    'message': result.message
                }
            }
        else:
            return {
                'success': False,
                'error': result.message or 'Failed to create account',
                'error_type': 'create_failed'
            }

    async def create_person(self, company_id: str, data: Dict[str, Any]) -> dict:
        """Create a new contact after checking for duplicates.

        Args:
            company_id: Account (company) record ID to link to
            data: Contact data (should include 'firstname', 'lastname')

        Returns:
            Dictionary with creation result or duplicate error
        """
        firstname = data.get('firstname')
        lastname = data.get('lastname')

        if not firstname and not lastname:
            return {
                'success': False,
                'error': 'firstname or lastname is required',
                'error_type': 'validation'
            }

        self._log(f"Creating contact: {firstname} {lastname}")

        # Check for duplicates
        search_results = await self.search_service.search_person(
            firstname=firstname,
            lastname=lastname
        )

        if search_results['count'] > 0:
            self._log(f"Found {search_results['count']} duplicate(s)")
            return {
                'success': False,
                'error': f"Found {search_results['count']} existing contact(s) with similar name",
                'error_type': 'duplicate',
                'details': {
                    'duplicates': search_results['results']
                }
            }

        # No duplicates, create contact
        self._log("No duplicates found, creating contact")
        result = await self.contact_page.create(company_id, data)

        if result.success:
            return {
                'success': True,
                'data': {
                    'record_id': result.record_id,
                    'url': result.url,
                    'message': result.message
                }
            }
        else:
            return {
                'success': False,
                'error': result.message or 'Failed to create contact',
                'error_type': 'create_failed'
            }

    async def create_potential(self, company_id: str, data: Dict[str, Any]) -> dict:
        """Create a new potential linked to a company.

        Args:
            company_id: Account (company) record ID to link to
            data: Potential data (should include 'potentialname')

        Returns:
            Dictionary with creation result
        """
        potential_name = data.get('potentialname')
        if not potential_name:
            return {
                'success': False,
                'error': 'potentialname is required',
                'error_type': 'validation'
            }

        self._log(f"Creating potential: {potential_name}")

        # Note: Not checking for duplicates on potentials as per typical CRM workflow
        # (multiple potentials with same name are often valid)

        result = await self.potential_page.create(company_id, data)

        if result.success:
            return {
                'success': True,
                'data': {
                    'record_id': result.record_id,
                    'url': result.url,
                    'message': result.message
                }
            }
        else:
            return {
                'success': False,
                'error': result.message or 'Failed to create potential',
                'error_type': 'create_failed'
            }
