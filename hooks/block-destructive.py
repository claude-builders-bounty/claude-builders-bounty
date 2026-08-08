#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rm -rf", re.compile(r"\brm\s+(?:(?:-[A-Za-z]+)\s+)*-rf\b", re.IGNORECASE)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\r\n]*--force(?:-with-lease)?\b", re.IGNORECASE),
    ),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
)
_DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
_WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)


def _command_from_event(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _matched_rule(command: str) -> str | None:
    for label, pattern in _RULES:
        if pattern.search(command):
            return label

    delete_match = _DELETE_FROM.search(command)
    if delete_match and not _WHERE.search(command, delete_match.end()):
        return "DELETE FROM without WHERE"
    return None


def _project_path(event: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "projectPath"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def _log_path() -> Path:
    override = os.environ.get("CLAUDE_HOOK_LOG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def _record_block(event: dict[str, Any], command: str, rule: str) -> None:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": _project_path(event),
        "rule": rule,
    }
    with path.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record, ensure_ascii=False) + "\n")


def _deny(rule: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive command ({rule}). "
                "See ~/.claude/hooks/blocked.log for the recorded attempt."
            ),
        }
    }
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def main() -> int:
    try:
        raw_event = sys.stdin.read()
        event = json.loads(raw_event) if raw_event.strip() else {}
    except (json.JSONDecodeError, TypeError):
        # A malformed event should not interfere with ordinary shell usage.
        return 0

    if not isinstance(event, dict):
        return 0

    command = _command_from_event(event)
    rule = _matched_rule(command)
    if rule is None:
        return 0

    _record_block(event, command, rule)
    _deny(rule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
