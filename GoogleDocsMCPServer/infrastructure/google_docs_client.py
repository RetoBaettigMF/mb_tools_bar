"""Google Docs API client wrapper."""

from typing import List, Dict, Any, Optional

from googleapiclient.discovery import build

from infrastructure.auth_manager import AuthManager


class GoogleDocsClient:
    """Wrapper for Google Docs API operations."""

    def __init__(self, auth_manager: AuthManager):
        """Initialize client with auth manager.

        Args:
            auth_manager: AuthManager instance for obtaining credentials
        """
        self.auth_manager = auth_manager
        self._service = None

    @property
    def service(self):
        """Lazy-load Google Docs service."""
        if self._service is None:
            creds = self.auth_manager.get_credentials()
            self._service = build('docs', 'v1', credentials=creds)
        return self._service

    def get_document(self, doc_id: str) -> dict:
        """Fetch document structure.

        Args:
            doc_id: Google Doc ID

        Returns:
            Document structure from API
        """
        return self.service.documents().get(documentId=doc_id).execute()

    def extract_text_content(self, doc: dict) -> str:
        """Extract plain text from document structure.

        Args:
            doc: Document structure from API

        Returns:
            Plain text content
        """
        content = doc.get('body', {}).get('content', [])
        return self._extract_text_recursive(content)

    def _extract_text_recursive(self, elements: List[dict]) -> str:
        """Recursively extract text from document elements."""
        text = ""
        for element in elements:
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text += elem['textRun'].get('content', '')
            elif 'table' in element:
                for row in element['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        cell_content = cell.get('content', [])
                        text += self._extract_text_recursive(cell_content)
        return text

    def extract_formatted_structure(self, doc: dict) -> List[Dict[str, Any]]:
        """Extract text with formatting metadata, including tables.

        Args:
            doc: Document structure from API

        Returns:
            List of formatted text segments with metadata:
            {
                'text': str,
                'style': str (HEADING_1, HEADING_2, etc.),
                'bold': bool,
                'italic': bool,
                'list_type': Optional[str] (BULLET, DECIMAL, etc.)
            }
            OR for tables:
            {
                'type': 'table',
                'rows': [[[{'text': '...', 'bold': bool, 'italic': bool}, ...], ...], ...]
            }
        """
        content = doc.get('body', {}).get('content', [])
        formatted_segments = []

        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                para_style = paragraph.get('paragraphStyle', {})
                named_style = para_style.get('namedStyleType', 'NORMAL_TEXT')

                # Check for list
                bullet = para_style.get('bullet')
                list_type = None
                if bullet:
                    list_id = bullet.get('listId')
                    nesting_level = bullet.get('nestingLevel', 0)
                    # Get glyph type from the bullet
                    lists = doc.get('lists', {})
                    if list_id and list_id in lists:
                        list_props = lists[list_id]
                        level_props = list_props.get('listProperties', {}).get(
                            'nestingLevels', []
                        )
                        if nesting_level < len(level_props):
                            glyph_type = level_props[nesting_level].get('glyphType')
                            list_type = glyph_type

                # Extract text runs with styles
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_run = elem['textRun']
                        text = text_run.get('content', '')
                        text_style = text_run.get('textStyle', {})

                        formatted_segments.append({
                            'text': text,
                            'style': named_style,
                            'bold': text_style.get('bold', False),
                            'italic': text_style.get('italic', False),
                            'list_type': list_type
                        })

            elif 'table' in element:
                # Extract table structure
                table_segment = self._extract_table_structure(element['table'])
                formatted_segments.append(table_segment)

        return formatted_segments

    def _extract_table_structure(self, table: dict) -> Dict[str, Any]:
        """Extract table as structured data with formatting.

        Returns:
            {
                'type': 'table',
                'rows': [
                    [  # Row 0 (header)
                        [{'text': '...', 'bold': bool, 'italic': bool}, ...],  # Cell 0
                        [{'text': '...', 'bold': bool, 'italic': bool}, ...],  # Cell 1
                    ],
                    [  # Row 1
                        [{'text': '...', 'bold': bool, 'italic': bool}, ...],
                    ],
                ]
            }
        """
        rows_data = []

        for table_row in table.get('tableRows', []):
            row_cells = []

            for table_cell in table_row.get('tableCells', []):
                # Extract cell content with formatting
                cell_content = table_cell.get('content', [])
                cell_segments = self._extract_cell_formatted_text(cell_content)
                row_cells.append(cell_segments)

            rows_data.append(row_cells)

        return {
            'type': 'table',
            'rows': rows_data
        }

    def _extract_cell_formatted_text(
        self, cell_content: List[dict]
    ) -> List[Dict[str, Any]]:
        """Extract formatted text segments from a table cell.

        Returns:
            List of {'text': str, 'bold': bool, 'italic': bool}
        """
        segments = []

        for element in cell_content:
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text_run = elem['textRun']
                        text = text_run.get('content', '').rstrip('\n')  # Strip paragraph newline

                        if text:  # Only include non-empty segments
                            text_style = text_run.get('textStyle', {})
                            segments.append({
                                'text': text,
                                'bold': text_style.get('bold', False),
                                'italic': text_style.get('italic', False)
                            })

        return segments

    def batch_update(self, doc_id: str, requests: List[dict]) -> dict:
        """Execute batch update requests.

        Args:
            doc_id: Google Doc ID
            requests: List of API request objects

        Returns:
            API response
        """
        return self.service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

    def insert_text(self, doc_id: str, text: str, index: int) -> dict:
        """Simple text insertion.

        Args:
            doc_id: Google Doc ID
            text: Text to insert
            index: Position index

        Returns:
            API response
        """
        requests = [{
            'insertText': {
                'location': {'index': index},
                'text': text
            }
        }]
        return self.batch_update(doc_id, requests)

    def replace_all_text(self, doc_id: str, old_text: str, new_text: str) -> dict:
        """Replace all occurrences of text.

        Args:
            doc_id: Google Doc ID
            old_text: Text to find
            new_text: Replacement text

        Returns:
            API response with occurrences changed
        """
        requests = [{
            'replaceAllText': {
                'containsText': {
                    'text': old_text,
                    'matchCase': True
                },
                'replaceText': new_text
            }
        }]
        return self.batch_update(doc_id, requests)

    def get_document_end_index(self, doc_id: str) -> int:
        """Get the end index of the document.

        Args:
            doc_id: Google Doc ID

        Returns:
            End index of document
        """
        doc = self.get_document(doc_id)
        return doc.get('body', {}).get('content', [{}])[-1].get('endIndex', 1)
