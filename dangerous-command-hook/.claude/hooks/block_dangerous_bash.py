#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(r"(^|[;&|()\s])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF][A-Za-z]*|-[A-Za-z]*[fF][A-Za-z]*[rR][A-Za-z]*)(?:\s|$)"),
        "Recursive forced deletion is blocked because it can remove large parts of the project or filesystem.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE is blocked because it can permanently destroy database schema and data.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b(?=[^\n;|&]*\s--force(?:-with-lease)?\b)", re.IGNORECASE),
        "Force pushing is blocked because it can overwrite shared branch history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "TRUNCATE is blocked because it can remove all rows from a table.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?![^;]*\bwhere\b)", re.IGNORECASE | re.DOTALL),
        "DELETE FROM without a WHERE clause is blocked because it can delete every row in a table.",
    ),
]


def load_hook_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        allow_with_warning(f"Could not parse hook input JSON: {exc}")


def allow_with_warning(message: str) -> None:
    print(json.dumps({"systemMessage": message}))
    raise SystemExit(0)


def find_block_reason(command: str) -> tuple[str, str] | None:
    for rule_name, pattern, reason in RULES:
        if pattern.search(command):
            return rule_name, reason
    return None


def write_block_log(command: str, cwd: str, rule_name: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    log_line = f"{timestamp}\tproject={cwd}\trule={rule_name}\tcommand={safe_command}\n"
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(log_line)


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    raise SystemExit(0)


def main() -> None:
    payload = load_hook_input()
    tool_name = payload.get("tool_name")
    command = str(payload.get("tool_input", {}).get("command", ""))
    cwd = str(payload.get("cwd") or os.getcwd())

    if tool_name != "Bash" or not command.strip():
        raise SystemExit(0)

    match = find_block_reason(command)
    if not match:
        raise SystemExit(0)

    rule_name, reason = match
    write_block_log(command=command, cwd=cwd, rule_name=rule_name)
    deny(f"Blocked dangerous Bash command: {rule_name}. {reason}")


if __name__ == "__main__":
    main()
