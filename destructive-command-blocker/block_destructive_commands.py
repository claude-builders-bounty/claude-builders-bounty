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


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def _lower_tokens(command: str) -> list[str]:
    try:
        return [token.lower() for token in shlex.split(command)]
    except ValueError:
        return command.lower().split()


def _is_forced_recursive_rm(command: str) -> bool:
    tokens = _lower_tokens(command)
    if not tokens or tokens[0] != "rm":
        return False

    has_recursive = False
    has_force = False
    for token in tokens[1:]:
        if token == "--":
            break
        if token in {"-r", "-R", "--recursive", "--dir"}:
            has_recursive = True
            continue
        if token in {"-f", "--force"}:
            has_force = True
            continue
        if token.startswith("-") and not token.startswith("--"):
            flags = token[1:]
            has_recursive = has_recursive or "r" in flags or "R" in flags
            has_force = has_force or "f" in flags

    return has_recursive and has_force


def _has_delete_without_where(command: str) -> bool:
    statements = re.split(r";|\n", command, flags=re.IGNORECASE)
    for statement in statements:
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE):
            if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
                return True
    return False


def find_block_reason(command: str) -> str | None:
    """Return a human-readable block reason, or None if the command is allowed."""
    normalized = re.sub(r"\s+", " ", command).strip()

    if _is_forced_recursive_rm(command):
        return "The command uses rm with both recursive and force flags."

    if re.search(r"\bdrop\s+table\b", normalized, flags=re.IGNORECASE):
        return "The command contains a DROP TABLE statement."

    if re.search(r"\btruncate\b", normalized, flags=re.IGNORECASE):
        return "The command contains a TRUNCATE statement."

    if re.search(r"\bgit\s+push\b.*\s--force(?:\s|$|=)", normalized, flags=re.IGNORECASE):
        return "The command attempts to force-push with git push --force."

    if _has_delete_without_where(normalized):
        return "The command contains DELETE FROM without a WHERE clause."

    return None


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _write_block_log(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    safe_project_path = project_path.replace("\n", "\\n")
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{timestamp}\tproject={safe_project_path}\treason={reason}\tcommand={safe_command}\n"
        )


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command: "
                f"{reason} Rewrite the command to use a safer, reversible operation."
            ),
        }
    }
    print(json.dumps(response))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Could not parse Claude Code hook input as JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    _write_block_log(command, _project_path(payload), reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
