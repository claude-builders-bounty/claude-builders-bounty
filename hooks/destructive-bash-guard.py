#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads the hook event JSON from stdin. If the event targets the Bash tool and the
command matches a destructive pattern, writes a blocked-attempt log entry to
~/.claude/hooks/blocked.log, prints a JSON block decision, and exits 2.

Normal/non-Bash commands exit 0 without output so ordinary tool use is not
interrupted.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_PATTERNS = [
    (
        "recursive forced removal",
        re.compile(r"(?:^|[;&|()\s])rm\s+(?=[^\n;&|]*-[A-Za-z]*r)(?=[^\n;&|]*-[A-Za-z]*f)", re.I),
        "`rm -rf` can irreversibly delete project or system files.",
    ),
    (
        "DROP TABLE statement",
        re.compile(r"\bdrop\s+table\b", re.I),
        "`DROP TABLE` can permanently remove database tables.",
    ),
    (
        "TRUNCATE statement",
        re.compile(r"\btruncate\b", re.I),
        "`TRUNCATE` can permanently remove all rows from a table.",
    ),
    (
        "forced git push",
        re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b", re.I),
        "forced pushes can rewrite shared Git history.",
    ),
]

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.I)
WHERE_RE = re.compile(r"\bwhere\b", re.I)

def _strip_sql_comments(statement: str) -> str:
    statement = re.sub(r"--.*?(?=\n|$)", " ", statement)
    statement = re.sub(r"/\*.*?\*/", " ", statement, flags=re.S)
    return statement


def _sql_statements(command: str) -> list[str]:
    # Good enough for hook screening: split on semicolons/newlines. We prefer
    # a conservative block over letting a broad DELETE pass.
    return [part.strip() for part in re.split(r"[;\n]", command) if part.strip()]


def blocked_reason(command: str) -> str | None:
    for name, pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return f"Blocked {name}: {reason}"

    for statement in _sql_statements(command):
        cleaned = _strip_sql_comments(statement)
        if DELETE_FROM_RE.search(cleaned) and not WHERE_RE.search(cleaned):
            return "Blocked DELETE FROM without WHERE: this can remove every row in a table."

    return None


def extract_command(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input") or event.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    if isinstance(tool_input, str):
        return tool_input
    value = event.get("command")
    return value if isinstance(value, str) else ""


def is_bash_event(event: dict[str, Any]) -> bool:
    tool_name = str(event.get("tool_name") or event.get("tool") or "")
    if tool_name.lower() == "bash":
        return True
    # Some test harnesses only pass tool_input.command. Treat that as Bash-like.
    return bool(extract_command(event)) and not tool_name


def project_path(event: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "session_path"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def log_block(command: str, path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": path,
        "command": command,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def block(command: str, path: str, reason: str) -> int:
    log_block(command, path, reason)
    message = (
        "Destructive Bash command blocked by destructive-bash-guard. "
        f"{reason} If this is intentional, run it manually after review."
    )
    print(json.dumps({"decision": "block", "reason": message}), file=sys.stdout)
    print(message, file=sys.stderr)
    return 2


def main() -> int:
    try:
        raw = sys.stdin.read().strip()
        event = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        print(f"destructive-bash-guard: invalid hook JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(event, dict) or not is_bash_event(event):
        return 0

    command = extract_command(event)
    reason = blocked_reason(command)
    if reason:
        return block(command, project_path(event), reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
