#!/usr/bin/env python3
"""
MCP Server for Google Docs editing.
Supports: docs_read, docs_append, docs_insert, docs_replace
"""

import json
import sys
import os
from typing import Optional

# Google API imports
try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: google-api-python-client not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib", file=sys.stderr)
    sys.exit(1)

# MCP Protocol
SCOPES = ['https://www.googleapis.com/auth/documents']

def log(msg: str):
    print(msg, file=sys.stderr)

def send_response(response: dict):
    print(json.dumps(response), flush=True)

def get_docs_service():
    """Initialize and return Google Docs API service."""
    creds = None
    token_path = os.path.expanduser('~/.config/gogcli/tokens/bar.ai.bot@cudos.ch.json')

    # Try to use existing gog token if available
    if os.path.exists(token_path):
        try:
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            log(f"Warning: Could not load gog token: {e}")

    # Refresh expired credentials
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                log("Refreshing expired token...")
                creds.refresh(Request())
                # Save refreshed token
                with open(token_path, 'w') as f:
                    f.write(creds.to_json())
                log("Token refreshed successfully")
            except Exception as e:
                log(f"Warning: Could not refresh token: {e}")
                creds = None

    # If still no valid creds, try OAuth flow
    if not creds:
        creds_path = os.path.expanduser('~/.config/gogcli/credentials.json')
        if os.path.exists(creds_path):
            log("Starting OAuth flow (this will open a browser)...")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            # Save for future
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
        else:
            raise Exception("No credentials found. Please run setup_auth.py first.")

    if not creds or not creds.valid:
        raise Exception("Could not obtain valid credentials.")

    return build('docs', 'v1', credentials=creds)

def read_document(doc_id: str, start_line: int = 1, max_lines: int = 100) -> dict:
    """Read a document with pagination."""
    try:
        service = get_docs_service()
        doc = service.documents().get(documentId=doc_id).execute()
        
        # Extract text content
        content = doc.get('body', {}).get('content', [])
        lines = []
        
        def extract_text(element):
            text = ""
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text += elem['textRun'].get('content', '')
            elif 'table' in element:
                for row in element['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for cell_content in cell.get('content', []):
                            text += extract_text(cell_content)
            return text
        
        full_text = ""
        for element in content:
            full_text += extract_text(element)
        
        # Split into lines
        all_lines = full_text.split('\n')
        total_lines = len(all_lines)
        
        # Calculate slice
        start_idx = max(0, start_line - 1)
        end_idx = min(start_idx + max_lines, total_lines)
        
        selected_lines = all_lines[start_idx:end_idx]
        remaining = total_lines - end_idx
        
        return {
            "title": doc.get('title', 'Unknown'),
            "totalLines": total_lines,
            "startLine": start_line,
            "endLine": end_idx,
            "remainingLines": max(0, remaining),
            "hasMore": remaining > 0,
            "nextStartLine": end_idx + 1 if remaining > 0 else None,
            "content": '\n'.join(selected_lines)
        }
    except Exception as e:
        return {"error": str(e)}

def append_to_document(doc_id: str, text: str) -> dict:
    """Append text to end of document."""
    try:
        service = get_docs_service()
        
        # Get document to find end index
        doc = service.documents().get(documentId=doc_id).execute()
        end_index = doc.get('body', {}).get('content', [{}])[-1].get('endIndex', 1)
        
        requests = [{
            'insertText': {
                'location': {'index': end_index - 1},
                'text': text
            }
        }]
        
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        return {
            "success": True,
            "insertedCharacters": len(text),
            "replies": len(result.get('replies', []))
        }
    except Exception as e:
        return {"error": str(e)}

def insert_at_position(doc_id: str, text: str, index: int) -> dict:
    """Insert text at specific index."""
    try:
        service = get_docs_service()
        
        requests = [{
            'insertText': {
                'location': {'index': index},
                'text': text
            }
        }]
        
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        return {
            "success": True,
            "insertedCharacters": len(text),
            "index": index
        }
    except Exception as e:
        return {"error": str(e)}

def replace_text(doc_id: str, old_text: str, new_text: str) -> dict:
    """Replace all occurrences of text."""
    try:
        service = get_docs_service()
        
        requests = [{
            'replaceAllText': {
                'containsText': {
                    'text': old_text,
                    'matchCase': True
                },
                'replaceText': new_text
            }
        }]
        
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        return {
            "success": True,
            "replacements": result.get('replies', [{}])[0].get('replaceAllText', {}).get('occurrencesChanged', 0)
        }
    except Exception as e:
        return {"error": str(e)}

def insert_formatted_text(doc_id: str, text: str, index: int) -> dict:
    """Insert text with Markdown-like formatting support.
    
    Supported formats:
    - # Heading 1
    - ## Heading 2  
    - ### Heading 3
    - **bold text**
    - *italic text*
    """
    try:
        service = get_docs_service()
        
        # Parse markdown-like text into segments
        lines = text.split('\n')
        requests = []
        current_index = index
        
        import re
        
        for line in lines:
            if not line:
                # Empty line - just insert newline
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': '\n'
                    }
                })
                current_index += 1
                continue
            
            # Check for heading
            heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                
                # Insert the text
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': content + '\n'
                    }
                })
                
                # Apply heading style
                style_name = f'HEADING_{level}'
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(content) + 1
                        },
                        'paragraphStyle': {
                            'namedStyleType': style_name
                        },
                        'fields': 'namedStyleType'
                    }
                })
                current_index += len(content) + 1
            else:
                # Regular text - check for bold/italic
                segments = []
                remaining = line
                
                # Pattern for bold and italic
                bold_pattern = r'\*\*(.+?)\*\*'
                italic_pattern = r'\*(.+?)\*'
                
                # Simple approach: insert line, then apply formatting
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': line + '\n'
                    }
                })
                
                # Find all formatting and apply
                line_start = current_index
                
                # Apply bold formatting
                for match in re.finditer(bold_pattern, line):
                    bold_text = match.group(1)
                    start = line_start + match.start()
                    end = line_start + match.end()
                    requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': start,
                                'endIndex': end
                            },
                            'textStyle': {
                                'bold': True
                            },
                            'fields': 'bold'
                        }
                    })
                    # Update the text to remove **
                    requests.append({
                        'replaceAllText': {
                            'containsText': {
                                'text': '**' + bold_text + '**',
                                'matchCase': True
                            },
                            'replaceText': bold_text
                        }
                    })
                
                # Apply italic formatting
                for match in re.finditer(italic_pattern, line):
                    # Skip if it's part of bold (**)
                    if match.start() > 0 and line[match.start()-1:match.start()+1] == '**':
                        continue
                    if match.end() < len(line) and line[match.end()-1:match.end()+1] == '**':
                        continue
                    
                    italic_text = match.group(1)
                    start = line_start + match.start()
                    end = line_start + match.end()
                    requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': start,
                                'endIndex': end
                            },
                            'textStyle': {
                                'italic': True
                            },
                            'fields': 'italic'
                        }
                    })
                    # Update the text to remove *
                    requests.append({
                        'replaceAllText': {
                            'containsText': {
                                'text': '*' + italic_text + '*',
                                'matchCase': True
                            },
                            'replaceText': italic_text
                        }
                    })
                
                # Ensure normal paragraph style
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': line_start,
                            'endIndex': line_start + len(line) + 1
                        },
                        'paragraphStyle': {
                            'namedStyleType': 'NORMAL_TEXT'
                        },
                        'fields': 'namedStyleType'
                    }
                })
                
                current_index += len(line) + 1
        
        # Execute all requests
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        return {
            "success": True,
            "insertedCharacters": current_index - index,
            "startIndex": index,
            "endIndex": current_index
        }
    except Exception as e:
        return {"error": str(e)}

