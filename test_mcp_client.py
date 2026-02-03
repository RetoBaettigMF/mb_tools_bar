#!/usr/bin/env python3
"""Simple MCP client to test our servers"""
import subprocess
import json
import sys

def test_server(server_path, server_name):
    print(f"\n=== Testing {server_name} ===")

    # Start the server
    proc = subprocess.Popen(
        ["/home/reto/Development/mb_tools_bar/venv/bin/python3", server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # Test initialize
        print("1. Sending initialize...")
        init_req = {"method": "initialize", "params": {"protocolVersion": "2025-11-25"}, "id": 1}
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()

        response = proc.stdout.readline()
        print(f"   Response: {response[:100]}...")

        # Test tools/list
        print("2. Sending tools/list...")
        tools_req = {"method": "tools/list", "params": {}, "id": 2}
        proc.stdin.write(json.dumps(tools_req) + "\n")
        proc.stdin.flush()

        response = proc.stdout.readline()
        data = json.loads(response)
        print(f"   Found {len(data.get('tools', []))} tools:")
        for tool in data.get('tools', []):
            print(f"     - {tool['name']}")

        print(f"✓ {server_name} is working!")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        proc.terminate()

if __name__ == '__main__':
    test_server("/home/reto/Development/mb_tools_bar/CudosControllingMCPServer/server.py", "CudosControllingMCPServer")
    test_server("/home/reto/Development/mb_tools_bar/GoogleDocsMCPServer/server.py", "GoogleDocsMCPServer")
