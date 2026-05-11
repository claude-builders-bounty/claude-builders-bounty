#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
from typing import Callable, NamedTuple


class BlockRule(NamedTuple):
    name: str
    reason: str
    matches: Callable[[str], bool]


def _regex_matcher(pattern: str) -> Callable[[str], bool]:
    compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    return lambda command: compiled.search(command) is not None


def _delete_without_where(command: str) -> bool:
    """Return true when any DELETE FROM statement lacks a WHERE clause."""
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = command[match.start() :]
        statement = re.split(r"[;\n]", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


BLOCK_RULES: tuple[BlockRule, ...] = (
    BlockRule(
        "rm -rf",
        "The Bash command was blocked because it contains 'rm -rf', which can recursively delete files.",
        _regex_matcher(r"(^|[\s;&|()`])rm\s+-(?=[A-Za-z-]*r)(?=[A-Za-z-]*f)[A-Za-z-]*\b"),
    ),
    BlockRule(
        "DROP TABLE",
        "The Bash command was blocked because it contains 'DROP TABLE', which can destroy database tables.",
        _regex_matcher(r"\bdrop\s+table\b"),
    ),
    BlockRule(
        "git push --force",
        "The Bash command was blocked because 'git push --force' can overwrite shared Git history.",
        _regex_matcher(r"\bgit\s+push\b[^\n;|&]*?(--force(?:\b|=)|-f\b)"),
    ),
    BlockRule(
        "TRUNCATE",
        "The Bash command was blocked because it contains 'TRUNCATE', which can remove table data.",
        _regex_matcher(r"\btruncate\b"),
    ),
    BlockRule(
        "DELETE FROM without WHERE",
        "The Bash command was blocked because it contains 'DELETE FROM without WHERE', which can delete entire tables.",
        _delete_without_where,
    ),
)


def _load_hook_input() -> dict:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return {}

    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


def _bash_command(data: dict) -> str:
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _project_path(data: dict) -> str:
    for key in ("cwd", "project_path", "project_dir", "workspace"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value

    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _log_blocked_attempt(command: str, project_path: str, rule: BlockRule) -> None:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": rule.name,
    }

    with (hooks_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(response))


def main() -> int:
    data = _load_hook_input()

    tool_name = data.get("tool_name")
    if tool_name not in (None, "Bash"):
        return 0

    command = _bash_command(data)
    if not command:
        return 0

    for rule in BLOCK_RULES:
        if rule.matches(command):
            project_path = _project_path(data)
            _log_blocked_attempt(command, project_path, rule)
            _deny(rule.reason)
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
