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


def _collapse_sql(command: str) -> str:
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    command = re.sub(r"--[^\n\r]*", " ", command)
    return re.sub(r"\s+", " ", command).strip()


def _has_rm_rf(command: str) -> bool:
    for match in re.finditer(r"(?<![\w./-])rm\s+((?:-[A-Za-z]+\s+)+)", command):
        flags = "".join(part.lstrip("-") for part in match.group(1).split())
        if "r" in flags and "f" in flags:
            return True
    return False


def _delete_without_where(sql: str) -> bool:
    delete_matches = list(re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE))
    for index, match in enumerate(delete_matches):
        end = delete_matches[index + 1].start() if index + 1 < len(delete_matches) else len(sql)
        statement = sql[match.start() : end].split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def find_block_reason(command: str) -> str | None:
    normalized = _collapse_sql(command)

    if _has_rm_rf(command):
        return "The command uses rm with both recursive and force flags."
    if re.search(r"\bdrop\s+table\b", normalized, flags=re.IGNORECASE):
        return "The command contains DROP TABLE."
    if re.search(r"\btruncate\b", normalized, flags=re.IGNORECASE):
        return "The command contains TRUNCATE."
    if re.search(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\s|=|$)", command, flags=re.IGNORECASE):
        return "The command contains git push --force."
    if _delete_without_where(normalized):
        return "The command contains DELETE FROM without a WHERE clause."

    return None


def _log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    safe_project_path = project_path.replace("\r", "\\r").replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{timestamp}\tproject={safe_project_path}\treason={reason}\tcommand={safe_command}\n"
        )


def _deny(reason: str) -> None:
    message = (
        "Blocked potentially destructive Bash command. "
        f"{reason} Choose a safer command or ask the user for explicit approval."
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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook input JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    _log_block(command, str(project_path), reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
