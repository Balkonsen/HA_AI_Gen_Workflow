#!/usr/bin/env python3
"""Token-based API smoke checks against a local Home Assistant instance."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = ROOT / "bin"
sys.path.insert(0, str(BIN_DIR))

from ha_api_client import HomeAssistantAPI  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Token-based API smoke checks")
    parser.add_argument(
        "--url", default="http://localhost:8123", help="Home Assistant base URL"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("HA_TEST_TOKEN"),
        help="Long-lived access token (or set HA_TEST_TOKEN)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.token:
        print("SKIP token smoke: no token provided. Use --token or HA_TEST_TOKEN.")
        return 0

    client = HomeAssistantAPI(token=args.token, ha_url=args.url)

    results: list[tuple[str, bool, str]] = []

    success, message = client.test_connection()
    results.append(("test_connection", success, message))

    config = client.get_config()
    results.append(
        (
            "get_config",
            config is not None,
            "config loaded" if config is not None else "null response",
        )
    )

    states = client.get_states()
    state_count = len(states) if isinstance(states, list) else 0
    states_detail = f"states={state_count}" if states is not None else "null response"
    results.append(("get_states", states is not None, states_detail))

    failed = False
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"{status} {name}: {detail}")
        if not ok:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
