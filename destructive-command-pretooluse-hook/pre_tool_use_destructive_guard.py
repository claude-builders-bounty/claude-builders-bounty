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


BLOCKED_LOG = Path(
    os.environ.get(
        "CLAUDE_HOOKS_LOG_PATH",
        str(Path.home() / ".claude" / "hooks" / "blocked.log"),
    )
)


class BlockReason:
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


def _casefold_sql(command: str) -> str:
    command = command.replace("\\n", " ")
    return re.sub(r"\s+", " ", command).strip().casefold()


def _split_shell(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _contains_rm_rf(command: str) -> bool:
    tokens = _split_shell(command)
    for i, token in enumerate(tokens):
        if token != "rm":
            continue
        has_recursive = False
        has_force = False
        for flag in tokens[i + 1 :]:
            if flag == "--":
                break
            if not flag.startswith("-") or flag == "-":
                continue
            compact = flag.lstrip("-").casefold()
            has_recursive = has_recursive or "r" in compact
            has_force = has_force or "f" in compact
            if has_recursive and has_force:
                return True
    return False


def _contains_force_push(command: str) -> bool:
    tokens = _split_shell(command)
    for i, token in enumerate(tokens):
        if token != "git":
            continue
        if i + 1 >= len(tokens) or tokens[i + 1] != "push":
            continue
        for flag in tokens[i + 2 :]:
            if flag == "--force-with-lease" or flag.startswith("--force-with-lease="):
                continue
            if flag == "--force" or flag.startswith("--force="):
                return True
            if flag.startswith("-") and not flag.startswith("--") and "f" in flag[1:]:
                return True
    return False


def _delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        lowered = _casefold_sql(statement)
        if re.search(r"\bdelete\s+from\b", lowered) and not re.search(
            r"\bwhere\b", lowered
        ):
            return True
    return False


def find_block_reason(command: str) -> BlockReason | None:
    lowered = _casefold_sql(command)

    if _contains_rm_rf(command):
        return BlockReason(
            "rm-rf",
            "`rm` with both recursive and force flags can permanently delete files.",
        )
    if re.search(r"\bdrop\s+table\b", lowered):
        return BlockReason("drop-table", "`DROP TABLE` destroys database schema/data.")
    if re.search(r"\btruncate(?:\s+table)?\b", lowered):
        return BlockReason("truncate", "`TRUNCATE` removes all rows from a table.")
    if _contains_force_push(command):
        return BlockReason(
            "git-force-push",
            "`git push --force` can overwrite remote history.",
        )
    if _delete_without_where(command):
        return BlockReason(
            "delete-without-where",
            "`DELETE FROM` without a `WHERE` clause can remove every row.",
        )

    return None


def _read_hook_input() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def _extract_command(payload: dict[str, Any]) -> str | None:
    if payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    return command if isinstance(command, str) else None


def _project_path(payload: dict[str, Any]) -> str:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return project_dir
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.getcwd()


def _log_block(payload: dict[str, Any], command: str, reason: BlockReason) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": _project_path(payload),
        "blocked_pattern": reason.code,
        "reason": reason.message,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def _deny(command: str, reason: BlockReason) -> None:
    message = (
        "Destructive Bash command blocked.\n"
        f"Reason: {reason.message}\n"
        f"Command: {command}\n"
        f"Log: {BLOCKED_LOG}"
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


def main() -> int:
    try:
        payload = _read_hook_input()
    except json.JSONDecodeError:
        return 0

    command = _extract_command(payload)
    if command is None:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    try:
        _log_block(payload, command, reason)
    except OSError:
        pass
    _deny(command, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
