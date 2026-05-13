#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def _strip_wrappers(tokens: list[str]) -> list[str]:
    wrappers = {"sudo", "command", "builtin", "noglob", "time"}
    while tokens and tokens[0] in wrappers:
        tokens = tokens[1:]

    if tokens and tokens[0] == "env":
        tokens = tokens[1:]
        while tokens and ("=" in tokens[0] or tokens[0].startswith("-")):
            tokens = tokens[1:]

    return tokens


def _is_rm_force_recursive(command: str) -> bool:
    tokens = _strip_wrappers(_shell_tokens(command))
    if not tokens or Path(tokens[0]).name != "rm":
        return bool(re.search(r"(^|[;&|]\s*)rm\s+-(?=[A-Za-z]*r)(?=[A-Za-z]*f)[A-Za-z]*\b", command))

    has_recursive = False
    has_force = False
    for token in tokens[1:]:
        if token == "--":
            break
        if not token.startswith("-"):
            continue
        if token in {"--recursive", "--dir"}:
            has_recursive = True
        elif token == "--force":
            has_force = True
        elif token.startswith("--"):
            continue
        else:
            option_chars = token.lstrip("-")
            has_recursive = has_recursive or "r" in option_chars or "R" in option_chars
            has_force = has_force or "f" in option_chars

    return has_recursive and has_force


def _is_force_push(command: str) -> bool:
    tokens = _strip_wrappers(_shell_tokens(command))
    if len(tokens) >= 3 and Path(tokens[0]).name == "git" and tokens[1] == "push":
        return any(
            token == "-f"
            or token.startswith("--force")
            or (token.startswith("-") and "f" in token and not token.startswith("--"))
            for token in tokens[2:]
        )

    return bool(re.search(r"\bgit\s+push\b[^;&|]*\s(?:-f|--force(?:-with-lease)?(?:=|\s|$))", command))


def _sql_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n", command) if part.strip()]


def _has_drop_table(command: str) -> bool:
    return bool(re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE))


def _has_truncate(command: str) -> bool:
    return bool(
        re.search(
            r"\btruncate\s+(?:table\s+)?[`\"'\[]?[A-Za-z_][\w.$`\"'\]]*",
            command,
            flags=re.IGNORECASE,
        )
    )


def _has_delete_without_where(command: str) -> bool:
    for statement in _sql_statements(command):
        match = re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE)
        if match and not re.search(r"\bwhere\b", statement[match.end() :], flags=re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    checks = [
        (_is_rm_force_recursive, "recursive force delete"),
        (_is_force_push, "forced git push"),
        (_has_drop_table, "DROP TABLE statement"),
        (_has_truncate, "TRUNCATE statement"),
        (_has_delete_without_where, "DELETE FROM without WHERE clause"),
    ]

    for predicate, reason in checks:
        if predicate(command):
            return reason
    return None


def _command_from_payload(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or "",
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _deny(reason: str, command: str) -> dict[str, Any]:
    message = (
        f"Blocked Bash command: {reason}. "
        "Review the command manually or replace it with a safer, narrower operation. "
        f"Attempted command: {command}"
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    command = _command_from_payload(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if reason is None:
        return 0

    _log_block(payload, command, reason)
    json.dump(_deny(reason, command), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
