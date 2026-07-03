#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _has_rm_rf(command: str) -> bool:
    return bool(
        re.search(
            r"(?is)(?:^|[;&|]\s*)rm\s+(?=[^;&|]*-[^\s;&|]*r)(?=[^;&|]*-[^\s;&|]*f)",
            command,
        )
    )


def _has_force_push(command: str) -> bool:
    return bool(
        re.search(
            r"(?is)\bgit\s+push\b(?:(?![;&|]).)*(?:--force(?:=\S+)?|--force-with-lease|-f\b)",
            command,
        )
    )


def _has_drop_table(command: str) -> bool:
    return bool(re.search(r"(?is)\bdrop\s+table\b", command))


def _has_truncate(command: str) -> bool:
    if re.search(r"(?is)\btruncate\s+-", command):
        return False
    return bool(re.search(r"(?is)\btruncate(?:\s+table)?\s+[a-zA-Z_\"`[]", command))


def _has_delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if re.search(r"(?is)\bdelete\s+from\b", statement) and not re.search(
            r"(?is)\bwhere\b", statement
        ):
            return True
    return False


CHECKS = (
    ("rm -rf", _has_rm_rf),
    ("git push --force", _has_force_push),
    ("DROP TABLE", _has_drop_table),
    ("TRUNCATE", _has_truncate),
    ("DELETE FROM without WHERE", _has_delete_without_where),
)


def destructive_reason(command: str) -> str | None:
    for label, check in CHECKS:
        if check(command):
            return f"Blocked destructive Bash command: matched {label}."
    return None


def _one_line(value: str) -> str:
    return " ".join(value.split())


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    hook_dir = Path.home() / ".claude" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    log_path = hook_dir / "blocked.log"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "reason": reason,
        "command": _one_line(command),
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
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
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook input JSON: {exc}", file=sys.stderr)
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    reason = destructive_reason(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or payload.get("project_path") or "")
    log_blocked_attempt(command, project_path, reason)
    deny(
        f"{reason} The command was not run. Use a safer, scoped command or ask the user "
        "for explicit approval before destructive operations."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
