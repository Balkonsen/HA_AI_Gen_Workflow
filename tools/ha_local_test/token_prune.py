#!/usr/bin/env python3
"""Prune older Home Assistant sandbox long-lived tokens by client-name prefix."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

import websocket


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prune older HA sandbox long-lived tokens")
    parser.add_argument("--url", default="http://localhost:8123", help="Home Assistant base URL")
    parser.add_argument(
        "--seed-token",
        default=os.environ.get("HA_TEST_TOKEN"),
        help="Current long-lived token used for websocket authentication",
    )
    parser.add_argument(
        "--client-prefix",
        default="ha-ai-local-test",
        help="Delete tokens whose client_name starts with this prefix",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=1,
        help="Number of latest matching tokens to keep",
    )
    parser.add_argument(
        "--export-env",
        action="store_true",
        help="Print HA_TEST_TOKEN=<token> for the newest kept token when available",
    )
    return parser.parse_args()


def _ws_url(base_url: str) -> str:
    return base_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"


def _parse_created_at(value: str | None) -> datetime:
    if not value:
        return datetime.min
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _recv_json(ws: Any) -> dict[str, Any]:
    return json.loads(ws.recv())


def main() -> int:
    args = parse_args()

    if not args.seed_token:
        print("FAIL token-prune: missing token. Set HA_TEST_TOKEN or use --seed-token.")
        return 1

    ws = websocket.create_connection(_ws_url(args.url), timeout=20)
    try:
        first = _recv_json(ws)
        if first.get("type") != "auth_required":
            print(f"FAIL token-prune: unexpected auth handshake: {first}")
            return 1

        ws.send(json.dumps({"type": "auth", "access_token": args.seed_token}))
        second = _recv_json(ws)
        if second.get("type") != "auth_ok":
            print(f"FAIL token-prune: auth failed: {second}")
            return 1

        ws.send(json.dumps({"id": 1, "type": "auth/refresh_tokens"}))
        listed = _recv_json(ws)
        if not listed.get("success"):
            print(f"FAIL token-prune: could not list tokens: {listed}")
            return 1

        tokens = listed.get("result", [])
        matching = [
            t
            for t in tokens
            if t.get("type") == "long_lived_access_token"
            and str(t.get("client_name") or "").startswith(args.client_prefix)
        ]

        matching_sorted = sorted(matching, key=lambda t: _parse_created_at(t.get("created_at")), reverse=True)
        keep = matching_sorted[: max(args.keep, 0)]
        keep_ids = {t.get("id") for t in keep if t.get("id")}
        keep_ids.update({t.get("id") for t in matching_sorted if t.get("is_current")})

        deleted = 0
        for token in matching_sorted:
            token_id = token.get("id")
            if not token_id or token_id in keep_ids:
                continue
            delete_payload = {
                "id": 1000 + deleted,
                "type": "auth/delete_refresh_token",
                "refresh_token_id": token_id,
            }
            ws.send(json.dumps(delete_payload))
            result = _recv_json(ws)
            if result.get("success"):
                deleted += 1
            else:
                print(f"FAIL token-prune: delete failed for {token_id}: {result}")
                return 1

        print(f"PASS token-prune: kept={len(keep)} deleted={deleted} prefix={args.client_prefix}")

        if args.export_env:
            print(f"HA_TEST_TOKEN={args.seed_token}")

        return 0
    finally:
        ws.close()


if __name__ == "__main__":
    sys.exit(main())
