"""Data models for CRM MCP Server."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SearchResult:
    """Base class for search results."""
    record_id: str
    name: str
    url: str


@dataclass
class AccountSearchResult(SearchResult):
    """Search result for an account (company)."""
    city: Optional[str] = None
    additional_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactSearchResult(SearchResult):
    """Search result for a contact (person)."""
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    additional_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PotentialSearchResult(SearchResult):
    """Search result for a sales potential."""
    company: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    additional_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Comment:
    """Represents a comment on a record."""
    author: str
    date: str
    text: str


@dataclass
class CommentsResult:
    """Result of fetching comments."""
    record_id: str
    comments: List[Comment]
    count: int


@dataclass
class CreateResult:
    """Result of creating a record."""
    success: bool
    record_id: Optional[str] = None
    url: Optional[str] = None
    message: Optional[str] = None


@dataclass
class UpdateResult:
    """Result of updating a record."""
    success: bool
    record_id: str
    updated_fields: List[str]
    message: Optional[str] = None


@dataclass
class DuplicateCheckResult:
    """Result of duplicate checking."""
    has_duplicates: bool
    duplicates: List[SearchResult] = field(default_factory=list)
    count: int = 0


@dataclass
class ToolResponse:
    """Standard response format for MCP tools."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"success": self.success}

        if self.success:
            if self.data is not None:
                result["data"] = self.data
        else:
            if self.error:
                result["error"] = self.error
            if self.error_type:
                result["error_type"] = self.error_type
            if self.details:
                result["details"] = self.details

        return result
