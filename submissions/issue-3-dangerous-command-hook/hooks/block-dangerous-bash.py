#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path


BLOCKED_LOG = Path.home() / ".claude/hooks/blocked.log"


def split_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def flag_has(flag: str, short: str, long: str) -> bool:
    return flag == long or (flag.startswith("-") and not flag.startswith("--") and short in flag[1:])


def is_rm_rf(command: str) -> bool:
    words = split_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue
        flags = words[index + 1 :]
        has_recursive = any(flag_has(flag, "r", "--recursive") or flag_has(flag, "R", "--recursive") for flag in flags)
        has_force = any(flag_has(flag, "f", "--force") for flag in flags)
        if has_recursive and has_force:
            return True
    return bool(re.search(r"(?i)(^|[;&|()]\s*)rm\s+-[a-z]*r[a-z]*f|(^|[;&|()]\s*)rm\s+-[a-z]*f[a-z]*r", command))


def is_force_push(command: str) -> bool:
    words = split_words(command)
    for index in range(len(words) - 2):
        if words[index : index + 2] != ["git", "push"]:
            continue
        push_args = words[index + 2 :]
        if any(arg in {"--force", "-f", "--force-with-lease"} for arg in push_args):
            return True
    return False


def has_drop_table(command: str) -> bool:
    return bool(re.search(r"(?is)\bdrop\s+table\b", command))


def has_truncate(command: str) -> bool:
    return bool(re.search(r"(?is)\btruncate\b", command))


def has_delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if not re.search(r"(?is)\bdelete\s+from\b", statement):
            continue
        if not re.search(r"(?is)\bwhere\b", statement):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    checks = [
        (is_rm_rf, "rm -rf style recursive force deletion"),
        (has_drop_table, "DROP TABLE statement"),
        (is_force_push, "git push force option"),
        (has_truncate, "TRUNCATE statement or command"),
        (has_delete_without_where, "DELETE FROM without WHERE clause"),
    ]
    for checker, reason in checks:
        if checker(command):
            return reason
    return None


def project_path(payload: dict) -> str:
    for key in ("cwd", "project_path"):
        value = payload.get(key)
        if value:
            return str(value)
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def log_blocked(command: str, project: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "attempted_command": command,
        "project_path": project,
        "reason": reason,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {reason}. Rewrite with a safer, explicit command.",
        }
    }
    print(json.dumps(response, sort_keys=True))


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0
    reason = blocked_reason(command)
    if not reason:
        return 0
    log_blocked(command, project_path(payload), reason)
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
