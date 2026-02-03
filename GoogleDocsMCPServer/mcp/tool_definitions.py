"""MCP tool definitions for Google Docs operations."""

from typing import List, Dict


def get_all_tools() -> List[Dict]:
    """Get all available tool definitions.

    Returns:
        List of tool definition dictionaries
    """
    return [
        {
            "name": "text_read",
            "description": "Read plain text from a Google Doc with pagination support",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "documentId": {
                        "type": "string",
                        "description": "Google Doc ID"
                    },
                    "startLine": {
                        "type": "integer",
                        "description": "Starting line number (1-based)",
                        "default": 1
                    },
                    "maxLines": {
                        "type": "integer",
                        "description": "Maximum lines to return",
                        "default": 100
                    }
                },
                "required": ["documentId"]
            }
        },
        {
            "name": "text_write",
            "description": "Write plain text to a Google Doc (append or insert at position)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "documentId": {
                        "type": "string",
                        "description": "Google Doc ID"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to write"
                    },
                    "position": {
                        "type": "string",
                        "description": "Position to write: 'start' or 'end' (default 'end')",
                        "enum": ["start", "end"],
                        "default": "end"
                    },
                    "index": {
                        "type": "integer",
                        "description": "Custom position index (overrides position parameter)"
                    }
                },
                "required": ["documentId", "text"]
            }
        },
        {
            "name": "text_replace",
            "description": "Replace all occurrences of plain text in a Google Doc",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "documentId": {
                        "type": "string",
                        "description": "Google Doc ID"
                    },
                    "oldText": {
                        "type": "string",
                        "description": "Text to find"
                    },
                    "newText": {
                        "type": "string",
                        "description": "Replacement text"
                    }
                },
                "required": ["documentId", "oldText", "newText"]
            }
        },
        {
            "name": "markdown_read",
            "description": "Read document with formatting converted to Markdown (# headings, **bold**, *italic*, - lists, 1. numbered lists)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "documentId": {
                        "type": "string",
                        "description": "Google Doc ID"
                    },
                    "startLine": {
                        "type": "integer",
                        "description": "Starting line number (1-based)",
                        "default": 1
                    },
                    "maxLines": {
                        "type": "integer",
                        "description": "Maximum lines to return",
                        "default": 100
                    }
                },
                "required": ["documentId"]
            }
        },
        {
            "name": "markdown_write",
            "description": "Write text with Markdown formatting (# H1, ## H2, ### H3, **bold**, *italic*, - lists, 1. numbered, ```code```)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "documentId": {
                        "type": "string",
                        "description": "Google Doc ID"
                    },
                    "markdown": {
                        "type": "string",
                        "description": "Markdown-formatted text"
                    },
                    "position": {
                        "type": "string",
                        "description": "Position to write: 'start' or 'end' (default 'end')",
                        "enum": ["start", "end"],
                        "default": "end"
                    },
                    "index": {
                        "type": "integer",
                        "description": "Custom position index (overrides position parameter)"
                    }
                },
                "required": ["documentId", "markdown"]
            }
        },
        {
            "name": "markdown_replace",
            "description": "Replace text and apply Markdown formatting to the replacement",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "documentId": {
                        "type": "string",
                        "description": "Google Doc ID"
                    },
                    "oldText": {
                        "type": "string",
                        "description": "Plain text to find"
                    },
                    "newMarkdown": {
                        "type": "string",
                        "description": "Replacement text with Markdown formatting"
                    }
                },
                "required": ["documentId", "oldText", "newMarkdown"]
            }
        },
        {
            "name": "markdown_format",
            "description": "Apply formatting style to existing text in document",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "documentId": {
                        "type": "string",
                        "description": "Google Doc ID"
                    },
                    "text": {
                        "type": "string",
                        "description": "Exact text to find and format"
                    },
                    "style": {
                        "type": "string",
                        "description": "Style to apply",
                        "enum": ["heading1", "heading2", "heading3", "normal"],
                        "default": "normal"
                    }
                },
                "required": ["documentId", "text", "style"]
            }
        }
    ]
