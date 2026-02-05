#!/usr/bin/env python3
"""CRM MCP Server - Main entry point."""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.protocol import log, send_response
from mcp.tool_definitions import get_all_tools
from infrastructure.auth_manager import AuthManager
from infrastructure.browser_client import BrowserClient
from application.search_service import SearchService
from application.create_service import CreateService
from application.update_service import UpdateService
from application.comment_service import CommentService


class CRMMCPServer:
    """CRM MCP Server implementation."""

    def __init__(self):
        """Initialize the CRM MCP server."""
        self.auth_manager = None
        self.browser_client = None
        self.search_service = None
        self.create_service = None
        self.update_service = None
        self.comment_service = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure server is initialized (lazy initialization)."""
        if self._initialized:
            return

        log("Initializing CRM MCP Server...")

        # Load credentials
        self.auth_manager = AuthManager()
        if not self.auth_manager.has_credentials():
            raise ValueError("Credentials not configured. Run setup_auth.py first.")

        credentials = self.auth_manager.get_credentials()

        # Initialize browser
        self.browser_client = BrowserClient(
            username=credentials['username'],
            password=credentials['password'],
            headless=True
        )
        await self.browser_client.initialize()

        # Get page instance
        page = await self.browser_client.get_page()

        # Initialize services
        self.search_service = SearchService(page, log_func=log)
        self.create_service = CreateService(page, log_func=log)
        self.update_service = UpdateService(page, log_func=log)
        self.comment_service = CommentService(page, log_func=log)

        self._initialized = True
        log("CRM MCP Server initialized successfully")

    def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP request.

        Args:
            request: Request dictionary

        Returns:
            Response dictionary
        """
        method = request.get('method')
        params = request.get('params', {})

        if method == 'initialize':
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "CRM MCP Server",
                    "version": "1.0.0"
                }
            }

        elif method == 'tools/list':
            return {"tools": get_all_tools()}

        elif method == 'tools/call':
            # Use asyncio to run async tool execution
            result = asyncio.run(self._handle_tools_call(params))
            return result

        else:
            return {"error": f"Unknown method: {method}"}

    async def _handle_tools_call(self, params: dict) -> dict:
        """Handle tools/call request asynchronously.

        Args:
            params: Tool call parameters

        Returns:
            Response dictionary
        """
        tool_name = params.get('name')
        args = params.get('arguments', {})

        try:
            # Ensure server is initialized
            await self._ensure_initialized()

            # Ensure logged in
            await self.browser_client.ensure_logged_in()

            # Execute tool
            result = await self._execute_tool(tool_name, args)

            # Return result as MCP response
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }
                ]
            }

        except Exception as e:
            log(f"Error executing tool {tool_name}: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": "execution_error"
            }
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(error_result, ensure_ascii=False, indent=2)
                    }
                ]
            }

    async def _execute_tool(self, tool_name: str, args: dict):
        """Execute a specific tool.

        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments

        Returns:
            Tool execution result
        """
        log(f"Executing tool: {tool_name}")

        # Search & Read Tools
        if tool_name == 'search_account':
            return await self.search_service.search_account(
                name=args.get('name'),
                city=args.get('ort')
            )

        elif tool_name == 'search_person':
            return await self.search_service.search_person(
                firstname=args.get('vorname'),
                lastname=args.get('nachname'),
                company=args.get('firma')
            )

        elif tool_name == 'search_potential':
            return await self.search_service.search_potential(
                name=args.get('name'),
                company=args.get('firma'),
                owner=args.get('inhaber'),
                status=args.get('status')
            )

        elif tool_name == 'get_comments':
            return await self.comment_service.get_comments(
                account_id=args.get('account_id'),
                limit=args.get('limit', 5)
            )

        # Create Tools
        elif tool_name == 'create_account':
            return await self.create_service.create_account(
                data=args.get('data', {})
            )

        elif tool_name == 'create_person':
            return await self.create_service.create_person(
                company_id=args.get('firma_id'),
                data=args.get('data', {})
            )

        elif tool_name == 'create_potential':
            return await self.create_service.create_potential(
                company_id=args.get('firma_id'),
                data=args.get('data', {})
            )

        # Update Tools
        elif tool_name == 'update_account':
            return await self.update_service.update_account(
                record_id=args.get('account_id'),
                updates=args.get('updates', {})
            )

        elif tool_name == 'update_person':
            return await self.update_service.update_person(
                record_id=args.get('person_id'),
                updates=args.get('updates', {})
            )

        elif tool_name == 'update_potential':
            return await self.update_service.update_potential(
                record_id=args.get('potential_id'),
                updates=args.get('updates', {})
            )

        # Interaction Tools
        elif tool_name == 'add_comment_to_account':
            return await self.comment_service.add_comment_to_account(
                account_id=args.get('account_id'),
                author=args.get('autor'),
                text=args.get('text')
            )

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "error_type": "unknown_tool"
            }

    async def cleanup(self):
        """Cleanup resources."""
        if self.browser_client:
            await self.browser_client.close()


def main():
    """Main entry point for CRM MCP Server."""
    log("CRM MCP Server starting...")

    server = CRMMCPServer()

    try:
        while True:
            try:
                # Read request from stdin
                line = input()
                if not line:
                    continue

                request = json.loads(line)

                # Handle request
                response = server.handle_request(request)

                # Include request ID in response
                if 'id' in request:
                    response['id'] = request['id']

                # Send response
                send_response(response)

            except EOFError:
                log("EOF received, shutting down")
                break

            except json.JSONDecodeError as e:
                log(f"Invalid JSON received: {e}")
                continue

            except Exception as e:
                log(f"Error handling request: {e}")
                continue

    finally:
        # Cleanup
        try:
            asyncio.run(server.cleanup())
        except Exception as e:
            log(f"Error during cleanup: {e}")

    log("CRM MCP Server stopped")


if __name__ == '__main__':
    main()
