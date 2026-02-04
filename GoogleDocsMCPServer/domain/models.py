"""Domain models for Google Docs operations."""

from dataclasses import dataclass, field
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
class TableData:
    """Represents a parsed markdown table."""
    headers: List[str]
    alignments: List[str]  # 'left', 'center', 'right'
    rows: List[List[str]]  # Data rows (excluding header)
    num_rows: int  # Total including header
    num_cols: int
    start_line: int  # For error reporting
    insertion_index: int = 0  # Set during parsing


@dataclass
class MarkdownParseResult:
    """Result of parsing Markdown into Google Docs formatting."""
    plain_text: str
    formatting_requests: List[dict]  # Google Docs batch requests
    tables: List[TableData] = field(default_factory=list)


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
