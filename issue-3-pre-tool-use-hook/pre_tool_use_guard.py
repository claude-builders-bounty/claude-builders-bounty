#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: block destructive bash commands.

Reads JSON payload from stdin, extracts attempted command, blocks risky patterns,
logs blocked attempts, and returns a structured decision payload.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any

BLOCK_PATTERNS = [
    (re.compile(r"(^|\s)rm\s+-rf(\s|$)", re.IGNORECASE), "Blocked dangerous command pattern: rm -rf"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "Blocked SQL destructive command: DROP TABLE"),
    (re.compile(r"\bgit\s+push\b[^\n\r;]*\s--force(\s|$)", re.IGNORECASE), "Blocked dangerous git operation: git push --force"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "Blocked SQL destructive command: TRUNCATE"),
]


def _read_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # If payload is non-JSON, treat it as command text directly.
        return {"_raw": raw}
    return data if isinstance(data, dict) else {"value": data}


def _extract_command(payload: dict[str, Any]) -> str:
    candidates: list[str] = []

    # Known/common keys.
    for key in (
        "command",
        "input",
        "tool_input",
        "prompt",
        "text",
    ):
        value = payload.get(key)
        if isinstance(value, str):
            candidates.append(value)
        elif isinstance(value, dict):
            for subkey in ("command", "cmd", "input", "text"):
                subvalue = value.get(subkey)
                if isinstance(subvalue, str):
                    candidates.append(subvalue)

    # Try to find nested command in generic object tree.
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in {"command", "cmd"} and isinstance(v, str):
                    candidates.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)

    raw = payload.get("_raw")
    if isinstance(raw, str):
        candidates.append(raw)

    for cand in candidates:
        cleaned = cand.strip()
        if cleaned:
            return cleaned
    return ""


def _matches_delete_without_where(command: str) -> bool:
    # Block DELETE FROM when no WHERE exists before statement end.
    # Conservative check: analyze each SQL statement split by semicolon/newline.
    statements = re.split(r"[;\n\r]+", command)
    for stmt in statements:
        s = stmt.strip()
        if not s:
            continue
        if re.search(r"\bDELETE\s+FROM\b", s, re.IGNORECASE):
            if not re.search(r"\bWHERE\b", s, re.IGNORECASE):
                return True
    return False


def _blocked_reason(command: str) -> str | None:
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason

    if _matches_delete_without_where(command):
        return "Blocked SQL destructive command: DELETE FROM without WHERE clause"

    return None


def _log_block(command: str, reason: str) -> pathlib.Path:
    log_path = pathlib.Path(os.path.expanduser("~/.claude/hooks/blocked.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    project_path = os.getcwd()
    line = f"{ts}\t{project_path}\t{command}\t{reason}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)
    return log_path


def main() -> int:
    payload = _read_payload()
    command = _extract_command(payload)

    if not command:
        # Allow when no command is available.
        print(json.dumps({"decision": "allow", "message": "No command found in hook payload."}))
        return 0

    reason = _blocked_reason(command)
    if not reason:
        print(json.dumps({"decision": "allow", "message": "Command allowed."}))
        return 0

    log_path = _log_block(command=command, reason=reason)
    message = (
        "Command blocked by pre-tool-use safety hook. "
        f"Reason: {reason}. "
        f"Attempt logged to {log_path}."
    )

    # Structured message for integrations + plain stderr for humans.
    print(json.dumps({"decision": "block", "message": message, "command": command}))
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
