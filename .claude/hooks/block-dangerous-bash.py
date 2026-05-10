#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


class BlockReason:
    def __init__(self, pattern: str, detail: str) -> None:
        self.pattern = pattern
        self.detail = detail


def normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def has_delete_from_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command, flags=re.MULTILINE):
        lowered = statement.lower()
        if re.search(r"\bdelete\s+from\b", lowered) and not re.search(
            r"\bwhere\b", lowered
        ):
            return True
    return False


def find_block_reason(command: str) -> BlockReason | None:
    normalized = normalize_command(command)

    checks: list[tuple[str, re.Pattern[str], str]] = [
        (
            "rm -rf",
            re.compile(r"(^|[;&|]\s*)rm\s+(?:-[^\s]*r[^\s]*f|-[^\s]*f[^\s]*r)\b"),
            "Recursive force removal can delete large parts of the project or system.",
        ),
        (
            "DROP TABLE",
            re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
            "DROP TABLE destroys database schema and data.",
        ),
        (
            "TRUNCATE",
            re.compile(r"\btruncate\b", re.IGNORECASE),
            "TRUNCATE removes table contents without row-level review.",
        ),
        (
            "git push --force",
            re.compile(r"\bgit\s+push\b[^\n;]*\s--force(?:\s|=|$)"),
            "Force pushing can overwrite remote history.",
        ),
    ]

    for pattern, regex, detail in checks:
        if regex.search(normalized):
            return BlockReason(pattern, detail)

    if has_delete_from_without_where(command):
        return BlockReason(
            "DELETE FROM without WHERE",
            "DELETE FROM without a WHERE clause can remove every row in a table.",
        )

    return None


def project_path(payload: dict) -> str:
    return (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("PWD")
        or os.getcwd()
    )


def log_path() -> Path:
    try:
        home = Path.home()
    except RuntimeError:
        home = Path(os.getcwd())
    return home / ".claude" / "hooks" / "blocked.log"


def log_block(command: str, payload: dict, reason: BlockReason) -> None:
    blocked_log = log_path()
    blocked_log.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path(payload),
        "pattern": reason.pattern,
        "attempted_command": command,
    }
    with blocked_log.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=True) + "\n")


def deny(command: str, payload: dict, reason: BlockReason) -> int:
    log_block(command, payload, reason)
    message = (
        f"Blocked dangerous Bash command matching {reason.pattern!r}. "
        f"{reason.detail} Use a narrower, reversible command or ask the user "
        "for explicit approval before proceeding."
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
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block-dangerous-bash: invalid hook JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    return deny(command, payload, reason)


if __name__ == "__main__":
    raise SystemExit(main())
