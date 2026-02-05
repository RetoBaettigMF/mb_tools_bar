"""Update operations service."""

from typing import Dict, Any
from playwright.async_api import Page

from domain.page_objects import AccountPage, ContactPage, PotentialPage


class UpdateService:
    """Service for update operations."""

    def __init__(self, page: Page, log_func=None):
        """Initialize update service.

        Args:
            page: Playwright page instance
            log_func: Optional logging function
        """
        self.page = page
        self.log_func = log_func
        self.account_page = AccountPage(page)
        self.contact_page = ContactPage(page)
        self.potential_page = PotentialPage(page)

    def _log(self, message: str):
        """Log a message if log function is available."""
        if self.log_func:
            self.log_func(message)

    async def update_account(self, record_id: str, updates: Dict[str, Any]) -> dict:
        """Update account fields.

        Args:
            record_id: Account record ID
            updates: Dictionary of field names and values to update

        Returns:
            Dictionary with update result
        """
        if not updates:
            return {
                'success': False,
                'error': 'No fields to update',
                'error_type': 'validation'
            }

        self._log(f"Updating account {record_id}: {list(updates.keys())}")

        try:
            result = await self.account_page.update_fields(record_id, updates)

            return {
                'success': True,
                'data': {
                    'record_id': result.record_id,
                    'updated_fields': result.updated_fields,
                    'message': result.message
                }
            }

        except Exception as e:
            self._log(f"Error updating account: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'update_failed'
            }

    async def update_person(self, record_id: str, updates: Dict[str, Any]) -> dict:
        """Update contact fields.

        Args:
            record_id: Contact record ID
            updates: Dictionary of field names and values to update

        Returns:
            Dictionary with update result
        """
        if not updates:
            return {
                'success': False,
                'error': 'No fields to update',
                'error_type': 'validation'
            }

        self._log(f"Updating contact {record_id}: {list(updates.keys())}")

        try:
            result = await self.contact_page.update_fields(record_id, updates)

            return {
                'success': True,
                'data': {
                    'record_id': result.record_id,
                    'updated_fields': result.updated_fields,
                    'message': result.message
                }
            }

        except Exception as e:
            self._log(f"Error updating contact: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'update_failed'
            }

    async def update_potential(self, record_id: str, updates: Dict[str, Any]) -> dict:
        """Update potential fields.

        Args:
            record_id: Potential record ID
            updates: Dictionary of field names and values to update

        Returns:
            Dictionary with update result
        """
        if not updates:
            return {
                'success': False,
                'error': 'No fields to update',
                'error_type': 'validation'
            }

        self._log(f"Updating potential {record_id}: {list(updates.keys())}")

        try:
            result = await self.potential_page.update_fields(record_id, updates)

            return {
                'success': True,
                'data': {
                    'record_id': result.record_id,
                    'updated_fields': result.updated_fields,
                    'message': result.message
                }
            }

        except Exception as e:
            self._log(f"Error updating potential: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'update_failed'
            }
