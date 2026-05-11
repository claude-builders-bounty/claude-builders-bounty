#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # If quoting is malformed, still fall back to regex checks below.
        return []


def _contains_forced_recursive_rm(command: str) -> bool:
    tokens = _shell_tokens(command)
    separators = {";", "&&", "||", "|"}

    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        recursive = False
        force = False
        for arg in tokens[index + 1 :]:
            if arg in separators:
                break
            if arg == "--":
                break
            if arg in {"--recursive", "-r", "-R"}:
                recursive = True
                continue
            if arg == "--force" or arg == "-f":
                force = True
                continue
            if arg.startswith("-") and not arg.startswith("--"):
                recursive = recursive or "r" in arg.lower()
                force = force or "f" in arg.lower()

        if recursive and force:
            return True

    # Covers common shell strings that shlex may not split as separate commands,
    # such as command substitutions or compound command bodies.
    return bool(
        re.search(
            r"(?i)(^|[;&|`$()\s])rm\s+(?:(?:-[a-z]*r[a-z]*f[a-z]*)|(?:-[a-z]*f[a-z]*r[a-z]*)|(?:--recursive\s+--force)|(?:--force\s+--recursive)|(?:-r\s+-f)|(?:-f\s+-r))\b",
            command,
        )
    )


def _contains_forced_git_push(command: str) -> bool:
    tokens = _shell_tokens(command)
    separators = {";", "&&", "||", "|"}

    for index in range(len(tokens) - 1):
        if tokens[index] != "git" or tokens[index + 1] != "push":
            continue

        for arg in tokens[index + 2 :]:
            if arg in separators:
                break
            if arg in {"--force", "--force-with-lease", "-f"}:
                return True
            if arg.startswith("--force-with-lease="):
                return True

    return bool(re.search(r"(?i)(^|[;&|`$()\s])git\s+push\b[^;\n]*\s(?:--force(?:-with-lease)?(?:=\S+)?|-f)\b", command))


def _sql_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r";+", command) if part.strip()]


def _should_scan_sql(command: str) -> bool:
    stripped = command.lstrip().lower()
    if stripped.startswith(("drop table", "truncate", "delete from")):
        return True

    sql_clients = {"psql", "mysql", "mariadb", "sqlite3", "duckdb"}
    for token in _shell_tokens(command):
        if Path(token).name.lower() in sql_clients:
            return True

    return False


def _delete_without_where(command: str) -> bool:
    for statement in _sql_statements(command):
        match = re.search(r"(?is)\bdelete\s+from\b", statement)
        if not match:
            continue
        if not re.search(r"(?is)\bwhere\b", statement[match.end() :]):
            return True
    return False


def find_violation(command: str) -> str | None:
    if _contains_forced_recursive_rm(command):
        return "Blocked recursive force deletion (`rm -rf` style command)."
    if _contains_forced_git_push(command):
        return "Blocked forced git push."
    if _should_scan_sql(command):
        if re.search(r"(?is)\bdrop\s+table\b", command):
            return "Blocked SQL `DROP TABLE` statement."
        if re.search(r"(?is)\btruncate\b", command):
            return "Blocked SQL `TRUNCATE` statement."
        if _delete_without_where(command):
            return "Blocked SQL `DELETE FROM` statement without a `WHERE` clause."
    return None


def _write_log(command: str, cwd: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.UTC).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{cwd}\t{reason}\t{command}\n")


def _allow() -> dict[str, Any]:
    return {"continue": True, "suppressOutput": True}


def _deny(reason: str) -> dict[str, Any]:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }


def handle(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "PreToolUse":
        return _allow()
    if payload.get("tool_name") != "Bash":
        return _allow()

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return _allow()

    command = str(tool_input.get("command") or "")
    if not command:
        return _allow()

    violation = find_violation(command)
    if violation is None:
        return _allow()

    cwd = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    _write_log(command, cwd, violation)
    return _deny(violation)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps(_deny(f"Invalid hook JSON input: {exc}")))
        return 0

    print(json.dumps(handle(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
