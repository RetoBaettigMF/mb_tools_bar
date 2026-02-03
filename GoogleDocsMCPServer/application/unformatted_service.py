"""Service for unformatted (plain text) document operations."""

from typing import Optional

from infrastructure.google_docs_client import GoogleDocsClient
from domain.text_operations import TextOperations


class UnformattedDocumentService:
    """Handles plain text operations on Google Docs."""

    def __init__(self, client: GoogleDocsClient):
        """Initialize service.

        Args:
            client: GoogleDocsClient instance
        """
        self.client = client

    def read_document(
        self,
        doc_id: str,
        start_line: int = 1,
        max_lines: int = 100
    ) -> dict:
        """Read document with pagination.

        Args:
            doc_id: Google Doc ID
            start_line: Starting line number (1-based)
            max_lines: Maximum lines to return

        Returns:
            Dictionary with document content and pagination metadata
        """
        try:
            doc = self.client.get_document(doc_id)
            text = self.client.extract_text_content(doc)
            title = doc.get('title', 'Unknown')

            result = TextOperations.paginate_text(
                text, title, start_line, max_lines
            )

            return {
                "title": result.title,
                "totalLines": result.total_lines,
                "startLine": result.start_line,
                "endLine": result.end_line,
                "remainingLines": result.total_lines - result.end_line,
                "hasMore": result.has_more,
                "nextStartLine": result.next_start_line,
                "content": result.content
            }
        except Exception as e:
            return {"error": str(e)}

    def write_text(
        self,
        doc_id: str,
        text: str,
        position: str = 'end',
        index: Optional[int] = None
    ) -> dict:
        """Write text to document (unified append/insert operation).

        Args:
            doc_id: Google Doc ID
            text: Text to write
            position: 'start', 'end', or ignored if index is provided
            index: Custom index (takes precedence over position)

        Returns:
            Dictionary with operation result
        """
        try:
            doc_length = self.client.get_document_end_index(doc_id)

            # Calculate insertion index
            if index is not None:
                insert_index = index
            else:
                insert_index = TextOperations.calculate_insertion_index(
                    doc_length, position, index
                )

            # Insert text
            self.client.insert_text(doc_id, text, insert_index)

            return {
                "success": True,
                "insertedCharacters": len(text),
                "startIndex": insert_index,
                "endIndex": insert_index + len(text)
            }
        except Exception as e:
            return {"error": str(e)}

    def replace_text(
        self,
        doc_id: str,
        old_text: str,
        new_text: str
    ) -> dict:
        """Replace all occurrences of text.

        Args:
            doc_id: Google Doc ID
            old_text: Text to find
            new_text: Replacement text

        Returns:
            Dictionary with replacement count
        """
        try:
            result = self.client.replace_all_text(doc_id, old_text, new_text)

            replacements = result.get('replies', [{}])[0].get(
                'replaceAllText', {}
            ).get('occurrencesChanged', 0)

            return {
                "success": True,
                "replacements": replacements
            }
        except Exception as e:
            return {"error": str(e)}
