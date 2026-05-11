#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

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
        return command.split()


def _has_rm_rf(command: str) -> bool:
    words = _shell_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue

        flags = ""
        for candidate in words[index + 1 :]:
            if candidate == "--":
                break
            if not candidate.startswith("-"):
                continue
            flags += candidate.lstrip("-")

        if "r" in flags and "f" in flags:
            return True
    return False


def _delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command, flags=re.IGNORECASE):
        if not re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE):
            continue
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def find_block_reason(command: str) -> str | None:
    checks = [
        (_has_rm_rf(command), "rm -rf recursively removes files without confirmation"),
        (
            re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE),
            "DROP TABLE can permanently remove database tables",
        ),
        (
            re.search(r"\btruncate\b", command, flags=re.IGNORECASE),
            "TRUNCATE can remove table data without row-by-row safeguards",
        ),
        (
            re.search(
                r"\bgit\s+push\b(?=[^\n;]*?(?:--force(?:-with-lease)?|\s-f(?:\s|$)))",
                command,
                flags=re.IGNORECASE,
            ),
            "git push --force can overwrite shared branch history",
        ),
        (
            _delete_without_where(command),
            "DELETE FROM without WHERE can remove every row in a table",
        ),
    ]

    for matched, reason in checks:
        if matched:
            return reason
    return None


def _project_path(payload: dict[str, Any]) -> str:
    return str(
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("PWD")
        or Path.cwd()
    )


def _write_block_log(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\r", "\\r").replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp}\tproject={project_path}\treason={reason}\tcommand={safe_command}\n"
        )


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Blocked destructive Bash command: "
                        f"{reason}. Use a narrower, reversible command or ask the user "
                        "for explicit approval."
                    ),
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive_bash_guard: invalid hook JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    project_path = _project_path(payload)
    _write_block_log(command, project_path, reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