def handle_request(request: dict) -> dict:
    """Handle MCP tool requests."""
    method = request.get('method')
    params = request.get('params', {})
    
    if method == 'tools/list':
        return {
            "tools": [
                {
                    "name": "docs_read",
                    "description": "Read a Google Doc with pagination support",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documentId": {"type": "string", "description": "Google Doc ID"},
                            "startLine": {"type": "integer", "description": "Starting line number (1-based)", "default": 1},
                            "maxLines": {"type": "integer", "description": "Maximum lines to return", "default": 100}
                        },
                        "required": ["documentId"]
                    }
                },
                {
                    "name": "docs_append",
                    "description": "Append text to the end of a Google Doc",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documentId": {"type": "string", "description": "Google Doc ID"},
                            "text": {"type": "string", "description": "Text to append"}
                        },
                        "required": ["documentId", "text"]
                    }
                },
                {
                    "name": "docs_insert",
                    "description": "Insert text at a specific position in a Google Doc",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documentId": {"type": "string", "description": "Google Doc ID"},
                            "text": {"type": "string", "description": "Text to insert"},
                            "index": {"type": "integer", "description": "Position index (0-based)"}
                        },
                        "required": ["documentId", "text", "index"]
                    }
                },
                {
                    "name": "docs_replace",
                    "description": "Replace all occurrences of text in a Google Doc",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documentId": {"type": "string", "description": "Google Doc ID"},
                            "oldText": {"type": "string", "description": "Text to find"},
                            "newText": {"type": "string", "description": "Replacement text"}
                        },
                        "required": ["documentId", "oldText", "newText"]
                    }
                },
                {
                    "name": "docs_insert_formatted",
                    "description": "Insert formatted text with Markdown-like syntax (# Heading, ## Heading 2, **bold**, *italic*). Use # for Heading 1 and no prefix for normal text.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documentId": {"type": "string", "description": "Google Doc ID"},
                            "text": {"type": "string", "description": "Text to insert with Markdown formatting (# Heading, **bold**, *italic*)"},
                            "index": {"type": "integer", "description": "Position index (0-based)"}
                        },
                        "required": ["documentId", "text", "index"]
                    }
                },
                {
                    "name": "docs_format_as_heading",
                    "description": "Format existing text as Heading 1, 2, or 3",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documentId": {"type": "string", "description": "Google Doc ID"},
                            "text": {"type": "string", "description": "Exact text to find and format"},
                            "level": {"type": "integer", "description": "Heading level (1, 2, or 3)", "default": 1}
                        },
                        "required": ["documentId", "text"]
                    }
                },
                {
                    "name": "docs_format_as_normal",
                    "description": "Format existing text as Normal Text (removes heading formatting)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documentId": {"type": "string", "description": "Google Doc ID"},
                            "text": {"type": "string", "description": "Exact text to find and format"}
                        },
                        "required": ["documentId", "text"]
                    }
                }
            ]
        }
    
    elif method == 'tools/call':
        tool_name = params.get('name')
        args = params.get('arguments', {})
        doc_id = args.get('documentId')
        
        if tool_name == 'docs_read':
            start_line = args.get('startLine', 1)
            max_lines = args.get('maxLines', 100)
            result = read_document(doc_id, start_line, max_lines)
        elif tool_name == 'docs_append':
            result = append_to_document(doc_id, args.get('text', ''))
        elif tool_name == 'docs_insert':
            result = insert_at_position(doc_id, args.get('text', ''), args.get('index', 1))
        elif tool_name == 'docs_replace':
            result = replace_text(doc_id, args.get('oldText', ''), args.get('newText', ''))
        elif tool_name == 'docs_insert_formatted':
            result = insert_formatted_text(doc_id, args.get('text', ''), args.get('index', 1))
        elif tool_name == 'docs_format_as_heading':
            result = format_text_as_heading(doc_id, args.get('text', ''), args.get('level', 1))
        elif tool_name == 'docs_format_as_normal':
            result = format_text_as_normal(doc_id, args.get('text', ''))
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        }
    
    elif method == 'initialize':
        # Use the protocol version requested by the client
        requested_version = params.get('protocolVersion', '2024-11-05')
        return {
            "protocolVersion": requested_version,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "google-docs-mcp", "version": "1.0.0"}
        }
    
    return {"error": f"Unknown method: {method}"}

