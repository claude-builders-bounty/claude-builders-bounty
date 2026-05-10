#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks dangerous Bash commands.

Reads Claude Code hook JSON from stdin. If the tool call is a Bash command and the
command matches a destructive pattern, logs the attempt and returns a deny
permission decision. Non-Bash or safe commands exit 0 without output.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

BLOCK_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(r"(^|[;&|`$()\n])\s*rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|- [^\n]*|[^\n]*\s-rf\b|[^\n]*\s-fr\b)", re.IGNORECASE),
        "Recursive forced deletion can destroy project or system files.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE is destructive and should require explicit human review.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\b|=)|\bgit\s+push\b[^\n;|&]*\s-f(?:\b|\s)", re.IGNORECASE),
        "Force-pushing can rewrite shared history.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "TRUNCATE removes table data and should require explicit human review.",
    ),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b|;).)*(?:;|$)", re.IGNORECASE | re.DOTALL),
        "DELETE FROM without a WHERE clause can wipe entire tables.",
    ),
]


def _load_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def _command_from(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict) -> str:
    for key in ("cwd", "project_dir", "workspace", "transcript_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _log_blocked(command: str, project_path: str, rule_name: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "project_path": project_path,
            "rule": rule_name,
            "command": command,
        },
        ensure_ascii=False,
    )
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _deny(reason: str) -> None:
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
    payload = _load_payload()
    if payload.get("tool_name") != "Bash":
        return 0

    command = _command_from(payload)
    if not command:
        return 0

    for rule_name, pattern, explanation in BLOCK_RULES:
        if pattern.search(command):
            project_path = _project_path(payload)
            _log_blocked(command, project_path, rule_name)
            _deny(f"Blocked dangerous Bash command ({rule_name}): {explanation}")
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
