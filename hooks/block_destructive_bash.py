#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _strip_sql_comments(command: str) -> str:
    command = re.sub(r"--.*?(?=\n|$)", " ", command)
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    return command


def _delete_without_where(command: str) -> bool:
    sql = _strip_sql_comments(command)
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        tail = sql[match.end() :]
        statement = re.split(r";|\n", tail, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    checks: list[tuple[re.Pattern[str], str]] = [
        (
            re.compile(r"(?<!\S)rm\s+(?:-[^\s]*[rR][fF]|-[^\s]*[fF][rR])(?:\s|$)"),
            "rm -rf can recursively delete files without confirmation",
        ),
        (
            re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
            "DROP TABLE can permanently remove database tables",
        ),
        (
            re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|=|$)", re.IGNORECASE),
            "git push --force can overwrite shared history",
        ),
        (
            re.compile(r"\btruncate\b", re.IGNORECASE),
            "TRUNCATE can delete table contents without row-level checks",
        ),
    ]

    for pattern, reason in checks:
        if pattern.search(command):
            return reason

    if _delete_without_where(command):
        return "DELETE FROM without a WHERE clause can remove all matching table rows"

    return None


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{project_path}\t{reason}\t{safe_command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Invalid Claude Code hook input JSON: {error}", file=sys.stderr)
        return 1

    tool_name = payload.get("tool_name")
    command = extract_command(payload)
    if tool_name != "Bash" or not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = (
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_blocked_attempt(command, str(project_path), reason)
    print(
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {reason}\n"
        "Use a safer, scoped command or ask the user to confirm the destructive action.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
