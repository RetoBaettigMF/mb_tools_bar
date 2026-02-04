"""Service for formatted (Markdown) document operations."""

from typing import Optional

from infrastructure.google_docs_client import GoogleDocsClient
from domain.markdown_parser import MarkdownParser
from domain.text_operations import TextOperations


class FormattedDocumentService:
    """Handles Markdown-formatted operations on Google Docs."""

    def __init__(self, client: GoogleDocsClient, parser: MarkdownParser):
        """Initialize service.

        Args:
            client: GoogleDocsClient instance
            parser: MarkdownParser instance
        """
        self.client = client
        self.parser = parser

    def read_as_markdown(
        self,
        doc_id: str,
        start_line: int = 1,
        max_lines: int = 100
    ) -> dict:
        """Read document with formatting converted to Markdown.

        Args:
            doc_id: Google Doc ID
            start_line: Starting line number (1-based)
            max_lines: Maximum lines to return

        Returns:
            Dictionary with Markdown content and pagination metadata
        """
        try:
            doc = self.client.get_document(doc_id)
            title = doc.get('title', 'Unknown')

            # Extract formatted structure
            formatted_segments = self.client.extract_formatted_structure(doc)

            # Convert to Markdown
            markdown_text = self.parser.convert_docs_to_markdown(formatted_segments)

            # Paginate
            result = TextOperations.paginate_text(
                markdown_text, title, start_line, max_lines
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

    def write_markdown(
        self,
        doc_id: str,
        markdown: str,
        position: str = 'end',
        index: Optional[int] = None
    ) -> dict:
        """Write text with Markdown formatting, including tables.

        Args:
            doc_id: Google Doc ID
            markdown: Markdown-formatted text
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

            # Parse Markdown
            parse_result = self.parser.parse_markdown_to_formatting(markdown)

            # Phase 1: Insert plain text (non-table content)
            requests = []
            if parse_result.plain_text:
                requests.append({
                    'insertText': {
                        'location': {'index': insert_index},
                        'text': parse_result.plain_text
                    }
                })

            # Phase 2: Apply text formatting (adjusted indices)
            for req in parse_result.formatting_requests:
                # Deep copy and adjust indices
                adjusted_req = self._adjust_request_indices(
                    req, insert_index - 1
                )
                requests.append(adjusted_req)

            # Execute initial batch (text + basic formatting)
            if requests:
                self.client.batch_update(doc_id, requests)

            # Phase 3: Insert tables (requires document structure for cell indices)
            if parse_result.tables:
                for table_data in parse_result.tables:
                    table_insert_index = insert_index + table_data.insertion_index - 1

                    # Create table
                    insert_request, cell_data = self.parser._create_table_requests(
                        table_data, table_insert_index
                    )

                    self.client.batch_update(doc_id, [insert_request])

                    # Get updated document structure
                    doc = self.client.get_document(doc_id)

                    # Populate cells
                    cell_requests = self.parser._create_cell_update_requests(
                        cell_data, table_insert_index, doc
                    )

                    if cell_requests:
                        self.client.batch_update(doc_id, cell_requests)

            return {
                "success": True,
                "insertedCharacters": len(parse_result.plain_text),
                "startIndex": insert_index,
                "endIndex": insert_index + len(parse_result.plain_text)
            }
        except Exception as e:
            return {"error": str(e)}

    def replace_with_markdown(
        self,
        doc_id: str,
        old_text: str,
        new_markdown: str
    ) -> dict:
        """Replace text and apply Markdown formatting.

        Args:
            doc_id: Google Doc ID
            old_text: Text to find
            new_markdown: Replacement text with Markdown formatting

        Returns:
            Dictionary with operation result
        """
        try:
            # Get document to find text position
            doc = self.client.get_document(doc_id)
            full_text = self.client.extract_text_content(doc)

            # Find text position
            pos = full_text.find(old_text)
            if pos == -1:
                return {"error": f"Text not found: {old_text}"}

            start_index = pos + 1  # Google Docs uses 1-based indexing
            end_index = start_index + len(old_text)

            # Parse new Markdown
            parse_result = self.parser.parse_markdown_to_formatting(new_markdown)

            # Build requests: delete old text, insert new text, apply formatting
            requests = [
                {
                    'deleteContentRange': {
                        'range': {
                            'startIndex': start_index,
                            'endIndex': end_index
                        }
                    }
                },
                {
                    'insertText': {
                        'location': {'index': start_index},
                        'text': parse_result.plain_text
                    }
                }
            ]

            # Add formatting requests with adjusted indices
            for req in parse_result.formatting_requests:
                adjusted_req = self._adjust_request_indices(
                    req, start_index - 1
                )
                requests.append(adjusted_req)

            # Execute batch update
            self.client.batch_update(doc_id, requests)

            return {
                "success": True,
                "replacedText": old_text,
                "insertedCharacters": len(parse_result.plain_text),
                "startIndex": start_index,
                "endIndex": start_index + len(parse_result.plain_text)
            }
        except Exception as e:
            return {"error": str(e)}

    def format_existing_text(
        self,
        doc_id: str,
        text: str,
        style: str
    ) -> dict:
        """Apply formatting to existing text.

        Args:
            doc_id: Google Doc ID
            text: Text to find and format
            style: Style to apply ('heading1', 'heading2', 'heading3', 'normal')

        Returns:
            Dictionary with operation result
        """
        try:
            # Get document to find text position
            doc = self.client.get_document(doc_id)
            full_text = self.client.extract_text_content(doc)

            # Find text position
            pos = full_text.find(text)
            if pos == -1:
                return {"error": f"Text not found: {text}"}

            start_index = pos + 1  # Google Docs uses 1-based indexing
            end_index = start_index + len(text)

            # Map style to Google Docs style name
            style_map = {
                'heading1': 'HEADING_1',
                'heading2': 'HEADING_2',
                'heading3': 'HEADING_3',
                'normal': 'NORMAL_TEXT'
            }

            if style not in style_map:
                return {"error": f"Invalid style: {style}"}

            style_name = style_map[style]

            # Build update request
            requests = [{
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index
                    },
                    'paragraphStyle': {
                        'namedStyleType': style_name
                    },
                    'fields': 'namedStyleType'
                }
            }]

            # Execute batch update
            self.client.batch_update(doc_id, requests)

            return {
                "success": True,
                "formattedText": text,
                "style": style_name,
                "startIndex": start_index,
                "endIndex": end_index
            }
        except Exception as e:
            return {"error": str(e)}

    def _adjust_request_indices(self, request: dict, offset: int) -> dict:
        """Adjust indices in a formatting request.

        Args:
            request: Original request dict
            offset: Offset to add to indices

        Returns:
            New request dict with adjusted indices
        """
        import copy
        adjusted = copy.deepcopy(request)

        # Handle different request types
        for key in ['updateParagraphStyle', 'updateTextStyle', 'createParagraphBullets']:
            if key in adjusted:
                range_obj = adjusted[key].get('range', {})
                if 'startIndex' in range_obj:
                    range_obj['startIndex'] += offset
                if 'endIndex' in range_obj:
                    range_obj['endIndex'] += offset

        return adjusted
