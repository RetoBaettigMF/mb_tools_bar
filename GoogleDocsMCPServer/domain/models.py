"""Domain models for Google Docs operations."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class DocumentContent:
    """Represents paginated document content."""
    title: str
    total_lines: int
    content: str
    start_line: int
    end_line: int
    has_more: bool
    next_start_line: Optional[int] = None


@dataclass
class MarkdownParseResult:
    """Result of parsing Markdown into Google Docs formatting."""
    plain_text: str
    formatting_requests: List[dict]  # Google Docs batch requests


@dataclass
class WriteResult:
    """Result of a write operation."""
    success: bool
    inserted_characters: int
    start_index: int
    end_index: int


@dataclass
class ReplaceResult:
    """Result of a replace operation."""
    success: bool
    replacements: int


@dataclass
class FormatResult:
    """Result of a formatting operation."""
    success: bool
    formatted_text: str
    style: str
    start_index: int
    end_index: int
