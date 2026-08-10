#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks a small set of destructive commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path(os.environ.get("CLAUDE_HOOK_LOG", "~/.claude/hooks/blocked.log")).expanduser()


def _has_rm_recursive_force(command: str) -> bool:
    """Recognise rm with both recursive and force flags, in either order."""
    for match in re.finditer(r"(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+([^;&|\n]*)", command, re.IGNORECASE):
        args = match.group(1).split()
        flags = {arg[1:].lower() for arg in args if arg.startswith("-") and arg != "--"}
        long_flags = {arg.lower() for arg in args if arg.startswith("--")}
        if ("r" in flags or "R" in flags or any("r" in flag for flag in flags)) and (
            "f" in flags or any("f" in flag for flag in flags) or "--force" in long_flags
        ):
            return True
        if "--recursive" in long_flags and "--force" in long_flags:
            return True
    return False


def reason_for(command: str) -> str | None:
    """Return a human-readable denial reason, or None when the command is safe."""
    if _has_rm_recursive_force(command):
        return "blocked recursive forced removal (rm -r/-R with -f/--force)"
    if re.search(r"(?:^|[;&|]\s*)(?:sudo\s+)?git\s+push\b[^;&|\n]*(?:--force\b|-f(?:\s|$))", command, re.IGNORECASE):
        return "blocked forced git push"
    if re.search(r"(?:^|[;&|]\s*)drop\s+table\b", command, re.IGNORECASE):
        return "blocked DROP TABLE"
    if re.search(r"(?:^|[;&|]\s*)truncate(?:\s+table)?\b", command, re.IGNORECASE):
        return "blocked TRUNCATE"

    # Inspect each SQL statement separately so a later WHERE does not make an
    # earlier unconditional DELETE appear safe.
    for statement in re.split(r"[;\n]", command):
        if re.search(r"^\s*delete\s+from\b", statement, re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, re.IGNORECASE
        ):
            return "blocked DELETE FROM without WHERE"
    return None


def _write_log(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        # A safety hook must not break Claude when an unrelated/malformed event
        # reaches it. The command is allowed because it cannot be inspected.
        return 0

    if payload.get("tool_name") not in (None, "Bash"):
        return 0
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = reason_for(command)
    if reason is None:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    try:
        _write_log(command, project_path, reason)
    except OSError:
        # Still deny the command if the audit log cannot be written.
        pass

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
