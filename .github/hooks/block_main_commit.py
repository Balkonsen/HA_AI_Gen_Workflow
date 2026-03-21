#!/usr/bin/env python3
"""Copilot hook to block `git commit` on main branch in PreToolUse events."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Dict, Optional


def _read_input() -> Dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _find_first_command(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        for key in ("command", "cmd"):
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return value
        for value in obj.values():
            found = _find_first_command(value)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_first_command(item)
            if found:
                return found
    return None


def _find_tool_name(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        for key in ("toolName", "tool_name", "tool"):
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return value
        for value in obj.values():
            found = _find_tool_name(value)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_tool_name(item)
            if found:
                return found
    return None


def _current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def _deny(message: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        },
        "stopReason": message,
        "systemMessage": message,
    }
    print(json.dumps(payload))


def _allow() -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Command allowed by branch policy.",
        }
    }
    print(json.dumps(payload))


def main() -> int:
    event = _read_input()

    tool_name = (_find_tool_name(event) or "").lower()
    command = (_find_first_command(event) or "").strip().lower()

    # Only enforce on terminal/execute tools attempting to commit.
    if "git commit" not in command:
        _allow()
        return 0

    if tool_name and "execute" not in tool_name and "terminal" not in tool_name:
        _allow()
        return 0

    if _current_branch() in {"main", "master"}:
        _deny("Direct commits to main/master are blocked. Create/switch to a feature branch and open a PR.")
        return 2

    _allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
