#!/usr/bin/env python3
"""Simple health check for ASCII Motion Studio API."""
import sys
import urllib.request

URL = "http://127.0.0.1:8001/api/v1/health"
TIMEOUT = 10


def main() -> int:
    try:
        with urllib.request.urlopen(URL, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                print("OK")
                return 0
            print(f"Unexpected status: {resp.status}")
            return 1
    except Exception as e:
        print(f"Health check failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
