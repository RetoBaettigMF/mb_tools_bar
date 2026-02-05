"""Comment operations service."""

from typing import Optional
from playwright.async_api import Page

from domain.page_objects import CommentManager


class CommentService:
    """Service for comment operations."""

    def __init__(self, page: Page, log_func=None):
        """Initialize comment service.

        Args:
            page: Playwright page instance
            log_func: Optional logging function
        """
        self.page = page
        self.log_func = log_func
        self.comment_manager = CommentManager(page)

    def _log(self, message: str):
        """Log a message if log function is available."""
        if self.log_func:
            self.log_func(message)

    async def get_comments(self, account_id: str, limit: int = 5) -> dict:
        """Get comments from an account.

        Args:
            account_id: Account record ID
            limit: Maximum number of comments to retrieve

        Returns:
            Dictionary with comments list and count
        """
        self._log(f"Getting comments for account {account_id}, limit={limit}")

        try:
            comments = await self.comment_manager.get_comments(
                module='Accounts',
                record_id=account_id,
                limit=limit
            )

            return {
                'success': True,
                'data': {
                    'record_id': account_id,
                    'comments': [
                        {
                            'author': c.author,
                            'date': c.date,
                            'text': c.text
                        }
                        for c in comments
                    ],
                    'count': len(comments)
                }
            }

        except Exception as e:
            self._log(f"Error getting comments: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'fetch_failed'
            }

    async def add_comment_to_account(
        self,
        account_id: str,
        author: str,
        text: str
    ) -> dict:
        """Add a comment to an account.

        Args:
            account_id: Account record ID
            author: Comment author
            text: Comment text

        Returns:
            Dictionary with success status
        """
        if not text:
            return {
                'success': False,
                'error': 'Comment text is required',
                'error_type': 'validation'
            }

        self._log(f"Adding comment to account {account_id} by {author}")

        try:
            success = await self.comment_manager.add_comment(
                module='Accounts',
                record_id=account_id,
                author=author,
                text=text
            )

            if success:
                return {
                    'success': True,
                    'data': {
                        'message': 'Comment added successfully',
                        'record_id': account_id
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add comment',
                    'error_type': 'add_failed'
                }

        except Exception as e:
            self._log(f"Error adding comment: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'add_failed'
            }
