#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads Claude Code's hook payload from stdin. When the payload targets
the Bash tool, it inspects the command and exits with status 2 if the command is
considered destructive. Claude Code treats exit code 2 from a PreToolUse hook as
a block and shows stderr to the model/user.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("recursive forced remove (rm -rf / rm -fr)", re.compile(r"(^|[;&|]\s*)rm\s+-(?:[^\s-]*r[^\s-]*f|[^\s-]*f[^\s-]*r)\b", re.I)),
    ("DROP TABLE statement", re.compile(r"\bdrop\s+table\b", re.I)),
    ("TRUNCATE statement", re.compile(r"\btruncate\b", re.I)),
    ("force push", re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b", re.I)),
]


DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.I)
WHERE_RE = re.compile(r"\bwhere\b", re.I)


def _extract_command(payload: dict[str, Any]) -> str:
    """Extract the Bash command from common Claude Code hook payload shapes."""

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]

    input_data = payload.get("input")
    if isinstance(input_data, dict) and isinstance(input_data.get("command"), str):
        return input_data["command"]

    if isinstance(payload.get("command"), str):
        return payload["command"]

    return ""


def _strip_sql_comments(command: str) -> str:
    command = re.sub(r"--.*?$", "", command, flags=re.M)
    command = re.sub(r"/\*.*?\*/", "", command, flags=re.S)
    return command


def blocked_reason(command: str) -> str | None:
    """Return the block reason for a command, or None when it is allowed."""

    compact = " ".join(command.strip().split())
    for reason, pattern in PATTERNS:
        if pattern.search(compact):
            return reason

    sql_without_comments = _strip_sql_comments(compact)
    if DELETE_FROM_RE.search(sql_without_comments) and not WHERE_RE.search(sql_without_comments):
        return "DELETE FROM statement without a WHERE clause"

    return None


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "repository"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "project_path": _project_path(payload),
        "reason": reason,
        "command": command,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block-destructive-bash: invalid hook JSON: {exc}", file=sys.stderr)
        return 1

    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    if tool_name and tool_name.lower() != "bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    log_block(payload, command, reason)
    print(
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {reason}\n"
        "If this command is truly intended, rewrite it as a safer, narrower operation "
        "or run it manually after reviewing the risk.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

