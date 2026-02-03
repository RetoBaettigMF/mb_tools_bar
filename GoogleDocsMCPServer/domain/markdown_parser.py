"""Markdown parser for bidirectional conversion with Google Docs formatting."""

import re
from typing import List, Dict, Tuple, Any

from domain.models import MarkdownParseResult


class MarkdownParser:
    """Parse Markdown to Google Docs formatting and vice versa."""

    # Regex patterns
    HEADING_PATTERN = re.compile(r'^(#{1,3})\s+(.+)$')
    BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*')
    ITALIC_PATTERN = re.compile(r'(?<!\*)\*([^\*]+?)\*(?!\*)')  # Negative lookbehind/ahead to avoid matching **
    UNORDERED_LIST_PATTERN = re.compile(r'^-\s+(.+)$')
    ORDERED_LIST_PATTERN = re.compile(r'^\d+\.\s+(.+)$')
    CODE_PATTERN = re.compile(r'```(.+?)```')

    def parse_markdown_to_formatting(self, markdown: str) -> MarkdownParseResult:
        """Parse Markdown string into plain text and formatting requests.

        Args:
            markdown: Markdown-formatted text

        Returns:
            MarkdownParseResult with plain text and formatting requests
        """
        lines = markdown.split('\n')
        requests = []
        plain_lines = []
        current_index = 1  # Google Docs uses 1-based indexing

        for line in lines:
            if not line:
                # Empty line
                plain_lines.append('')
                current_index += 1
                continue

            # Check for heading
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                plain_lines.append(content)

                # Create heading style request
                line_length = len(content) + 1  # +1 for newline
                requests.extend(
                    self._create_heading_requests(content, level, current_index)
                )
                current_index += line_length
                continue

            # Check for unordered list
            unordered_match = self.UNORDERED_LIST_PATTERN.match(line)
            if unordered_match:
                content = unordered_match.group(1)
                plain_lines.append(content)

                line_length = len(content) + 1
                requests.extend(
                    self._create_list_requests(content, 'BULLET', current_index)
                )
                current_index += line_length
                continue

            # Check for ordered list
            ordered_match = self.ORDERED_LIST_PATTERN.match(line)
            if ordered_match:
                content = ordered_match.group(1)
                plain_lines.append(content)

                line_length = len(content) + 1
                requests.extend(
                    self._create_list_requests(content, 'DECIMAL', current_index)
                )
                current_index += line_length
                continue

            # Regular text - handle inline formatting
            plain_line, inline_requests = self._parse_inline_formatting(
                line, current_index
            )
            plain_lines.append(plain_line)

            # Add normal paragraph style FIRST (must come before text styles)
            line_length = len(plain_line) + 1
            requests.append({
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + line_length
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'NORMAL_TEXT'
                    },
                    'fields': 'namedStyleType'
                }
            })

            # Then add text styles (bold, italic, etc.)
            requests.extend(inline_requests)

            current_index += line_length

        plain_text = '\n'.join(plain_lines)
        if plain_text and not plain_text.endswith('\n'):
            plain_text += '\n'

        return MarkdownParseResult(
            plain_text=plain_text,
            formatting_requests=requests
        )

    def _parse_inline_formatting(
        self, line: str, start_index: int
    ) -> Tuple[str, List[dict]]:
        """Parse inline formatting (bold, italic, code) from a line.

        Args:
            line: Line of text with inline Markdown
            start_index: Starting index in document

        Returns:
            Tuple of (plain text, formatting requests)
        """
        requests = []

        # Build plain text and track formatting positions
        # We need to process the string while tracking position changes

        # First, find all formatting markers and their positions
        markers = []

        # Find code blocks
        for match in self.CODE_PATTERN.finditer(line):
            markers.append({
                'start': match.start(),
                'end': match.end(),
                'type': 'code',
                'text': match.group(1),
                'marker_len': 6  # ```...```
            })

        # Find bold
        for match in self.BOLD_PATTERN.finditer(line):
            # Check if it's inside a code block
            in_code = any(m['start'] < match.start() < m['end'] for m in markers if m['type'] == 'code')
            if not in_code:
                markers.append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'bold',
                    'text': match.group(1),
                    'marker_len': 4  # **...**
                })

        # Find italic
        for match in self.ITALIC_PATTERN.finditer(line):
            # Check if it's inside code or bold
            in_other = any(m['start'] < match.start() < m['end'] for m in markers)
            if not in_other:
                markers.append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'italic',
                    'text': match.group(1),
                    'marker_len': 2  # *...*
                })

        # Sort markers by position
        markers.sort(key=lambda x: x['start'])

        # Build plain text and calculate formatting positions
        plain_parts = []
        last_pos = 0
        offset = 0  # Tracks how many characters we've removed

        for marker in markers:
            # Add text before this marker
            plain_parts.append(line[last_pos:marker['start']])

            # Add the formatted text (without markers)
            formatted_text = marker['text']
            plain_parts.append(formatted_text)

            # Calculate position in plain text
            plain_start = marker['start'] - offset
            plain_end = plain_start + len(formatted_text)

            # Create formatting request
            if marker['type'] == 'code':
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': start_index + plain_start,
                            'endIndex': start_index + plain_end
                        },
                        'textStyle': {
                            'weightedFontFamily': {
                                'fontFamily': 'Courier New'
                            },
                            'fontSize': {
                                'magnitude': 10,
                                'unit': 'PT'
                            }
                        },
                        'fields': 'weightedFontFamily,fontSize'
                    }
                })
            elif marker['type'] == 'bold':
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': start_index + plain_start,
                            'endIndex': start_index + plain_end
                        },
                        'textStyle': {
                            'bold': True
                        },
                        'fields': 'bold'
                    }
                })
            elif marker['type'] == 'italic':
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': start_index + plain_start,
                            'endIndex': start_index + plain_end
                        },
                        'textStyle': {
                            'italic': True
                        },
                        'fields': 'italic'
                    }
                })

            # Update offset and position
            offset += marker['marker_len']
            last_pos = marker['end']

        # Add remaining text
        plain_parts.append(line[last_pos:])

        plain_line = ''.join(plain_parts)
        return plain_line, requests

    def _create_heading_requests(
        self, text: str, level: int, start_index: int
    ) -> List[dict]:
        """Create formatting requests for heading.

        Args:
            text: Heading text
            level: Heading level (1-3)
            start_index: Starting index in document

        Returns:
            List of formatting requests
        """
        style_name = f'HEADING_{level}'
        end_index = start_index + len(text) + 1

        return [{
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

    def _create_list_requests(
        self, text: str, list_type: str, start_index: int
    ) -> List[dict]:
        """Create formatting requests for list item.

        Args:
            text: List item text
            list_type: 'BULLET' or 'DECIMAL'
            start_index: Starting index in document

        Returns:
            List of formatting requests
        """
        end_index = start_index + len(text) + 1

        # Google Docs requires creating a bullet with glyphType
        return [{
            'createParagraphBullets': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': end_index
                },
                'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE' if list_type == 'BULLET' else 'NUMBERED_DECIMAL_ALPHA_ROMAN'
            }
        }]

    def convert_docs_to_markdown(
        self, formatted_segments: List[Dict[str, Any]]
    ) -> str:
        """Convert Google Docs formatting to Markdown.

        Args:
            formatted_segments: List of text segments with formatting metadata

        Returns:
            Markdown-formatted string
        """
        markdown_lines = []
        current_line = ""
        current_style = None
        current_list_type = None

        for segment in formatted_segments:
            text = segment['text']
            style = segment['style']
            bold = segment['bold']
            italic = segment['italic']
            list_type = segment.get('list_type')

            # Handle newlines
            if '\n' in text:
                parts = text.split('\n')
                for i, part in enumerate(parts):
                    if part:
                        formatted_part = self._format_text_segment(
                            part, bold, italic
                        )
                        current_line += formatted_part

                    # End of line
                    if i < len(parts) - 1 or text.endswith('\n'):
                        # Apply paragraph-level formatting
                        line = self._apply_paragraph_formatting(
                            current_line, style, list_type
                        )
                        if line:
                            markdown_lines.append(line)
                        current_line = ""
            else:
                # No newline - accumulate text
                formatted_text = self._format_text_segment(text, bold, italic)
                current_line += formatted_text

        # Handle any remaining text
        if current_line:
            markdown_lines.append(current_line)

        return '\n'.join(markdown_lines)

    def _format_text_segment(self, text: str, bold: bool, italic: bool) -> str:
        """Apply inline formatting to text segment.

        Args:
            text: Text to format
            bold: Whether text is bold
            italic: Whether text is italic

        Returns:
            Markdown-formatted text
        """
        if bold and italic:
            return f'***{text}***'
        elif bold:
            return f'**{text}**'
        elif italic:
            return f'*{text}*'
        else:
            return text

    def _apply_paragraph_formatting(
        self, line: str, style: str, list_type: Optional[str]
    ) -> str:
        """Apply paragraph-level formatting to line.

        Args:
            line: Line of text
            style: Paragraph style (HEADING_1, etc.)
            list_type: List type if applicable

        Returns:
            Markdown-formatted line
        """
        # Remove trailing whitespace
        line = line.rstrip()

        if not line:
            return ""

        # Apply heading
        if style == 'HEADING_1':
            return f'# {line}'
        elif style == 'HEADING_2':
            return f'## {line}'
        elif style == 'HEADING_3':
            return f'### {line}'

        # Apply list formatting
        if list_type:
            if list_type in ['BULLET', 'DISC', 'CIRCLE', 'SQUARE']:
                return f'- {line}'
            elif list_type in ['DECIMAL', 'NUMBERED']:
                return f'1. {line}'

        return line
