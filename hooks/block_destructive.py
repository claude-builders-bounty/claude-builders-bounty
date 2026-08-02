#!/usr/bin/env python3
"""Deny destructive Bash commands before Claude Code executes them.

The handler follows the Claude Code ``PreToolUse`` command-hook protocol:
input is JSON on stdin and a deny decision is emitted as JSON on stdout.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_RM_PATTERN = re.compile(
    r"(?<![\w-])rm(?:\s+(?:-[A-Za-z]*[rf][A-Za-z]*|--(?:force|recursive))\b)+",
    re.IGNORECASE,
)
_GIT_FORCE_PATTERN = re.compile(
    r"\bgit\b(?P<git_args>[^|;&\n]*)\bpush\b(?P<args>[^|;&\n]*)",
    re.IGNORECASE,
)
_DROP_PATTERN = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
_TRUNCATE_PATTERN = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
_DELETE_PATTERN = re.compile(
    r"\bdelete\s+from\b(?P<body>[^;|&\n]*)", re.IGNORECASE
)


def detect_destructive(command: str) -> str | None:
    """Return a short rule name when *command* matches a blocked pattern."""

    if _RM_PATTERN.search(command):
        return "rm -rf / recursive-force removal"

    git_match = _GIT_FORCE_PATTERN.search(command)
    if git_match and re.search(r"--force(?:-with-lease)?(?:\s|$)", git_match.group("args"), re.I):
        return "git push --force"

    if _DROP_PATTERN.search(command):
        return "DROP TABLE"

    if _TRUNCATE_PATTERN.search(command):
        return "TRUNCATE"

    for match in _DELETE_PATTERN.finditer(command):
        if not re.search(r"\bwhere\b", match.group("body"), re.IGNORECASE):
            return "DELETE FROM without WHERE"

    return None


def _log_path() -> Path:
    configured = os.environ.get("CLAUDE_HOOK_LOG_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".claude" / "hooks" / "blocked.log"


def _write_log(command: str, project_path: str, rule: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "rule": rule,
    }
    path = _log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # A logging failure must not allow a destructive command through.
        pass


def _deny_output(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0

    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return 0

    rule = detect_destructive(command)
    if rule is None:
        return 0

    project_path = payload.get("cwd") or os.getcwd()
    if not isinstance(project_path, str):
        project_path = os.getcwd()
    _write_log(command, project_path, rule)

    reason = (
        f"Blocked destructive Bash command ({rule}): {command!r}. "
        "The attempted command was logged to ~/.claude/hooks/blocked.log."
    )
    print(json.dumps(_deny_output(reason), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
