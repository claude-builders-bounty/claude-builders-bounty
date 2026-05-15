#!/usr/bin/env python3
"""Claude Code PreToolUse hook that denies destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockReason:
    rule: str
    message: str


def _normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command).strip()


def _contains_rm_rf(command: str) -> bool:
    return bool(
        re.search(
            r"(?ix)"
            r"(?:^|[;&|()]\s*|(?:sudo|doas|command|env)\s+)"
            r"rm\s+"
            r"(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|(?:-[A-Za-z]+\s+){0,4}-r\s+-f|(?:-[A-Za-z]+\s+){0,4}-f\s+-r)"
            r"(?:\s|$)",
            command,
        )
    )


def _contains_forced_git_push(command: str) -> bool:
    return bool(
        re.search(
            r"(?ix)"
            r"(?:^|[;&|()]\s*)"
            r"git(?:\s+-C\s+\S+)?\s+push\b"
            r"(?:(?![;&|]).)*"
            r"(?:--force(?:-with-lease)?\b|(?:^|\s)-[A-Za-z]*f[A-Za-z]*\b|\s\+\S+)",
            command,
        )
    )


def _contains_drop_table(command: str) -> bool:
    return bool(re.search(r"(?is)\bdrop\s+table\b", command))


def _contains_truncate(command: str) -> bool:
    return bool(re.search(r"(?is)\btruncate(?:\s+table)?\b", command))


def _delete_without_where(command: str) -> bool:
    for match in re.finditer(r"(?is)\bdelete\s+from\b(?P<body>.*?)(?:;|$)", command):
        body = match.group("body")
        if not re.search(r"(?is)\bwhere\b", body):
            return True
    return False


def find_block_reason(command: str) -> BlockReason | None:
    normalized = _normalize_command(command)
    checks = (
        (_contains_rm_rf, "rm -rf", "Recursive forced deletion can permanently remove project or system files."),
        (_contains_forced_git_push, "git push --force", "Force pushing can overwrite remote history for collaborators."),
        (_contains_drop_table, "DROP TABLE", "Dropping tables can permanently destroy database schema and data."),
        (_contains_truncate, "TRUNCATE", "Truncating tables can permanently remove all rows."),
        (_delete_without_where, "DELETE FROM without WHERE", "DELETE FROM without a WHERE clause can remove every row in a table."),
    )
    for check, rule, message in checks:
        if check(normalized):
            return BlockReason(rule=rule, message=message)
    return None


def _command_from_payload(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    return command if isinstance(command, str) else ""


def _project_path_from_payload(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    return env_project or os.getcwd()


def _log_block(payload: dict[str, Any], command: str, reason: BlockReason) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": _project_path_from_payload(payload),
        "rule": reason.rule,
        "message": reason.message,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def _deny_response(reason: BlockReason, command: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Dangerous command blocked by destructive-command-guard.\n"
                f"Rule: {reason.rule}\n"
                f"Reason: {reason.message}\n"
                f"Command: {command}\n"
                f"Log: {LOG_PATH}"
            ),
        }
    }


def handle(payload: dict[str, Any]) -> dict[str, Any] | None:
    command = _command_from_payload(payload)
    if not command:
        return None

    reason = find_block_reason(command)
    if reason is None:
        return None

    _log_block(payload, command, reason)
    return _deny_response(reason, command)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive-command-guard: invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    response = handle(payload)
    if response is not None:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
