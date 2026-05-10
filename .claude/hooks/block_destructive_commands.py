#!/usr/bin/env python3
"""PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # Fall back to whitespace splitting for partially typed or malformed
        # shell snippets so destructive commands are still caught.
        return command.split()


def _has_rm_rf(command: str) -> bool:
    words = _shell_words(command)

    for index, word in enumerate(words):
        if word not in {"rm", "/bin/rm", "sudo"}:
            continue

        rm_index = index
        if word == "sudo" and index + 1 < len(words) and words[index + 1] in {"rm", "/bin/rm"}:
            rm_index = index + 1
        elif word == "sudo":
            continue

        flags = words[rm_index + 1 :]
        has_recursive = False
        has_force = False

        for flag in flags:
            if not flag.startswith("-") or flag == "--":
                break
            has_recursive = has_recursive or "r" in flag.lower() or "R" in flag
            has_force = has_force or "f" in flag.lower()

        if has_recursive and has_force:
            return True

    return False


def _delete_from_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement_tail = command[match.end() :]
        statement_tail = statement_tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement_tail, flags=re.IGNORECASE):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    checks = [
        (_has_rm_rf, "Blocked rm command with both recursive and force flags."),
        (
            lambda value: re.search(r"\bdrop\s+table\b", value, flags=re.IGNORECASE) is not None,
            "Blocked DROP TABLE command.",
        ),
        (
            lambda value: re.search(r"\bgit\s+push\b(?=[^\n;|&]*\s--force(?:\s|=|$))", value, flags=re.IGNORECASE) is not None,
            "Blocked git push --force command.",
        ),
        (
            lambda value: re.search(r"\btruncate\b", value, flags=re.IGNORECASE) is not None,
            "Blocked TRUNCATE command.",
        ),
        (_delete_from_without_where, "Blocked DELETE FROM command without a WHERE clause."),
    ]

    for check, reason in checks:
        if check(command):
            return reason

    return None


def _project_path(payload: dict[str, Any]) -> str:
    return (
        str(payload.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("PWD")
        or os.getcwd()
    )


def _log_blocked(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        deny(f"Could not parse PreToolUse hook input as JSON: {exc}")
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = blocked_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _log_blocked(command, project_path, reason)
    deny(f"{reason} Command was logged to {BLOCKED_LOG}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
