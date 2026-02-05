"""Search operations service."""

from typing import List, Optional
from playwright.async_api import Page

from domain.models import AccountSearchResult, ContactSearchResult, PotentialSearchResult
from domain.page_objects import AccountPage, ContactPage, PotentialPage
from domain.fuzzy_search import FuzzySearchStrategy


class SearchService:
    """Service for search operations with fuzzy search support."""

    def __init__(self, page: Page, log_func=None):
        """Initialize search service.

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

    async def search_account(
        self,
        name: Optional[str] = None,
        city: Optional[str] = None
    ) -> dict:
        """Search for accounts with fuzzy search.

        Args:
            name: Account name to search for
            city: City filter

        Returns:
            Dictionary with 'results' and 'count' keys
        """
        self._log(f"Searching accounts: name={name}, city={city}")

        if not name and not city:
            return {'results': [], 'count': 0}

        # Define search function for fuzzy search
        async def do_search(search_term: str) -> List[AccountSearchResult]:
            return await self.account_page.search(name=search_term, city=city)

        # Use fuzzy search if name is provided
        if name:
            results = await FuzzySearchStrategy.search_with_retry(
                search_func=do_search,
                search_term=name,
                log_func=self._log
            )
        else:
            # Search by city only
            results = await self.account_page.search(name=None, city=city)

        return {
            'results': [
                {
                    'record_id': r.record_id,
                    'name': r.name,
                    'url': r.url,
                    'city': r.city
                }
                for r in results
            ],
            'count': len(results)
        }

    async def search_person(
        self,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        company: Optional[str] = None
    ) -> dict:
        """Search for contacts with fuzzy search.

        Args:
            firstname: First name
            lastname: Last name
            company: Company name

        Returns:
            Dictionary with 'results' and 'count' keys
        """
        self._log(f"Searching contacts: firstname={firstname}, lastname={lastname}, company={company}")

        if not firstname and not lastname and not company:
            return {'results': [], 'count': 0}

        # Define search function for fuzzy search on lastname
        async def do_search(search_term: str) -> List[ContactSearchResult]:
            return await self.contact_page.search(
                firstname=firstname,
                lastname=search_term,
                company=company
            )

        # Use fuzzy search on lastname if provided
        if lastname:
            results = await FuzzySearchStrategy.search_with_retry(
                search_func=do_search,
                search_term=lastname,
                log_func=self._log
            )
        else:
            # Search without lastname
            results = await self.contact_page.search(
                firstname=firstname,
                lastname=None,
                company=company
            )

        return {
            'results': [
                {
                    'record_id': r.record_id,
                    'name': r.name,
                    'url': r.url,
                    'firstname': r.firstname,
                    'lastname': r.lastname,
                    'company': r.company,
                    'email': r.email
                }
                for r in results
            ],
            'count': len(results)
        }

    async def search_potential(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None
    ) -> dict:
        """Search for potentials with fuzzy search.

        Args:
            name: Potential name
            company: Company name
            owner: Owner name
            status: Status filter (inaktiv, gewonnen, verloren, gestorben)

        Returns:
            Dictionary with 'results' and 'count' keys
        """
        self._log(f"Searching potentials: name={name}, company={company}, owner={owner}, status={status}")

        if not name and not company and not owner and not status:
            return {'results': [], 'count': 0}

        # Define search function for fuzzy search on name
        async def do_search(search_term: str) -> List[PotentialSearchResult]:
            return await self.potential_page.search(
                name=search_term,
                company=company,
                owner=owner,
                status=status
            )

        # Use fuzzy search on name if provided
        if name:
            results = await FuzzySearchStrategy.search_with_retry(
                search_func=do_search,
                search_term=name,
                log_func=self._log
            )
        else:
            # Search without name
            results = await self.potential_page.search(
                name=None,
                company=company,
                owner=owner,
                status=status
            )

        return {
            'results': [
                {
                    'record_id': r.record_id,
                    'name': r.name,
                    'url': r.url,
                    'company': r.company,
                    'owner': r.owner,
                    'status': r.status
                }
                for r in results
            ],
            'count': len(results)
        }