def format_text_as_heading(doc_id: str, text_to_find: str, heading_level: int = 1) -> dict:
    """Find text and format it as heading."""
    try:
        service = get_docs_service()
        
        # Get document to find the text
        doc = service.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])
        
        # Find the text in the document
        full_text = ""
        for element in content:
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        full_text += elem['textRun'].get('content', '')
        
        # Find the position
        pos = full_text.find(text_to_find)
        if pos == -1:
            return {"error": f"Text not found: {text_to_find}"}
        
        start_index = pos + 1  # Google Docs uses 1-based indexing
        end_index = start_index + len(text_to_find)
        
        # Apply heading style
        style_name = f'HEADING_{heading_level}'
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
        
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        return {
            "success": True,
            "formattedText": text_to_find,
            "headingLevel": heading_level,
            "startIndex": start_index,
            "endIndex": end_index
        }
    except Exception as e:
        return {"error": str(e)}

def format_text_as_normal(doc_id: str, text_to_find: str) -> dict:
    """Find text and format it as normal text."""
    try:
        service = get_docs_service()
        
        # Get document to find the text
        doc = service.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])
        
        # Find the text in the document
        full_text = ""
        for element in content:
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        full_text += elem['textRun'].get('content', '')
        
        # Find the position
        pos = full_text.find(text_to_find)
        if pos == -1:
            return {"error": f"Text not found: {text_to_find}"}
        
        start_index = pos + 1  # Google Docs uses 1-based indexing
        end_index = start_index + len(text_to_find)
        
        # Apply normal text style
        requests = [{
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': end_index
                },
                'paragraphStyle': {
                    'namedStyleType': 'NORMAL_TEXT'
                },
                'fields': 'namedStyleType'
            }
        }]
        
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        return {
            "success": True,
            "formattedText": text_to_find,
            "style": "NORMAL_TEXT",
            "startIndex": start_index,
            "endIndex": end_index
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    log("Google Docs MCP Server starting...")
    
    while True:
        try:
            line = input()
            if not line:
                continue
            
            request = json.loads(line)
            response = handle_request(request)
            
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
            send_response({"error": str(e)})

if __name__ == '__main__':
    main()
