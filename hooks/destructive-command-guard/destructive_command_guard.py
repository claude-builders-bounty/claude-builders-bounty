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


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(
            r"""
            (?<![\w.-])
            rm
            \s+
            (?:
                -[A-Za-z]*[rR][A-Za-z]*[fF][A-Za-z]*
              | -[A-Za-z]*[fF][A-Za-z]*[rR][A-Za-z]*
              | --recursive\s+--force
              | --force\s+--recursive
              | -[rR]\s+-[fF]
              | -[fF]\s+-[rR]
            )
            (?:\s|$)
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        "Recursive forced removal is blocked.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE statements are blocked.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE statements are blocked.",
    ),
    (
        "git push --force",
        re.compile(
            r"""
            (?<![\w.-])
            git
            \s+
            push
            (?:
                (?=[^;&|`$()]*\s(?:--force(?:-with-lease|-if-includes)?|-f)\b)
              | (?=[^;&|`$()]*\s\+[^\s;&|`$()]+)
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        "Forced git pushes are blocked.",
    ),
)


DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def _project_path(payload: dict[str, Any]) -> str:
    return (
        str(payload.get("cwd") or "")
        or str(payload.get("project_dir") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.getcwd()
    )


def _bash_command(payload: dict[str, Any]) -> str | None:
    if payload.get("tool_name") != "Bash":
        return None

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return None

    return command


def _delete_from_without_where(command: str) -> bool:
    for match in DELETE_FROM_RE.finditer(command):
        statement_tail = command[match.end() :]
        statement_tail = re.split(r";|&&|\|\||\n", statement_tail, maxsplit=1)[0]
        if not WHERE_RE.search(statement_tail):
            return True
    return False


def blocked_rules(command: str) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for rule_name, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            matches.append((rule_name, reason))

    if _delete_from_without_where(command):
        matches.append(("DELETE FROM without WHERE", "DELETE FROM without WHERE is blocked."))

    return matches


def log_blocked_attempt(command: str, project_path: str, matches: list[tuple[str, str]]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "attempted_command": command,
        "rules": [name for name, _reason in matches],
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, separators=(",", ":")) + "\n")


def deny(matches: list[tuple[str, str]]) -> None:
    rule_names = ", ".join(name for name, _reason in matches)
    reasons = " ".join(reason for _name, reason in matches)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command ({rule_names}). {reasons} "
                f"Details were logged to {LOG_PATH}."
            ),
        }
    }
    print(json.dumps(output))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict):
        return 0

    command = _bash_command(payload)
    if command is None:
        return 0

    matches = blocked_rules(command)
    if not matches:
        return 0

    log_blocked_attempt(command, _project_path(payload), matches)
    deny(matches)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
