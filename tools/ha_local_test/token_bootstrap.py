#!/usr/bin/env python3
"""Bootstrap and rotate a long-lived token for local Home Assistant sandbox use."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import requests
import websocket


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap HA sandbox token")
    parser.add_argument("--url", default="http://localhost:8123", help="Home Assistant base URL")
    parser.add_argument("--username", default="sandbox_owner", help="Sandbox owner username")
    parser.add_argument("--password", default="SandboxPass!2026", help="Sandbox owner password")
    parser.add_argument("--name", default="Sandbox Owner", help="Display name for onboarding user")
    parser.add_argument("--client-id", default="http://localhost:8123", help="OAuth client_id")
    parser.add_argument(
        "--client-name",
        default="",
        help="Optional long-lived token client name; defaults to a unique generated name",
    )
    parser.add_argument("--language", default="en", help="Language used during onboarding")
    parser.add_argument("--lifespan", type=int, default=3650, help="Long-lived token lifespan in days")
    parser.add_argument(
        "--seed-token",
        default=os.environ.get("HA_TEST_TOKEN"),
        help="Existing long-lived token used to rotate into a fresh token",
    )
    parser.add_argument(
        "--export-env",
        action="store_true",
        help="Print token as HA_TEST_TOKEN=<token> for shell export",
    )
    return parser.parse_args()


def _http_post_json(url: str, payload: dict[str, Any], timeout: int = 30) -> requests.Response:
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response


def _http_post_form(url: str, payload: dict[str, Any], timeout: int = 30) -> requests.Response:
    response = requests.post(url, data=payload, timeout=timeout)
    response.raise_for_status()
    return response


def _is_user_onboarded(base_url: str) -> bool:
    response = requests.get(f"{base_url}/api/onboarding", timeout=20)
    response.raise_for_status()
    steps = response.json()
    for step in steps:
        if step.get("step") == "user":
            return bool(step.get("done"))
    return False


def _create_onboarding_user(args: argparse.Namespace) -> str:
    payload = {
        "name": args.name,
        "username": args.username,
        "password": args.password,
        "client_id": args.client_id,
        "language": args.language,
    }
    response = _http_post_json(f"{args.url}/api/onboarding/users", payload)
    data = response.json()
    auth_code = data.get("auth_code")
    if not auth_code:
        raise RuntimeError("Onboarding user creation did not return auth_code")
    return auth_code


def _login_flow_auth_code(args: argparse.Namespace) -> str:
    init_payload = {
        "client_id": args.client_id,
        "redirect_uri": args.client_id,
        "handler": ["homeassistant", None],
    }
    init_response = _http_post_json(f"{args.url}/auth/login_flow", init_payload)
    flow_id = init_response.json().get("flow_id")
    if not flow_id:
        raise RuntimeError("Login flow did not return flow_id")

    step_payload = {
        "username": args.username,
        "password": args.password,
        "client_id": args.client_id,
    }
    step_response = _http_post_json(f"{args.url}/auth/login_flow/{flow_id}", step_payload)
    data = step_response.json()

    if isinstance(data.get("errors"), dict) and data["errors"].get("base"):
        raise RuntimeError(f"Login flow failed: {data['errors']['base']}")

    auth_code = data.get("result") or data.get("data", {}).get("code")
    if not auth_code:
        raise RuntimeError("Login flow did not return an authorization code")
    return auth_code


def _exchange_auth_code(args: argparse.Namespace, auth_code: str) -> str:
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": args.client_id,
    }
    response = _http_post_form(f"{args.url}/auth/token", payload)
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Auth token exchange did not return access_token")
    return token


def _create_long_lived_token(args: argparse.Namespace, auth_token: str) -> str:
    client_name = args.client_name or f"ha-ai-local-test-{int(time.time())}"
    ws_url = args.url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
    ws = websocket.create_connection(ws_url, timeout=20)
    try:
        first = json.loads(ws.recv())
        if first.get("type") != "auth_required":
            raise RuntimeError(f"Unexpected websocket pre-auth message: {first}")

        ws.send(json.dumps({"type": "auth", "access_token": auth_token}))
        second = json.loads(ws.recv())
        if second.get("type") != "auth_ok":
            raise RuntimeError(f"Websocket auth failed: {second}")

        ws.send(
            json.dumps(
                {
                    "id": 1,
                    "type": "auth/long_lived_access_token",
                    "client_name": client_name,
                    "lifespan": args.lifespan,
                }
            )
        )
        result = json.loads(ws.recv())
        token = result.get("result")
        if not token:
            raise RuntimeError(f"Long-lived token creation failed: {result}")
        return token
    finally:
        ws.close()


def main() -> int:
    args = parse_args()

    try:
        if args.seed_token:
            long_lived = _create_long_lived_token(args, args.seed_token)
        else:
            if _is_user_onboarded(args.url):
                auth_code = _login_flow_auth_code(args)
            else:
                auth_code = _create_onboarding_user(args)

            access_token = _exchange_auth_code(args, auth_code)
            long_lived = _create_long_lived_token(args, access_token)
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        print(f"FAIL token bootstrap: {exc}")
        if not args.seed_token:
            print("Tip: set HA_TEST_TOKEN to rotate from an existing token on already-initialized sandboxes.")
        return 1

    if args.export_env:
        print(f"HA_TEST_TOKEN={long_lived}")
    else:
        print(long_lived)

    return 0


if __name__ == "__main__":
    sys.exit(main())
