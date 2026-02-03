#!/usr/bin/env python3
"""
MCP Server for Google Docs editing.
Refactored version with clean architecture.
"""

import json
import sys
import os

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import infrastructure
from infrastructure.auth_manager import AuthManager
from infrastructure.google_docs_client import GoogleDocsClient

# Import domain
from domain.markdown_parser import MarkdownParser

# Import application services
from application.unformatted_service import UnformattedDocumentService
from application.formatted_service import FormattedDocumentService

# Import MCP protocol
from mcp.protocol import log, send_response
from mcp.tool_definitions import get_all_tools


class GoogleDocsMCPServer:
    """Main MCP server for Google Docs operations."""

    def __init__(self):
        """Initialize server with all dependencies."""
        # Infrastructure
        self.auth_manager = AuthManager(log_func=log)
        self.client = GoogleDocsClient(self.auth_manager)

        # Domain
        self.parser = MarkdownParser()

        # Application services
        self.unformatted_service = UnformattedDocumentService(self.client)
        self.formatted_service = FormattedDocumentService(
            self.client, self.parser
        )

    def handle_request(self, request: dict) -> dict:
        """Handle MCP protocol requests.

        Args:
            request: MCP request dictionary

        Returns:
            MCP response dictionary
        """
        method = request.get('method')
        params = request.get('params', {})

        if method == 'initialize':
            return self._handle_initialize(params)
        elif method == 'tools/list':
            return self._handle_tools_list()
        elif method == 'tools/call':
            return self._handle_tools_call(params)
        else:
            return {"error": f"Unknown method: {method}"}

    def _handle_initialize(self, params: dict) -> dict:
        """Handle initialize request."""
        requested_version = params.get('protocolVersion', '2024-11-05')
        return {
            "protocolVersion": requested_version,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "google-docs-mcp",
                "version": "2.0.0"
            }
        }

    def _handle_tools_list(self) -> dict:
        """Handle tools/list request."""
        return {"tools": get_all_tools()}

    def _handle_tools_call(self, params: dict) -> dict:
        """Handle tools/call request."""
        tool_name = params.get('name')
        args = params.get('arguments', {})

        # Route to appropriate service
        if tool_name == 'text_read':
            result = self.unformatted_service.read_document(
                doc_id=args.get('documentId'),
                start_line=args.get('startLine', 1),
                max_lines=args.get('maxLines', 100)
            )
        elif tool_name == 'text_write':
            result = self.unformatted_service.write_text(
                doc_id=args.get('documentId'),
                text=args.get('text', ''),
                position=args.get('position', 'end'),
                index=args.get('index')
            )
        elif tool_name == 'text_replace':
            result = self.unformatted_service.replace_text(
                doc_id=args.get('documentId'),
                old_text=args.get('oldText', ''),
                new_text=args.get('newText', '')
            )
        elif tool_name == 'markdown_read':
            result = self.formatted_service.read_as_markdown(
                doc_id=args.get('documentId'),
                start_line=args.get('startLine', 1),
                max_lines=args.get('maxLines', 100)
            )
        elif tool_name == 'markdown_write':
            result = self.formatted_service.write_markdown(
                doc_id=args.get('documentId'),
                markdown=args.get('markdown', ''),
                position=args.get('position', 'end'),
                index=args.get('index')
            )
        elif tool_name == 'markdown_replace':
            result = self.formatted_service.replace_with_markdown(
                doc_id=args.get('documentId'),
                old_text=args.get('oldText', ''),
                new_markdown=args.get('newMarkdown', '')
            )
        elif tool_name == 'markdown_format':
            result = self.formatted_service.format_existing_text(
                doc_id=args.get('documentId'),
                text=args.get('text', ''),
                style=args.get('style', 'normal')
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2, ensure_ascii=False)
            }]
        }


def main():
    """Main entry point."""
    log("Google Docs MCP Server v2.0 starting...")

    server = GoogleDocsMCPServer()

    while True:
        try:
            line = input()
            if not line:
                continue

            request = json.loads(line)
            response = server.handle_request(request)

            # Add request ID if present
            if 'id' in request:
                response['id'] = request['id']

            send_response(response)

        except json.JSONDecodeError as e:
            log(f"JSON decode error: {e}")
        except EOFError:
            log("EOF received, shutting down")
            break
        except Exception as e:
            log(f"Error: {e}")
            import traceback
            log(traceback.format_exc())
            send_response({"error": str(e)})


if __name__ == '__main__':
    main()
