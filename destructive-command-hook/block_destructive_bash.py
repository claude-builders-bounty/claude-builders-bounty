#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _log_path() -> Path:
    home = os.environ.get("HOME")
    base = Path(home) if home else Path.home()
    return base / ".claude" / "hooks" / "blocked.log"


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _strip_sql_comments(command: str) -> str:
    command = re.sub(r"--.*?$", "", command, flags=re.MULTILINE)
    command = re.sub(r"/\*.*?\*/", "", command, flags=re.DOTALL)
    return command


def _delete_without_where(command: str) -> bool:
    sql = _strip_sql_comments(command)
    statements = [part.strip() for part in sql.split(";") if part.strip()]
    for statement in statements:
        normalized = _collapse_whitespace(statement).lower()
        if not re.search(r"\bdelete\s+from\b", normalized):
            continue
        if not re.search(r"\bwhere\b", normalized):
            return True
    return False


def detect_block_reason(command: str) -> str | None:
    checks = [
        (r"(?i)(^|[;&|]\s*)rm\s+(-[A-Za-z]*r[A-Za-z]*f|-[-A-Za-z]*force[-A-Za-z]*recursive|-[-A-Za-z]*recursive[-A-Za-z]*force)\b", "rm -rf recursively deletes files without confirmation"),
        (r"(?i)\bdrop\s+table\b", "DROP TABLE can destroy database schema/data"),
        (r"(?i)\bgit\s+push\b[^\n;&|]*\s(--force|-f)(\s|$)", "force-pushing can overwrite remote history"),
        (r"(?i)\btruncate\b", "TRUNCATE can delete table contents without row-level safeguards"),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command):
            return reason
    if _delete_without_where(command):
        return "DELETE FROM without WHERE can delete every row in a table"
    return None


def _read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _command_from_payload(payload: dict) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict) -> str:
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return str(cwd)


def _log_block(command: str, project_path: str, reason: str) -> None:
    try:
        log_path = _log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        safe_command = command.replace("\n", "\\n")
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"{timestamp}\tproject={project_path}\trule={reason}\tcommand={safe_command}\n"
            )
    except OSError:
        pass


def _deny(reason: str, command: str) -> None:
    message = (
        "Blocked destructive Bash command before execution. "
        f"Reason: {reason}. Command: {command}"
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def _allow() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": "Command passed destructive-command checks.",
                }
            }
        )
    )


def main() -> int:
    payload = _read_payload()
    command = _command_from_payload(payload)
    if not command:
        _allow()
        return 0

    reason = detect_block_reason(command)
    if reason:
        _log_block(command, _project_path(payload), reason)
        _deny(reason, command)
        return 0

    _allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

