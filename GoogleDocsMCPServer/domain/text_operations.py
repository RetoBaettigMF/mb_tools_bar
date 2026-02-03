"""Text manipulation helpers."""

from typing import Optional

from domain.models import DocumentContent


class TextOperations:
    """Helper class for text manipulation operations."""

    @staticmethod
    def paginate_text(
        text: str,
        title: str,
        start_line: int = 1,
        max_lines: int = 100
    ) -> DocumentContent:
        """Paginate text content.

        Args:
            text: Full text content
            title: Document title
            start_line: Starting line number (1-based)
            max_lines: Maximum lines to return

        Returns:
            DocumentContent with pagination metadata
        """
        all_lines = text.split('\n')
        total_lines = len(all_lines)

        # Calculate slice
        start_idx = max(0, start_line - 1)
        end_idx = min(start_idx + max_lines, total_lines)

        selected_lines = all_lines[start_idx:end_idx]
        remaining = total_lines - end_idx

        return DocumentContent(
            title=title,
            total_lines=total_lines,
            content='\n'.join(selected_lines),
            start_line=start_line,
            end_line=end_idx,
            has_more=remaining > 0,
            next_start_line=end_idx + 1 if remaining > 0 else None
        )

    @staticmethod
    def calculate_insertion_index(
        doc_length: int,
        position: str,
        index: Optional[int] = None
    ) -> int:
        """Calculate insertion index based on position.

        Args:
            doc_length: Document end index
            position: 'start', 'end', or 'custom'
            index: Custom index (used when position is 'custom')

        Returns:
            Calculated insertion index

        Raises:
            ValueError: If position is invalid
        """
        if position == 'start':
            return 1
        elif position == 'end':
            return doc_length - 1
        elif index is not None:
            return index
        else:
            raise ValueError(
                "Either position must be 'start'/'end' or index must be provided"
            )
