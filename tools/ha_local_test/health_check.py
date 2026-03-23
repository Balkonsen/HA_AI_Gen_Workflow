#!/usr/bin/env python3
"""Quick health checks for the local Home Assistant sandbox."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import requests


def _probe(url: str, timeout: int, token: Optional[str] = None) -> tuple[bool, str, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        return True, f"status={response.status_code}", response.status_code
    except requests.exceptions.RequestException as exc:
        return False, str(exc), 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Health check for local HA sandbox")
    parser.add_argument("--url", default="http://localhost:8123", help="Base HA URL")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument("--token", default=None, help="Optional HA long-lived access token")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ok, detail, code = _probe(args.url, args.timeout)
    if not ok or code != 200:
        print(f"FAIL root endpoint: {detail}")
        return 1
    print(f"PASS root endpoint: {detail}")

    api_url = f"{args.url}/api"
    ok, detail, code = _probe(api_url, args.timeout, args.token)
    if not ok:
        print(f"FAIL /api reachability: {detail}")
        return 1

    if args.token:
        if code == 200:
            print(f"PASS /api token auth: {detail}")
            return 0
        print(f"FAIL /api token auth: expected 200, got {code}")
        return 1

    if code in (401, 403, 404):
        print(f"PASS /api unauthenticated behavior: {detail}")
        return 0

    print(f"FAIL /api unauthenticated behavior: expected 401/403/404, got {code}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
