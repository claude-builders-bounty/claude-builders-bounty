#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path


HOOK_EVENT_NAME = "PreToolUse"


def _strip_sql_comments(command: str) -> str:
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    return re.sub(r"--[^\n\r]*", " ", command)


def _shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def _contains_rm_rf(command: str) -> bool:
    words = _shell_words(command)
    for index, word in enumerate(words[:-1]):
        if word != "rm":
            continue
        for candidate in words[index + 1 :]:
            if not candidate.startswith("-"):
                break
            flags = candidate.lstrip("-")
            if "r" in flags and "f" in flags:
                return True
    return False


def _contains_force_push(command: str) -> bool:
    words = _shell_words(command)
    if len(words) < 3 or words[0] != "git" or words[1] != "push":
        return False
    return any(
        word == "--force"
        or word.startswith("--force=")
        or word == "--force-with-lease"
        or word.startswith("--force-with-lease=")
        for word in words[2:]
    )


def _delete_from_without_where(command: str) -> bool:
    sql = _strip_sql_comments(command)
    for statement in re.split(r";+", sql):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, flags=re.IGNORECASE
        ):
            return True
    return False


def find_block_reason(command: str) -> str | None:
    if _contains_rm_rf(command):
        return "Blocked rm -rf style recursive force removal."
    if _contains_force_push(command):
        return "Blocked force-push attempt."
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "Blocked DROP TABLE statement."
    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return "Blocked TRUNCATE statement."
    if _delete_from_without_where(command):
        return "Blocked DELETE FROM statement without a WHERE clause."
    return None


def _project_path(payload: dict) -> str:
    return (
        str(payload.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("PWD")
        or os.getcwd()
    )


def _log_block(command: str, project_path: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT_NAME,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = _project_path(payload)
    _log_block(command, project_path, reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
