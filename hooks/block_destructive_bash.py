#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin. If the event is a Bash tool call and the
command matches a destructive pattern, writes a PreToolUse deny decision to stdout
and appends a JSONL audit record to ~/.claude/hooks/blocked.log.

Safe commands exit 0 without output so Claude Code proceeds normally.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable


def log_path() -> Path:
    """Return the Claude Code blocked-command audit log path."""
    return Path.home() / ".claude" / "hooks" / "blocked.log"


RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm-rf",
        re.compile(r"(?is)(?:^|[;&|`$()])\s*rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b"),
        "rm -rf / rm -fr recursively deletes files without confirmation",
    ),
    (
        "drop-table",
        re.compile(r"(?is)\bdrop\s+table\b"),
        "DROP TABLE can permanently remove database schema and data",
    ),
    (
        "git-push-force",
        re.compile(r"(?is)\bgit\s+push\b[^\n;]*?(?:--force(?:-with-lease)?\b|-f\b)"),
        "git push --force can rewrite shared history",
    ),
    (
        "truncate",
        re.compile(r"(?is)\btruncate\b"),
        "TRUNCATE can erase table contents immediately",
    ),
)


def _sql_statements(command: str) -> Iterable[str]:
    """Split a shell command into SQL-ish statements for DELETE FROM checks."""
    # This intentionally stays conservative: split on semicolons/newlines only.
    # If a DELETE FROM appears without WHERE before the next separator, block it.
    for piece in re.split(r"[;\n]", command):
        stripped = piece.strip()
        if stripped:
            yield stripped


def detect_destructive_command(command: str) -> tuple[str, str] | None:
    """Return (rule_id, reason) if command should be denied, otherwise None."""
    for rule_id, pattern, reason in RULES:
        if pattern.search(command):
            return rule_id, reason

    for statement in _sql_statements(command):
        if re.search(r"(?is)\bdelete\s+from\b", statement) and not re.search(r"(?is)\bwhere\b", statement):
            return "delete-without-where", "DELETE FROM without a WHERE clause can erase every row"

    return None


def _project_path(payload: dict[str, Any]) -> str:
    return str(payload.get("cwd") or payload.get("project_path") or os.getcwd())


def log_block(payload: dict[str, Any], command: str, rule_id: str, reason: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "project_path": _project_path(payload),
        "command": command,
        "rule_id": rule_id,
        "reason": reason,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        # Malformed hook input should not brick the user's Claude session.
        print(f"block_destructive_bash.py: invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    match = detect_destructive_command(command)
    if match is None:
        return 0

    rule_id, reason = match
    log_block(payload, command, rule_id, reason)
    deny(
        "Destructive Bash command blocked by PreToolUse hook "
        f"({rule_id}): {reason}. If this action is intentional, ask the user "
        "for explicit approval and use a safer, scoped command."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
