#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash before it runs."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# Whole-token / flag patterns (do not fire on comments-only chatter in other tools).
RM_RF = re.compile(r"(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+(?:[^\n;|&]*\s+)?-[^\n;|&]*r[^\n;|&]*f\b", re.I)
RM_FR = re.compile(r"(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+(?:[^\n;|&]*\s+)?-[^\n;|&]*f[^\n;|&]*r\b", re.I)
DROP_TABLE = re.compile(r"\bDROP\s+TABLE\b", re.I)
TRUNCATE = re.compile(r"\bTRUNCATE\b", re.I)
FORCE_PUSH = re.compile(r"\bgit\s+push\b[^\n]*?(?:--force(?:\s|$|=)|(?<![a-z])-f(?:\s|$))", re.I)
DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.I)
WHERE = re.compile(r"\bWHERE\b", re.I)

RULES = (
    ("rm -rf", lambda cmd: bool(RM_RF.search(cmd) or RM_FR.search(cmd))),
    ("DROP TABLE", lambda cmd: bool(DROP_TABLE.search(cmd))),
    ("git push --force", lambda cmd: bool(FORCE_PUSH.search(cmd))),
    ("TRUNCATE", lambda cmd: bool(TRUNCATE.search(cmd))),
    ("DELETE FROM without WHERE", lambda cmd: bool(DELETE_FROM.search(cmd) and not WHERE.search(cmd))),
)


def extract_command(payload: dict) -> str:
    tool = payload.get("tool_input") or {}
    if isinstance(tool, dict):
        for key in ("command", "cmd", "bash"):
            val = tool.get(key)
            if isinstance(val, str):
                return val
    return ""


def project_path(payload: dict) -> str:
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return str(cwd)


def first_match(command: str) -> str | None:
    for name, pred in RULES:
        if pred(command):
            return name
    return None


def log_block(command: str, path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}\t{reason}\t{path}\t{command.replace(chr(10), ' ')}\n"
    with BLOCKED_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)


def deny(reason: str, command: str) -> None:
    message = (
        f"Blocked by block_destructive hook: {reason}. "
        f"Refusing to run: {command!r}. "
        "Use a safer command (for DELETE, add a WHERE clause; for cleanup, avoid rm -rf)."
    )
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    json.dump(decision, sys.stdout)
    sys.stdout.write("\n")
    print(message, file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    if tool_name and tool_name.lower() not in {"bash", "shell"}:
        return 0

    command = extract_command(payload)
    if not command.strip():
        return 0

    reason = first_match(command)
    if not reason:
        return 0

    path = project_path(payload)
    log_block(command, path, reason)
    deny(reason, command)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
