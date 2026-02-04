"""Markdown parser for bidirectional conversion with Google Docs formatting."""

import re
from typing import List, Dict, Optional, Tuple, Any

from domain.models import MarkdownParseResult, TableData


class MarkdownParser:
    """Parse Markdown to Google Docs formatting and vice versa."""

    # Regex patterns
    HEADING_PATTERN = re.compile(r'^(#{1,3})\s+(.+)$')
    BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*')
    ITALIC_PATTERN = re.compile(r'(?<!\*)\*([^\*]+?)\*(?!\*)')  # Negative lookbehind/ahead to avoid matching **
    UNORDERED_LIST_PATTERN = re.compile(r'^-\s+(.+)$')
    ORDERED_LIST_PATTERN = re.compile(r'^\d+\.\s+(.+)$')
    CODE_PATTERN = re.compile(r'```(.+?)```')
    TABLE_ROW_PATTERN = re.compile(r'^\|(.+)\|$')
    TABLE_SEPARATOR_PATTERN = re.compile(r'^\|([\s:]*-+[\s:]*\|)+$')
    TABLE_CELL_SPLIT = re.compile(r'(?<!\\)\|')  # Split on pipes, not escaped \|

    def _is_table_start(self, line: str, line_idx: int, all_lines: List[str]) -> bool:
        """Check if line starts a table (pipe-delimited with separator next line)."""
        if not self.TABLE_ROW_PATTERN.match(line):
            return False

        # Check next line is separator
        if line_idx + 1 >= len(all_lines):
            return False

        next_line = all_lines[line_idx + 1]
        return bool(self.TABLE_SEPARATOR_PATTERN.match(next_line))

    def _extract_table_lines(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Extract all consecutive table lines starting from start_idx.

        Returns: (table_lines, num_lines_consumed)
        """
        table_lines = [lines[start_idx]]  # Header row
        idx = start_idx + 1

        # Must have separator row
        if idx >= len(lines) or not self.TABLE_SEPARATOR_PATTERN.match(lines[idx]):
            raise ValueError(f"Line {start_idx+1}: Table header must be followed by separator row")

        table_lines.append(lines[idx])  # Separator row
        idx += 1

        # Extract data rows
        while idx < len(lines) and self.TABLE_ROW_PATTERN.match(lines[idx]):
            table_lines.append(lines[idx])
            idx += 1

        # Validate minimum rows
        if len(table_lines) < 3:
            raise ValueError(f"Line {start_idx+1}: Table must have header, separator, and at least one data row")

        return table_lines, idx - start_idx

    def _parse_table_structure(self, table_lines: List[str], start_line: int) -> TableData:
        """Parse markdown table lines into structured data.

        Args:
            table_lines: List of table lines (header, separator, data rows)
            start_line: Line number in original markdown (for error reporting)

        Returns:
            TableData with headers, alignments, rows, dimensions
        """
        # Parse header row
        header_line = table_lines[0].strip('|').strip()
        headers = [cell.strip() for cell in self.TABLE_CELL_SPLIT.split(header_line)]
        num_cols = len(headers)

        # Parse separator row for alignment
        separator_line = table_lines[1].strip('|').strip()
        separator_cells = self.TABLE_CELL_SPLIT.split(separator_line)

        alignments = []
        for cell in separator_cells:
            cell = cell.strip()
            if cell.startswith(':') and cell.endswith(':'):
                alignments.append('center')
            elif cell.endswith(':'):
                alignments.append('right')
            else:
                alignments.append('left')  # Default or explicit :---

        # Validate alignment count matches headers
        if len(alignments) != num_cols:
            raise ValueError(
                f"Line {start_line+1}: Separator has {len(alignments)} columns, "
                f"header has {num_cols}"
            )

        # Parse data rows
        rows = []
        for row_idx, line in enumerate(table_lines[2:], start=2):
            row_line = line.strip('|').strip()
            cells = [cell.strip() for cell in self.TABLE_CELL_SPLIT.split(row_line)]

            # Strict validation - reject uneven columns
            if len(cells) != num_cols:
                raise ValueError(
                    f"Line {start_line+row_idx+1}: Row has {len(cells)} columns, "
                    f"expected {num_cols}"
                )

            rows.append(cells)

        return TableData(
            headers=headers,
            alignments=alignments,
            rows=rows,
            num_rows=len(rows) + 1,  # +1 for header
            num_cols=num_cols,
            start_line=start_line
        )

    def _create_table_requests(
        self,
        table_data: TableData,
        start_index: int
    ) -> Tuple[dict, List[Tuple[int, int, str, str]]]:
        """Create requests to insert and populate a table.

        Returns:
            (insertTable_request, cell_population_data)

            cell_population_data format: List of (row, col, text, alignment)
        """
        # Create table structure request
        insert_request = {
            'insertTable': {
                'rows': table_data.num_rows,
                'columns': table_data.num_cols,
                'location': {'index': start_index}
            }
        }

        # Prepare cell content (will be populated after table insertion)
        cell_data = []

        # Header row
        for col, header_text in enumerate(table_data.headers):
            cell_data.append((
                0,  # row
                col,  # column
                header_text,  # text
                table_data.alignments[col]  # alignment
            ))

        # Data rows
        for row_idx, row in enumerate(table_data.rows, start=1):
            for col, cell_text in enumerate(row):
                cell_data.append((
                    row_idx,
                    col,
                    cell_text,
                    table_data.alignments[col]
                ))

        return insert_request, cell_data

    def _create_cell_update_requests(
        self,
        cell_data: List[Tuple[int, int, str, str]],
        table_start_index: int,
        doc_structure: dict
    ) -> List[dict]:
        """Create requests to populate table cells with content and alignment.

        Args:
            cell_data: List of (row, col, text, alignment) tuples
            table_start_index: Index where table was inserted
            doc_structure: Updated document structure from insertTable response

        Returns:
            List of API requests for cell content and styling
        """
        requests = []

        # Find the table in document structure
        table_element = self._find_table_at_index(doc_structure, table_start_index)

        if not table_element:
            raise RuntimeError(f"Could not find table at index {table_start_index}")

        # Iterate through cell data
        for row, col, text, alignment in cell_data:
            # Get cell start index from table structure
            cell_start = self._get_table_cell_index(
                table_element, row, col
            )

            # Parse inline formatting in cell text
            plain_text, inline_format_requests = self._parse_inline_formatting(
                text, cell_start
            )

            # Insert text
            if plain_text:
                requests.append({
                    'insertText': {
                        'location': {'index': cell_start},
                        'text': plain_text
                    }
                })

            # Apply inline formatting
            requests.extend(inline_format_requests)

            # Apply cell alignment
            requests.append({
                'updateTableCellStyle': {
                    'tableRange': {
                        'tableCellLocation': {
                            'tableStartLocation': {'index': table_start_index + 1},
                            'rowIndex': row,
                            'columnIndex': col
                        }
                    },
                    'tableCellStyle': {
                        'contentAlignment': self._alignment_to_docs_api(alignment)
                    },
                    'fields': 'contentAlignment'
                }
            })

        return requests

    def _alignment_to_docs_api(self, alignment: str) -> str:
        """Convert alignment string to Google Docs API format."""
        mapping = {
            'left': 'START',
            'center': 'CENTER',
            'right': 'END'
        }
        return mapping.get(alignment, 'START')

    def _find_table_at_index(self, doc: dict, index: int) -> Optional[dict]:
        """Find table element at specified index in document structure."""
        # Google Docs inserts newline before table, so table is at index + 1
        target_index = index + 1

        for element in doc.get('body', {}).get('content', []):
            if 'table' in element:
                if element.get('startIndex') == target_index:
                    return element['table']

        return None

    def _get_table_cell_index(self, table: dict, row: int, col: int) -> int:
        """Get start index of cell content from table structure."""
        table_rows = table.get('tableRows', [])

        if row >= len(table_rows):
            raise IndexError(f"Row {row} out of range (table has {len(table_rows)} rows)")

        table_row = table_rows[row]
        table_cells = table_row.get('tableCells', [])

        if col >= len(table_cells):
            raise IndexError(f"Column {col} out of range (row has {len(table_cells)} columns)")

        table_cell = table_cells[col]

        # Cell content starts at first paragraph's start index
        content = table_cell.get('content', [])
        if content and 'paragraph' in content[0]:
            return content[0]['startIndex']

        raise RuntimeError(f"Could not determine cell index for ({row}, {col})")

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
        tables = []  # Track tables separately
        current_index = 1  # Google Docs uses 1-based indexing

        line_idx = 0
        while line_idx < len(lines):
            line = lines[line_idx]

            if not line:
                # Empty line
                plain_lines.append('')
                current_index += 1
                line_idx += 1
                continue

            # Check for table
            if self._is_table_start(line, line_idx, lines):
                try:
                    table_lines, consumed = self._extract_table_lines(lines, line_idx)
                    table_data = self._parse_table_structure(table_lines, line_idx)

                    # Store table data and insertion point
                    table_data.insertion_index = current_index
                    tables.append(table_data)

                    # Placeholder in plain text (empty line)
                    plain_lines.append('')

                    # Table creates: newline + table structure
                    # Actual size determined after insertion
                    # For now, increment by 1 for the newline
                    current_index += 1

                    line_idx += consumed
                    continue

                except ValueError as e:
                    # Strict validation - propagate error
                    raise ValueError(f"Table parsing error: {e}")

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
                line_idx += 1
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
                line_idx += 1
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
                line_idx += 1
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
            line_idx += 1

        plain_text = '\n'.join(plain_lines)
        if plain_text and not plain_text.endswith('\n'):
            plain_text += '\n'

        return MarkdownParseResult(
            plain_text=plain_text,
            formatting_requests=requests,
            tables=tables
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
        """Convert Google Docs formatting to Markdown, including tables.

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
            if segment.get('type') == 'table':
                # Flush any accumulated text
                if current_line:
                    markdown_lines.append(current_line)
                    current_line = ""

                # Convert table to markdown
                table_md = self._convert_table_to_markdown(segment)
                markdown_lines.append(table_md)
                markdown_lines.append('')  # Empty line after table
                continue

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

    def _convert_table_to_markdown(self, table_segment: Dict[str, Any]) -> str:
        """Convert table structure to markdown table format.

        Args:
            table_segment: {
                'type': 'table',
                'rows': [[[{'text': '...', 'bold': bool, 'italic': bool}], ...], ...]
            }

        Returns:
            GFM markdown table string
        """
        rows = table_segment['rows']

        if not rows or not rows[0]:
            return ''

        num_cols = len(rows[0])

        # Convert each row to plain text with formatting
        text_rows = []
        for row in rows:
            text_row = []
            for cell_segments in row:
                cell_text = self._format_table_cell(cell_segments)
                text_row.append(cell_text)
            text_rows.append(text_row)

        # Calculate column widths for alignment
        col_widths = [0] * num_cols
        for row in text_rows:
            for col_idx, cell in enumerate(row):
                col_widths[col_idx] = max(col_widths[col_idx], len(cell))

        # Build markdown table
        lines = []

        # Header row (first row)
        header_cells = [
            cell.ljust(col_widths[i])
            for i, cell in enumerate(text_rows[0])
        ]
        lines.append('| ' + ' | '.join(header_cells) + ' |')

        # Separator row (default left alignment)
        # Note: We don't preserve alignment on read since Google Docs
        # may not maintain it consistently
        separators = ['-' * max(3, col_widths[i]) for i in range(num_cols)]
        lines.append('|' + '|'.join(separators) + '|')

        # Data rows
        for row in text_rows[1:]:
            cells = [
                cell.ljust(col_widths[i])
                for i, cell in enumerate(row)
            ]
            lines.append('| ' + ' | '.join(cells) + ' |')

        return '\n'.join(lines)

    def _format_table_cell(self, cell_segments: List[Dict[str, Any]]) -> str:
        """Format a table cell's content with inline markdown.

        Args:
            cell_segments: List of {'text': str, 'bold': bool, 'italic': bool}

        Returns:
            Markdown-formatted cell text
        """
        formatted_parts = []

        for segment in cell_segments:
            text = segment['text']
            bold = segment['bold']
            italic = segment['italic']

            # Apply formatting (reuse existing logic)
            if bold and italic:
                formatted_parts.append(f'***{text}***')
            elif bold:
                formatted_parts.append(f'**{text}**')
            elif italic:
                formatted_parts.append(f'*{text}*')
            else:
                formatted_parts.append(text)

        # Join segments with space, handle empty cells
        result = ' '.join(formatted_parts).strip()
        return result if result else ''

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
