#!/usr/bin/env python3
import json
import sys

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            method = request.get('method')

            if method == 'initialize':
                response = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "test-minimal", "version": "1.0.0"}
                }
            elif method == 'tools/list':
                response = {"tools": []}
            else:
                response = {"error": "unknown method"}

            if 'id' in request:
                response['id'] = request['id']

            print(json.dumps(response), flush=True)
        except EOFError:
            break
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)

if __name__ == '__main__':
    main()
