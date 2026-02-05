"""Fuzzy search strategies with retry logic."""

import re
from typing import Callable, List, Optional, Any


class FuzzySearchStrategy:
    """Implements fuzzy search with multiple retry strategies."""

    MAX_RETRIES = 5

    @staticmethod
    def remove_special_chars(text: str) -> str:
        """Remove special characters from text.

        Args:
            text: Input text

        Returns:
            Text with special characters removed
        """
        # Remove characters like *, ?, etc.
        return re.sub(r'[*?+\[\](){}^$|\\]', '', text)

    @staticmethod
    def replace_umlauts(text: str) -> str:
        """Replace German umlauts with ASCII equivalents.

        Args:
            text: Input text

        Returns:
            Text with umlauts replaced (ä→ae, ö→oe, ü→ue, ß→ss)
        """
        replacements = {
            'ä': 'ae', 'Ä': 'Ae',
            'ö': 'oe', 'Ö': 'Oe',
            'ü': 'ue', 'Ü': 'Ue',
            'ß': 'ss'
        }

        result = text
        for umlaut, replacement in replacements.items():
            result = result.replace(umlaut, replacement)

        return result

    @staticmethod
    def shorten_incrementally(text: str) -> List[str]:
        """Generate incrementally shortened versions of text.

        Args:
            text: Input text

        Returns:
            List of shortened variants (e.g., "Müller" → ["Mülle", "Müll"])
        """
        if len(text) <= 3:
            return []

        variants = []
        for length in range(len(text) - 1, 2, -1):
            variants.append(text[:length])

        return variants

    @staticmethod
    async def search_with_retry(
        search_func: Callable[[str], Any],
        search_term: str,
        log_func: Optional[Callable[[str], None]] = None
    ) -> Any:
        """Execute search with multiple retry strategies.

        Retry strategies (max 5 attempts):
        1. Original term
        2. Remove special characters
        3. Shorten incrementally
        4. Replace umlauts
        5. Shorten umlaut-replaced versions

        Args:
            search_func: Async function that performs the search
            search_term: Original search term
            log_func: Optional logging function

        Returns:
            Search results from first successful attempt
        """
        def log(msg: str):
            if log_func:
                log_func(msg)

        attempts = []

        # Strategy 1: Original term
        attempts.append(('original', search_term))

        # Strategy 2: Remove special characters
        cleaned = FuzzySearchStrategy.remove_special_chars(search_term)
        if cleaned != search_term:
            attempts.append(('no_special_chars', cleaned))

        # Strategy 3: Shorten incrementally
        shortened = FuzzySearchStrategy.shorten_incrementally(search_term)
        for variant in shortened[:2]:  # Limit to 2 shortened versions
            attempts.append(('shortened', variant))

        # Strategy 4: Replace umlauts
        no_umlauts = FuzzySearchStrategy.replace_umlauts(search_term)
        if no_umlauts != search_term:
            attempts.append(('no_umlauts', no_umlauts))

        # Strategy 5: Shorten umlaut-replaced versions
        if no_umlauts != search_term:
            umlaut_shortened = FuzzySearchStrategy.shorten_incrementally(no_umlauts)
            for variant in umlaut_shortened[:1]:  # Limit to 1 variant
                attempts.append(('no_umlauts_shortened', variant))

        # Limit to MAX_RETRIES total attempts
        attempts = attempts[:FuzzySearchStrategy.MAX_RETRIES]

        # Try each strategy
        for attempt_num, (strategy, term) in enumerate(attempts, 1):
            log(f"Search attempt {attempt_num}/{len(attempts)} ({strategy}): '{term}'")

            try:
                results = await search_func(term)

                # Check if results found
                if results and (
                    (isinstance(results, list) and len(results) > 0) or
                    (isinstance(results, dict) and results.get('count', 0) > 0)
                ):
                    log(f"✓ Found results with strategy '{strategy}'")
                    return results

                log(f"No results with strategy '{strategy}'")

            except Exception as e:
                log(f"Error with strategy '{strategy}': {e}")
                continue

        # No results found after all attempts
        log("All search strategies exhausted, no results found")
        return [] if isinstance(results, list) else {'count': 0, 'results': []}
