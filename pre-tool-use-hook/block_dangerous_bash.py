#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks dangerous Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


BLOCK_REASONS = {
    "rm": "Blocked `rm -rf` because recursive force deletes are destructive.",
    "git_push": "Blocked `git push --force` because force-pushing can overwrite shared history.",
    "drop_table": "Blocked `DROP TABLE` because it would destroy database data.",
    "truncate": "Blocked `TRUNCATE` because it would clear table data.",
    "delete_from": "Blocked `DELETE FROM` without a `WHERE` clause because it would delete every row.",
}


def _normalize(command: str) -> str:
    return re.sub(r"\s+", " ", command).strip().lower()


def _has_rm_rf(command: str) -> bool:
    return bool(
        re.search(r"\brm\b\s+(-[^\s]*r[^\s]*f[^\s]*|-f[^\s]*r[^\s]*|-r[^\s]*f[^\s]*)", command)
        or "rm -rf" in command
        or "rm -fr" in command
    )


def _has_git_push_force(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    if len(tokens) < 2 or tokens[0] != "git" or tokens[1] != "push":
        return False

    return "--force" in tokens or "-f" in tokens


def _has_drop_table(command: str) -> bool:
    return "drop table" in command


def _has_truncate(command: str) -> bool:
    return bool(re.search(r"\btruncate\b", command))


def _has_delete_without_where(command: str) -> bool:
    match = re.search(r"\bdelete\s+from\b", command)
    if not match:
        return False
    tail = command[match.end() :]
    return not re.search(r"\bwhere\b", tail)


def _blocked_reason(command: str) -> tuple[str | None, str | None]:
    normalized = _normalize(command)
    if _has_rm_rf(normalized):
        return "rm", BLOCK_REASONS["rm"]
    if _has_git_push_force(normalized):
        return "git_push", BLOCK_REASONS["git_push"]
    if _has_drop_table(normalized):
        return "drop_table", BLOCK_REASONS["drop_table"]
    if _has_truncate(normalized):
        return "truncate", BLOCK_REASONS["truncate"]
    if _has_delete_without_where(normalized):
        return "delete_from", BLOCK_REASONS["delete_from"]
    return None, None


def _log_block(command: str, cwd: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        line = f"{timestamp}\t{cwd}\t{command}\t{reason}\n"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        # Logging should never prevent the hook from blocking a dangerous command.
        pass


def _emit_block(reason: str) -> None:
    payload: Dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return 0

    block_key, reason = _blocked_reason(command)
    if not reason:
        return 0

    cwd = str(payload.get("cwd") or os.getcwd())
    _log_block(command=command, cwd=cwd, reason=reason)
    _emit_block(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
