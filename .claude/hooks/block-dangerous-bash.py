#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks dangerous Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional


RM_COMMAND_RE = re.compile(
    r"(^|[;&|(\n])\s*(?:sudo\s+)?(?:command\s+)?rm\b(?P<args>[^;&|\n]*)",
    re.IGNORECASE,
)
GIT_COMMAND_RE = re.compile(
    r"(^|[;&|(\n])\s*(?:sudo\s+)?git\b(?P<args>[^;&|\n]*)",
    re.IGNORECASE,
)
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def shell_words(text: str) -> list[str]:
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def has_rm_rf(command: str) -> bool:
    for match in RM_COMMAND_RE.finditer(command):
        saw_recursive = False
        saw_force = False

        for word in shell_words(match.group("args")):
            if word == "--":
                break
            if not word.startswith("-") or word == "-":
                continue

            if word in {"--recursive", "--dir"} or word.startswith("--recursive="):
                saw_recursive = True
            if word == "--force" or word.startswith("--force="):
                saw_force = True

            if word.startswith("--"):
                continue

            flags = word[1:]
            saw_recursive = saw_recursive or "r" in flags.lower()
            saw_force = saw_force or "f" in flags.lower()

        if saw_recursive and saw_force:
            return True

    return False


def has_git_push_force(command: str) -> bool:
    for match in GIT_COMMAND_RE.finditer(command):
        words = shell_words(match.group("args"))
        if "push" not in words:
            continue

        push_index = words.index("push")
        push_args = words[push_index + 1 :]
        if any(
            word in {"--force", "-f", "--force-with-lease"}
            or word.startswith("--force=")
            or word.startswith("--force-with-lease=")
            for word in push_args
        ):
            return True

    return False


def has_delete_from_without_where(command: str) -> bool:
    for match in DELETE_FROM_RE.finditer(command):
        statement_tail = command[match.end() :].split(";", 1)[0]
        if not WHERE_RE.search(statement_tail):
            return True
    return False


def first_block_reason(command: str) -> Optional[str]:
    checks: list[tuple[str, Callable[[str], bool]]] = [
        ("rm -rf is blocked because it can recursively delete files", has_rm_rf),
        (
            "DROP TABLE is blocked because it can destroy database schema",
            lambda value: bool(DROP_TABLE_RE.search(value)),
        ),
        (
            "TRUNCATE is blocked because it can erase table contents",
            lambda value: bool(TRUNCATE_RE.search(value)),
        ),
        (
            "DELETE FROM without WHERE is blocked because it can erase entire tables",
            has_delete_from_without_where,
        ),
        (
            "git push --force is blocked because it can rewrite shared history",
            has_git_push_force,
        ),
    ]

    for reason, check in checks:
        if check(command):
            return reason
    return None


def project_path(payload: dict) -> str:
    value = (
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
    )
    return str(value or Path.cwd())


def log_blocked_attempt(command: str, reason: str, project: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project,
        "attempted_command": command,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Dangerous command hook could not parse Claude Code input: {exc}", file=sys.stderr)
        return 0

    tool_name = payload.get("tool_name")
    if isinstance(tool_name, str) and tool_name.lower() != "bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = first_block_reason(command)
    if reason is None:
        return 0

    project = project_path(payload)
    try:
        log_blocked_attempt(command, reason, project)
    except OSError as exc:
        print(f"Warning: failed to write blocked command log: {exc}", file=sys.stderr)

    print("Blocked dangerous Bash command.", file=sys.stderr)
    print(f"Reason: {reason}.", file=sys.stderr)
    print(f"Project: {project}", file=sys.stderr)
    print(f"Command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
