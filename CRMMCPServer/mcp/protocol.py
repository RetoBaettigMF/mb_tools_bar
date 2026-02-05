"""MCP protocol helpers."""

import json
import sys


def log(msg: str):
    """Log message to stderr.

    Args:
        msg: Message to log
    """
    print(msg, file=sys.stderr)


def send_response(response: dict):
    """Send JSON response to stdout.

    Args:
        response: Response dictionary
    """
    print(json.dumps(response), flush=True)
