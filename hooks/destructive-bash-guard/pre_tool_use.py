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


class BlockReason:
    def __init__(self, rule: str, reason: str) -> None:
        self.rule = rule
        self.reason = reason


def _split_shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def _has_rm_recursive_force(command: str) -> bool:
    words = _split_shell_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue
        flags = []
        for candidate in words[index + 1 :]:
            if candidate == "--":
                break
            if not candidate.startswith("-"):
                break
            flags.append(candidate)
        flag_text = "".join(flags)
        if "r" in flag_text.lower() and "f" in flag_text.lower():
            return True

    return bool(
        re.search(r"(?<![\w-])rm\s+-(?:[^\s;|&]*r[^\s;|&]*f|[^\s;|&]*f[^\s;|&]*r)", command)
    )


def _has_git_force_push(command: str) -> bool:
    if not re.search(r"(?<![\w-])git\s+push(?:\s|$)", command):
        return False
    words = _split_shell_words(command)
    for index, word in enumerate(words):
        if word == "git" and index + 1 < len(words) and words[index + 1] == "push":
            push_args = words[index + 2 :]
            return any(
                arg in {"-f", "--force", "--force-with-lease", "--force-if-includes"}
                or arg.startswith("--force=")
                for arg in push_args
            )
    return bool(re.search(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:[=\s]|$)|\s-f(?:\s|$))", command))


def _sql_statements(command: str) -> list[str]:
    return [statement.strip() for statement in re.split(r";+", command) if statement.strip()]


def _delete_without_where(command: str) -> bool:
    for statement in _sql_statements(command):
        match = re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE)
        if not match:
            continue
        tail = statement[match.end() :]
        if not re.search(r"\bwhere\b", tail, flags=re.IGNORECASE):
            return True
    return False


def find_block_reason(command: str) -> BlockReason | None:
    checks = [
        (
            "rm -rf",
            "Recursive forced removal can irreversibly delete project or system files.",
            _has_rm_recursive_force,
        ),
        (
            "git push --force",
            "Force-pushing rewrites remote history and can destroy collaborators' work.",
            _has_git_force_push,
        ),
        (
            "DROP TABLE",
            "DROP TABLE permanently removes a database table.",
            lambda value: bool(re.search(r"\bdrop\s+table\b", value, re.IGNORECASE)),
        ),
        (
            "TRUNCATE",
            "TRUNCATE removes all rows from a table.",
            lambda value: bool(re.search(r"\btruncate\b", value, re.IGNORECASE)),
        ),
        (
            "DELETE FROM without WHERE",
            "DELETE FROM without a WHERE clause can remove every row in a table.",
            _delete_without_where,
        ),
    ]
    for rule, reason, predicate in checks:
        if predicate(command):
            return BlockReason(rule, reason)
    return None


def _project_path(payload: dict[str, Any]) -> str:
    value = (
        payload.get("cwd")
        or payload.get("project_path")
        or payload.get("workspace")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    return str(value)


def log_blocked_attempt(
    payload: dict[str, Any], command: str, block_reason: BlockReason
) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": payload.get("tool_name"),
        "rule": block_reason.rule,
        "reason": block_reason.reason,
        "project_path": _project_path(payload),
        "command": command,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(block_reason: BlockReason) -> None:
    message = (
        f"Blocked destructive Bash command ({block_reason.rule}). "
        f"{block_reason.reason} Review the command manually or replace it with a narrower, reversible operation."
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
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    block_reason = find_block_reason(command)
    if not block_reason:
        return 0

    log_blocked_attempt(payload, command, block_reason)
    deny(block_reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
